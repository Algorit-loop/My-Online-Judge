# BÁO CÁO REVIEW CODE — BKDN Online Judge (ALOJ)
## Phần I — Phân tích theo chủ đề / vấn đề

> **Phạm vi:** repo `Algorit-loop/BKDN-Online-Judge`, nhánh `master`.
> Chỉ review **từ commit thứ 2 trở đi** (commit đầu tiên `70f62ef "update stogare + credit"` là code nền, bỏ qua).
> Tổng cộng **83 commit** được xét, trải từ 27/03/2026 → 28/06/2026.
> Nền tảng gốc là **VNOJ/DMOJ** (Django + trình chấm bridge + WebSocket event daemon). Các thay đổi của bạn xoay quanh việc "Việt hoá" thành ALOJ/BKDNOJ và bổ sung các tính năng lớn: **IDE chạy thử (RUN), chấm partial theo testcase, các tính năng AI (tạo đề, sinh testcase, review code, gợi ý tag), khoá tập trung khi thi (Contest Focus Lock)**.

---

## Mục lục
1. [Kiến trúc tổng thể — để hiểu các vấn đề bên dưới](#1)
2. [NHÓM A — Bảo mật (nghiêm trọng)](#a)
3. [NHÓM B — Cơ chế chấm điểm (scoring)](#b)
4. [NHÓM C — Luồng RUN / IDE và realtime WebSocket](#c)
5. [NHÓM D — Tính năng AI](#d)
6. [NHÓM E — Contest (thi đấu)](#e)
7. [NHÓM F — Migration & tính nhất quán DB](#f)
8. [Tổng hợp mức độ ưu tiên & checklist](#g)

---

<a id="1"></a>
## 1. Kiến trúc tổng thể

Trước khi đi vào từng vấn đề, cần nắm 5 thành phần vì gần như mọi vấn đề đều nằm trong một trong số đó:

- **Site (Django/uWSGI):** xử lý HTTP, form, view, template Jinja2. Đây là nơi bạn viết phần lớn code.
- **Bridge (`judge/bridge/*.py`):** cầu nối TCP giữa Django và các máy chấm (judge server). File trung tâm là `judge_handler.py` — nhận packet `grading-end`, `test-case`, `compile-error`… rồi cập nhật DB. Đây là nơi tính điểm cuối cùng.
- **Judge server (`judge_update/*.py`):** code chấm thực tế (bản của bạn nằm trong thư mục `judge_update/`, sync tay sang máy chấm).
- **wsevent (WebSocket daemon, `websocket/daemon.js`):** đẩy sự kiện realtime (submission update, run result) xuống trình duyệt. Có cơ chế "catch-up" replay các message bị lỡ.
- **Celery + Redis + MariaDB:** hàng đợi tác vụ nền (rescore, on_new_problem…), cache, và CSDL.

Một "submission" đi qua chuỗi: `Site (lưu DB, QU) → Bridge → Judge → Bridge (grading-end, tính điểm) → DB (D) → wsevent → trình duyệt`. Hiểu chuỗi này thì các bug ở nhóm B và C sẽ rõ ngay.

---

<a id="a"></a>
## 2. NHÓM A — BẢO MẬT (đây là nhóm cần xử lý gấp nhất)

### A1. Secrets bị commit thẳng vào Git — **NGHIÊM TRỌNG, đang tồn tại ở HEAD**

**Thành phần:** file cấu hình `dmoj/config/local_settings.py` và bản copy `dmoj/repo/dmoj/local_settings.py`.

**Vấn đề là gì:** Commit thứ 2 (`8fc54e1`) hard-code một loạt bí mật thật vào repo public:
```python
SECRET_KEY = os.environ.get('SECRET_KEY', 'algoritxxx-secret-key')
EMAIL_HOST_USER = 'nguyenducnha10022004@gmail.com'
EMAIL_HOST_PASSWORD = 'wmsy vhzm vpux nojp'   # Gmail App Password thật
```
Sau đó các commit về tính năng RUN/AI còn thêm nhiều khoá HMAC/mã hoá vào `settings.py` (đã version-control):
```python
EVENT_DAEMON_SUBMISSION_KEY = '6Sdmkx^%pk@...'
EVENT_DAEMON_RUN_KEY        = 'R#kP9$mQ!xZ5vLw@...'
EVENT_DAEMON_GENSOL_KEY     = 'G#nS0l$kP3y!xZ7...'
```

**Tại sao lại có vấn đề:** DMOJ để `local_settings.py` là file mẫu (`.example`) và người dùng tự điền — file thật đáng lẽ phải nằm trong `.gitignore`. Khi bạn điền giá trị thật rồi commit, ai clone repo (repo đang **public**) cũng đọc được.

Hệ quả cụ thể:
- **App Password Gmail bị lộ** → bất kỳ ai cũng gửi mail giả danh địa chỉ của bạn, hoặc dùng để đăng nhập SMTP.
- **`SECRET_KEY` bị lộ** → đây là mấu chốt nguy hiểm nhất trong Django. `SECRET_KEY` dùng để ký session cookie, token reset password, CSRF, và (quan trọng với dự án này) để **suy ra khoá mã hoá API key AI**. Xem đoạn này ở `models/api_key.py`:
  ```python
  def _get_fernet():
      key_material = ('aiapikey-encryption-' + settings.SECRET_KEY).encode('utf-8')
      derived = hashlib.sha256(key_material).digest()
      return Fernet(base64.urlsafe_b64encode(derived))
  ```
  Nghĩa là: nếu ai biết `SECRET_KEY` (đang public!) thì họ **giải mã được toàn bộ API key OpenAI/Claude/Gemini/DeepSeek** mà người dùng đã lưu. Người dùng sẽ bị "cháy" hạn mức, mất tiền.
- **`EVENT_DAEMON_*_KEY` bị lộ** → có thể giả mạo/nghe lén kênh sự kiện realtime của người khác (đoán channel của run/submission).

**Ví dụ minh hoạ khai thác:** kẻ tấn công clone repo → lấy `SECRET_KEY` → forge một session cookie cho `user_id` bất kỳ (Django signed cookie) → đăng nhập với tư cách admin mà không cần mật khẩu.

**Cách sửa:**
1. **Xoay (rotate) TẤT CẢ secret ngay lập tức:** tạo `SECRET_KEY` mới, thu hồi App Password Gmail cũ và tạo cái mới, đổi cả 3 khoá `EVENT_DAEMON_*` và khoá Fernet. Việc đổi `SECRET_KEY` sẽ đăng xuất mọi session và làm hỏng các ciphertext API key cũ → chấp nhận, yêu cầu người dùng nhập lại API key.
2. Đưa `local_settings.py` (cả 2 bản) và các khoá vào biến môi trường / file `.env` **không** version-control. Sửa `settings.py` để đọc từ `os.environ`.
3. **Gỡ secret khỏi lịch sử Git**, không chỉ khỏi HEAD (vì repo public, lịch sử vẫn đọc được). Dùng `git filter-repo` hoặc BFG Repo-Cleaner, rồi force-push. Lưu ý: kể cả sau khi gỡ, phải coi như secret đã lộ vĩnh viễn → vẫn phải rotate.
4. Bổ sung dòng vào `.gitignore`:
   ```
   dmoj/config/local_settings.py
   dmoj/repo/dmoj/local_settings.py
   ```
   và chỉ commit bản `*.example`.
5. Với khoá mã hoá API key, nên tách riêng một biến `AI_API_KEY_ENCRYPTION_KEY` độc lập với `SECRET_KEY`, để sau này rotate `SECRET_KEY` không phá hỏng toàn bộ key đã lưu.

**Cách kiểm tra:** `git log -p -- dmoj/config/local_settings.py | grep -i "password\|secret_key"` phải không còn trả về giá trị thật. Chạy công cụ như `gitleaks detect` trên toàn repo để chắc chắn.

---

### A2. `ALLOWED_HOSTS = ['*']` — cấu hình production không an toàn

**Vấn đề:** cùng commit `8fc54e1`:
```python
ALLOWED_HOSTS = ['*']
```
**Tại sao có vấn đề:** `['*']` chấp nhận mọi giá trị header `Host`. Kết hợp với việc email reset password/kích hoạt được sinh từ header `Host` (DMOJ dùng `SITE_FULL_URL` nhưng nhiều chỗ vẫn dựa host của request), điều này mở ra **Host header injection** → link reset password trỏ về domain của kẻ tấn công → chiếm tài khoản.

**Cách sửa:** liệt kê tường minh domain thật: `ALLOWED_HOSTS = ['aloj.your-domain.com', 'localhost']`. Nếu cần linh hoạt theo môi trường thì đọc từ biến môi trường và split.

**Kiểm tra:** gửi request với `Host: evil.com` → server phải trả về 400 (Bad Request), không phải 200.

---

### A3. XSS trong admin panel — **đã fix đúng** ở `b6ed72d`

**Thành phần:** trang admin hiển thị output/lỗi của RunSubmission (`admin/run_submission.py`).

**Vấn đề (trước fix):** khi trình chấm trả về lỗi (`obj.error`), nếu không convert được ANSI thì code cũ đưa thẳng chuỗi đó vào `mark_safe(...)`:
```python
html = _ANSI_ESCAPE.sub('', obj.error)   # <-- chưa escape HTML
...
return mark_safe('<pre ...>' + html + '</pre>')
```
`obj.error` bắt nguồn từ output chương trình người dùng nộp → người dùng kiểm soát được. Nếu họ in ra `<script>...</script>`, admin mở trang là script chạy trong phiên admin → **stored XSS leo thang quyền**.

**Cách bạn đã sửa (đúng):**
```python
from django.utils.html import escape, format_html, format_html_join
...
html = escape(_ANSI_ESCAPE.sub('', obj.error))
```

**Nhận xét & gợi ý bổ sung:** Fix này chỉ vá nhánh `except`. Ở nhánh `try` bạn dùng `Ansi2HTMLConverter(...).convert(...)` — thư viện này về nguyên tắc **có** escape HTML trước khi tô màu, nên tạm ổn. Nhưng để chắc chắn, nên kiểm thử với payload `<img src=x onerror=alert(1)>` ở **cả hai** nhánh. Về lâu dài, cân nhắc dùng `format_html` với placeholder thay vì nối chuỗi `mark_safe` thủ công, vì nối chuỗi rồi `mark_safe` là anti-pattern dễ tái phạm.

**Kiểm tra:** nộp một bài in ra `<script>document.title='xss'</script>` cho RunSubmission, mở trang admin → tiêu đề trang không được đổi, phải thấy literal text.

---

### A4. Gỡ giới hạn domain đăng ký — **rủi ro nghiệp vụ, cần xác nhận có chủ đích**

**Vấn đề:** commit `a5e15d8` comment-out đoạn chỉ cho phép email `@lge.com`:
```python
# if domain != 'lge.com':
#     raise forms.ValidationError('Only LGE email addresses ... allowed')
```
**Tại sao đáng lưu ý:** sau thay đổi này, **bất kỳ email nào** cũng đăng ký được (chỉ còn lọc `BAD_MAIL_PROVIDERS`). Với một OJ mở thì đây là hành vi mong muốn; nhưng nếu BKDNOJ chỉ dành cho sinh viên Bách Khoa Đà Nẵng thì bạn đã **mở toang cổng đăng ký**, dễ bị bot tạo tài khoản hàng loạt.

**Cách sửa (tuỳ mục tiêu):** nếu muốn giới hạn theo trường, đổi thành cho phép domain `@dut.udn.vn` (hoặc danh sách domain) thay vì xoá hẳn. Nếu chủ đích mở công khai thì nên **xoá hẳn code chết** thay vì để comment (code comment lâu ngày gây nhiễu). Kèm theo, bật CAPTCHA khi đăng ký và giữ giới hạn reset password bạn đã thêm (`DMOJ_PASSWORD_RESET_LIMIT_*`).

---

<a id="b"></a>
## 3. NHÓM B — CƠ CHẾ CHẤM ĐIỂM (SCORING)

Đây là phần logic lõi nhất của một OJ và cũng là nơi bạn có một bug tinh vi đã sửa.

### B1. Thêm chế độ chấm "partial theo testcase" — thiết kế tốt

**Bối cảnh:** DMOJ gốc chấm theo **batch/subtask**: trong 1 subtask, chỉ cần 1 test sai là cả subtask 0 điểm (lấy `min` điểm các test). Commit `e4a38fa` bạn thêm enum `ScoringMode` với 3 chế độ: `short_circuit`, `partial_batch`, `partial_testcase`. Chế độ mới `partial_testcase` cho phép **mỗi test đúng trong subtask đều được cộng điểm** — hợp lý cho mục tiêu giáo dục.

**Cách hoạt động:** `scoring_mode` được đọc trong `judge_handler.py` khi tính `grading-end`, đẩy xuống judge qua field `'scoring-mode'`. Với `partial_testcase`, điểm subtask = (trung bình hệ số các test) × điểm subtask.

**Điểm cần lưu ý về thiết kế:** bạn giữ lại 2 field cũ `short_circuit` và `partial` "for backward compatibility with judge protocol. Computed from scoring_mode in save()". Đây là quyết định đúng để không phá giao thức chấm. Nhưng nó tạo ra **nguồn sự thật kép** (scoring_mode vs short_circuit/partial). Cần đảm bảo `save()` **luôn** đồng bộ 2 field dẫn xuất; nếu ai đó set `short_circuit` trực tiếp qua admin/script mà không qua `save()`, dữ liệu sẽ lệch. Gợi ý: viết một test đơn vị chốt bất biến "sau save(), (short_circuit, partial) luôn khớp scoring_mode".

### B2. Bug tính điểm sai với custom checker — **bug tinh vi, đã sửa đúng** ở `c69bb6e`

Đây là bug đáng để mổ xẻ kỹ vì nó minh hoạ một lỗi rất hay gặp: **trộn lẫn hai đơn vị đo (điểm tuyệt đối vs hệ số 0..1)**.

**Vấn đề:** Trong lần thêm `partial_testcase` đầu tiên (`e4a38fa`), code cộng dồn trực tiếp `case.points`:
```python
# BẢN LỖI
batches[case.batch] = [case.points, 1, case.total]   # sum_of_points
...
points += (sum_of_points / total_count)              # trung bình điểm
```
Vấn đề nằm ở chỗ `case.points` mang **ý nghĩa khác nhau** tuỳ loại checker:
- **Checker chuẩn:** test đúng thì `case.points = case.total` (ví dụ = 10), sai thì = 0. Đây là **điểm tuyệt đối**.
- **Custom checker (partial):** `case.points` là **hệ số 0..1** (ví dụ 0.5 nghĩa là đúng 50%).

Vì trộn hai thang đo, công thức `sum_of_points / total_count` cho ra con số vô nghĩa. Ví dụ subtask 10 điểm, 2 test, checker chuẩn, cả 2 đúng → `sum = 10 + 10 = 20`, `20/2 = 10` (may mắn đúng); nhưng nếu 1 đúng 1 sai → `(10+0)/2 = 5` (đúng ý), còn với custom checker mỗi test trả 0.8 → `(0.8+0.8)/2 = 0.8` điểm cho **cả subtask 10 điểm** → sai bét (đáng lẽ 8 điểm).

**Cách bạn đã sửa (đúng):** chuẩn hoá mọi thứ về **hệ số [0,1]** trước, rồi mới nhân với điểm subtask:
```python
# BẢN SỬA — heuristic phân biệt hai thang đo
coeff = case.points if case.points <= 1 else (case.points / case.total if case.total else 0)
...
points += (sum_coeff / total_count * batch_pts)   # trung bình hệ số × điểm subtask
```
Và bạn đã **đồng bộ cùng công thức ở 3 nơi** (rất quan trọng để hiển thị khớp với chấm):
- `judge/bridge/judge_handler.py` (điểm thật lưu DB),
- `judge/views/submission.py` hàm `make_batch` (điểm hiển thị trên trang submission),
- template `status-testcases.html` (cột "(coeff/1)").

**Điểm yếu còn lại của cách sửa — cần biết:** heuristic `case.points <= 1` là **giả định mong manh**. Nếu tồn tại một bài có điểm mỗi test = 1 (subtask nhiều test, mỗi test 1 điểm) với checker chuẩn, thì test đúng cho `case.points = 1`, rơi vào nhánh "coi là hệ số" → tình cờ vẫn đúng ở đây (hệ số 1 = full). Nhưng nếu một ngày checker chuẩn trả điểm phân số hợp lệ ≤ 1 mà **không** phải hệ số, heuristic sẽ nhầm. Giải pháp bền hơn: để judge server gửi kèm một cờ tường minh `is_partial_checker` cho mỗi case, thay vì đoán qua giá trị. Trước mắt, cách hiện tại chấp nhận được nhưng **nên ghi rõ giả định này thành comment + test hồi quy**.

**Cách kiểm tra (rất nên làm cho phần scoring):** viết một bộ test tự động dựng sẵn các `SubmissionTestCase` giả với 4 kịch bản — (checker chuẩn / custom checker) × (batch / testcase) — và assert điểm cuối. Đây đúng "gu" stress-test mà bạn hay dùng cho competitive programming: so điểm tính bằng `judge_handler` với một hàm brute-force tính tay.

### B3. `total_time` cho submission — bổ sung hợp lý

Commit `fd73532` thêm field `total_time` (tổng thời gian mọi test) bên cạnh `time` (test lâu nhất), và sửa template để với TLE vẫn hiển thị tổng thời gian thay vì `---`. Thay đổi nhỏ, đúng, không rủi ro. Chỉ lưu ý migration `0220` cần chạy trước khi deploy code mới (nếu không, `submission.total_time = total_time` ở bridge sẽ lỗi cột không tồn tại).

---

<a id="c"></a>
## 4. NHÓM C — LUỒNG RUN / IDE & REALTIME WEBSOCKET

Đây là tính năng lớn nhất bạn tự xây: IDE kiểu LeetCode, nút **RUN** chạy thử với sample/custom testcase, kết quả realtime.

### C1. Kiến trúc RUN — tách pipeline riêng, thiết kế tốt

Bạn tạo model `RunSubmission` riêng (bảng DB mới), pipeline `run-request` độc lập với `submission-request`, không đụng vào luồng chấm chính thức. Đây là lựa chọn kiến trúc **đúng**: RUN không được ghi vào bảng `Submission` thật (không tính vào thống kê/ranking), và tách biệt giúp giới hạn rate riêng.

Điểm cộng về bảo mật trong `views/run.py`:
- Kiểm tra `is_accessible_by`, `banned_users`, ngôn ngữ hợp lệ — **tái sử dụng đúng** các ràng buộc của luồng submit.
- Rate limit gộp cả submission thật và run (`pending_real + pending_run >= DMOJ_SUBMISSION_LIMIT`) → chống spam qua ngả RUN.
- `RunPollView` kiểm tra quyền sở hữu: `RunSubmission.objects.get(id=run_id, user=request.profile)` → không xem được run của người khác.

### C2. Bug race condition mất event ở lần RUN thứ 2+ — **bug hay, đã sửa đúng** ở `811358d`

**Vấn đề (triệu chứng):** RUN lần đầu OK; RUN lần 2 trở đi (hoặc đổi ngôn ngữ rồi RUN) bị kẹt "Running..." dù DB đã có kết quả.

**Tại sao có vấn đề (root cause):** khác với Submit (mỗi lần submit là **reload trang → WebSocket mới**), RUN **tái dùng WebSocket trên cùng trang**. Trong `websocket/daemon.js`, hàm `gotMessage()` cũ advance `socket.lastMessage` cho **mọi** message kể cả message không khớp filter của client:
```javascript
// BẢN LỖI
socket.gotMessage = (message) => {
  if (message.channel in socket.filter) {
    socket.send(JSON.stringify(message));
  }
  socket.lastMessage = message.id;   // <-- advance kể cả khi KHÔNG gửi
};
```
Cơ chế "catch-up" (replay event bị lỡ khi client vừa `set-filter`) dựa vào `lastMessage` để biết cần replay từ đâu. Vì `lastMessage` đã bị đẩy qua khỏi event của lần RUN mới trước khi client kịp đăng ký filter (client đăng ký filter sau ~200ms), event `grading-end` không bao giờ được replay → UI kẹt.

**Cách bạn đã sửa (đúng, 2 mũi):**
1. Trong `daemon.js`, chỉ advance `lastMessage` khi **thực sự gửi**:
   ```javascript
   if (message.channel in socket.filter) {
     socket.send(JSON.stringify(message));
     socket.lastMessage = message.id;   // <-- chuyển vào trong if
   }
   ```
2. Trong `resources/event.js`, bỏ độ trễ 200ms khi WebSocket đã mở sẵn — gửi `set-filter` ngay, giống cách Submit gửi `start-msg` ngay khi connect. Chỉ giữ delay khi socket chưa sẵn sàng.

**Nhận xét:** đây là loại bug realtime kinh điển (message ordering + late subscription). Cách sửa hợp lý. Có một rủi ro phụ cần lưu: chuyển `lastMessage` vào trong `if` nghĩa là những message **không khớp filter** không còn cập nhật con trỏ — với client này thì đúng, nhưng nếu logic catch-up ở nơi khác giả định `lastMessage` là "id message toàn cục cuối cùng đã thấy" thì có thể lệch. Nên kiểm thử thêm kịch bản nhiều tab/nhiều channel cùng lúc.

**Kiểm tra:** mở 1 bài, RUN 3 lần liên tiếp không reload; đổi ngôn ngữ rồi RUN. Cả 3 lần đều phải trả kết quả, không kẹt.

### C3. Chuyển từ POLLING sang WSEVENT + fallback — tiến hoá hợp lý nhưng lịch sử "lắt léo"

Chuỗi commit `a9873dc → c829b4a` cho thấy quá trình: ban đầu RUN dùng cả wsevent lẫn polling fallback (`a9873dc`), sau đó `c829b4a` **xoá hẳn** polling fallback và thêm `event_dispatcher.off()` để huỷ đăng ký channel khi xong. Rồi ở tính năng Gensol (`05fa706`) bạn **thêm lại** polling fallback (interval 10s) để bắt event WS bị lỡ.

**Vấn đề tiềm ẩn:** việc bỏ hẳn fallback ở RUN (`c829b4a`) khiến RUN **phụ thuộc hoàn toàn** vào WebSocket. Nếu wsevent chết hoặc bị proxy chặn, RUN sẽ kẹt vĩnh viễn (không có đường lui). Trong khi đó Gensol lại có fallback. Nên **thống nhất triết lý**: hoặc mọi luồng realtime đều có polling fallback nhẹ (an toàn hơn), hoặc mọi luồng đều có timeout phía client để không kẹt UI vô hạn.

**Gợi ý:** thêm một `setTimeout` an toàn (ví dụ 60s) ở RUN: nếu quá thời gian mà chưa có terminal event, tự gọi `RunPollView` một lần để lấy kết quả từ DB rồi kết thúc. Vừa nhẹ, vừa không kẹt.

### C4. `id_secret` cho kênh RUN — chống đoán channel, tốt

`RunSubmission.get_id_secret()` dùng HMAC-SHA512 với `EVENT_DAEMON_RUN_KEY` để sinh tên channel khó đoán, thay vì lộ `run_id` tuần tự. Đây là pattern đúng của DMOJ. **Nhưng** hiệu quả của nó phụ thuộc `EVENT_DAEMON_RUN_KEY` bí mật — mà khoá này đang bị commit public (xem A1). Rotate khoá là điều kiện tiên quyết để cơ chế này có ý nghĩa.

### C5. IDE limit cấu hình hoá — tốt, và một anti-pattern đã sửa

`07a481f` đưa các hằng số giới hạn IDE (số custom testcase, độ dài input/source/output) ra `settings.py` thay vì hard-code `5`/`65536` rải rác — dễ chỉnh, đúng. `c2b659a` ("fix anti-pattern") sửa **mutable default argument** kinh điển của Python:
```python
# BẢN LỖI — list mặc định dùng chung giữa các lần gọi
def judge_run(self, ..., banned_judges=[], sample_input_files=[], custom_inputs=[]):
# BẢN SỬA
def judge_run(self, ..., banned_judges=None, ...):
    if banned_judges is None: banned_judges = []
```
Sửa đúng. Đây là bug tiềm ẩn thật sự (list mặc định bị chia sẻ trạng thái giữa các request), không phải chỉ về style.

---

<a id="d"></a>
## 5. NHÓM D — TÍNH NĂNG AI

Đây là mảng nhiều code nhất, gồm 4 tính năng: **API key management, tạo đề bằng AI, sinh testcase bằng AI (Gensol), review code bằng AI, gợi ý tag bằng AI**.

### D1. Lưu API key người dùng — hướng đúng, nhưng gắn chặt với `SECRET_KEY`

**Cách hoạt động:** người dùng nhập API key của provider (OpenAI/Gemini/Claude/DeepSeek), hệ thống mã hoá bằng Fernet, chỉ lưu `key_ciphertext` + `key_last4`, không giữ plaintext. Chỉ giải mã khi thực sự gọi provider. **Tư duy đúng.**

**Vấn đề:** như đã nói ở A1, khoá Fernet được suy ra từ `SECRET_KEY`. Điều này tạo 2 rủi ro: (1) `SECRET_KEY` lộ → giải mã được mọi key; (2) khi rotate `SECRET_KEY` (bắt buộc sau sự cố lộ) thì **toàn bộ ciphertext cũ thành rác** không giải mã được. Nên tách `AI_API_KEY_ENCRYPTION_KEY` riêng.

**Rủi ro bổ sung — SSRF:** các view AI (`ai_code_review.py`, `ai_tag_suggest.py`) gọi `urllib.request.urlopen(url, ...)` tới `base_url` lấy từ `AI_PROVIDER_CONFIGS`. Nếu config này cố định (hard-code endpoint) thì an toàn; nhưng nếu về sau cho phép admin/người dùng nhập base_url tuỳ ý (ví dụ "self-hosted endpoint"), sẽ mở **SSRF** (server gọi tới `http://169.254.169.254/` metadata nội bộ…). Hiện tại endpoint đang cố định theo provider → tạm ổn; **đừng** cho nhập URL tự do mà không whitelist.

### D2. Gensol — sinh testcase bằng generator + solution, kiến trúc phức tạp nhất

**Cách hoạt động (utils/gensol.py):** một `GensolJob` chạy 2 bước — (1) chạy `generator` để sinh input, (2) chạy `solution` để sinh output — rồi đóng gói thành `data.zip`, upload vào problem data, tái tạo `init.yml`. Trạng thái đẩy realtime qua channel `gensol_<id_secret>`.

**Điểm mạnh:** máy trạng thái rõ ràng (`GENERATING_INPUT → GENERATING_OUTPUT → DONE/ERROR`), có cleanup working dir, có giới hạn kích thước zip (`GENSOL_MAX_ZIP_SIZE`).

**Vấn đề & rủi ro:**

1. **Thao tác phá huỷ dữ liệu không hoàn tác (nghiêm trọng về nghiệp vụ).** `start_gensol_job` gọi `ProblemTestCase.objects.filter(dataset=problem).delete()` **ngay từ đầu**, và `_upload_zip_and_compile` ghi đè `data.zip`. Nếu generator/solution lỗi giữa chừng, **testcase gốc của bài đã bị xoá sạch** mà không có backup. Với một bài đã có bộ test được chăm chút, đây là mất mát lớn.
   - *Cách sửa:* sinh testcase vào một **thư mục/zip tạm**, chỉ **swap** vào chỗ chính khi job `DONE`. Hoặc backup `data.zip` cũ trước khi ghi đè, cho phép rollback khi `ERROR`.

2. **`_upload_zip_and_compile` chạy trong luồng nào?** Nó thao tác I/O nặng (ghi zip, tái tạo init.yml). Nếu chạy đồng bộ trong request `start_gensol_job` (không phải Celery task), request có thể timeout với `num_cases` lớn, và block worker. Cần xác nhận nó nằm trong tác vụ nền.

3. **Chuỗi bug được vá dần cho thấy phần này còn "mỏng".** Riêng commit cuối `05fa706` vá 3 lỗi: (a) `GensolJob.DoesNotExist` im lặng không báo user → thêm event `internal-error`; (b) thiếu polling fallback → thêm; (c) `start_gensol_job` thất bại sau khi tạo job nhưng vẫn trả 200 → thêm `refresh_from_db()` kiểm tra `status == 'ERROR'`. Ba lỗi này đều là **thiếu xử lý nhánh thất bại** — dấu hiệu cho thấy nên rà soát tổng thể "mọi nhánh lỗi đều phải (1) cập nhật DB status, (2) báo user, (3) cleanup". Hiện `_transition_to_solution` và `_finalize_job` đã bọc try/except khá đầy đủ; nên đảm bảo `save_testcase_output` và `_dispatch_gensol` cũng vậy.

4. **`aceGenerator.setReadOnly(false)` chỉ cho superuser** (ở `05fa706`) — hợp lý, tránh người thường sửa generator. Tốt.

### D3. Review code AI & Tag suggest — sạch, có kiểm soát quyền

**Review code (`ai_code_review.py`):** kiểm tra **quyền sở hữu submission** (`submission.user_id != user.id → 403`), chặn file-only, chặn source rỗng, yêu cầu API key `status='verified'`. Prompt cố định, output plain text. **Ổn.**

**Tag suggest (`ai_tag_suggest.py`):** lấy top 3 AC submission ngắn nhất làm ngữ cảnh, yêu cầu ≥3 AC mới chạy, prompt buộc AI trả JSON array. **Lưu ý:** kết quả AI là JSON do model sinh — phải **parse phòng thủ** (try/except, validate từng tag id có nằm trong danh sách hợp lệ không) trước khi ghi DB, tránh model trả rác hoặc tag không tồn tại. Cần xác nhận đoạn parse (nằm ở phần sau file) có validate chặt.

**Rủi ro chung của mọi tính năng AI — chi phí & lạm dụng:** mỗi lần gọi AI tốn tiền/token của **người dùng** (dùng key của họ). Cần rate limit riêng cho endpoint AI (số lần review/giờ), và timeout hợp lý (`_AI_REVIEW_TIMEOUT = 120s` khá dài — một request giữ worker 2 phút, nhiều request đồng thời có thể cạn worker pool). Cân nhắc chạy call AI qua Celery task + trả kết quả qua wsevent thay vì giữ HTTP request 2 phút.

### D4. Prompt template cho phép admin sửa — tốt, nhưng cẩn thận `.format()`

`5acceee` cho admin sửa prompt qua DB (`AIPromptTemplate`). Tiện lợi. **Rủi ro:** prompt dùng `template.format(problem_description=..., available_tags=...)`. Nếu nội dung đề bài chứa ký tự `{` `}` (ví dụ code mẫu, LaTeX `\frac{}{}`), `str.format()` sẽ **ném KeyError/ném lỗi** hoặc hiểu nhầm placeholder. Đây là bug chờ nổ. *Cách sửa:* escape `{`→`{{`, `}`→`}}` trong nội dung động trước khi format, hoặc dùng `string.Template` (cú pháp `$var`) an toàn hơn với nội dung tuỳ ý.

---

<a id="e"></a>
## 6. NHÓM E — CONTEST (THI ĐẤU)

### E1. Contest Focus Lock — chống gian lận, thiết kế hợp lý

**Cách hoạt động (`28f6914`):** khi bật `enable_focus_lock`, thí sinh LIVE bị chuyển sang trang wrapper fullscreen; khi rời fullscreen/đổi tab, client báo về `ContestReportFocusViolation` → tăng `focus_violations`. Middleware set `request.focus_lock_active`.

**Điểm cần lưu ý:**
- Đây là **chống gian lận phía client** — về bản chất **bỏ qua được** (tắt JS, sửa DOM, dùng máy thứ hai). Nên hiểu nó là "răn đe + ghi nhận", **không** phải rào chắn tuyệt đối. Cần nêu rõ trong tài liệu để giám thị không ỷ lại.
- `ContestReportFocusViolation` chỉ `+1` mỗi lần báo. Kẻ gian có thể **không** gửi report (chặn request). Server không thể phân biệt "không vi phạm" với "vi phạm nhưng chặn report". Có thể bổ sung heartbeat: client định kỳ báo "còn trong fullscreen"; thiếu heartbeat ⇒ nghi ngờ.
- Endpoint report cần **rate limit** để không bị spam làm phồng `focus_violations`.

### E2. Fix join contest LIVE/SPECTATE sau khi rời — logic đúng

**Vấn đề nghiệp vụ:** thí sinh đang thi LIVE bấm "Leave" rồi vào lại — nếu cho vào LIVE tiếp thì họ "reset" được đồng hồ/tình huống. Commit `e9633a6` thêm cờ `has_left`: khi rời một participation LIVE lúc contest chưa kết thúc thì đánh dấu `has_left=True`; lần sau vào chỉ được **SPECTATE**. Và ở danh sách contest, participation `has_left` được coi như đã "kết thúc". Logic **đúng và cần thiết** cho tính công bằng.

**Kiểm tra:** join LIVE → leave → join lại → phải ở chế độ spectate, không nộp bài tính điểm được.

### E3. Auto-rescore khi đổi format contest — vá đúng chỗ

`bfcc912` thêm: khi sửa `format_name`/`format_config`/`frozen_last_minutes` qua view `EditContest`, tự trigger `rescore_contest` (giống hành vi ở Django Admin). Trước đó sửa qua site thì ranking hiện `???` tới khi rescore tay. Vá đúng. Dùng `transaction.on_commit(...)` để chỉ rescore sau khi commit thành công — chuẩn.

Cùng commit, `add_admin_to_group` đổi `Group.objects.get(...)` → `get_or_create(...)` để không crash khi group quyền chưa tồn tại — phòng thủ tốt.

---

<a id="f"></a>
## 7. NHÓM F — MIGRATION & TÍNH NHẤT QUÁN DB

### F1. Xung đột đánh số migration `0228`/`0229`/`0230`/`0231` — **rủi ro tiềm ẩn cao**

Do bạn phát triển song song nhiều nhánh feature rồi merge (`ai-review-code`, `generate-testcase-v2`, `contest-focus-lock`, `tags-and-reviews`), có nhiều migration **trùng số thứ tự nhưng khác tên**, xuất hiện rải rác qua các commit:
- `0228_generate_testcase_job` (nhánh gensol) vs `0228_contest_focus_lock` (nhánh contest)
- `0229_ai_code_review` vs `0229_alter_generatetestcasejob...`
- `0230_ai_prompt_template` vs `0230_generatetestcasejob_language_fields`
- `0231_seed_ai_prompts` vs `0231_gensol_submission`

Ở HEAD hiện tại, chuỗi đã "duỗi thẳng" thành `0226…0238` liền mạch (tốt), nhưng lịch sử cho thấy đã có giai đoạn **hai leaf migration cùng phụ thuộc một parent** → Django sẽ báo "Conflicting migrations" và cần `makemigrations --merge`. `768140b` ("Generate Testcase feature removed and will be reimplemented later") xoá 2506 dòng — đúng là một lần gỡ rối nhánh gensol để đánh số lại.

**Tại sao nguy hiểm:** nếu ai deploy từ một commit ở giữa (trong lúc conflict), `migrate` sẽ fail hoặc áp dụng sai thứ tự. Với DB production, migration lỗi giữa chừng rất khó cứu.

**Cách phòng ngừa:**
- Trước mỗi merge nhánh có migration, chạy `python manage.py makemigrations --check --dry-run` để phát hiện conflict.
- Sau merge, `python manage.py migrate --plan` để xem thứ tự áp dụng thực tế.
- Quy ước: nhánh feature không tự đánh số cao; rebase lên main mới nhất trước khi tạo migration.

### F2. `0221_remove_free_credit_fields` — `SeparateDatabaseAndState` dùng đúng

Khi gỡ tính năng credit (`80da28e`), bạn xoá field `free_credit`/`monthly_free_credit_limit`. Migration `0221` dùng `SeparateDatabaseAndState` với `database_operations=[]` (vì cột "chưa từng tồn tại trong DB thật", chỉ có trong state). Đây là kỹ thuật **nâng cao và đúng** cho tình huống model-state lệch DB-thật. Cần chắc chắn giả định "cột không tồn tại trong DB" đúng với **mọi** môi trường đang chạy; nếu có DB nào đã thực sự tạo cột thì migration này sẽ để lại cột mồ côi.

### F3. `0068`/`0117` sửa migration cũ đã squash — cẩn thận

`0bf7ab6` sửa các migration **rất cũ** (`0001_squashed`, `0088`, `0116`, `0117`) đổi `related_name='_contest_..._+'`→`'..._+'` và `to='judge.Profile'`→`'judge.profile'`. Đây là sửa để tương thích Django mới. **Rủi ro:** sửa migration đã áp dụng ở production **không** khiến DB đổi (Django chỉ so state), nhưng làm **hash migration lệch** giữa các môi trường, và nếu môi trường mới chạy lại từ đầu sẽ ra schema khác môi trường cũ. Chỉ nên sửa migration lịch sử khi thật cần và hiểu rõ hệ quả. Nên kiểm tra `showmigrations` khớp nhau giữa dev/prod.

### F4. `VNOJ_DISPLAY_RANKS` alias — vá tương thích thông minh

`5dd6f59` thêm `VNOJ_DISPLAY_RANKS = ALOJ_DISPLAY_RANKS` vì migration `0153` cũ tham chiếu tên cũ. Cách vá gọn, đúng — giữ migration lịch sử chạy được sau khi bạn đổi tên biến VNOJ→ALOJ.

---

<a id="g"></a>
## 8. TỔNG HỢP MỨC ĐỘ ƯU TIÊN & CHECKLIST

### Bảng ưu tiên

| Mức | Vấn đề | Trạng thái | Hành động |
|-----|--------|-----------|-----------|
| 🔴 Khẩn | A1 — Secrets (SECRET_KEY, App Password, EVENT keys) commit public | **Đang tồn tại ở HEAD** | Rotate tất cả + xoá khỏi lịch sử Git + .gitignore |
| 🔴 Khẩn | A2 — `ALLOWED_HOSTS=['*']` | Đang tồn tại | Liệt kê domain tường minh |
| 🟠 Cao | D1 — Khoá mã hoá API key gắn `SECRET_KEY` | Đang tồn tại | Tách `AI_API_KEY_ENCRYPTION_KEY` riêng |
| 🟠 Cao | D2.1 — Gensol xoá testcase gốc trước khi chắc thành công | Đang tồn tại | Sinh vào tạm, chỉ swap khi DONE + backup |
| 🟠 Cao | F1 — Xung đột số migration khi merge nhánh | Đã duỗi ở HEAD | Thêm `makemigrations --check` vào quy trình |
| 🟡 TB | C3 — RUN bỏ hẳn fallback, phụ thuộc WS | Đang tồn tại | Thêm timeout/poll an toàn phía client |
| 🟡 TB | D4 — `.format()` prompt vỡ khi đề chứa `{}` | Đang tồn tại | Escape `{{}}` hoặc dùng `string.Template` |
| 🟡 TB | D3 — Rate limit & timeout dài cho endpoint AI | Đang tồn tại | Đưa call AI vào Celery + rate limit |
| 🟡 TB | A4 — Mở toang đăng ký (gỡ lọc @lge.com) | Có chủ đích? | Xác nhận mục tiêu; nếu giới hạn thì lọc domain trường |
| 🟢 Thấp | B1/B2 — Scoring dùng heuristic `points<=1` | Đã sửa, còn mong manh | Thêm cờ tường minh từ judge + test hồi quy |
| 🟢 Thấp | E1 — Focus lock là client-side | Theo thiết kế | Ghi rõ giới hạn; thêm heartbeat |

### Những điểm bạn làm TỐT (đáng ghi nhận)
- Tách `RunSubmission` khỏi luồng chấm chính — kiến trúc sạch.
- Đồng bộ công thức scoring ở cả 3 tầng (bridge/view/template) — nhất quán hiển thị và chấm.
- Vá đúng bản chất các bug realtime (race condition), XSS, mutable default arg.
- Mã hoá API key thay vì lưu plaintext — đúng tư duy bảo mật.
- Dùng `transaction.on_commit`, `get_or_create`, `SeparateDatabaseAndState` — cho thấy hiểu Django ở mức khá.
- Tài liệu hoá kỹ (README, IDE_RUN_FEATURE.md, SUBMIT_RUN_GENSOL_FLOW.md, agents_*.md) — rất hữu ích cho người sau.

### Checklist hành động ngay (theo thứ tự)
1. [ ] Rotate & xoá secrets khỏi lịch sử Git (A1) — **làm đầu tiên, hôm nay**.
2. [ ] Sửa `ALLOWED_HOSTS` (A2).
3. [ ] Tách khoá mã hoá API key (D1).
4. [ ] Backup/swap-when-done cho Gensol testcase (D2.1).
5. [ ] Thêm `makemigrations --check` vào CI (F1).
6. [ ] Thêm test hồi quy cho 4 kịch bản scoring (B2).
7. [ ] Thêm timeout client cho RUN + đưa call AI vào Celery (C3, D3).

---

*Hết Phần I. Xem **Phần II** để có review chi tiết từng commit theo trình tự thời gian.*
