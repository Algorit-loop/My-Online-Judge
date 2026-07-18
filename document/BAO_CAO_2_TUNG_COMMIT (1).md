# BÁO CAO REVIEW CODE — BKDN Online Judge (ALOJ)
## Phần II — Review chi tiết TỪNG COMMIT

> **Phạm vi:** nhánh `master`, từ **commit thứ 2** (`8fc54e1`) đến commit mới nhất (`05fa706`).
> Commit đầu tiên `70f62ef "update stogare + credit"` là code nền → **bỏ qua**.
> Định dạng mỗi commit: **Hash · Ngày · Tiêu đề** → *Làm gì* → *Đánh giá / rủi ro* → *Cần làm (nếu có)*.
> Ký hiệu: ✅ tốt · ⚠️ cần lưu ý · 🔴 nghiêm trọng · 🧹 dọn dẹp/nhỏ · 🔀 merge commit.

---

### 2. `8fc54e1` · 27/03 · update local_settings.py.example
**Làm gì:** cấu hình lại `local_settings.py` cho môi trường ALOJ — đổi `SITE_NAME`/`SERVER_EMAIL` sang ALOJ, bật `SESSION_ENGINE=cached_db`, session sống 4 ngày, dùng `LenientManifestStaticFilesStorage`, sửa `EVENT_DAEMON_GET`, thêm giới hạn reset password.
**Đánh giá:** 🔴 **Commit nguy hiểm nhất về bảo mật.** Hard-code secret thật vào repo public:
- `SECRET_KEY = os.environ.get('SECRET_KEY', 'algoritxxx-secret-key')` — fallback là secret thật.
- `EMAIL_HOST_PASSWORD = 'wmsy vhzm vpux nojp'` — **Gmail App Password thật**.
- `ALLOWED_HOSTS = ['*']` — mở mọi Host header (nguy cơ Host header injection).
`SECRET_KEY` này về sau còn dùng để suy ra khoá mã hoá API key AI → lộ nó = lộ mọi thứ.
**Cần làm:** 🔴 rotate toàn bộ secret, xoá khỏi lịch sử Git (`git filter-repo`/BFG), đưa `local_settings.py` vào `.gitignore`, chỉ commit `.example`. Sửa `ALLOWED_HOSTS` thành danh sách domain thật. *(Chi tiết: Phần I — A1, A2.)*

---

### 3. `dc10036` · 27/03 · update READ.MD
**Làm gì:** viết lại README thành hướng dẫn thiết lập Judge Server chi tiết bằng tiếng Việt (+1215 dòng).
**Đánh giá:** ✅ Tài liệu tốt, không đụng code chạy. Không rủi ro.

---

### 4. `fd73532` · 31/03 · update Maximum single-case runtime
**Làm gì:** thêm field `Submission.total_time` (migration `0220`), gán `submission.total_time = total_time` ở bridge, sửa template để với TLE hiển thị tổng thời gian thay vì `---`.
**Đánh giá:** ✅ Đúng, nhỏ, có ích (phân biệt "thời gian test lâu nhất" vs "tổng thời gian").
**Cần làm:** ⚠️ đảm bảo migration `0220` chạy **trước** khi deploy code bridge mới, nếu không sẽ lỗi cột không tồn tại.

---

### 5. `80da28e` · 02/04 · deleted free_credit
**Làm gì:** gỡ bỏ hệ thống "credit miễn phí hàng tháng" của org — xoá field `free_credit`/`monthly_free_credit_limit`, đơn giản hoá `consume_credit()`/`has_credit_left()`, migration `0221` dùng `SeparateDatabaseAndState`.
**Đánh giá:** ✅ Gỡ tính năng gọn gàng, migration dùng đúng kỹ thuật khi model-state lệch DB-thật.
**Cần làm:** ⚠️ xác nhận giả định "cột `monthly_credit`/`free_credit` chưa từng tồn tại trong DB thật" đúng ở **mọi** môi trường, tránh cột mồ côi. *(Phần I — F2.)*

---

### 6. `21c3069` · 02/04 · realtime for problem_is_private
**Làm gì:** bật `EVENT_DAEMON_USE=True`; bỏ điều kiện `if problem.is_public` khi post event submission (ở cả `judge_handler.py` và `judgeapi.py`) → mọi submission đều phát event realtime.
**Đánh giá:** ⚠️ Trước đây chỉ bài public mới đẩy realtime; giờ bài private cũng đẩy. Cần kiểm tra **phía nhận (client)** có lọc quyền không — nếu channel `submissions` chung mà client bài private nhận được event, có thể **rò rỉ** thông tin (user X vừa nộp bài private Y). DMOJ vốn lọc quyền ở tầng subscribe; hãy xác nhận việc bỏ `is_public` không khiến người không có quyền thấy hoạt động của bài ẩn.
**Cần làm:** kiểm thử: user thường mở trang list submission → không được thấy submission của bài họ không có quyền xem.

---

### 7. `fd3ca97` · 02/04 · design submission page
**Làm gì:** viết lại toàn bộ SCSS trang submission (toolbar, dropdown filter, bảng dạng table, result-bar). +473/−273.
**Đánh giá:** ✅ Thuần frontend/CSS. Không rủi ro logic.

---

### 8. `4cb95ef` · 03/04 · update submissions/ and solved/
**Làm gì:** tinh chỉnh màu result-bar, thêm cột `.col-state`, thêm i18n "Execution time"/"Memory".
**Đánh giá:** ✅ Nhỏ, CSS + dịch. Ổn.

---

### 9. `bf1c619` · 03/04 · .col-state + realtime submissions
**Làm gì:** tiếp tục UX cột trạng thái + realtime. +26/−6.
**Đánh giá:** ✅ Nhỏ. Ổn (đi kèm điểm cần kiểm tra của commit 6 về realtime).

---

### 10. `4d43a4f` · 04/04 · .sub-actions + animation result-bar
**Làm gì:** animation độc lập cho result-bar. +22/−8.
**Đánh giá:** ✅ CSS. Ổn.

---

### 11. `b71c202` · 07/04 · migrations 0221_remove_free_credit_fields
**Làm gì:** hoàn thiện migration `0221`.
**Đánh giá:** ✅ Đi kèm commit 5. Ổn.

---

### 12. `b5283b7` · 09/04 · django.po + UX submissions + SKILL AI
**Làm gì:** thêm file `agents_frontend.md` (142 dòng tham chiếu cho AI agent), cập nhật i18n + UX.
**Đánh giá:** ✅ Tài liệu + UX. Không rủi ro.
**Cần làm:** 🧹 `agents_frontend.md` ghi đường dẫn tuyệt đối `/home/algoritonlinejudge/...` — không nhạy cảm nhưng nên tránh path cá nhân trong repo public.

---

### 13. `a5e15d8` · 09/04 · edit register.py for del @lge.com
**Làm gì:** comment-out ràng buộc chỉ cho đăng ký email `@lge.com`.
**Đánh giá:** ⚠️ Sau commit này **mọi email** đều đăng ký được. Nếu BKDNOJ dành riêng cho sinh viên trường thì đây là mở cổng đăng ký (nguy cơ bot). Nếu chủ đích công khai thì OK.
**Cần làm:** xác nhận mục tiêu. Nếu giới hạn: đổi thành whitelist domain trường (`@dut.udn.vn`). Nếu mở: **xoá hẳn** code chết thay vì để comment. Thêm CAPTCHA đăng ký. *(Phần I — A4.)*

---

### 14. `76bcce3` · 10/04 · UX contests/
**Làm gì:** i18n "Author"/"Action" + SCSS trang contest list.
**Đánh giá:** ✅ Nhỏ. Ổn.

---

### 15. `e4a38fa` · 13/04 · Scoring mode → Partial by subtask/testcase ⭐
**Làm gì:** **tính năng lõi** — thêm enum `ScoringMode` (short_circuit / partial_batch / partial_testcase), field `Problem.scoring_mode` (migration `0222`), đẩy `scoring-mode` xuống judge, tính điểm `partial_testcase` trong `judge_handler.grading-end`. Giữ `short_circuit`/`partial` làm field dẫn xuất cho tương thích giao thức.
**Đánh giá:** ✅ Thiết kế đúng hướng, mở rộng khả năng chấm. ⚠️ **nhưng chứa mầm bug** (sẽ vỡ ở commit 17): công thức cộng thẳng `case.points` trộn lẫn hai thang đo (điểm tuyệt đối của checker chuẩn vs hệ số 0..1 của custom checker). ⚠️ tạo "nguồn sự thật kép" scoring_mode vs short_circuit/partial.
**Cần làm:** đảm bảo `save()` luôn đồng bộ field dẫn xuất; thêm test bất biến. *(Phần I — B1, B2.)*

---

### 16. `1809873` · 13/04 · small update
**Làm gì:** chỉnh docker-compose/nginx nhỏ.
**Đánh giá:** ✅ Nhỏ. Ổn.

---

### 17. `c69bb6e` · 13/04 · fix bug point of Batch/Subtask ⭐
**Làm gì:** **sửa bug scoring** của commit 15. Chuẩn hoá mọi test về **hệ số [0,1]** (`coeff = case.points if case.points <= 1 else case.points/case.total`) rồi tính `points += sum_coeff/total_count * batch_pts`. Đồng bộ công thức ở **3 nơi**: `judge_handler.py`, `views/submission.py` (`make_batch`), template `status-testcases.html`.
**Đánh giá:** ✅ **Vá đúng bản chất** (thống nhất đơn vị đo) và đồng bộ cả 3 tầng — rất tốt. ⚠️ Heuristic `case.points <= 1` là giả định mong manh: nếu checker chuẩn trả điểm ≤ 1 hợp lệ mà không phải hệ số, sẽ nhầm.
**Cần làm:** để judge gửi cờ tường minh `is_partial_checker` thay vì đoán; thêm test hồi quy 4 kịch bản (chuẩn/custom × batch/testcase) theo kiểu stress-test brute-force. *(Phần I — B2.)*

---

### 18. `ad860a0` · 13/04 · Submission detail page UI redesign
**Làm gì:** làm lại UI trang chi tiết submission (+1017/−187), SCSS + template.
**Đánh giá:** ✅ Frontend. Ổn.

---

### 19. `bfcc912` · 15/04 · fix bug org/ + contest/key/edit ⭐
**Làm gì:** (a) `add_admin_to_group`: `Group.objects.get` → `get_or_create` (không crash khi group quyền chưa có); (b) `EditContest`: auto-trigger `rescore_contest` qua `transaction.on_commit` khi đổi `format_name`/`format_config`/`frozen_last_minutes`.
**Đánh giá:** ✅ Cả hai đều vá đúng. Dùng `on_commit` để chỉ rescore sau commit — chuẩn. Trước đó sửa format qua site khiến ranking `???` tới khi rescore tay.
**Cần làm:** không. *(Phần I — E3.)*

---

### 20. `db62168` · 15/04 · problem_label_style cho ContestForm
**Làm gì:** thêm field `problem_label_style` (migration `0223`), sửa `icpc.py` format, form, admin.
**Đánh giá:** ✅ Tính năng nhỏ hợp lý (kiểu đánh nhãn A/B/C hay 1/2/3). Ổn.

---

### 21. `d4c5b2e` · 16/04 · Penalty Time Format
**Làm gì:** thêm định dạng thời gian phạt cho các contest format (atcoder/base/default/ecoo…). +113/−22.
**Đánh giá:** ✅ Mở rộng format. ⚠️ đụng nhiều file contest_format — cần kiểm thử ranking của **từng** format bị sửa để không lệch cách tính penalty.

---

### 22. `84b49d9` · 17/04 · Improve contest list UI + editor
**Làm gì:** UI contest list, luôn hiện "Publicly visible" trong editor, giữ scroll sau rejudge trong admin.
**Đánh giá:** ✅ UX. Ổn.

---

### 23. `9ddf418` · 17/04 · judge-server dùng partial by testcase
**Làm gì:** cập nhật code **judge server** (`judge_update/judge.py`, `packet.py`, +1082 dòng) để hiểu `scoring-mode` và chấm partial theo testcase.
**Đánh giá:** ✅ Phần đối ứng phía máy chấm cho commit 15/17. ⚠️ `judge_update/` là code sync **tay** sang máy chấm — dễ lệch phiên bản giữa site và judge. Cần quy trình đảm bảo judge chạy đúng bản này (ghi version/hash).
**Cần làm:** ghi rõ commit hash judge đang deploy; test end-to-end site↔judge cho partial_testcase.

---

### 24. `652697c` · 18/04 · UI/UX contest ranking + penalty_time_format
**Làm gì:** thêm `penalty_time_format` vào `/contest/key/edit`, chỉnh ranking. +24.
**Đánh giá:** ✅ Nhỏ. Ổn.

---

### 25. `aea5f05` · 21/04 · leaderboard podium (top 3) + avatars
**Làm gì:** thêm bục top-3 + avatar user vào bảng xếp hạng user. +200/−10.
**Đánh giá:** ✅ Frontend + view nhẹ. Ổn.

---

### 26. `428eb34` · 25/04 · update RUN flow ⭐
**Làm gì:** **tính năng lớn** — dựng luồng RUN/IDE. Model `RunSubmission` (migration `0226`), field `Problem.enable_new_ide` + `ProblemTestCase.is_sample` (migration `0225`), view `run.py` (`RunSubmitView`/`RunPollView`/`SampleTestCaseView`), template `problem-ide.html`, sửa bridge/judge_list/judgeapi. +2757/−780.
**Đánh giá:** ✅ **Kiến trúc tốt** — tách `RunSubmission` khỏi luồng chấm chính, tái dùng đúng các ràng buộc bảo mật của submit (access, ban, rate limit gộp real+run), `RunPollView` kiểm tra quyền sở hữu. ⚠️ commit rất lớn, khó review một lần; nên tách nhỏ trong tương lai.
**Cần làm:** không gấp. *(Phần I — C1.)*

---

### 27. `0122028` · 25/04 · judge update RUN
**Làm gì:** thêm `judge_update/judge_new_25_04_2025_RUN.py` (+726) — code judge cho luồng RUN.
**Đánh giá:** ✅ Đối ứng judge cho commit 26. ⚠️ đặt tên file theo ngày (`_25_04_2025_`) — dễ tích tụ nhiều bản, khó biết bản nào đang chạy. Nên versioning rõ hơn.

---

### 28. `773975b` · 25/04 · fix small bug
**Làm gì:** sửa nhỏ RUN (url/bridge/template). +4/−9.
**Đánh giá:** ✅ Nhỏ. Ổn.

---

### 29. `a337220` · 02/05 · UX problem-ide
**Làm gì:** đổi field `feedback`→`output` trong `RunPollView`, làm lại UI IDE. +743/−1341 (dọn nhiều).
**Đánh giá:** ✅ Refactor + đổi tên field cho đúng nghĩa. Ổn.

---

### 30. `c0b7a7c` · 02/05 · RUN Custom Testcase
**Làm gì:** cho phép RUN với testcase tự nhập (custom input), không chỉ sample. Sửa bridge/judge_list/judgeapi/view/template.
**Đánh giá:** ✅ Mở rộng hữu ích. ⚠️ custom input là dữ liệu người dùng chạy trực tiếp trên judge — cần giới hạn kích thước/số lượng (được xử lý ở commit 32) và đảm bảo sandbox judge an toàn.

---

### 31. `eca96cc` · 04/05 · update UX
**Làm gì:** truyền `ACE_URL` vào context, chỉnh RUN poll/UI.
**Đánh giá:** ✅ Nhỏ. Ổn.

---

### 32. `07a481f` · 16/05 · IDE limits cho custom testcase + source/output
**Làm gì:** đưa giới hạn IDE ra `settings.py` (`DMOJ_IDE_MAX_CUSTOM_TESTCASES`, `..._INPUT_LENGTH`, `..._OUTPUT_DISPLAY_LENGTH`, `..._SOURCE_LENGTH`), thay hard-code `5`/`65536` bằng `getattr(settings, ...)` ở view + template.
**Đánh giá:** ✅ Cấu hình hoá đúng, chống lạm dụng (input/source quá lớn). Ổn.

---

### 33. `befe0ac` · 16/05 · fix bug Error Display
**Làm gì:** thêm tô màu ANSI cho error display admin (regex `_ANSI_ESCAPE`, `_STATUS_COLOR`). +101/−4.
**Đánh giá:** ⚠️ Chính đoạn code này chứa lỗ hổng XSS được vá ở commit 38 — ở đây error được đưa vào `mark_safe` **chưa escape**. (Xem commit 38.)

---

### 34. `a9873dc` · 16/05 · wsevent cho RUN thay polling ⭐
**Làm gì:** RUN dùng WebSocket realtime thay vì poll. Thêm `EVENT_DAEMON_RUN_KEY`, `RunSubmission.get_id_secret()` (HMAC-SHA512), phát event `run_<id_secret>` ở mọi mốc (processing/grading-begin/test-case/grading-end/compile-error/aborted…). Vẫn giữ polling fallback.
**Đánh giá:** ✅ Nâng cấp UX (realtime), channel khó đoán (`id_secret`) — pattern đúng của DMOJ. 🔴 **nhưng** `EVENT_DAEMON_RUN_KEY` được commit vào `settings.py` (version-controlled) → hiệu quả chống-đoán-channel mất tác dụng nếu không rotate. *(Phần I — A1, C4.)*
**Cần làm:** đưa `EVENT_DAEMON_RUN_KEY` ra biến môi trường.

---

### 35. `d66f3a1` · 20/05 · remove unused .gitmodules
**Làm gì:** xoá `.gitmodules` không dùng.
**Đánh giá:** ✅ 🧹 Dọn dẹp. Ổn.

---

### 36. `9622204` · 22/05 · Update docker for ALOJ
**Làm gì:** đổi tên container thành `aloj_*`, cập nhật docker-compose/Dockerfile/AGENTS.md. +1586/−780.
**Đánh giá:** ✅ Đổi thương hiệu hạ tầng. Ổn. ⚠️ commit này trùng nội dung với merge `1548293` (thấy cùng số dòng) — có dấu hiệu merge chồng nhánh, xem commit 41.

---

### 37. `c829b4a` · 23/05 · fix wsevent RUN, POLLING→WSEVENT
**Làm gì:** thêm `event_dispatcher.off()` (huỷ đăng ký channel khi xong), **xoá hẳn** polling fallback ở RUN.
**Đánh giá:** ⚠️ `off()` là bổ sung đúng (tránh rò channel). Nhưng bỏ hẳn fallback khiến RUN **phụ thuộc hoàn toàn** WebSocket — nếu wsevent chết, RUN kẹt vô hạn. Trớ trêu là ở Gensol (commit 84) bạn lại thêm fallback về.
**Cần làm:** thêm timeout an toàn phía client (ví dụ 60s → poll `RunPollView` 1 lần rồi kết thúc). Thống nhất triết lý fallback giữa RUN và Gensol. *(Phần I — C3.)*

---

### 38. `b6ed72d` · 23/05 · XSS vulnerability in admin panel ⭐
**Làm gì:** escape HTML output lỗi ở nhánh `except` của `RunSubmissionAdmin`: `html = escape(_ANSI_ESCAPE.sub('', obj.error))`.
**Đánh giá:** ✅ **Vá đúng** một stored-XSS leo thang quyền (output do người dùng kiểm soát chảy vào `mark_safe`). ⚠️ chỉ vá nhánh `except`; nhánh `try` (Ansi2HTMLConverter) tạm ổn vì lib có escape, nhưng nên test cả hai nhánh với payload `<script>`/`<img onerror>`.
**Cần làm:** kiểm thử XSS cả 2 nhánh. *(Phần I — A3.)*

---

### 39. `c2b659a` · 23/05 · fix anti-pattern ⭐
**Làm gì:** (a) sửa **mutable default argument** ở `judge_run` (`banned_judges=[]` → `None` + gán trong hàm); (b) `SESSION_SAVE_EVERY_REQUEST=True→False`; (c) giảm IDE limit (5→3, 16384→8192).
**Đánh giá:** ✅ Mutable default arg là bug thật (chia sẻ trạng thái list giữa các lần gọi) — vá đúng. `SESSION_SAVE_EVERY_REQUEST=False` giảm tải ghi session mỗi request — hợp lý. Giảm limit — an toàn hơn.

---

### 40. `6bd44f4` · 23/05 · 🔀 Merge branch 'contest-focus-lock'
**Làm gì:** merge nhánh focus-lock.
**Đánh giá:** ✅ Merge. Nội dung thực chất xem commit 53.

---

### 41. `1548293` · 27/05 · 🔀 Merge remote-tracking 'origin/ALOJ'
**Làm gì:** merge nhánh ALOJ (docker). +1586/−780 — **trùng** commit 36.
**Đánh giá:** ⚠️ Dấu hiệu **lịch sử merge chồng chéo** (cùng thay đổi xuất hiện 2 lần). Không sai chức năng nhưng làm lịch sử khó đọc và dễ gây xung đột. Về sau nên rebase gọn trước khi merge.

---

### 42. `5dd6f59` · 27/05 · alias VNOJ_DISPLAY_RANKS
**Làm gì:** `VNOJ_DISPLAY_RANKS = ALOJ_DISPLAY_RANKS` để migration cũ `0153` (tham chiếu tên VNOJ) vẫn chạy sau khi đổi tên biến.
**Đánh giá:** ✅ Vá tương thích thông minh, gọn. Ổn. *(Phần I — F4.)*

---

### 43. `178cd16` · 28/05 · .MD cho RUN/IDE
**Làm gì:** thêm `IDE_RUN_FEATURE.md` (251 dòng) tài liệu hoá luồng RUN.
**Đánh giá:** ✅ Tài liệu tốt. Ổn.

---

### 44. `72206ff` · 28/05 · Add API KEY + Test Connection ⭐
**Làm gì:** **tính năng AI (nền tảng)** — model `AIAPIKey`/`AIAPIKeyTestLog` (migration `0227`), mã hoá Fernet, `_get_fernet()` suy khoá từ `SECRET_KEY`, view thêm/test/xoá key, trang `api-keys.html`. +854.
**Đánh giá:** ✅ **Tư duy bảo mật đúng** — chỉ lưu ciphertext + last4, không giữ plaintext. 🔴 **nhưng** khoá mã hoá phụ thuộc `SECRET_KEY` (đang lộ ở commit 2) → lộ SECRET_KEY = giải mã mọi API key; và rotate SECRET_KEY = mất mọi key đã lưu.
**Cần làm:** 🟠 tách `AI_API_KEY_ENCRYPTION_KEY` riêng khỏi `SECRET_KEY`. *(Phần I — A1, D1.)*

---

### 45. `e5ddcc5` · 01/06 · update feature AI - add API KEYS
**Làm gì:** admin cho AIAPIKey, tinh chỉnh model/view/template. +183/−38.
**Đánh giá:** ✅ Hoàn thiện commit 44. Ổn. ⚠️ trang admin xem key — đảm bảo **không** hiển thị plaintext, chỉ last4.

---

### 46. `ba46be1` · 01/06 · demo Generate Problem
**Làm gì:** bắt đầu tính năng **tạo đề bằng AI** (`ai_problem_creator.py`), template admin, settings (`AI_PROBLEM_CREATOR_MAX_FILE_SIZE=10MB`, whitelist ext ảnh). +815.
**Đánh giá:** ✅ MVP. ⚠️ nhận **upload ảnh** cho AI đọc đề → cần validate MIME thật (không chỉ đuôi file), giới hạn kích thước (đã có), chống upload file độc.

---

### 47. `0648d6c` · 01/06 · 90% Create Prob with AI
**Làm gì:** tiếp tục tạo đề bằng AI. +133/−398.
**Đánh giá:** ✅ WIP. Ổn.

---

### 48. `cb38aee` · 02/06 · Create Problem + Testcase with AI (MVP) ⭐
**Làm gì:** hoàn thiện MVP tạo đề + sinh testcase bằng AI. Model `generate_testcase`, task Celery, view, migration `0228`/`0229`. +1743.
**Đánh giá:** ✅ MVP lớn. ⚠️ đây là nhánh gensol-v1 — sẽ bị **gỡ bỏ** ở commit 51 rồi làm lại (v2). Cho thấy phần này lặp nhiều lần trước khi ổn.

---

### 49. `d9ba124` · 02/06 · upgrade and fixbug
**Làm gì:** sửa lỗi + thêm field ngôn ngữ cho generate_testcase (migration `0230`). +418/−309.
**Đánh giá:** ✅ WIP. Ổn.

---

### 50. `71fed25` · 03/06 · Generate Testcase with AI
**Làm gì:** thêm model `gensol_submission` (migration `0231`), sửa bridge/judge_list/judgeapi cho luồng gensol. +725/−80.
**Đánh giá:** ⚠️ Bắt đầu đụng bridge cho gensol. Đây là bản v1 sắp bị gỡ (commit 51).

---

### 51. `768140b` · 05/06 · Generate Testcase removed, reimplement later ⭐
**Làm gì:** **gỡ bỏ toàn bộ** tính năng generate-testcase v1 (−2506 dòng), xoá migration `0228`/`0229` cũ.
**Đánh giá:** ⚠️ Đây là bằng chứng của **xung đột đánh số migration & nhánh rối** — phải gỡ để đánh số lại. Không sai, nhưng cho thấy quy trình migration cần siết. *(Phần I — F1.)*
**Cần làm:** thêm `makemigrations --check` vào CI để phát hiện xung đột sớm.

---

### 52. `f79f3d5` · 05/06 · merge AI-feature-v1.1
**Làm gì:** thêm `SUBMIT_RUN_GENSOL_FLOW.md`, `IDE_RUN_FEATURE.md`, `README_ex.md`. +494.
**Đánh giá:** ✅ Tài liệu hoá luồng. Tốt.

---

### 53. `28f6914` · 06/06 · Contest Focus Lock ⭐
**Làm gì:** **tính năng chống gian lận** — `enable_focus_lock` (migration `0228`), middleware set `request.focus_lock_active`, view `ContestFocusLockWrapper` (fullscreen) + `ContestReportFocusViolation` (đếm `focus_violations`), template wrapper.
**Đánh giá:** ✅ Thiết kế hợp lý. ⚠️ là **chống gian lận phía client** → về bản chất bỏ qua được (tắt JS, máy thứ 2); endpoint report có thể bị **không gửi** (không phân biệt "không vi phạm" vs "chặn report") hoặc **spam** (cần rate limit).
**Cần làm:** ghi rõ giới hạn cho giám thị; thêm heartbeat + rate limit endpoint report. *(Phần I — E1.)*

---

### 54. `65f6889` · 08/06 · fix bug not have Testcase
**Làm gì:** xử lý trường hợp bài chưa có testcase khi RUN (import `ProblemTestCase`, thông báo phù hợp).
**Đánh giá:** ✅ Vá nhánh biên hợp lý (tránh crash khi thiếu sample).

---

### 55. `811358d` · 08/06 · fix bug race condition on flow RUN ⭐
**Làm gì:** **sửa bug realtime kinh điển** — RUN lần 2+ kẹt "Running...". Fix ở `daemon.js` (chỉ advance `socket.lastMessage` khi thực sự gửi message) + `event.js` (gửi `set-filter` ngay khi WS đã mở, bỏ delay 200ms) + lưu/khôi phục ngôn ngữ đã chọn.
**Đánh giá:** ✅ **Vá đúng root cause** (late subscription + con trỏ message bị đẩy quá event). Phân tích trong `IDE_RUN_FEATURE.md` rất rõ. ⚠️ chuyển `lastMessage` vào trong `if` — kiểm thử thêm kịch bản nhiều tab/nhiều channel.
**Cần làm:** test đa-tab. *(Phần I — C2.)*

---

### 56. `f99c5fb` · 08/06 · build ai-code-review feature (97%) ⭐
**Làm gì:** **review code bằng AI** — model `AICodeReview` (migration `0229`), view `ai_code_review.py` (build payload cho 4 provider, gọi qua `urllib`), kiểm tra **quyền sở hữu submission**, chặn file-only/source rỗng, yêu cầu key `verified`. +798.
**Đánh giá:** ✅ Kiểm soát quyền + validate tốt. ⚠️ `_AI_REVIEW_TIMEOUT=120s` giữ HTTP request 2 phút → nhiều request đồng thời cạn worker; nên đưa vào Celery. ⚠️ endpoint cần rate limit (tốn token người dùng). ⚠️ endpoint gọi `urllib` tới `base_url` — giữ **whitelist** provider, đừng cho nhập URL tự do (SSRF).
**Cần làm:** Celery + rate limit + timeout hợp lý. *(Phần I — D3.)*

---

### 57. `5acceee` · 08/06 · admin-editable AI prompts
**Làm gì:** model `AIPromptTemplate` (migration `0230`/`0231`) cho admin sửa prompt, thống nhất thông báo no-judge/no-testcase.
**Đánh giá:** ✅ Linh hoạt. 🔴 **rủi ro `.format()`:** prompt dùng `template.format(problem_description=...)`; nếu đề chứa `{`/`}` (code, LaTeX) → `str.format` **crash** hoặc hiểu nhầm placeholder.
**Cần làm:** escape `{{}}` hoặc dùng `string.Template`. *(Phần I — D4.)*

---

### 58. `fc425d2` · 12/06 · UX/UI - PDF - button
**Làm gì:** UX lớn cho problem-detail/IDE/submission, thêm `local_settings_root.py`. +1678/−486.
**Đánh giá:** ✅ Frontend chủ yếu. ⚠️ kiểm tra `local_settings_root.py` **không** chứa secret thật (rủi ro lặp lại commit 2).

---

### 59. `9c0c30f` · 13/06 · 🔀 Merge branch 'ai-review-code'
**Làm gì:** merge nhánh review code. +2719/−506.
**Đánh giá:** ✅ Merge (commit 56/57).

---

### 60. `158f43e` · 13/06 · update EDITOR ⭐
**Làm gì:** tích hợp **CodeMirror 6** (build `_build/codemirror6/*`, completions, min.js). +3000/−1434 (bao gồm file build lớn).
**Đánh giá:** ✅ Nâng cấp editor. ⚠️ commit chứa **file build/minified** (`codemirror-ide.min.js`, `package-lock.json`) — nên cân nhắc build ở CI thay vì commit artefact, để repo nhẹ và tránh review nhầm code sinh tự động.

---

### 61. `9e6e533` · 13/06 · rewrite vnoj → aloj
**Làm gì:** đổi tên thương hiệu VNOJ→ALOJ trên **495 file** (chủ yếu asset ace/accordion + settings). +534/−21.
**Đánh giá:** ✅ Đổi tên hàng loạt. ⚠️ commit đụng gần 500 file rất khó review — rủi ro sửa nhầm string trong code logic. Nên tách "đổi tên asset" và "đổi tên trong code" thành 2 commit.

---

### 62. `f00eec8` · 13/06 · 🔀 Merge branch 'editor-tool'
**Đánh giá:** ✅ Merge (commit 60/61).

---

### 63. `8b3a289` · 13/06 · update LOGO, icons, favicon
**Làm gì:** thay logo/icon/manifest. +822/−648.
**Đánh giá:** ✅ Branding. Ổn.

---

### 64. `3dd6e95` · 14/06 · build generate testcase with AI (v2) ⭐
**Làm gì:** **Gensol v2** — `utils/gensol.py` (máy trạng thái generator→solution→zip, +321 dòng), model `gensol_job` (migration `0232`), view `gensol.py`/`ai_gen_code.py`, sửa bridge (`base_handler`/`django_handler`/`judge_handler`/`judge_list`), settings (`GENSOL_*`, `EVENT_DAEMON_GENSOL_KEY`), command cleanup. +1881.
**Đánh giá:** ✅ Máy trạng thái rõ, có cleanup + giới hạn zip. 🔴 **`start_gensol_job` xoá testcase gốc NGAY từ đầu** (`ProblemTestCase...delete()`) và ghi đè `data.zip` — nếu lỗi giữa chừng **mất sạch test gốc, không rollback**. 🔴 `EVENT_DAEMON_GENSOL_KEY` commit vào settings. ⚠️ cần xác nhận `_upload_zip_and_compile` (I/O nặng) chạy trong Celery, không block request.
**Cần làm:** 🟠 sinh vào tạm + backup, chỉ swap khi DONE; đưa key ra env. *(Phần I — D2.)*

---

### 65. `87d8421` · 14/06 · changes prompt generate testcase
**Làm gì:** chỉnh prompt gensol (migration `0233` seed prompt).
**Đánh giá:** ✅ Nhỏ. Ổn.

---

### 66. `362c70b` · 14/06 · upgrade prompt cho subtask
**Làm gì:** prompt gensol hiểu subtask. +44/−13.
**Đánh giá:** ✅ Nhỏ. Ổn.

---

### 67. `fb6de8d` · 14/06 · update prompt and validate
**Làm gì:** thêm validate cho gensol prompt. +32/−2.
**Đánh giá:** ✅ Thêm validate — tốt.

---

### 68. `0bf7ab6` · 15/06 · update migrations ⚠️
**Làm gì:** sửa các migration **rất cũ** (`0001_squashed`, `0088`, `0116`, `0117`) đổi `related_name` và `to='judge.Profile'`→`'judge.profile'`.
**Đánh giá:** ⚠️ Sửa để tương thích Django mới, **nhưng sửa migration lịch sử đã áp dụng** làm hash lệch giữa các môi trường; môi trường chạy lại từ đầu có thể ra schema khác. Chỉ nên làm khi thật cần.
**Cần làm:** so `showmigrations` giữa dev/prod; tài liệu hoá lý do. *(Phần I — F3.)*

---

### 69. `fbd2cea` · 15/06 · 🔀 Merge branch 'generate-testcase-v2'
**Đánh giá:** ✅ Merge Gensol v2 (commit 64–68).

---

### 70. `e9633a6` · 15/06 · fix join contest LIVE/SPECTATE ⭐
**Làm gì:** thêm cờ `ContestParticipation.has_left` (migration `0234`): rời LIVE khi contest chưa xong → đánh dấu; vào lại chỉ được SPECTATE; list contest coi `has_left` như đã kết thúc. +2687 (kèm tài liệu `document/`).
**Đánh giá:** ✅ **Logic đúng, cần thiết cho công bằng** (chống reset đồng hồ bằng leave/rejoin).
**Cần làm:** test join→leave→rejoin phải ra spectate. *(Phần I — E2.)*

---

### 71. `d365019` · 15/06 · update
**Làm gì:** thêm README BKDNOJ (520 dòng), `throttle_discord_webhook.py`, chỉnh nhiều file (comments/forms/middleware/judge_list). +868/−322.
**Đánh giá:** ✅ Tài liệu + tinh chỉnh. ⚠️ commit "update" gộp nhiều thứ không liên quan — khó review; nên tách theo chủ đề.

---

### 72. `35788b5` · 15/06 · update document
**Đánh giá:** ✅ Tài liệu. Ổn.

---

### 73. `05cc076` · 15/06 · update document
**Làm gì:** đổi tên/di chuyển file (0 dòng thay đổi nội dung).
**Đánh giá:** ✅ 🧹 Rename. Ổn.

---

### 74. `abf4f93` · 16/06 · update OJ
**Làm gì:** `Disconnect` exception nhận `reason`, sửa bridge/base_handler/judge_handler, `problem.py`, tags.json, judge_update. +316/−44.
**Đánh giá:** ✅ Cải thiện xử lý ngắt kết nối (kèm lý do) — tốt cho debug. Ổn.

---

### 75. `577d5dc` · 16/06 · Suggest tags + assess user capabilities ⭐
**Làm gì:** **gợi ý tag bằng AI** (`ai_tag_suggest.py`) — lấy top-3 AC ngắn nhất làm ngữ cảnh, prompt buộc trả JSON array tag id; model `user_problem_tag` (migration `0236`/`0237`), đánh giá năng lực user. +924.
**Đánh giá:** ✅ Tính năng hay. ⚠️ **phải parse JSON phòng thủ**: model có thể trả rác/tag không tồn tại → validate từng id nằm trong danh sách hợp lệ trước khi ghi DB. ⚠️ yêu cầu ≥3 AC — hợp lý.
**Cần làm:** xác nhận đoạn parse có try/except + validate id. *(Phần I — D3.)*

---

### 76. `8286b74` · 16/06 · update BKDNOJ
**Làm gì:** Dockerfile (bridged/celery/site), oj-status, `document/BAOCAO.md`. +155/−68.
**Đánh giá:** ✅ Hạ tầng + tài liệu. Ổn.

---

### 77. `e855cec` · 16/06 · update .gitignore
**Làm gì:** thêm 1 dòng vào `.gitignore`.
**Đánh giá:** ✅ 🧹 Tốt — nhưng **quá muộn** cho secret đã commit ở commit 2. Cần kèm việc xoá secret khỏi lịch sử.

---

### 78. `49ca955` · 16/06 · 🔀 Merge branch 'tags-and-reviews'
**Đánh giá:** ✅ Merge (commit 75).

---

### 79. `9bdde5c` · 17/06 · remove PDF for AI create problem
**Làm gì:** bỏ hỗ trợ PDF khi tạo đề bằng AI (chỉ còn ảnh), thêm `chuong5_thuc_nghiem.md`, `k6_load_test.js`. +423/−36.
**Đánh giá:** ✅ Thu hẹp input (chỉ ảnh) — giảm bề mặt tấn công. Có script load-test k6 — tốt cho đánh giá hiệu năng.

---

### 80. `5898fc8` · 17/06 · update README.md
**Đánh giá:** ✅ Tài liệu. Ổn.

---

### 81. `67f0a6c` · 17/06 · update infomation BKDNOJ
**Làm gì:** đổi thông tin thương hiệu trên 12 file. +40/−30.
**Đánh giá:** ✅ Branding. Ổn.

---

### 82. `e0bfe03` · 21/06 · update README + initialize
**Làm gì:** thêm `docker compose build base`, script `initialize` tạo thêm thư mục `generate_testcase`.
**Đánh giá:** ✅ Vá quy trình khởi tạo (Gensol cần thư mục working). Ổn.

---

### 83. `0e0626b` · 28/06 · fix bug GENERATOR and UX/UI
**Làm gì:** model/admin/view `ai_gen_code` (migration `0238`), sửa gensol view + template. +233/−97.
**Đánh giá:** ✅ Hoàn thiện Gensol. Ổn.

---

### 84. `05fa706` · 28/06 · GensolJob.DoesNotExist + Polling fallback + start fail ⭐
**Làm gì:** vá **3 nhánh thất bại** của Gensol: (a) `GensolJob.DoesNotExist` im lặng → phát event `internal-error` báo user; (b) thêm **polling fallback** (interval 10s) bắt event WS bị lỡ; (c) `start_gensol_job` fail sau khi tạo job vẫn trả 200 → thêm `refresh_from_db()` + kiểm tra `status=='ERROR'` trả 500; (d) generator editor cho superuser sửa.
**Đánh giá:** ✅ Cả 3 fix đúng, đều là **thiếu xử lý nhánh lỗi** — dấu hiệu nên rà tổng thể "mọi nhánh lỗi phải (1) cập nhật DB, (2) báo user, (3) cleanup". ⚠️ Gensol thêm lại fallback trong khi RUN (commit 37) đã bỏ → **không nhất quán** triết lý.
**Cần làm:** thống nhất chiến lược fallback; rà mọi nhánh lỗi Gensol. *(Phần I — C3, D2.)*

---

## Tổng kết Phần II

**Nhóm commit đáng chú ý nhất (đọc kỹ):**
- 🔴 **Bảo mật:** `8fc54e1` (secret+hosts), `72206ff`/`3dd6e95`/`a9873dc` (khoá commit public), `b6ed72d` (XSS đã vá).
- ⭐ **Bug hay đã vá đúng:** `c69bb6e` (scoring), `811358d` (race condition), `39...c2b659a` (mutable default), `bfcc912` (auto-rescore), `e9633a6` (leave/rejoin).
- 🟠 **Rủi ro còn lại:** `3dd6e95` (Gensol xoá test gốc), `5acceee` (`.format` prompt), `768140b`/`0bf7ab6` (migration lộn xộn), `37...c829b4a` (bỏ fallback RUN).

**Quan sát về quy trình (không phải bug code, nhưng ảnh hưởng chất lượng):**
1. Nhiều commit **quá lớn/gộp nhiều việc** (`428eb34`, `9e6e533`, `d365019`) → khó review, khó bisect.
2. **Migration lộn xộn khi merge nhiều nhánh** → nên thêm `makemigrations --check` vào CI.
3. **Secret & khoá lọt vào version control nhiều lần** → cần chuẩn hoá dùng biến môi trường ngay.
4. **Judge code sync tay** (`judge_update/`) đặt tên theo ngày → khó biết bản đang chạy; nên versioning.

Nhìn tổng thể, đây là một project **tham vọng và có chiều sâu kỹ thuật tốt** (realtime, scoring, AI, chống gian lận). Các bug bạn tự phát hiện và vá đều đúng bản chất. Vấn đề lớn nhất **không** nằm ở năng lực code mà ở **quản lý secret** và **quy trình (migration, kích thước commit)** — đều khắc phục được bằng thói quen, không cần viết lại gì.

---

*Hết Phần II. Kết hợp với **Phần I** (phân tích theo chủ đề) để có bức tranh đầy đủ.*
