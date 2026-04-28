# Tính năng IDE + Run cho ALOJ

> **Mục đích file này**: Reference chi tiết cho AI agent khi cần sửa/mở rộng tính năng IDE hoặc Run.
> Đọc file này khi làm việc với: `problem-ide.html`, `run.py`, `run_submission.py`, bridge run handlers, judge sample-testcase filtering.

---

## 1. Tổng quan

Thêm **IDE kiểu LeetCode** cho từng bài toán. Khi admin bật `enable_new_ide=True`, trang `/problem/<CODE>` chuyển sang giao diện 2 cột:
- **Trái**: đề bài (problem statement)
- **Phải**: ACE code editor + testcase tabs + result panel

User có thể **Run** (chạy sample testcases) hoặc **Submit** (nộp bài như thường).

---

## 2. Kiến trúc hiện tại

### 2.1. Hai model riêng biệt

| | Submit | Run |
|---|---|---|
| **Model** | `Submission` + `SubmissionTestCase` | `RunSubmission` (model riêng) |
| **Testcase results** | Mỗi test = 1 row `SubmissionTestCase` | `RunSubmission.case_results` (JSONField, list of dicts) |
| **Ghi DB vĩnh viễn** | ✅ | ✅ (nhưng không ảnh hưởng stats) |
| **Events (WebSocket)** | ✅ `event.post()` | ❌ Skip |
| **Stats/Contest update** | ✅ | ❌ Skip |

### 2.2. Cùng Judge Server packet, khác meta

Cả Submit và Run đều gửi `submission-request` packet tới Judge Server. Khác biệt nằm ở `meta`:

```python
# Submit
{'name': 'submission-request', 'meta': {'pretests-only': ..., 'in-contest': ..., ...}}

# Run
{'name': 'submission-request', 'meta': {'sample-testcase-only': True, 'sample-input-files': [...]}}
```

Judge Server nhận `sample-testcase-only=True` → lọc `flattened_cases` chỉ giữ cases có `config['in']` nằm trong `sample-input-files`.

### 2.3. Bridge phân biệt qua `_is_run` flag

`judge_handler._is_run` được set bởi `run_submit()` (True) hoặc `submit()` (False). Tất cả handler đều check `_is_run`:

| Handler | Khi `_is_run=True` |
|---------|---------------------|
| `on_submission_processing` | Update `RunSubmission.status='P'`, skip event |
| `on_grading_begin` | Update `RunSubmission.status='G'`, clear `_run_test_cases`, skip event |
| `on_test_case` | Append vào `_run_test_cases[]`, update `RunSubmission.current_testcase`, skip event |
| `on_grading_end` | Gọi `_on_run_grading_end()`: tính max time/memory, xác định result, save `case_results` JSON, skip stats |
| `on_compile_error` | Update `RunSubmission` status='CE', skip event |
| `on_compile_message` | Update `RunSubmission.error`, skip event |
| `on_internal_error` | Update `RunSubmission` status='IE', skip event |
| `on_submission_terminated` | Update `RunSubmission` status='AB', skip event |
| `on_disconnect` | Update `RunSubmission` status='IE' |

---

## 3. Chi tiết từng thành phần

### 3.1. Model — `RunSubmission`

**File: `judge/models/run_submission.py`**

```python
class RunSubmission(models.Model):
    STATUS = SUBMISSION_STATUS       # QU, P, G, D, IE, CE, AB
    RESULT = SUBMISSION_RESULT       # AC, WA, TLE, MLE, RTE, CE, IE, OLE
    IN_PROGRESS_GRADING_STATUS = ('QU', 'P', 'G')

    user = models.ForeignKey(Profile)
    problem = models.ForeignKey(Problem)
    date = models.DateTimeField(auto_now_add=True)
    time = models.FloatField(null=True)          # max time across cases
    memory = models.FloatField(null=True)        # max memory across cases
    points = models.FloatField(null=True)        # always 0 for run
    language = models.ForeignKey(Language)
    status = models.CharField(max_length=2)      # QU → P → G → D
    result = models.CharField(max_length=3)      # AC, WA, TLE, etc.
    error = models.TextField(null=True)          # compile errors
    current_testcase = models.IntegerField(default=0)
    batch = models.BooleanField(default=False)
    case_points = models.FloatField(default=0)   # passed count
    case_total = models.FloatField(default=0)    # total count
    judged_on = models.ForeignKey('Judge', null=True)
    judged_date = models.DateTimeField(null=True)
    source = models.TextField(max_length=65536)
    case_results = models.JSONField(default=list)  # [{case, status, time, memory, feedback, output}, ...]
```

**Migration**: `0226_run_submission.py`

### 3.2. Model — Problem fields

**File: `judge/models/problem.py`** — thêm field:
```python
enable_new_ide = models.BooleanField(default=False,
    verbose_name=_('Bật giao diện IDE mới'))
```

**File: `judge/models/problem_data.py`** — thêm field trên `ProblemTestCase`:
```python
is_sample = models.BooleanField(default=False, verbose_name=_('sample testcase?'))
```

**Migration**: `0225_problem_enable_new_ide_problemtestcase_is_sample.py`

### 3.3. View — Template switching

**File: `judge/views/problem.py`**
```python
class ProblemDetail(ProblemMixin, ...):
    template_name = 'problem/problem.html'

    def get_template_names(self):
        if self.object.enable_new_ide:
            return ['problem/problem-ide.html']
        return [self.template_name]
```

### 3.4. View — Run API

**File: `judge/views/run.py`** — 3 view classes:

| View | URL | Method | Logic |
|------|-----|--------|-------|
| `RunSubmitView` | `/problem/<code>/run` | POST | Validate → query sample cases → create `RunSubmission` → `judge_run_submission()` → return `{run_id}` |
| `RunPollView` | `/run/poll/<run_id>` | GET | Query `RunSubmission` by id+user → return status/results JSON |
| `SampleTestCaseView` | `/problem/<code>/sample-testcases` | GET | Query `ProblemTestCase(is_sample=True, type='C')` → read from zipfile/storage → return `{samples: [{input, output}]}` |

**RunSubmitView validation checklist** (same rigor as Submit):
1. Problem exists
2. `enable_new_ide` is True
3. User has access (`is_accessible_by`)
4. User not banned from problem
5. Rate limit: `pending_real + pending_run < DMOJ_SUBMISSION_LIMIT`
6. Valid JSON body with `source` and `language`
7. Source length ≤ 65536
8. Language exists and is allowed for problem
9. At least 1 sample testcase configured

### 3.5. Bridge — judgeapi

**File: `judge/judgeapi.py`** — function `judge_run_submission(run_sub, sample_input_files)`:
- Reset RunSubmission fields (time, memory, points, etc.)
- Send `run-request` packet to bridge with `sample-input-files`
- Bridge receives via `django_handler.on_run_request()` → `judge_list.judge_run()`

### 3.6. Bridge — django_handler

**File: `judge/bridge/django_handler.py`** — handler `on_run_request(data)`:
- Extracts: `submission-id`, `problem-id`, `language`, `source`, `judge-id`, `priority`, `banned-judges`, `sample-input-files`
- Calls `self.judges.judge_run(...)` 
- Returns `{'name': 'run-received', 'submission-id': id}`

### 3.7. Bridge — judge_list

**File: `judge/bridge/judge_list.py`**

Key additions:
- `_key(id, is_run=False)` → returns `('run', id)` if is_run else `id` — prevents collision with Submission IDs
- `judge_run(id, problem, language, source, judge_id, priority, banned_judges, sample_input_files)`:
  - Same logic as `judge()` but calls `judge.run_submit()` instead of `judge.submit()`
  - Uses `_key(id, True)` for tracking
  - Queues with `is_run=True` flag in queue tuple
- `_handle_free_judge(judge)` — dispatches queued items, checks `is_run` flag:
  ```python
  id, problem, language, source, judge_id, banned_judges, is_run, sample_input_files = node.value
  if is_run:
      judge.run_submit(id, problem, language, source, sample_input_files)
  else:
      judge.submit(id, problem, language, source)
  ```
- `on_judge_free(judge, submission)` — uses `_key(submission, judge._is_run)` to clean up, then resets `_is_run=False`
- `remove(judge)` — uses `_key(sub, judge._is_run)` for cleanup

### 3.8. Bridge — judge_handler

**File: `judge/bridge/judge_handler.py`**

Key additions:
- `RunSubmissionData` namedtuple: `(time, memory, user_id, file_only, file_size_limit, sample_input_files)`
- `self._is_run = False` — initialized on connect, set by `run_submit()`/`submit()`
- `self._run_test_cases = []` — accumulates test results during grading

**`run_submit(id, problem, language, source, sample_input_files)`**:
```python
data = self.get_related_run_data(id)        # Query RunSubmission + LanguageLimit + ProblemTestCase
self._working = id
self._is_run = True
self._no_response_job = threading.Timer(20, self._kill_if_no_response)
self._no_response_job.start()
self.send({
    'name': 'submission-request',           # SAME packet name as submit!
    'submission-id': id,
    'scoring-mode': 'partial_testcase',
    'meta': {
        'sample-testcase-only': True,
        'sample-input-files': data.sample_input_files,
    },
})
```

**`_on_run_grading_end(packet)`**:
- Iterates `_run_test_cases` → compute max time/memory, determine worst status
- Count passed (AC) vs total
- Save to `RunSubmission`: status='D', case_results=JSON, case_points=passed, case_total=total

### 3.9. Judge Server — Sample testcase filtering

**File: `judge_update/judge_new_25_04_2025_RUN.py`** (patched `judge.py`, deployed to judge containers)

In the `JudgeWorker` grading loop, after flattening all cases:

```python
sample_testcase_only = self.submission.meta.get('sample-testcase-only', False)
if sample_testcase_only:
    sample_input_files = set(self.submission.meta.get('sample-input-files', []))
    if not sample_input_files:
        yield IPC.GRADING_END, ()
        return
    filtered = []
    for batch_no, case in flattened_cases:
        case_input = case.config['in']
        if case_input and str(case_input) in sample_input_files:
            filtered.append((None, case))  # Remove batch context — sample cases run standalone
    if not filtered:
        yield IPC.GRADING_END, ()
        return
    flattened_cases = filtered
    batch_dependencies = []
```

This removes batch structure for sample cases — they run as independent standalone cases.

### 3.10. Admin

**File: `judge/admin/problem.py`** — added IDE fieldset:
```python
(_('IDE'), {'fields': ('enable_new_ide',)}),
```

**File: `judge/admin/run_submission.py`** — full admin for RunSubmission:
- `RunSubmissionStatusFilter`, `RunSubmissionResultFilter`
- Readonly fields, list display, search

**File: `judge/views/problem_data.py`** — added `is_sample` to testcase form fields

**File: `templates/problem/data.html`** — added "Sample?" column in testcase table

### 3.11. URL Configuration

**File: `dmoj/urls.py`**
```python
from judge.views.run import RunSubmitView, RunPollView, SampleTestCaseView

# Inside problem_url_patterns:
path('/run', RunSubmitView.as_view(), name='run_submit'),
path('/sample-testcases', SampleTestCaseView.as_view(), name='sample_testcases'),

# Top-level:
path('run/poll/<int:run_id>', RunPollView.as_view(), name='run_poll'),
```

### 3.12. Template — problem-ide.html

**File: `templates/problem/problem-ide.html`** — extends `base.html`

Layout structure:
```
.ide-container (flex, 100vh - 60px)
├── .ide-left (flex:1, scrollable)
│   ├── .ide-left-header (title, meta, links)
│   └── .ide-left-body
│       └── {% include "problem/problem-detail.html" %}  ← shared markdown rendering
└── .ide-right (flex:1)
    ├── .ide-toolbar (language select, Run btn, Submit btn)
    ├── .ide-editor-area
    │   └── .ide-editor-wrapper (ACE editor, absolute positioned)
    └── .ide-bottom (max-height:45%)
        ├── .ide-bottom-tabs (Testcase | Result)
        └── .ide-bottom-content
            ├── .ide-panel#testcase-panel
            │   ├── .tc-tabs-bar (Sample 1, Sample 2, +Add)
            │   └── .tc-case-content (textarea input + expected output)
            └── .ide-panel#result-panel
                └── Per-testcase table (status, time, memory)
```

**JavaScript behavior**:
- On load: fetch `/problem/<code>/sample-testcases` → populate tabs
- Run button: POST `/problem/<code>/run` → poll `/run/poll/<id>` every 1s
- Submit button: hidden form POST to `/problem/<code>/submit` (standard flow)
- Poll states: `PENDING` (show grading_status QU/P/G), `done` (show results), error states

---

## 4. Danh sách file thay đổi

| File | Loại | Mô tả |
|------|------|-------|
| `judge/models/problem.py` | Modified | +`enable_new_ide` field |
| `judge/models/problem_data.py` | Modified | +`is_sample` field on ProblemTestCase |
| `judge/models/run_submission.py` | **New** | RunSubmission model |
| `judge/models/__init__.py` | Modified | Import RunSubmission |
| `judge/admin/problem.py` | Modified | +IDE fieldset |
| `judge/admin/run_submission.py` | **New** | RunSubmission admin |
| `judge/admin/__init__.py` | Modified | Register RunSubmissionAdmin |
| `judge/views/problem.py` | Modified | +`get_template_names()` IDE toggle |
| `judge/views/problem_data.py` | Modified | +`is_sample` in form |
| `judge/views/run.py` | **New** | RunSubmitView, RunPollView, SampleTestCaseView |
| `judge/judgeapi.py` | Modified | +`judge_run_submission()` |
| `judge/bridge/django_handler.py` | Modified | +`on_run_request()` handler |
| `judge/bridge/judge_handler.py` | Modified | +`run_submit()`, +`_on_run_grading_end()`, `_is_run` branching in all handlers |
| `judge/bridge/judge_list.py` | Modified | +`judge_run()`, +`_key(id, is_run)`, updated `_handle_free_judge`/`on_judge_free`/`remove` |
| `dmoj/urls.py` | Modified | +3 URL patterns (run, sample-testcases, run/poll) |
| `templates/problem/data.html` | Modified | +Sample? column |
| `templates/problem/problem-ide.html` | **New** | IDE template (CSS + HTML + JS) |
| `judge/migrations/0225_...py` | **New** | Migration: enable_new_ide + is_sample |
| `judge/migrations/0226_run_submission.py` | **New** | Migration: RunSubmission model |
| `judge_update/judge_new_25_04_2025_RUN.py` | **New** | Patched judge.py with sample-testcase-only filtering |

---

## 5. Lịch sử phát triển & Bugs đã fix

### Giai đoạn 1: Custom Run (đã BỎ)

Ban đầu thử cách tiếp cận **custom-run-request**: tạo packet type mới `custom-run-request`, code path riêng từ `judge_custom_run()` → bridge `on_custom_run()` → `judge_list.custom_run()` → `judge_handler.custom_run()` → judge-server `begin_custom_run()` → `_custom_run_thread()`. Kết quả lưu Redis cache.

**Lý do bỏ**: Code path riêng gây 3 lỗi không fix triệt để:
1. **Lock leak**: `_custom_run_thread()` có early `return` bypass `_grading_lock.release()` → judge bị lock vĩnh viễn
2. **Lần Run thứ 2 treo**: Do lock leak, judge bận mãi
3. **Submit sau Run bị IE**: Judge locked → submission timeout

### Giai đoạn 2: Ghost Submission (đã BỎ)

Thử tạo `Submission` thật trong DB → chạy qua pipeline Submit → sau khi có kết quả, lưu vào Redis cache → xóa Submission. Dùng Redis cache markers để bridge detect run submission.

**Lý do bỏ**: Phức tạp, race conditions khi xóa Submission, cache markers không reliable.

### Giai đoạn 3: RunSubmission model (HIỆN TẠI) ✅

Tạo model `RunSubmission` riêng biệt. Gửi cùng `submission-request` packet nhưng thêm meta `sample-testcase-only`. Bridge phân biệt qua `_is_run` flag (set bởi `run_submit()` vs `submit()`).

**Ưu điểm**:
- Tái sử dụng 100% judge infrastructure (JudgeWorker, multiprocessing, sandbox)
- Không ảnh hưởng pipeline Submit
- Không cần Redis cache — kết quả lưu DB
- Bridge handlers đơn giản: chỉ check `if self._is_run` → write RunSubmission thay vì Submission
- Judge queuing/dispatch hoạt động bình thường (cùng queue, phân biệt qua `_key`)

### Bugs đã fix trong quá trình phát triển

| Bug | Vấn đề | Fix |
|-----|--------|-----|
| `submission_acknowledged` crash | `self.submission_acknowledged_packet()` trong custom-run handler gây bridge đóng connection | Bỏ dòng đó (custom-run không cần acknowledge) |
| `executor.launch()` không tạo pipe | Pass `stdin=True` (=1) ≠ `PIPE` (=-1) → không tạo pipe | Pass `subprocess.PIPE` explicitly |
| `communicate(timeout=...)` TypeError | `safe_communicate()` không có param `timeout` | Bỏ `timeout` (sandbox enforce wall_time) |
| Race condition judge dispatch | `_working` không được set cho custom run → judge bị dispatch 2 task | Set `_working = run_id` |
| Judge leak (never freed) | `on_custom_run_result()` không gọi `_free_self()` | Gọi `_free_self(packet)` |
| Disconnect crash | `_working` là string `cr_xxx` nhưng code dùng `Submission.objects.filter(id=...)` | Check `isinstance(self._working, str)` |
| `%d` format crash | `logger.info('Judge available after grading %d: %s', submission, ...)` với string submission | Đổi `%d` → `%s` |
| Template markdown rendering | Tự viết HTML thay vì dùng template gốc | Dùng `{% include "problem/problem-detail.html" %}` |

> Tất cả bugs trên đều thuộc giai đoạn Custom Run/Ghost Submission (đã bỏ). Giai đoạn RunSubmission model hiện tại không có các bugs này vì tái sử dụng pipeline có sẵn.

---

## 6. Hướng dẫn cho AI agent

### Khi cần sửa Run feature

1. **View logic** → `judge/views/run.py`
2. **Model fields** → `judge/models/run_submission.py`
3. **Bridge routing** → `judge/bridge/django_handler.py` (on_run_request) → `judge_list.py` (judge_run) → `judge_handler.py` (run_submit, _is_run handlers)
4. **Judge-side filtering** → `judge_update/judge_new_25_04_2025_RUN.py` (sample-testcase-only logic)
5. **Frontend** → `templates/problem/problem-ide.html` (CSS + JS inline)
6. **URLs** → `dmoj/urls.py`

### Khi cần thêm tính năng vào Run

- Nếu thêm field vào RunSubmission → cần migration + update `_on_run_grading_end()` trong judge_handler
- Nếu thay đổi packet meta → cần update cả `run_submit()` (bridge) và `judge_new_25_04_2025_RUN.py` (judge)
- Nếu thay đổi kết quả trả về → update `RunPollView.get()` + frontend JS poll handler

### QUAN TRỌNG: Deploy judge changes

Judge Server chạy trong container riêng (`judge01`–`judge04`). Thay đổi judge-side cần:
1. Sửa file trong `judge_update/`
2. Copy vào container: `docker cp judge_update/judge_new_25_04_2025_RUN.py judge01:/judge/dmoj/judge.py`
3. Restart judge: `docker restart judge01`
4. Lặp lại cho mỗi judge container

### Build & deploy site changes

```bash
cd /home/algoritonlinejudge/aloj-docker/dmoj && \
docker compose exec site bash -c "cd /site && bash make_style.sh 2>&1 | tail -3 && python manage.py collectstatic --noinput 2>&1 | tail -2" && \
docker compose restart site 2>&1 | tail -2
```

Nếu thay đổi bridge: `docker compose restart bridged`
Nếu thay đổi model: `docker compose exec site python manage.py migrate`
