# Tính năng IDE mới cho BKDNOJ

## Tổng quan

Thêm giao diện **IDE kiểu LeetCode** cho từng bài trên BKDNOJ. Khi admin bật `enable_new_ide`, trang `/problem/<CODE>` chuyển sang layout 2 cột: trái là đề bài, phải là ACE editor + panel kết quả. Tính năng **RUN** dùng model riêng `RunSubmission` (bảng DB mới), gửi qua pipeline `run-request` độc lập với `submission-request`, kết quả trả về realtime qua **WebSocket (wsevent)**.

---

## 1. Model & Migration

### Migration 0225 — `enable_new_ide` + `is_sample`

**`judge/models/problem.py`**
```python
enable_new_ide = models.BooleanField(
    verbose_name=_('Bật giao diện IDE mới'),
    default=False,
)
```
Toggle per-problem, admin bật/tắt IDE cho từng bài.

**`judge/models/problem_data.py`**
```python
is_sample = models.BooleanField(verbose_name=_('sample testcase?'), default=False)
```
Đánh dấu testcase nào là sample — được hiển thị sẵn trong IDE panel và được chạy khi RUN.

### Migration 0226 — `RunSubmission` (bảng mới)

**`judge/models/run_submission.py`**

Bảng DB riêng biệt, **không** dùng bảng `Submission`. Các field chính:

| Field | Type | Mô tả |
|-------|------|-------|
| `user` | FK Profile | Người chạy |
| `problem` | FK Problem | Bài tập |
| `language` | FK Language | Ngôn ngữ |
| `source` | TextField | Source code (max 65536) |
| `status` | CharField | QU / P / G / D / CE / IE / AB |
| `result` | CharField | AC / WA / TLE / MLE / RTE / OLE / IE / ... |
| `error` | TextField | Compile error log |
| `time` | FloatField | Thời gian chạy tối đa (s) |
| `memory` | FloatField | Memory tối đa (KB) |
| `case_points` | FloatField | Số sample passed |
| `case_total` | FloatField | Tổng số sample |
| `case_results` | JSONField | Per-testcase results list |
| `judged_on` | FK Judge | Judge đã chạy |
| `judged_date` | DateTimeField | Thời điểm chấm xong |

**`id_secret`:** HMAC-SHA512 (key=`EVENT_DAEMON_RUN_KEY`) của `run_id` — dùng làm channel WebSocket `run_<id_secret>`.

---

## 2. Admin & Form

**`judge/admin/problem.py`** — thêm fieldset `IDE` chứa `enable_new_ide`.

**`judge/views/problem_data.py`** — thêm `is_sample` vào form quản lý testcase.

**`templates/problem/data.html`** — thêm cột `Sample?` trong bảng testcase.

---

## 3. View — Chọn template theo toggle

**`judge/views/problem.py`**
```python
def get_template_names(self):
    if self.object.enable_new_ide:
        return ['problem/problem-ide.html']
    return [self.template_name]
```

---

## 4. API Views — `judge/views/run.py`

File mới `judge/views/run.py` (không phải `custom_run.py`):

| View | URL | Method | Chức năng |
|------|-----|--------|-----------|
| `RunSubmitView` | `/problem/<code>/run` | POST | Tạo `RunSubmission`, gọi `judge_run_submission()`, trả `run_id` + `id_secret` |
| `RunPollView` | `/run/poll/<int:run_id>` | GET | Fallback: fetch kết quả từ DB sau khi wsevent báo xong |
| `SampleTestCaseView` | `/problem/<code>/sample-testcases` | GET | Trả JSON sample testcase (input + expected output) |

**Logic `RunSubmitView`:**
- Validate: problem tồn tại, `enable_new_ide=True`, user có quyền, không bị ban, rate limit (đếm cả `RunSubmission` + `Submission` pending).
- Nhận `{source, language, custom_inputs[]}` từ JSON body.
- Kiểm tra `is_sample=True` testcase có tồn tại không.
- Tạo `RunSubmission(status='QU')` → gọi `judge_run_submission(run_sub, sample_input_files, custom_inputs)`.
- Trả `{run_id: <int>, id_secret: <str>}`.

**Logic `RunPollView`:**
- Query `RunSubmission.objects.get(id=run_id, user=request.profile)`.
- Nếu status trong `IN_PROGRESS_GRADING_STATUS` ('QU', 'P', 'G'): trả `{status: 'PENDING', grading_status}`.
- Nếu xong: trả full kết quả gồm `result`, `time`, `memory`, `passed`, `total_cases`, `testcases[]`, `error`.

**Logic `SampleTestCaseView`:** query `ProblemTestCase` với `is_sample=True, type='C'`, đọc từ zipfile hoặc `problem_data_storage`, trả `{samples: [{input, output}]}`.

---

## 5. URL Configuration

**`dmoj/urls.py`**
```python
from judge.views.run import RunSubmitView, RunPollView, SampleTestCaseView
...
# Trong problem URL group:
path('/run',               RunSubmitView.as_view(),    name='run_submit'),
path('/sample-testcases',  SampleTestCaseView.as_view(), name='sample_testcases'),
...
# Global:
path('run/poll/<int:run_id>', RunPollView.as_view(), name='run_poll'),
```

---

## 6. judgeapi — `judge_run_submission()`

**`judge/judgeapi.py`**

```python
def judge_run_submission(run_submission, sample_input_files=None, custom_inputs=None):
    judge_request({
        'name': 'run-request',
        'submission-id': run_submission.id,
        'problem-id': run_submission.problem.code,
        'language': run_submission.language.key,
        'source': run_submission.source,
        'sample-input-files': sample_input_files or [],
        'custom-inputs': custom_inputs or [],
        ...
    })
```
Gửi packet `run-request` (khác với `submission-request`). Bridge trả `run-received`.

---

## 7. Bridge — Luồng RUN

### django_handler.py — nhận `run-request` từ site

```python
def on_run_request(self, data):
    self.judges.judge_run(id, problem, language, source, ..., sample_input_files, custom_inputs)
    return {'name': 'run-received', 'submission-id': id}
```

### judge_list.py — dispatch `run_submit`

Queue entry bao gồm `is_run=True`. `_handle_free_judge()` kiểm tra flag `is_run` để gọi `judge.run_submit()` thay vì `judge.submit()`.

### judge_handler.py — `run_submit()` và `_is_run`

```python
def run_submit(self, id, problem, language, source, sample_input_files, custom_inputs=None):
    self._working = id
    self._is_run = True
    self._run_num_samples = len(data.sample_input_files)
    ...
    self.send({
        'name': 'submission-request',  # Dùng CÙNG packet với submit thật
        'meta': {
            'sample-testcase-only': True,
            'sample-input-files': data.sample_input_files,
            'custom-inputs': custom_inputs or [],
            'run-output-limit': ...,
        },
    })
```

Toàn bộ handler (`on_grading_begin`, `on_test_case`, `on_grading_end`, `on_compile_error`, `on_internal_error`, `on_disconnect`, ...) kiểm tra `self._is_run` để:
- Ghi vào `RunSubmission` thay vì `Submission`.
- Post event lên channel `run_<id_secret>` thay vì `sub_<id_secret>`.
- Skip: stats update, contest update, `event.post` WebSocket cho submission.
- `_on_run_grading_end()`: chỉ tính điểm từ sample cases (first `_run_num_samples`), lưu toàn bộ `case_results` vào `RunSubmission.case_results` JSON field.

---

## 8. Judge Server — `sample-testcase-only`

**`judge_update/judge.py`** (và `judge-server/dmoj/judge.py`):

Khi `meta['sample-testcase-only'] = True`:
1. Lọc `flattened_cases` chỉ giữ case có `input_file` trong `meta['sample-input-files']`.
2. Với `meta['custom-inputs']`: tạo **virtual TestCase in-memory** dùng `MemoryIO(prefill=ci_bytes)` — không ghi disk.
3. Override `output_prefix_length` = `meta['run-output-limit']` để IDE nhận đủ output.

---

## 9. Kết quả — WebSocket + Fallback Poll

**Kênh WebSocket:** `run_<id_secret>` (channel name dùng HMAC secret, không phải run_id số).

**Luồng nhận kết quả trong frontend:**
```
POST /problem/<code>/run
  → nhận {run_id, id_secret}
  → event_dispatcher.on('run_' + id_secret, onRunEvent)

Bridge event.post('run_' + id_secret, {type: ...})  →  wsevent  →  Browser

onRunEvent:
  - 'processing'    → hiển thị "Processing..."
  - 'grading-begin' → hiển thị "Grading..."
  - 'test-case'     → giữ nguyên "Grading..."
  - 'grading-end' / 'compile-error' / 'internal-error' / 'aborted'
      → gọi fetchResult() = GET /run/poll/<run_id>
      → nhận kết quả đầy đủ từ DB → hiển thị
```

`RunPollView` **không** được dùng để poll liên tục — nó chỉ được gọi **1 lần** khi wsevent báo terminal event (done). Đây là HTTP fallback để lấy dữ liệu chi tiết từ DB.

### 9.1. Bug đã fix: Race condition mất event ở lần RUN thứ 2+

**Triệu chứng:** RUN lần đầu OK, RUN lần 2+ (hoặc đổi ngôn ngữ rồi RUN) bị stuck "Running..." mặc dù DB có kết quả.

**Root cause:** Khác với Submit (page reload → WebSocket mới), RUN dùng lại WebSocket trên cùng trang. Daemon `gotMessage()` advance `socket.lastMessage` cho MỌI message kể cả không match filter → khi `set-filter` đến sau 200ms, `messagesCatchUp()` không replay được event đã bị advance qua.

Chi tiết đầy đủ xem **mục 5 trong SUBMIT_RUN_GENSOL_FLOW.md**.

**Fix 1 — `websocket/daemon.js` line 139-144:**
```javascript
// Chỉ advance lastMessage khi message match filter (được gửi cho client)
socket.gotMessage = (message) => {
    if (message.channel in socket.filter) {
        socket.send(JSON.stringify(message));
        socket.lastMessage = message.id;
    }
};
```

**Fix 2 — `resources/event.js` `set_filters()`:**
```javascript
// Gửi set-filter ngay khi WebSocket đã sẵn sàng, chỉ delay khi chưa connect
if (ws ready) { send immediately; }
else { setTimeout(set_filters, 200); }
```

**Tác động hiệu suất:** Không thêm request. Daemon iterate thêm vài message cũ trong queue (max 50) khi `set-filter` — chi phí không đáng kể.

---

## 10. Template IDE

**`templates/problem/problem-ide.html`** — layout 2 cột full-viewport, extend `base.html`.

- **Cột trái:** title, meta (time/memory/IO), language limits, authors, links đầy đủ (My submissions, All submissions, Best submissions, Editorial, Edit problem, Edit test data, ...) + `{% include "problem/problem-detail.html" %}`.
- **Cột phải:** toolbar (language select, ▶ Run, Submit) + ACE Editor + bottom panel.
- **Bottom panel:** Testcase tabs (Sample 1/2/..., nút +Add, ×Delete) + Result panel.
- **Result panel:** grading progress → verdict + score (passed/total) → bảng per-testcase (status, time, memory, output, expected).
- **Draft auto-save:** localStorage per user+problem+language, tự save sau 800ms idle.
- **Language persistence:** Ngôn ngữ đã chọn được lưu vào localStorage (key `ide:<uid>:<problem>:lang`). Khi truy cập lại bài, IDE restore cả code lẫn ngôn ngữ đã lưu.
- **Submit:** tạo hidden form POST sang `/problem/<code>/submit` — giống hệt flow cũ.

---

## 11. Danh sách file đã thay đổi

| File | Loại | Mô tả |
|------|------|-------|
| `judge/models/problem.py` | Modified | + `enable_new_ide` field |
| `judge/models/problem_data.py` | Modified | + `is_sample` field |
| `judge/models/run_submission.py` | **New** | Model `RunSubmission` (bảng DB mới) |
| `judge/migrations/0225_...py` | **New** | Migration cho `enable_new_ide` + `is_sample` |
| `judge/migrations/0226_run_submission.py` | **New** | Migration tạo bảng `RunSubmission` |
| `judge/admin/problem.py` | Modified | + IDE fieldset |
| `judge/views/problem.py` | Modified | + `get_template_names()` |
| `judge/views/problem_data.py` | Modified | + `is_sample` trong form |
| `judge/views/run.py` | **New** | `RunSubmitView`, `RunPollView`, `SampleTestCaseView` |
| `judge/judgeapi.py` | Modified | + `judge_run_submission()` |
| `judge/bridge/django_handler.py` | Modified | + `on_run_request()` handler |
| `judge/bridge/judge_handler.py` | Modified | + `run_submit()`, `_is_run` logic trong tất cả handler, `_on_run_grading_end()` |
| `judge/bridge/judge_list.py` | Modified | + `judge_run()`, `is_run` flag trong queue + dispatch |
| `dmoj/urls.py` | Modified | + `run_submit`, `run_poll`, `sample_testcases` URLs |
| `templates/problem/data.html` | Modified | + cột `Sample?` |
| `templates/problem/problem-ide.html` | **New** | Template IDE 2 cột |
| `websocket/daemon.js` | Modified | Fix `gotMessage()`: chỉ advance `lastMessage` khi match filter |
| `resources/event.js` | Modified | Fix `set_filters()`: gửi ngay khi WS ready thay vì luôn delay 200ms |
| `judge_update/judge.py` | Modified | + `sample-testcase-only` logic, virtual TestCase in-memory |
| `judge_update/packet.py` | Modified | (sync từ judge-server nếu có thay đổi) |
