# Tài liệu chi tiết: Tính năng IDE mới cho VNOJ

## Tổng quan

Thêm tính năng **IDE kiểu LeetCode** cho từng bài toán trên VNOJ/DMOJ. Khi bật, trang `/problem/<CODE>` chuyển sang giao diện 2 cột: bên trái là đề bài, bên phải là code editor + testcase runner.

---

## 1. Những gì đã làm

### 1.1. Model — Thêm field mới

**File: `judge/models/problem.py`**
```diff
+    enable_new_ide = models.BooleanField(
+        verbose_name=_('Bật giao diện IDE mới'),
+        default=False,
+        help_text=_('Enable the new IDE layout with code editor and custom testcase runner.'),
+    )
```
→ Thêm toggle per-problem để admin bật/tắt IDE mới.

**File: `judge/models/problem_data.py`**
```diff
+    is_sample = models.BooleanField(verbose_name=_('sample testcase?'), default=False)
```
→ Thêm field `is_sample` vào `ProblemTestCase` để đánh dấu testcase nào là sample (hiển thị cho thí sinh).

**File: `judge/migrations/0225_problem_enable_new_ide_problemtestcase_is_sample.py`**
→ Migration thêm 2 field trên vào database.

---

### 1.2. Admin — Cho phép toggle IDE từ admin panel

**File: `judge/admin/problem.py`**
```diff
+        (_('IDE'), {'fields': ('enable_new_ide',)}),
```
→ Thêm fieldset "IDE" trong admin Problem.

**File: `judge/views/problem_data.py`**
```diff
-        fields = ('order', 'type', 'input_file', 'output_file', 'points', 'is_pretest', ...)
+        fields = ('order', 'type', 'input_file', 'output_file', 'points', 'is_pretest', 'is_sample', ...)
```
→ Thêm `is_sample` vào form quản lý test data.

**File: `templates/problem/data.html`**
```diff
+                <th>{{ _('Sample?') }}</th>
...
+                    <td>{{ form.is_sample.errors }}{{ form.is_sample }}</td>
```
→ Hiển thị cột "Sample?" trong bảng quản lý testcase.

---

### 1.3. View — Chuyển template khi `enable_new_ide=True`

**File: `judge/views/problem.py`**
```diff
+    def get_template_names(self):
+        if self.object.enable_new_ide:
+            return ['problem/problem-ide.html']
+        return [self.template_name]
```
→ `ProblemDetail` trả về template IDE nếu bật, ngược lại giữ template gốc.

---

### 1.4. View — Custom Run API (file mới)

**File: `judge/views/custom_run.py`** _(file mới)_

3 view class:

| View | URL | Method | Chức năng |
|------|-----|--------|-----------|
| `CustomRunSubmitView` | `/problem/<code>/custom-run` | POST | Nhận source + language + input, gửi tới judge qua bridge |
| `CustomRunPollView` | `/custom-run/poll/<run_id>` | GET | Poll kết quả từ Redis cache |
| `SampleTestCaseView` | `/problem/<code>/sample-testcases` | GET | Trả về danh sách sample testcase (input + expected output) |

**Logic `CustomRunSubmitView`:**
1. Validate problem access, language, source length
2. Lấy time/memory limit (bao gồm LanguageLimit nếu có)
3. Lấy output_limit từ ProblemData
4. Tạo `run_id = cr_<uuid>`
5. Set cache `custom_run_<run_id>` = `{status: PENDING}` (timeout 300s)
6. Gọi `judge_custom_run()` qua bridge
7. Trả về `{run_id: ...}`

**Logic `SampleTestCaseView`:**
1. Query `ProblemTestCase` where `is_sample=True, type='C'`
2. Đọc input/output file từ zipfile hoặc file storage
3. Trả về JSON `{samples: [{input, output}, ...]}`

---

### 1.5. URL Configuration

**File: `dmoj/urls.py`**
```diff
+from judge.views import custom_run
...
+        path('/custom-run', custom_run.CustomRunSubmitView.as_view(), name='custom_run_submit'),
+        path('/sample-testcases', custom_run.SampleTestCaseView.as_view(), name='sample_testcases'),
...
+    path('custom-run/poll/<str:run_id>', custom_run.CustomRunPollView.as_view(), name='custom_run_poll'),
```

---

### 1.6. Bridge — Xử lý custom-run request

**Luồng dữ liệu:**
```
Browser → Site (POST /custom-run) → judgeapi.py (socket) → Bridge (django_handler.py)
→ judge_list.py (chọn judge) → judge_handler.py (gửi tới judge) → Judge Server (packet.py → judge.py)
→ Kết quả: Judge Server → judge_handler.py → Redis cache → Browser (poll GET /custom-run/poll/<id>)
```

**File: `judge/judgeapi.py`**
```diff
+def judge_custom_run(run_id, language, source, custom_input, time_limit, memory_limit, output_limit=65536):
+    response = judge_request({
+        'name': 'custom-run-request',
+        'run-id': run_id,
+        'language': language,
+        'source': source,
+        'custom-input': custom_input,
+        'time-limit': time_limit,
+        'memory-limit': memory_limit,
+        'output-limit': output_limit,
+    })
+    return response.get('name') == 'custom-run-received'
```

**File: `judge/bridge/django_handler.py`**
```diff
+    'custom-run-request': self.on_custom_run,
...
+    def on_custom_run(self, data):
+        self.judges.custom_run(run_id, language, source, custom_input, ...)
+        return {'name': 'custom-run-received', 'run-id': run_id}
```

**File: `judge/bridge/judge_list.py`**
```diff
+    def custom_run(self, run_id, language, source, custom_input, ...):
+        # Tìm judge rảnh có executor phù hợp
+        available = [judge for judge in self.current_tier_judges()
+                     if not judge.working and not judge.is_disabled and language in judge.executors]
+        if available:
+            judge = min(available, key=lambda judge: (judge.load, random()))
+            judge.custom_run(...)
+        else:
+            cache.set('custom_run_<id>', {status: 'IE', error: 'No judge available'}, timeout=300)
```

**File: `judge/bridge/judge_handler.py`**
```diff
+    'custom-run-result': self.on_custom_run_result,
...
+    def custom_run(self, run_id, ...):
+        self.send({'name': 'custom-run-request', 'submission-id': run_id, ...})
+
+    def on_custom_run_result(self, packet):
+        cache.set('custom_run_<run_id>', result, timeout=300)
```

---

### 1.7. Judge Server — Thực thi custom run

**File: `judge-server/dmoj/packet.py`**
```diff
+        elif name == 'custom-run-request':
+            self.judge.begin_custom_run(
+                run_id=packet['submission-id'],
+                language=packet['language'],
+                source=packet['source'],
+                custom_input=packet['custom-input'],
+                time_limit=float(packet['time-limit']),
+                memory_limit=int(packet['memory-limit']),
+                output_limit=int(packet.get('output-limit', 65536)),
+            )
...
+    def custom_run_result_packet(self, run_id, result: dict):
+        self._send_packet({'name': 'custom-run-result', 'submission-id': run_id, 'result': result})
```

**File: `judge-server/dmoj/judge.py`**
```diff
+    def begin_custom_run(self, run_id, language, source, custom_input, time_limit, memory_limit, output_limit=65536):
+        from subprocess import PIPE as SUBPROCESS_PIPE
+        # 1. Tìm executor cho language
+        # 2. Compile source code
+        # 3. Launch process với stdin=PIPE, stdout=PIPE, stderr=PIPE
+        process = executor.launch(
+            time=time_limit,
+            memory=memory_limit,
+            stdin=SUBPROCESS_PIPE,
+            stdout=SUBPROCESS_PIPE,
+            stderr=SUBPROCESS_PIPE,
+        )
+        # 4. Ghi custom_input vào stdin, đọc stdout + stderr
+        stdout, stderr = process.communicate(input=input_data)
+        # 5. Xác định status (OK/TLE/MLE/OLE/RTE/CE/IE)
+        # 6. Gửi kết quả về bridge
+        self.packet_manager.custom_run_result_packet(run_id, result)
```

---

### 1.8. Template IDE (file mới)

**File: `templates/problem/problem-ide.html`**

Giao diện 2 cột kiểu LeetCode:
- **Trái:** Header (title, meta, links) + Problem statement (dùng `{% include "problem/problem-detail.html" %}` — giữ nguyên markdown rendering gốc với MathJax)
- **Phải:** Toolbar (language select, Run, Submit) + ACE Editor + Bottom panel (Testcase tabs + Result)

**Testcase panel (LeetCode-style):**
- Nhiều tab testcase: `Sample 1`, `Sample 2`, `Case 3`, ...
- Nút `+ Add` để thêm custom testcase
- Nút `×` để xóa custom testcase (sample không xóa được)
- Mỗi tab hiển thị: Input (textarea editable) + Expected Output (nếu là sample)

**Result panel:**
- Status (Accepted/CE/RTE/TLE/MLE/OLE/IE) với màu sắc
- Time + Memory
- Input, Output, Expected Output, Stderr

---

## 2. Các bug đã fix

### Bug 1: `submission_acknowledged_packet` gây crash judge connection

**Vấn đề:** Trong `packet.py` (judge-server), khi nhận `custom-run-request`, code gọi `self.submission_acknowledged_packet()` trước khi xử lý. Packet này gửi `submission-acknowledged` về bridge. Bridge handler `on_submission_acknowledged()` kiểm tra `self._working` (là None cho custom run), thấy mismatch → **đóng kết nối judge** → custom run chết trước khi trả kết quả.

**Fix:** Xóa dòng `self.submission_acknowledged_packet(packet['submission-id'])` khỏi handler `custom-run-request`.

```diff
 elif name == 'custom-run-request':
-    self.submission_acknowledged_packet(packet['submission-id'])
     self.judge.begin_custom_run(...)
```

### Bug 2: `executor.launch()` không tạo pipe cho stdin/stdout

**Vấn đề:** Code ban đầu gọi `executor.launch(stdin=True, stdout=True, stderr=True)`.

Trong `base_executor.py`, method `launch()` có logic:
```python
stdin=stdin if stdin is not None else kwargs.get('stdin'),  # local stdin starts as None
```
Khi không pass explicit kwargs, `kwargs.get('stdin')` trả về `None` → override TracedPopen default `PIPE` → **không tạo pipe** → `communicate()` không ghi được input, không đọc được output.

Khi pass `stdin=True` (=1), TracedPopen kiểm tra `if stdin == PIPE` (PIPE=-1), 1 ≠ -1 → cũng không tạo pipe.

**Fix:** Pass `subprocess.PIPE` (-1) explicitly:
```diff
 process = executor.launch(
     time=time_limit,
     memory=memory_limit,
-    stdin=True,
-    stdout=True,
-    stderr=True,
+    stdin=SUBPROCESS_PIPE,
+    stdout=SUBPROCESS_PIPE,
+    stderr=SUBPROCESS_PIPE,
 )
```

### Bug 3: `communicate(timeout=...)` không hợp lệ

**Vấn đề:** `safe_communicate()` (được assign làm `TracedPopen.communicate`) chỉ nhận `(input, outlimit, errlimit)`, không có parameter `timeout`. Gọi `process.communicate(input=data, timeout=time_limit+5)` sẽ raise `TypeError`.

**Fix:** Bỏ parameter `timeout` (sandbox đã enforce time limit qua `wall_time`):
```diff
-stdout, stderr = process.communicate(input=input_data, timeout=time_limit + 5)
+stdout, stderr = process.communicate(input=input_data)
```

### Bug 4: Template thiếu nút và markdown xấu

**Vấn đề:** Template IDE ban đầu extend `base.html` trực tiếp nhưng không include đủ các links/buttons từ template gốc (`problem.html`), và render markdown bằng cách tự viết HTML thay vì dùng `{% include "problem/problem-detail.html" %}`.

**Fix:** Viết lại template:
- Include `comments/media-css.html` cho CSS
- Dùng `{% include "problem/problem-detail.html" %}` trong div `.content-description` (giữ nguyên markdown rendering gốc + MathJax + cache)
- Include `mathjax-load.html` trong `bodyend` block
- Include `add_code_copy_buttons` cho nút copy code blocks
- Thêm đầy đủ links: My submissions, All submissions, Best submissions, Editorial, Manage tickets, Edit problem, Edit test data, Manage submissions, Clone problem, Report an issue, PDF

---

## 2.5. Nâng cấp Custom Run thành "Fake Submit" (bảo mật + ổn định)

Sau khi phát hiện 5 lỗ hổng so với luồng submit thật, custom run được nâng cấp để hoạt động **giống hệt submit thật** — chỉ khác là không ghi database.

### Lỗ hổng 1: Race condition — judge bị dispatch 2 task cùng lúc

**Vấn đề:** `judge_handler.custom_run()` không set `self._working`. Property `working = bool(self._working)` luôn trả về `False` trong khi đang chạy custom run → `judge_list` thấy judge "free" → có thể dispatch thêm submission/custom-run khác vào cùng judge đang bận.

**Fix — `judge_handler.py`:**
```diff
 def custom_run(self, run_id, ...):
+    self._working = run_id
+    self._no_response_job = threading.Timer(60, self._kill_if_no_response)
+    self._no_response_job.daemon = True
+    self._no_response_job.start()
     self.send({'name': 'custom-run-request', ...})
```

### Lỗ hổng 2: Judge bị "leak" — không bao giờ được free

**Vấn đề:** `on_custom_run_result()` không gọi `_free_self()` → `_working` không bao giờ được clear → judge bị đánh dấu busy mãi mãi → mọi custom run tiếp theo đều nhận "No judge available".

**Fix — `judge_handler.py`:**
```diff
 def on_custom_run_result(self, packet):
+    if self._no_response_job:
+        self._no_response_job.cancel()
+        self._no_response_job = None
     cache.set('custom_run_%s' % run_id, result, timeout=300)
+    self._free_self(packet)
```

### Lỗ hổng 3: Disconnect không cleanup custom run

**Vấn đề:** `on_disconnect()` chỉ handle `Submission.objects.filter(id=self._working)` — nhưng custom run `_working` là string `cr_xxx`, không phải integer DB ID → query crash hoặc không tìm thấy → user poll mãi không có kết quả.

**Fix — `judge_handler.py`:**
```diff
 if self._working:
-    Submission.objects.filter(id=self._working).update(status='IE', ...)
+    if isinstance(self._working, str) and self._working.startswith('cr_'):
+        cache.set('custom_run_%s' % self._working, {'status': 'IE', 'error': 'Judge disconnected...'}, ...)
+    else:
+        Submission.objects.filter(id=self._working).update(status='IE', ...)
```

### Lỗ hổng 4: Custom run không được track trong `submission_map`

**Vấn đề:** `judge_list.custom_run()` không add vào `self.submission_map` → khi judge disconnect, cleanup loop qua `submission_map` không biết custom run đang chạy → không thể recover.

**Fix — `judge_list.py`:**
```diff
 judge = min(available, ...)
+self.submission_map[run_id] = judge
 judge.custom_run(...)
```

### Lỗ hổng 5: `begin_custom_run` chạy trên network thread

**Vấn đề:** `packet.py` gọi `judge.begin_custom_run()` trực tiếp từ network thread (thread đọc packet). Custom run có thể mất vài giây (compile + run) → block network thread → không nhận được ping → bridge nghĩ judge chết → kill connection.

**Fix — `judge.py`:**
```diff
 def begin_custom_run(self, run_id, ...):
+    self._grading_lock.acquire()         # Đảm bảo 1 task/judge như submit thật
+    thread = threading.Thread(
+        target=self._custom_run_thread,  # Chạy trong thread riêng
+        args=(...), daemon=True
+    )
+    thread.start()                       # Trả về ngay, không block network thread

+def _custom_run_thread(self, run_id, ...):
     # compile + run + send result
+    try:
+        self.packet_manager.custom_run_result_packet(run_id, result)
+    finally:
+        self._grading_lock.release()     # Luôn release dù có exception
```

### Bug thêm: `%d` format crash khi free judge

**Vấn đề:** `judge_list.on_judge_free()` dùng `logger.info('Judge available after grading %d: %s', submission, ...)`. Với submit thật `submission` là integer → OK. Với custom run `submission` là string `cr_xxx` → `TypeError: %d format: a number is required` → crash → `_working` không được clear → judge bị leak.

**Fix — `judge_list.py`:**
```diff
-logger.info('Judge available after grading %d: %s', submission, judge.name)
+logger.info('Judge available after grading %s: %s', submission, judge.name)
+# + try/except KeyError cho del submission_map để robust
```

---

## 3. Verify logic

### 3.1. So sánh Custom Run vs Submit thật (sau nâng cấp)

| Aspect | Submit thật | Custom Run (TRƯỚC) | Custom Run (SAU) |
|--------|------------|-------------------|-----------------|
| `_working` set? | ✅ `= submission_id` | ❌ Không | ✅ `= run_id` |
| Timer watchdog? | ✅ 20s | ❌ Không | ✅ 60s |
| Track `submission_map`? | ✅ | ❌ | ✅ |
| Free judge khi xong? | ✅ `_free_self()` | ❌ | ✅ `_free_self()` |
| Disconnect cleanup? | ✅ Set IE in DB | ❌ Crash | ✅ Set IE in cache |
| `_grading_lock`? | ✅ Thread riêng | ❌ Block network thread | ✅ Thread riêng |
| Sandbox (ptrace+seccomp+jail)? | ✅ | ✅ | ✅ |
| Ghi DB? | ✅ | ❌ | ❌ (đúng như thiết kế) |

### 3.2. Luồng Run (đã test thành công)

```
1. User click "▶ Run"
2. JS lấy source + language + input từ active testcase
3. POST /problem/<code>/custom-run → CustomRunSubmitView
4. View set cache PENDING, gọi judge_custom_run()
5. judgeapi.py gửi socket tới bridge (port 9998)
6. django_handler.py nhận, gọi judge_list.custom_run()
7. judge_list chọn judge rảnh, gọi judge_handler.custom_run()
8. judge_handler gửi packet tới judge-server (port 9999)
9. packet.py nhận, gọi judge.begin_custom_run()
10. judge.py: compile → launch(stdin=PIPE, stdout=PIPE, stderr=PIPE) → communicate(input)
11. Xác định status, gửi custom_run_result_packet() về bridge
12. judge_handler.on_custom_run_result() → cache.set() vào Redis
13. JS poll GET /custom-run/poll/<id> → cache.get() → trả kết quả
14. JS hiển thị: status, time, memory, input, output, expected output, stderr
```

**Test thực tế (3 lần chạy liên tiếp):**
```
Run 0: OK '10'   (n+0)
Run 1: OK '11'   (n+1)
Run 2: OK '12'   (n+2)
```
→ Judge được free đúng cách sau mỗi run, không bị leak.

### 3.3. Luồng Submit (không thay đổi)

Submit tạo hidden form POST tới `/problem/<code>/submit` — giống hệt flow cũ.

### 3.4. Sample testcase loading

1. Admin đánh dấu `is_sample=True` cho testcase trong trang data
2. `SampleTestCaseView` query và đọc input/output file
3. JS tự động load thành các tab "Sample 1", "Sample 2", ...
4. Hiển thị Input (editable) + Expected Output (read-only)

---

## 3. Xây lại RUN: Ghost Submission (thay thế toàn bộ Custom Run)

### 3.1. Vấn đề với Custom Run cũ

Custom Run cũ dùng code path riêng biệt hoàn toàn so với Submit: `judge_custom_run()` → bridge `on_custom_run()` → `judge_list.custom_run()` → `judge_handler.custom_run()` → judge-server `begin_custom_run()` → `_custom_run_thread()`. Cách tiếp cận này gây ra **3 lỗi nghiêm trọng không fix được triệt để**:

1. **Lock leak trên judge-server:** `_custom_run_thread()` có các `return` sớm (unsupported language, compile error) mà **bypass** `_grading_lock.release()` trong `finally` block → judge bị lock vĩnh viễn → mọi submission/run tiếp theo bị kẹt
2. **Lần RUN thứ 2 bị treo:** Do lock leak ở trên, lần RUN thứ 1 OK nhưng lần thứ 2 hiện "Waiting for judge..." mãi mãi
3. **Submit sau RUN bị IE:** Judge bị lock → submit mới vào cùng judge → processing mãi → timeout → Internal Error

### 3.2. Giải pháp: Ghost Submission

**Ý tưởng:** RUN = tạo Submission thật trong DB → chạy qua **đúng pipeline của Submit** (`judge_submission()` → bridge → judge-server `begin_grading()` với multiprocessing JudgeWorker) → sau khi có kết quả, lưu vào Redis cache → xóa Submission + SubmissionTestCase khỏi DB.

Cách này **tận dụng 100% infrastructure đã ổn định của Submit**, bao gồm:
- Queuing tự động khi judge bận (qua `judge_list.judge()`)
- Multiprocessing grading (JudgeWorker) — không block network thread
- Lock management đúng cách (qua `_grading_lock` trong `begin_grading()`)
- Tất cả testcase của problem được chạy (không chỉ 1 custom input)

**Cơ chế phát hiện Run submission:** Dùng Redis cache markers:
- `cache.set('run_sub_%d' % submission.id, run_id)` — đánh dấu submission nào là run
- Bridge kiểm tra marker này trong `on_submission_acknowledged()` để set `self._is_run = True`
- Khi `_is_run = True`: skip event posting, skip stats update, collect results → cache, delete from DB

### 3.3. Chi tiết thay đổi

#### View — `judge/views/custom_run.py` (viết lại hoàn toàn)

| View | URL | Method | Chức năng |
|------|-----|--------|-----------|
| `RunSubmitView` | `/problem/<code>/run` | POST | Tạo ghost Submission + SubmissionSource, gọi `judge_submission()`, trả `run_id` |
| `RunPollView` | `/run/poll/<run_id>` | GET | Poll kết quả từ cache + kiểm tra DB status (QU/P/G) |
| `SampleTestCaseView` | `/problem/<code>/sample-testcases` | GET | Không đổi |

**Logic `RunSubmitView`:**
```python
submission = Submission(user=request.profile, problem=prob, language=language, status='QU')
submission.save()
source_obj = SubmissionSource(submission=submission, source=source)
source_obj.save()
run_id = 'run_%s' % uuid.uuid4().hex[:16]
cache.set(run_id, {'sub_id': submission.id, 'status': 'PENDING'}, timeout=600)
cache.set('run_sub_%d' % submission.id, run_id, timeout=600)
judge_submission(submission)  # Exact same function as Submit!
return JsonResponse({'run_id': run_id})
```

#### Bridge — `judge/bridge/judge_handler.py`

Thêm run detection vào tất cả handler:

| Handler | Khi `_is_run = True` |
|---------|---------------------|
| `on_submission_acknowledged()` | Detect via `cache.get('run_sub_%d')`, set `self._is_run` |
| `on_submission_processing()` | Skip `event.post()` |
| `on_grading_begin()` | Skip `event.post()` |
| `on_test_case()` | Save testcases to DB (cần cho `on_grading_end`), skip event posting |
| `on_compile_message()` | Skip `event.post()` |
| `on_grading_end()` | Collect testcase results → cache, delete Submission+TestCases, skip stats |
| `on_compile_error()` | Store CE + error log → cache, delete Submission |
| `on_internal_error()` | Store IE + error message → cache, delete Submission+TestCases |
| `on_submission_terminated()` | Store AB → cache, delete Submission+TestCases |
| `on_disconnect()` | Store IE → cache, delete Submission+TestCases |

**Removed:** `custom_run()` method, `on_custom_run_result()` method, `'custom-run-result'` handler

#### Bridge — `judge/bridge/judge_list.py`

**Removed:** `custom_run_queue`, `_dispatch_queued_custom_run()`, `custom_run()` methods
**Reverted:** `_handle_free_judge()` — dùng `break` thay vì `return` (không cần check custom_run queue)

#### Bridge — `judge/bridge/django_handler.py`

**Removed:** `'custom-run-request'` handler, `on_custom_run()` method

#### Site — `judge/judgeapi.py`

**Removed:** `judge_custom_run()` function

#### Judge Server — `judge-server/dmoj/judge.py` + `judge_update/judge.py`

**Removed:** `begin_custom_run()`, `_custom_run_thread()` methods (đây là nơi chứa bug lock leak gốc)

#### Judge Server — `judge-server/dmoj/packet.py` + `judge_update/packet.py`

**Removed:** `custom-run-request` handling, `custom_run_result_packet()` method

#### URL — `dmoj/urls.py`

```diff
-from judge.views import custom_run
+from judge.views.custom_run import RunSubmitView, RunPollView, SampleTestCaseView
...
-        path('/custom-run', custom_run.CustomRunSubmitView.as_view(), name='custom_run_submit'),
+        path('/run', RunSubmitView.as_view(), name='run_submit'),
...
-    path('custom-run/poll/<str:run_id>', custom_run.CustomRunPollView.as_view(), name='custom_run_poll'),
+    path('run/poll/<str:run_id>', RunPollView.as_view(), name='run_poll'),
```

#### Frontend — `templates/problem/problem-ide.html`

- URL: `custom_run_submit` → `run_submit`, `/custom-run/poll/` → `/run/poll/`
- RUN không gửi `input` nữa (chạy tất cả testcase qua pipeline thật)
- Hiển thị grading status chi tiết: `Queued`, `Processing`, `Grading`
- Kết quả hiển thị: Score (points/total), per-testcase table (status, time, memory, score)
- Hỗ trợ tất cả status: AC, WA, TLE, MLE, RTE, OLE, CE, IE, AB, IR, SC

### 3.4. So sánh RUN mới vs Submit

| Aspect | Submit | RUN (Ghost Submission) |
|--------|--------|----------------------|
| Tạo Submission trong DB? | ✅ Giữ lại | ✅ Tạo tạm, xóa sau khi chấm xong |
| Pipeline chấm | `judge_submission()` → bridge → judge-server `begin_grading()` | **Giống hệt** |
| Queuing khi judge bận? | ✅ Tự động | ✅ Tự động (cùng queue) |
| Multiprocessing (JudgeWorker)? | ✅ | ✅ |
| Lock management? | ✅ Qua `begin_grading()` | ✅ Qua `begin_grading()` |
| Event posting (WebSocket)? | ✅ | ❌ Skip |
| Stats update (user points, problem stats)? | ✅ | ❌ Skip |
| Contest update? | ✅ | ❌ Skip |
| Kết quả lưu ở đâu? | DB (Submission + SubmissionTestCase) | Redis cache (timeout 300s) |
| Hiển thị kết quả | Trang submission detail | IDE Result panel (inline) |

### 3.5. Luồng RUN mới

```
1. User click "▶ Run"
2. JS gửi POST /problem/<code>/run với {source, language}
3. RunSubmitView:
   a. Tạo Submission (status='QU') + SubmissionSource
   b. Set cache markers: run_id → {sub_id, PENDING}, run_sub_{id} → run_id
   c. Gọi judge_submission(submission) — ĐÚNG HÀM CỦA SUBMIT
4. judge_submission() → bridge (port 9998)
5. django_handler → judge_list.judge() — ĐÚNG HÀM CỦA SUBMIT
6. judge_list chọn judge rảnh (hoặc queue nếu bận)
7. judge_handler.submit() — ĐÚNG HÀM CỦA SUBMIT
8. judge-server begin_grading() → JudgeWorker (multiprocessing)
9. Kết quả: test-case-status → on_test_case (save DB, skip events)
10. grading-end → on_grading_end:
    a. Collect testcase results từ DB → cache
    b. Delete SubmissionTestCase + Submission
    c. Skip stats/events
11. JS poll GET /run/poll/<run_id>:
    a. PENDING + grading_status (QU/P/G) → hiện progress
    b. done → hiện bảng kết quả per-testcase
```

---

## 4. Danh sách file đã thay đổi

| File | Loại | Mô tả |
|------|------|-------|
| `judge/models/problem.py` | Modified | +`enable_new_ide` field |
| `judge/models/problem_data.py` | Modified | +`is_sample` field |
| `judge/admin/problem.py` | Modified | +IDE fieldset |
| `judge/views/problem.py` | Modified | +`get_template_names()` |
| `judge/views/problem_data.py` | Modified | +`is_sample` in form |
| `judge/views/custom_run.py` | **New** | 3 API views |
| `judge/judgeapi.py` | Modified | +`judge_custom_run()` |
| `judge/bridge/django_handler.py` | Modified | +`on_custom_run()` |
| `judge/bridge/judge_handler.py` | Modified | +`custom_run()`, +`on_custom_run_result()` |
| `judge/bridge/judge_list.py` | Modified | +`custom_run()` |
| `dmoj/urls.py` | Modified | +3 URL patterns |
| `templates/problem/data.html` | Modified | +Sample? column |
| `templates/problem/problem-ide.html` | **New** | IDE template |
| `judge/migrations/0225_...py` | **New** | Migration |
| `judge-server/dmoj/packet.py` | Modified | +custom-run handler, +result packet |
| `judge-server/dmoj/judge.py` | Modified | +`begin_custom_run()`, +`scoring_mode` |
| `judge_update/packet.py` | Modified | Copy of judge-server |
| `judge_update/judge.py` | Modified | Copy of judge-server |
