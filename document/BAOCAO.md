# ĐỀ TÀI

**“Nghiên cứu, xây dựng và mở rộng hệ thống chấm bài lập trình trực tuyến BKDNOJ dựa trên nền tảng DMOJ/VNOJ, tích hợp IDE trực tuyến, trợ lý AI và cơ chế chống gian lận trong thi đấu”**

> Ghi chú dàn ý: Báo cáo được tổ chức theo cấu trúc đồ án tốt nghiệp gồm phần Mở đầu, 5 chương nội dung, phần Kết luận, Tài liệu tham khảo và Phụ lục. Mỗi mục bên dưới nêu *nội dung cần viết* và *bằng chứng/đối chiếu mã nguồn thực tế* để đảm bảo báo cáo bám sát hệ thống đã cài đặt.

---

# PHẦN ĐẦU (Front matter)

Các thành phần đặt trước Chương 1, theo mẫu đồ án:

* **Trang bìa, trang phụ bìa, nhiệm vụ đồ án, lời cam đoan, lời cảm ơn.**
* **Tóm tắt (Abstract):** 1 trang tiếng Việt + 1 trang tiếng Anh, tóm tắt mục tiêu, phương pháp, kết quả chính và đóng góp.
* **Mục lục, Danh mục hình vẽ, Danh mục bảng biểu.**
* **Danh mục từ viết tắt:** OJ (Online Judge), IDE, AI/LLM, API, WS (WebSocket), DB, AC/WA/TLE/MLE/RTE/CE/IE/OLE, GenSol (Generate Solution/Testcase), Elo-MMR…

---

# MỞ ĐẦU — 3 đến 5 trang

Phần mở đầu cần có đủ: **lý do chọn đề tài, mục tiêu, phạm vi và đối tượng nghiên cứu, phương pháp nghiên cứu, câu hỏi nghiên cứu và cấu trúc đồ án.**

## 1. Lý do chọn đề tài

* Việc học lập trình và rèn luyện thuật toán cần một môi trường thực hành **liên tục, tự động và công bằng**.
* Chấm bài thủ công tốn thời gian, dễ sai sót và khó bảo đảm tính khách quan; Online Judge tự động hóa toàn bộ chu trình *nộp bài → biên dịch → chạy test → so khớp kết quả → trả điểm*.
* Các nền tảng mã nguồn mở như DMOJ/VNOJ đã trưởng thành nhưng **chưa đáp ứng đầy đủ** một số nhu cầu thực tế: thiếu IDE trực tuyến để thử nghiệm nhanh, chưa có trợ lý AI hỗ trợ người học và người ra đề, thiếu cơ chế chống gian lận khi thi.
* Hệ thống **BKDNOJ** được xây dựng dựa trên DMOJ/VNOJ nhằm khắc phục các hạn chế đó, phục vụ luyện tập, tổ chức kỳ thi và hỗ trợ giảng dạy.

## 2. Mục tiêu đề tài

* Nghiên cứu kiến trúc và cơ chế hoạt động của hệ thống Online Judge (DMOJ/VNOJ).
* Triển khai hệ thống BKDNOJ nhiều dịch vụ bằng Docker Compose (site, bridge, judge, WebSocket, Redis, Celery, database).
* Mở rộng các chức năng mới: **IDE trực tuyến**, **chế độ chấm điểm linh hoạt**, **AI Code Review / AI Problem Creator / AI Generate Testcase**, **quản lý API key mã hóa**, **chống gian lận Contest Focus Lock**, **hệ thống rating Elo-MMR**.
* Kiểm thử, thực nghiệm và đánh giá hệ thống trên các luồng nộp bài, chạy thử, chấm điểm và cập nhật realtime.

## 3. Phạm vi và đối tượng nghiên cứu

* **Đối tượng:** kiến trúc Online Judge mã nguồn mở, cơ chế judge/sandbox, hàng đợi tác vụ, giao tiếp realtime, tích hợp mô hình ngôn ngữ lớn (LLM).
* **Phạm vi:** tập trung vào hệ thống web (problem, submission, contest, judge, IDE, AI, rating). Kế thừa và cấu hình sandbox của DMOJ judge thay vì viết lại từ đầu; không phát triển ứng dụng di động.

## 4. Phương pháp nghiên cứu

* Nghiên cứu tài liệu và mã nguồn DMOJ/VNOJ; phân tích kiến trúc hệ thống hiện có.
* Thiết kế và cài đặt bổ sung chức năng mới theo quy trình kỹ thuật phần mềm (phân tích yêu cầu → thiết kế → cài đặt → kiểm thử).
* Triển khai thực nghiệm bằng Docker Compose; thu thập số liệu chức năng và hiệu năng để đánh giá.

## 5. Câu hỏi nghiên cứu (Research Questions)

* **RQ1:** Có thể mở rộng nền tảng DMOJ/VNOJ để bổ sung IDE trực tuyến và chấm điểm linh hoạt mà vẫn giữ tương thích với giao thức judge gốc không?
* **RQ2:** Việc tích hợp trợ lý AI (review code, sinh đề, sinh testcase) có khả thi và hữu ích cho người học và người ra đề không?
* **RQ3:** Cơ chế Contest Focus Lock kết hợp auto-ban có giúp giảm gian lận khi thi trên nền web không?
* **RQ4:** Hệ thống có đáp ứng được yêu cầu phi chức năng (hiệu năng, realtime, bảo mật) ở quy mô luyện tập/thi nội bộ không?

## 6. Cấu trúc đồ án

* **Chương 1 — Tổng quan:** bối cảnh, các hệ thống liên quan, đóng góp của đề tài.
* **Chương 2 — Cơ sở lý thuyết và công nghệ.**
* **Chương 3 — Phân tích và thiết kế hệ thống.**
* **Chương 4 — Xây dựng và triển khai hệ thống.**
* **Chương 5 — Kiểm thử, thực nghiệm và đánh giá.**
* **Kết luận và hướng phát triển.**

---

# CHƯƠNG 1: TỔNG QUAN — 8 đến 10 trang

## 1.1. Bối cảnh và động lực

### 1.1.1. Nhu cầu đào tạo lập trình và tổ chức thi đấu

* Phong trào học lập trình, luyện thuật toán và thi đấu (ICPC, Olympic Tin học, các kỳ thi nội bộ) ngày càng phát triển.
* Nhu cầu một nền tảng tự động hóa chấm bài, tổ chức contest và theo dõi tiến bộ của người học là thiết yếu đối với trường học và câu lạc bộ.

### 1.1.2. Hạn chế của các nền tảng hiện có

* Nền tảng thương mại (Codeforces, LeetCode, AtCoder): mạnh nhưng **đóng**, khó tùy biến cho môi trường nội bộ, khó kiểm soát dữ liệu.
* Nền tảng mã nguồn mở (DMOJ/VNOJ): mở và mạnh nhưng **thiếu** IDE trực tuyến tích hợp, trợ lý AI, cơ chế chống gian lận hiện đại, và việc sinh testcase còn thủ công.
* Đây chính là **khoảng trống** mà đề tài hướng tới lấp đầy.

## 1.2. Các hệ thống liên quan

### 1.2.1. Online Judge truyền thống

Mô tả nguyên lý chung và so sánh các nền tảng tiêu biểu:

| Hệ thống   | Đặc điểm                                 |
| ---------- | ---------------------------------------- |
| Codeforces | Contest mạnh, cộng đồng lớn, hệ thống rating chuẩn |
| AtCoder    | Bộ đề chuẩn, contest định kỳ              |
| LeetCode   | IDE thân thiện, phù hợp luyện phỏng vấn   |
| DMOJ       | Mã nguồn mở, kiến trúc judge/sandbox riêng |
| VNOJ       | Fork từ DMOJ, bản địa hóa cho cộng đồng Việt Nam |
| BKDNOJ     | Fork/tùy biến từ VNOJ, bổ sung IDE + AI + chống gian lận |

### 1.2.2. Nền tảng mã nguồn mở DMOJ/VNOJ và lý do kế thừa

* DMOJ là Online Judge mã nguồn mở với kiến trúc tách biệt **site ↔ bridge ↔ judge**, hỗ trợ sandbox (`cptbox`) và hơn 60 ngôn ngữ lập trình.
* VNOJ kế thừa DMOJ, bản địa hóa và bổ sung tính năng cho cộng đồng Việt Nam.
* BKDNOJ kế thừa DMOJ/VNOJ → **không viết lại từ số 0** mà nghiên cứu, triển khai, tùy biến và mở rộng một hệ thống lớn, tận dụng sandbox và giao thức judge đã được kiểm chứng.

### 1.2.3. Định vị đề tài

Khác với các nền tảng nguồn mở gốc, BKDNOJ bổ sung đồng thời bốn nhóm mở rộng: IDE trực tuyến, trợ lý AI đa nhà cung cấp, chống gian lận thi đấu, và chấm điểm linh hoạt — tạo nên một nền tảng "luyện tập + thi đấu + hỗ trợ học tập" toàn diện hơn.

## 1.3. Đóng góp của đề tài

### 1.3.1. Yêu cầu đặc thù

* Cần giữ **tương thích ngược** với giao thức judge của DMOJ trong khi mở rộng tính năng.
* Cần cơ chế **chạy thử nhanh** tách biệt khỏi luồng chấm chính thức.
* Cần **bảo mật** khóa API của người dùng và dữ liệu cuộc thi.

### 1.3.2. Các đóng góp chính

1. **Chế độ chấm điểm linh hoạt (Scoring Mode):** 3 chế độ short circuit / partial by subtask / partial by testcase.
2. **IDE trực tuyến** kiểu LeetCode dựa trên CodeMirror 6, với pipeline `run-request` độc lập.
3. **Bộ trợ lý AI:** Code Review, Problem Creator, Generate Testcase (GenSol), hỗ trợ 4 nhà cung cấp (OpenAI/Gemini/Claude/DeepSeek).
4. **Quản lý API key** theo người dùng, mã hóa bằng Fernet.
5. **Contest Focus Lock** + cơ chế auto-ban chống gian lận.
6. **Hệ thống rating Elo-MMR** và bảng xếp hạng.

## 1.4. Bài toán đặt ra cho BKDNOJ

Tổng hợp các vấn đề cần giải quyết: hệ thống chấm bài ổn định, giao diện dễ dùng, IDE chạy thử, trợ lý AI cho người học/người ra đề, chống gian lận, và kiến trúc dễ triển khai – dễ mở rộng.

---

# CHƯƠNG 2: CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ SỬ DỤNG — 12 đến 16 trang

Chương này trình bày nền tảng lý thuyết của các thành phần cốt lõi, sau đó tổng hợp các công nghệ thực tế được dùng trong hệ thống (Python 3.11, Django 4.2+, uWSGI, Celery, MariaDB, Redis, Node.js WebSocket, jQuery, SCSS, ACE Editor, CodeMirror 6, Chart.js, MathJax, Docker, Nginx, giao thức TCP + Zlib và các nhà cung cấp AI).

## 2.1. Mô hình chấm bài trong hệ thống Online Judge

### 2.1.1. Quy trình chấm tự động

Trình bày nguyên lý: *người dùng nộp mã → biên dịch trong môi trường cô lập → chạy lần lượt từng testcase với giới hạn thời gian/bộ nhớ → so khớp output với đáp án (hoặc qua checker) → tổng hợp điểm và trạng thái*.

### 2.1.2. Các trạng thái và kết quả chấm

Trình bày tập trạng thái và kết quả (sẽ chi tiết hóa ở mục 3.4): QU/P/G/D và AC/WA/TLE/MLE/RTE/CE/IE/OLE; ý nghĩa của checker (so khớp tuyệt đối, bỏ qua khoảng trắng, checker tùy biến).

### 2.1.3. Mô hình chấm điểm (scoring model)

Cơ sở lý thuyết cho ba chiến lược tính điểm — đây là nền tảng cho đóng góp "Scoring Mode" ở Chương 3:

* **All-or-nothing (short circuit):** dừng tại test sai đầu tiên, "được tất cả hoặc không gì".
* **Partial theo subtask/batch (kiểu IOI):** mỗi subtask độc lập, một test sai làm subtask đó 0 điểm.
* **Partial theo từng testcase:** cộng dồn điểm theo từng test đúng.

## 2.2. Cô lập và bảo mật môi trường thực thi (Sandbox)

Mã người dùng là **mã không tin cậy**, cần chạy trong môi trường cô lập:

* **`cptbox` (ptrace-based sandbox của DMOJ):** lọc system call, kiểm soát truy cập file/mạng, ngăn mã độc thoát khỏi sandbox.
* **Giới hạn tài nguyên:** thời gian CPU/thực thi, bộ nhớ (address space), kích thước output, số tiến trình.
* Nền tảng lý thuyết: namespace/cgroup của Linux, nguyên tắc least-privilege.

## 2.3. Kiến trúc bất đồng bộ và hàng đợi tác vụ

### 2.3.1. Mô hình xử lý bất đồng bộ với message broker

Lý do tách tác vụ nặng (chấm bài, rejudge, export, gửi email, sinh PDF) khỏi luồng request HTTP để bảo đảm độ phản hồi của web.

### 2.3.2. Redis và Celery

* **Redis:** cache, session, message broker.
* **Celery:** xử lý tác vụ nền bất đồng bộ (concurrency 2 worker trong cấu hình mặc định).
* Cơ chế Generate Testcase (GenSol) cũng tận dụng pipeline Bridge/Judge để xử lý nền.

## 2.4. Giao tiếp realtime với WebSocket

* Vấn đề: trạng thái chấm bài thay đổi liên tục, polling tốn tài nguyên.
* Giải pháp: dịch vụ **WSEvent (Node.js)** đẩy sự kiện realtime; trình duyệt không cần reload; có HTTP polling fallback cho client không hỗ trợ WebSocket.

## 2.5. Giao thức Judge (Bridge protocol)

* Site gửi request → **Bridge** (trung gian) → **Judge** biên dịch và chạy test → kết quả về Bridge.
* Đóng gói gói tin: `json.dumps` → nén `zlib` → đóng khung bằng **4 byte độ dài** (header) trên kết nối TCP.
* Kết quả đi: Judge → Bridge → DB/WSEvent → Browser.

## 2.6. Containerization với Docker và Docker Compose

* Đóng gói môi trường, chạy nhiều dịch vụ tách biệt, dễ tái tạo và triển khai.
* Cô lập tài nguyên giữa các container; định nghĩa network nội bộ và volume bền vững.

## 2.7. Mã hóa và bảo mật dữ liệu nhạy cảm

* **Fernet (symmetric encryption):** dùng để mã hóa **API key của người dùng** trước khi lưu DB; khóa Fernet dẫn xuất từ **SHA-256 của `SECRET_KEY`**.
* Chỉ lưu **last4** của key để nhận diện; không lưu khóa ở dạng rõ.

## 2.8. Tích hợp mô hình ngôn ngữ lớn (LLM)

* Nguyên lý gọi LLM qua API: prompt template + ngữ cảnh (mã nguồn/đề bài) → mô hình trả về phân tích/đề bài/lời giải.
* Hệ thống hỗ trợ **4 nhà cung cấp**: OpenAI, Gemini, Claude, DeepSeek; prompt template cấu hình được từ admin (gồm khóa `ai_gen_code` cho GenSol).

## 2.9. Thuật toán xếp hạng Elo-MMR

* Mô hình rating người chơi như **phân phối xác suất** (mean $\mu$, variance $\sigma^2$), cập nhật theo Bayesian sau mỗi contest `is_rated = True`.
* Dùng hàm **tanh** mô hình hóa phi tuyến kết quả đối đầu; rating hiển thị $= \mu - (\sigma - \sigma_{lim})$.
* Tệp mã nguồn: `judge/ratings.py`. (Chi tiết ở mục 3.8 và Phụ lục.)

## 2.10. Các code editor: ACE và CodeMirror 6

* **ACE Editor (1.4.14):** editor truyền thống cho trang submit/admin.
* **CodeMirror 6:** editor hiện đại cho giao diện IDE mới (`problem-ide.html`), hỗ trợ 30+ ngôn ngữ syntax highlighting, layout 2 cột co giãn.

## 2.11. Tổng hợp lựa chọn công nghệ

Đưa **một bảng tổng hợp** ánh xạ *yêu cầu → công nghệ → lý do lựa chọn* (ví dụ: web backend → Django; broker → Redis; realtime → WSEvent; sandbox → cptbox; container → Docker; mã hóa → Fernet…), kèm nhận xét ngắn về sự phù hợp.

---

# CHƯƠNG 3: PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG — 14 đến 18 trang

Đây nên là chương mạnh nhất.

## 3.1. Yêu cầu chức năng

Chia theo actor:

### Người dùng

* Đăng ký, đăng nhập.
* Xem bài tập.
* Submit code.
* Xem kết quả (theo chế độ chấm điểm: short circuit / partial by subtask / partial by testcase).
* Chạy thử bằng IDE.
* Xem contest.
* Tham gia contest ở chế độ Focus Lock (khóa tập trung): bắt buộc fullscreen, không chuyển tab/thoát màn hình khi đang thi.
* Bình luận/blog/ticket nếu có.

### Admin/Giảng viên

* Quản lý problem.
* Quản lý testcase.
* Quản lý contest.
* Chọn chế độ chấm điểm cho problem (`scoring_mode`: short circuit / partial by subtask / partial by testcase).
* Bật/tắt Contest Focus Lock (khóa tập trung) cho từng contest và theo dõi số lần vi phạm (`focus_violations`).
* Quản lý user.
* Cấu hình judge.
* Tạo đề bằng AI.
* Quản lý API key hoặc prompt.

### Judge server

* Nhận packet.
* Biên dịch code.
* Chạy test.
* Trả kết quả từng testcase.

### AI service

* Review code.
* Tạo đề bài.
* Generate testcase tự động.
* Kiểm tra API key.

### 3.1.5. Đặc tả Use Case

Lập **sơ đồ Use Case** cho ba nhóm tác nhân (Người dùng/Thí sinh, Admin/Giảng viên, và các tác nhân hệ thống Judge/AI), kèm **bảng đặc tả** cho các use case trọng yếu. Mẫu bảng đặc tả:

| Mục | Nội dung |
| --- | --- |
| **Use case** | Nộp bài (Submit) |
| **Tác nhân** | Người dùng đã đăng nhập |
| **Tiền điều kiện** | Đã đăng nhập, problem cho phép nộp |
| **Luồng chính** | Chọn ngôn ngữ → nhập/upload mã → gửi → hệ thống tạo `Submission` (QU) → chấm → cập nhật kết quả realtime |
| **Luồng phụ/ngoại lệ** | CE nếu lỗi biên dịch; IE nếu lỗi nội bộ; rate-limit nếu nộp quá nhanh |
| **Hậu điều kiện** | Lưu kết quả, cập nhật điểm/bảng xếp hạng |

Lập bảng tương tự cho: *Chạy thử bằng IDE (Run)*, *Yêu cầu AI Review*, *Tạo đề bằng AI*, *Sinh testcase (GenSol)*, *Tham gia contest có Focus Lock*, *Quản lý API key*.

## 3.2. Yêu cầu phi chức năng

Trình bày dưới dạng **bảng tiêu chí phi chức năng**:

| Nhóm | Yêu cầu |
| --- | --- |
| **Bảo mật** | Mã hóa API key (Fernet); phân quyền theo vai trò; chống XSS/CSRF; cô lập sandbox khi chấm |
| **Hiệu năng** | Chấm bài ổn định; cập nhật trạng thái realtime; chịu được tải nộp đồng thời ở quy mô lớp/CLB |
| **Khả dụng/Realtime** | WebSocket cập nhật không cần reload; có HTTP polling fallback |
| **Khả mở rộng** | Dễ thêm judge server; kiến trúc nhiều dịch vụ tách biệt |
| **Khả triển khai** | Triển khai bằng Docker Compose; cấu hình qua biến môi trường |
| **Tính dùng được** | Giao diện responsive; hỗ trợ nhiều ngôn ngữ lập trình; đa ngôn ngữ giao diện |

## 3.3. Kiến trúc tổng thể

Dựa trên repo, kiến trúc BKDNOJ gồm nhiều service: Nginx, Site Django, WSEvent Node, Redis, Celery, MariaDB, Bridge Daemon và External Judge Servers. ([GitHub][3])

Sơ đồ nên vẽ:

```text
Browser
   |
 Nginx
   |
   +--> Django Site / uWSGI
   |        |
   |        +--> MariaDB
   |        +--> Redis
   |        +--> Celery
   |        +--> Bridge
   |
   +--> WSEvent
            ^
            |
Bridge <--> Judge Server
```

## 3.4. Thiết kế luồng nộp bài chính thức

Nên viết rất kỹ.

Theo repo, luồng submit là: User submit → Nginx → Django Site → lưu Submission vào DB với status `QU` → gửi packet đến Bridge → Judge biên dịch/chạy testcase → Bridge lưu kết quả → cập nhật status `D` → gửi event đến WSEvent → Browser cập nhật realtime. ([GitHub][3])

Các status nên đưa vào bảng:

| Status | Ý nghĩa    |
| ------ | ---------- |
| QU     | Queued     |
| P      | Processing |
| G      | Grading    |
| D      | Done       |

Các result:

| Result | Ý nghĩa               |
| ------ | --------------------- |
| AC     | Accepted              |
| WA     | Wrong Answer          |
| TLE    | Time Limit Exceeded   |
| MLE    | Memory Limit Exceeded |
| RTE    | Runtime Error         |
| CE     | Compile Error         |
| IE     | Internal Error        |
| OLE    | Output Limit Exceeded |

### 3.4.1. Thiết kế chế độ chấm điểm (Scoring Mode)

Đây là một đóng góp riêng so với cách chấm mặc định của DMOJ/VNOJ. Thay vì chỉ có cờ boolean `partial`, hệ thống bổ sung trường `scoring_mode` trên model `Problem` (migration `0222_problem_scoring_mode`) với 3 chế độ:

| Scoring mode       | Giá trị            | Ý nghĩa                                                                 |
| ------------------ | ------------------ | ---------------------------------------------------------------------- |
| Short circuit      | `short_circuit`    | Dừng ngay khi gặp test sai, tính điểm theo kiểu “được tất cả hoặc không gì” (all-or-nothing). |
| Partial by subtask | `partial_batch`    | Chấm theo subtask/batch: một subtask sai thì subtask đó được 0 điểm, các subtask khác vẫn được tính. |
| Partial by testcase| `partial_testcase` | Chấm theo từng testcase: mỗi test đúng đều được cộng điểm tương ứng.    |

Nên nhấn mạnh:

* Mặc định là `partial_batch` (chấm theo subtask).
* Trường boolean `short_circuit` cũ vẫn được giữ lại và tự động tính từ `scoring_mode` trong `Problem.save()` để tương thích ngược với giao thức judge.
* Logic gom test theo batch/subtask được xử lý ở `judge/views/submission.py` (`group_test_cases`, `make_batch`), hiển thị điểm từng subtask/testcase trên trang submission.
* Giúp giảng viên linh hoạt thiết kế bài: bài kiểu IOI (subtask) hoặc bài cộng điểm từng test.

File liên quan:
* Model: `judge/models/problem.py` (`ScoringMode`, `SCORING_MODE_CHOICES`, `scoring_mode`).
* View: `judge/views/submission.py` (`group_test_cases`, `make_batch`).
* Migration: `0222_problem_scoring_mode.py`.

## 3.5. Thiết kế luồng IDE Run

Đây là điểm mới nên viết riêng.

Theo tài liệu IDE, BKDNOJ thêm giao diện IDE kiểu LeetCode cho từng bài; khi admin bật `enable_new_ide`, trang problem chuyển sang layout 2 cột gồm đề bài và CodeMirror 6 editor + panel kết quả. Tính năng Run dùng model riêng `RunSubmission`, gửi qua pipeline `run-request` độc lập với `submission-request`, kết quả trả realtime qua WebSocket. ([GitHub][5])

Nên nhấn mạnh:

* Không dùng bảng `Submission`.
* Có bảng riêng `RunSubmission`.
* Chỉ chạy sample testcase.
* Không ảnh hưởng bảng xếp hạng/chấm chính thức.
* Phù hợp để user test code trước khi submit.

## 3.6. Thiết kế cơ sở dữ liệu

### 3.6.1. Sơ đồ thực thể – quan hệ (ERD)

Trình bày **ERD tổng thể** ở mức khái quát (xem `document/gzx/05_erd_database.dbml`), tập trung vào các bảng cốt lõi và quan hệ giữa chúng. Nêu nguyên tắc thiết kế: chuẩn hóa dữ liệu, dùng khóa ngoại để bảo toàn toàn vẹn tham chiếu, đánh chỉ mục cho các trường truy vấn nhiều (user, problem, contest, submission).

### 3.6.2. Các nhóm bảng theo domain nghiệp vụ

Dựa trên repo, các model được chia nhóm:

* User/Profile/Organization.
* Problem/ProblemData/ProblemTestCase/ProblemTranslation.
* Submission/SubmissionSource/SubmissionTestCase.
* Contest/ContestParticipation/ContestProblem/ContestSubmission.
* Comment/Blog/Ticket.
* AI: AICodeReview, AIPromptTemplate, AIAPIKey, AIAPIKeyTestLog.
* RunSubmission.
* GensolJob (AI Generate Testcase).
* Problem.scoring_mode (chế độ chấm điểm: short_circuit / partial_batch / partial_testcase).
* Contest.enable_focus_lock + ContestParticipation.focus_violations (Contest Focus Lock).

Tài liệu repo liệt kê nhóm AI gồm `AICodeReview`, `AIPromptTemplate`, `AIAPIKey`, `AIAPIKeyTestLog`; `RunSubmission` cho IDE Run; `GensolJob` cho Generate Testcase (migration 0232, 0233). ([GitHub][3]) ([GitHub][5])

### 3.6.3. Các quyết định thiết kế chính

* **Tách bảng `RunSubmission` khỏi `Submission`:** để luồng chạy thử (IDE) không ảnh hưởng dữ liệu chấm chính thức và bảng xếp hạng.
* **Giữ trường `short_circuit` cũ song song với `scoring_mode`:** bảo đảm tương thích ngược với giao thức judge gốc.
* **Lưu API key dạng mã hóa + last4:** cân bằng giữa bảo mật và khả năng nhận diện key.
* **Đánh số migration nối tiếp DMOJ/VNOJ (0222–0233):** giữ lịch sử schema rõ ràng, dễ rollback.

## 3.7. Thiết kế chức năng AI

Chia làm 5 phần:

### AI API Key Management

* Người dùng thêm API key.
* Key được mã hóa.
* Lưu last4 để nhận diện.
* Có log test API key.

### AI Code Review

* Lấy source code submission.
* Gửi prompt đến AI provider.
* AI trả về phân tích thuật toán, độ phức tạp, lỗi, gợi ý cải thiện.
* Lưu kết quả review.

Theo repo, AI Code Review phân tích thuật toán/cấu trúc dữ liệu, luồng thực thi, độ phức tạp thời gian, độ phức tạp bộ nhớ và chất lượng code. ([GitHub][3])

### AI Problem Creator

* Admin nhập ảnh/PDF/text.
* AI trích xuất hoặc tạo thông tin đề.
* Điền vào form problem.

### AI Generate Testcase

Tính năng đã được implement đầy đủ với model `GensolJob`, view, utils, admin, bridge handler và management command.

* Admin/Problem Setter nhập source code generator (sinh input) và source code solution (sinh output).
* Chọn ngôn ngữ lập trình cho generator và solution.
* Chỉ định số lượng test case cần sinh.
* Hệ thống gửi job đến Judge Server qua Bridge pipeline.
* Judge biên dịch generator → chạy sinh input → biên dịch solution → chạy sinh output → lặp cho từng test case.
* Kết quả trả realtime qua WebSocket (channel `gensol_<id_secret>`).
* Trạng thái job: PENDING → GENERATING_INPUT → GENERATING_OUTPUT → UPLOADING → DONE/ERROR.
* Test case được tự động upload vào ProblemData.

File liên quan:
* Model: `judge/models/gensol_job.py`
* View: `judge/views/gensol.py`
* Utils: `judge/utils/gensol.py`
* Admin: `judge/admin/gensol_job.py`
* Bridge: `judge/bridge/django_handler.py`, `judge/bridge/judge_handler.py`
* Migration: `0232_gensol_job.py`, `0233_seed_ai_gen_code_prompt.py`
* Cleanup: `judge/management/commands/cleanup_gensol_jobs.py`

## 3.8. Thiết kế cơ chế chống gian lận (Contest Focus Lock)

Thiết kế logic chống gian lận khi thi trên nền web (cài đặt chi tiết ở mục 4.9):

* Admin bật `enable_focus_lock` cho contest → giao diện thi yêu cầu fullscreen, ẩn navbar.
* Client phát hiện mất focus/đổi tab/thoát fullscreen → gọi endpoint `/contest/report_focus_violation` (chỉ áp dụng khi contest đang **LIVE**).
* Server cập nhật **nguyên tử** số lần vi phạm bằng `F()` expression trên `ContestParticipation.focus_violations`.
* Cơ chế **auto-ban**: khi số lần vi phạm vượt ngưỡng `BKDNOJ_MAX_DISQUALIFICATIONS_BEFORE_BANNING` → `check_ban()` gọi `ban_user()`; khi giảm xuống dưới ngưỡng → `unban_user()`.
* Nêu rõ giới hạn: cơ chế web không thay thế được proctoring chuyên dụng (đóng góp ở mức "hạn chế" gian lận).

File liên quan: `judge/models/contest.py` (`focus_violations`, `check_ban`), `judge/views/contests.py` (`ContestReportFocusViolation`).

## 3.9. Thiết kế hệ thống xếp hạng và bảng xếp hạng

* **Rating Elo-MMR** (`judge/ratings.py`): cập nhật rating sau mỗi contest `is_rated`; lưu mean/variance/performance; rating hiển thị khuyến khích thi đấu nhiều.
* **Rating tiers:** phân hạng theo mốc rating (màu/nhãn) hiển thị trên hồ sơ và bảng xếp hạng.
* **Bảng xếp hạng (leaderboard):** podium top 3 kèm avatar, định dạng penalty time, sắp xếp theo điểm và thời gian phạt.
* (Chi tiết hằng số và thuật toán đặt ở Phụ lục, tham chiếu `RATING_SYSTEM_REPORT.md`.)

## 3.10. Thiết kế bảo mật nhiều lớp

Tổng hợp thiết kế bảo mật theo chiều sâu (defense-in-depth):

* **Lớp xác thực & phân quyền:** đăng nhập, phân quyền theo vai trò, kiểm soát truy cập view.
* **Lớp ứng dụng web:** chống XSS (đã vá lỗi hiển thị), CSRF token, kiểm tra đầu vào ở biên hệ thống, rate-limit nộp bài.
* **Lớp dữ liệu nhạy cảm:** mã hóa API key bằng Fernet, chỉ lưu last4.
* **Lớp thực thi mã không tin cậy:** sandbox `cptbox`, giới hạn tài nguyên, cô lập tiến trình.
* **Lớp dữ liệu cuộc thi:** ẩn kết quả/bảng xếp hạng theo cấu hình, kiểm soát truy cập trong thời gian thi.

---

# CHƯƠNG 4: XÂY DỰNG VÀ TRIỂN KHAI HỆ THỐNG — 16 đến 22 trang

Chương này viết theo source code và ảnh chụp thực tế.

## 4.1. Môi trường triển khai

Nên có bảng:

| Thành phần        | Công nghệ          |
| ----------------- | ------------------ |
| OS                | Ubuntu 20.04/22.04 |
| Web framework     | Django             |
| App server        | uWSGI              |
| Reverse proxy     | Nginx              |
| Database          | MariaDB            |
| Cache/Broker      | Redis              |
| Background worker | Celery             |
| Realtime          | WSEvent Node.js    |
| Judge             | VNOJ/DMOJ judge    |
| Container         | Docker Compose     |

## 4.2. Cấu trúc source code

Dựa trên repo, có thể mô tả:

```text
My-Online-Judge/
├── dmoj/
│   ├── base/              # Base Docker image (Python 3.11)
│   ├── site/              # Site Dockerfile (Django + uWSGI)
│   ├── bridged/           # Bridge Dockerfile
│   ├── celery/            # Celery Dockerfile
│   ├── wsevent/           # WebSocket Dockerfile (Node.js)
│   ├── nginx/conf.d/      # Nginx reverse proxy config
│   ├── config/            # App configs (uwsgi.ini...)
│   ├── environment/       # Env files (mysql.env, site.env)
│   ├── scripts/           # Setup/deploy scripts
│   ├── repo/              # Django source code (git submodule)
│   │   ├── dmoj/          # Django project settings
│   │   ├── judge/         # App chính (models, views, admin, migrations)
│   │   ├── templates/     # Jinja2/Django templates
│   │   ├── resources/     # Static files (JS, CSS, ACE, CodeMirror 6)
│   │   └── ...
│   ├── generate_testcase/ # GensolJob working directory
│   ├── problems/          # Problem data/testcase files
│   ├── media/             # Uploaded files
│   ├── database/          # MariaDB data volume
│   └── docker-compose.yml
├── document/
├── judge_update/
└── README.md
```

Repo có cấu trúc 2 lớp: thư mục `dmoj/` chứa Docker infrastructure, bên trong `dmoj/repo/` là source code Django (git submodule). ([GitHub][1]) ([GitHub][2])

## 4.3. Triển khai Docker Compose

Nên viết:

* Build image.
* Start containers.
* Kiểm tra logs.
* Cấu hình volume cho database, media, problems.
* Cấu hình network nội bộ.

Theo tài liệu repo, hệ thống gồm các container như `aloj_mysql`, `aloj_redis`, `aloj_site`, `aloj_celery`, `aloj_bridged`, `aloj_wsevent`, `aloj_nginx`. ([GitHub][6])

## 4.4. Xây dựng giao diện IDE mới

Nên có ảnh:

* Trang problem layout 2 cột (CodeMirror 6 editor).
* Code editor với syntax highlighting, auto-completion.
* Panel testcase sample + custom input (tối đa 3).
* Nút Run (chạy thử sample) và nút Submit (nộp chính thức).
* Kết quả AC/WA/TLE hiển thị realtime qua WebSocket.

## 4.5. Xây dựng AI Code Review

Nên có ảnh:

* Nút AI Review ở source/submission.
* Modal kết quả review.
* Log review hoặc bảng AICodeReview.

## 4.6. Xây dựng AI Problem Creator

Nên có ảnh:

* Giao diện admin AI create problem.
* Input ảnh/PDF/text.
* Kết quả AI trả về.
* Form problem sau khi điền.

## 4.7. Quản lý AI API Key

Nên có ảnh:

* Trang thêm API key.
* Test connection.
* Danh sách key đã lưu.
* Trạng thái active/error.

## 4.8. Xây dựng AI Generate Testcase

Nên có ảnh:

* Giao diện Generate Testcase cho problem.
* Nhập source code generator và solution.
* Chọn ngôn ngữ, số lượng test case.
* Trạng thái job realtime (PENDING → GENERATING_INPUT → GENERATING_OUTPUT → UPLOADING → DONE).
* Kết quả test case được tạo tự động.

## 4.9. Contest Focus Lock / Cheating Management

Chức năng đã có trong master (migration 0228). Nên viết:

* Mục tiêu: hạn chế gian lận khi thi.
* Admin bật `enable_focus_lock` cho contest → ẩn navbar, yêu cầu fullscreen.
* Khi user tham gia contest, giao diện chuyển chế độ focus/fullscreen.
* Phát hiện mất focus/thoát tab → ghi nhận vào `focus_violations` (ContestParticipation).
* Cơ chế auto-ban: nếu user bị disqualify quá N lần (cấu hình qua `BKDNOJ_MAX_DISQUALIFICATIONS_BEFORE_BANNING`), hệ thống tự động ban user thông qua method `check_ban()`.
* Khi bỏ disqualify (số lần giảm dưới ngưỡng) → tự động unban.

Phần này nên đưa như **đóng góp riêng**, vì nó khác hệ thống OJ gốc.

## 4.10. Cài đặt hệ thống rating và bảng xếp hạng

* Cài đặt tính rating Elo-MMR trong `judge/ratings.py`, kích hoạt sau contest `is_rated`.
* Hiển thị rating tiers (màu/nhãn) trên hồ sơ người dùng.
* Trang bảng xếp hạng: podium top 3 + avatar, định dạng penalty time, cập nhật theo điểm và thời gian phạt.
* Nên có ảnh: trang bảng xếp hạng và trang lịch sử rating của người dùng.

---

# CHƯƠNG 5: KIỂM THỬ, THỰC NGHIỆM VÀ ĐÁNH GIÁ — 10 đến 14 trang

## 5.1. Mục tiêu và phạm vi thực nghiệm

Thực nghiệm nhằm trả lời các câu hỏi nghiên cứu (RQ1–RQ4) ở phần Mở đầu:

* Kiểm tra hệ thống chạy ổn định và đúng chức năng (submit, run IDE, AI, realtime, phân quyền, Focus Lock, rating).
* Đánh giá hiệu năng xử lý nộp bài và độ trễ cập nhật realtime.
* Đánh giá tính hữu ích và độ tin cậy của các chức năng AI.

## 5.2. Thiết lập thực nghiệm

* **Môi trường:** mô tả cấu hình máy chủ/host (CPU, RAM), phiên bản Docker, số worker uWSGI (8) và Celery (2), số judge server.
* **Dữ liệu thử:** bộ problem mẫu (AC/WA/TLE/MLE), tài khoản thử cho từng vai trò, contest mẫu có/không bật Focus Lock.
* **Công cụ đo:** ApacheBench/wrk cho tải HTTP; quan sát log bridge/judge; đo thời gian từ lúc nộp đến lúc có kết quả realtime.

## 5.3. Phương pháp thu thập và tính toán số liệu

* Mỗi kịch bản chạy nhiều lần, lấy trung vị (median) và giá trị lớn nhất để giảm nhiễu.
* Số liệu hiệu năng: requests/second, độ trễ trung vị, tỉ lệ lỗi (failed requests).
* Số liệu chức năng: tỉ lệ pass của bảng kiểm thử đầu cuối.

## 5.4. Bảng kiểm thử chức năng đầu cuối

Ví dụ:

| STT | Chức năng       | Dữ liệu kiểm thử     | Kết quả mong đợi          |
| --- | --------------- | -------------------- | ------------------------- |
| 1   | Đăng nhập       | Tài khoản hợp lệ     | Đăng nhập thành công      |
| 2   | Submit code AC  | Code đúng            | Trả kết quả AC            |
| 3   | Submit code WA  | Code sai             | Trả kết quả WA            |
| 4   | Submit code TLE | Vòng lặp vô hạn      | Trả kết quả TLE           |
| 5   | IDE Run         | Chạy sample          | Hiển thị kết quả realtime |
| 6   | AI Review       | Source code C++      | AI trả phân tích          |
| 7   | Test API key    | Key hợp lệ           | Trạng thái success        |
| 8   | WebSocket       | Submission đang chấm | UI tự cập nhật            |
| 9   | Gen Testcase    | Generator + Solution | Sinh test case thành công |
| 10  | AI Problem Creator | Upload ảnh đề bài | AI trả về markdown đề   |
| 11  | Focus Lock      | Chuyển tab khi thi   | Ghi nhận vi phạm          |

## 5.5. Kiểm thử hiệu năng

Đưa kết quả đo tải (ví dụ ApacheBench/wrk) trên các endpoint chính:

* Số request và mức đồng thời (concurrency).
* Thời gian xử lý (trung vị, lớn nhất).
* Số request thất bại (failed requests).
* Throughput (requests per second).
* Độ trễ cập nhật realtime của WebSocket khi chấm bài.

## 5.6. Đánh giá các chức năng AI

* **AI Code Review:** đánh giá chất lượng phân tích (thuật toán, độ phức tạp, lỗi) trên một số bài mẫu.
* **AI Problem Creator:** tỉ lệ trích xuất đúng nội dung đề từ ảnh/PDF/text.
* **AI Generate Testcase (GenSol):** tỉ lệ sinh testcase thành công, thời gian sinh, kiểm soát chất lượng input/output.
* Nhận xét về sự phụ thuộc vào nhà cung cấp và chất lượng prompt template.

## 5.7. Thảo luận — trả lời câu hỏi nghiên cứu

* **RQ1:** Kết quả cho thấy có/không thể mở rộng IDE + chấm điểm linh hoạt mà vẫn tương thích judge gốc (dẫn chứng từ 5.4, 5.5).
* **RQ2:** Mức độ khả thi và hữu ích của trợ lý AI (dẫn chứng từ 5.6).
* **RQ3:** Hiệu quả của Focus Lock + auto-ban trong giảm gian lận (dẫn chứng từ 5.4).
* **RQ4:** Mức đáp ứng yêu cầu phi chức năng (dẫn chứng từ 5.5).

## 5.8. Tổng hợp đánh giá

### Ưu điểm

* Hệ thống đầy đủ chức năng Online Judge.
* Có kiến trúc nhiều service rõ ràng (7 Docker containers).
* Có realtime WebSocket.
* Có IDE trực tuyến (CodeMirror 6).
* Có AI hỗ trợ đa dạng (Code Review, Problem Creator, Generate Testcase).
* Hỗ trợ 4 AI provider (OpenAI, Gemini, Claude, DeepSeek).
* Triển khai được bằng Docker.
* Có cơ chế chống gian lận Contest Focus Lock.
* Có hệ thống rating Elo-MMR và bảng xếp hạng (podium top 3 + avatar).

### Hạn chế

* Việc kế thừa DMOJ/VNOJ khiến source code lớn, khó tùy biến.
* Cần kiểm thử tải lớn hơn.
* AI phụ thuộc provider và API key.
* AI Generate Testcase cần kiểm soát chất lượng chặt.
* Bảo mật contest focus lock trên web không thể tuyệt đối.

### So sánh trước/sau

| Tiêu chí              | Hệ thống gốc                 | BKDNOJ              |
| --------------------- | ---------------------------- | ----------------- |
| Chấm bài              | Có                           | Có                |
| Chế độ chấm điểm       | Boolean partial              | 3 chế độ (short circuit / subtask / testcase) |
| Contest               | Có                           | Có                |
| IDE trực tuyến        | Hạn chế/không phải trọng tâm | Có                |
| AI Code Review        | Không                        | Có                |
| AI Problem Creator    | Không                        | Có                |
| AI Generate Testcase  | Không                        | Có                |
| API key theo user     | Không                        | Có                |
| Contest Focus Lock    | Không                        | Có                |
| Auto-ban gian lận     | Không                        | Có                |
| Rating Elo-MMR        | Có (cơ bản)                  | Có + bảng xếp hạng cải tiến |
| Docker hóa triển khai | Có/tùy cấu hình              | Có cấu hình riêng |

---

# KẾT LUẬN — 2 đến 3 trang

Theo mẫu, phần kết luận cần nêu **kết quả đạt được, đóng góp, đề xuất và kiến nghị**. 

Nên viết theo 3 mục:

## Kết quả đạt được

* Nghiên cứu kiến trúc DMOJ/VNOJ.
* Triển khai hệ thống BKDNOJ bằng Docker Compose.
* Cấu hình luồng chấm bài Site → Bridge → Judge → WebSocket.
* Bổ sung chế độ chấm điểm linh hoạt (Scoring Mode: short circuit / partial by subtask / partial by testcase).
* Xây dựng IDE trực tuyến (CodeMirror 6, layout 2 cột kiểu LeetCode).
* Bổ sung AI Code Review.
* Bổ sung AI Problem Creator.
* Xây dựng AI Generate Testcase (GensolJob + Bridge/Judge pipeline).
* Xây dựng quản lý API key (mã hóa Fernet, hỗ trợ 4 provider).
* Xây dựng Contest Focus Lock và cơ chế auto-ban gian lận.
* Xây dựng hệ thống rating Elo-MMR và bảng xếp hạng.
* Cải tiến UI/UX và contest.

## Hạn chế

* Hệ thống còn phụ thuộc nhiều vào nền tảng gốc.
* Chưa kiểm thử trên quy mô người dùng lớn.
* Một số tính năng AI cần tối ưu prompt và kiểm soát dữ liệu.
* Contest lock trên trình duyệt chỉ hỗ trợ hạn chế gian lận, không thay thế được proctoring chuyên dụng.

## Hướng phát triển

* AI Hint System — gợi ý giải thuật khi user bị kẹt.
* AI Plagiarism Detection — phát hiện gian lận bằng AI (bổ sung MOSS).
* Tối ưu queue judge và scale judge server.
* Bổ sung monitoring Prometheus/Grafana.
* Tích hợp CI/CD pipeline tự động test và deploy.
* HTTPS (Let's Encrypt) — bảo mật SSL/TLS.
* Tăng bảo mật sandbox và API key.
* Hoàn thiện hệ thống tag problem chuẩn.
* Tối ưu giao diện mobile responsive.
* Contest Analytics — phân tích sâu về kết quả thi.

---

# Phụ lục nên có

Phần phụ lục có thể giúp báo cáo dày và chuyên nghiệp hơn:

* Phụ lục A: Cấu hình Docker Compose.
* Phụ lục B: Cấu hình Nginx.
* Phụ lục C: Danh sách bảng database chính.
* Phụ lục D: Một số màn hình hệ thống.
* Phụ lục E: Prompt AI Code Review / AI Problem Creator / AI Generate Testcase.
* Phụ lục F: Log kiểm thử submission.
* Phụ lục G: Hướng dẫn cài đặt Judge Server.
* Phụ lục H: Danh sách migration BKDNOJ mới (0222–0233), gồm `0222_problem_scoring_mode`, `0225_problem_enable_new_ide`, `0226_run_submission`, `0228` (Contest Focus Lock), `0232_gensol_job`, `0233_seed_ai_gen_code_prompt`.

---

# Ước tính số trang theo dàn ý này

| Phần               | Số trang |
| ------------------ | -------: |
| Mở đầu             |      3–5 |
| Chương 1           |     8–10 |
| Chương 2           |    12–16 |
| Chương 3           |    16–20 |
| Chương 4           |    18–24 |
| Chương 5           |    10–14 |
| Kết luận           |      2–3 |
| Tài liệu tham khảo |      2–4 |
| Phụ lục            |     8–15 |

Với dàn ý này, báo cáo của Jack rất hợp lý ở mức **65–80 trang**, tính cả ảnh, bảng, sơ đồ và phụ lục.

Điểm nên nhấn mạnh khi viết là:

> **BKDNOJ không chỉ là cài đặt lại DMOJ/VNOJ, mà là quá trình nghiên cứu kiến trúc Online Judge, triển khai hệ thống thực tế, tùy biến giao diện, bổ sung IDE trực tuyến (CodeMirror 6), tích hợp AI đa nhà cung cấp (Code Review, Problem Creator, Generate Testcase), xây dựng cơ chế chống gian lận và cải tiến luồng vận hành phù hợp với nhu cầu riêng.**

---

# TÀI LIỆU THAM KHẢO (gợi ý nhóm nguồn)

Sắp xếp theo chuẩn trích dẫn của trường (IEEE hoặc APA). Các nhóm nguồn nên có:

* **Nền tảng nguồn mở:** tài liệu và mã nguồn DMOJ, VNOJ (judge, bridge, sandbox `cptbox`).
* **Công nghệ:** tài liệu Django, Celery, Redis, Docker, Nginx, uWSGI, CodeMirror 6.
* **Thuật toán rating:** bài báo Elo-MMR (Aram Ebtekar, Paul Liu — "An Elo-like System for Massive Multiplayer Competitions").
* **Mô hình ngôn ngữ lớn:** tài liệu API của OpenAI, Google Gemini, Anthropic Claude, DeepSeek.
* **Bảo mật:** OWASP Top 10; tài liệu Fernet (cryptography).
* **Tài liệu nội bộ dự án:** `THESIS_REFERENCE.md`, `IDE_RUN_FEATURE.md`, `SUBMIT_RUN_GENSOL_FLOW.md`, `RATING_SYSTEM_REPORT.md` và các sơ đồ trong `document/gzx/`.

[1]: https://github.com/Algorit-loop/My-Online-Judge "GitHub - Algorit-loop/My-Online-Judge · GitHub"
[2]: https://github.com/Algorit-loop/My-Online-Judge/tree/master/dmoj "My-Online-Judge/dmoj at master · Algorit-loop/My-Online-Judge · GitHub"
[3]: https://github.com/Algorit-loop/My-Online-Judge/blob/master/document/THESIS_REFERENCE.md "My-Online-Judge/document/THESIS_REFERENCE.md at master · Algorit-loop/My-Online-Judge · GitHub"
[4]: https://github.com/Algorit-loop/My-Online-Judge/blob/master/document/SUBMIT_RUN_GENSOL_FLOW.md "My-Online-Judge/document/SUBMIT_RUN_GENSOL_FLOW.md at master · Algorit-loop/My-Online-Judge · GitHub"
[5]: https://github.com/Algorit-loop/My-Online-Judge/blob/master/document/IDE_RUN_FEATURE.md "My-Online-Judge/document/IDE_RUN_FEATURE.md at master · Algorit-loop/My-Online-Judge · GitHub"
[6]: https://github.com/Algorit-loop/My-Online-Judge/tree/master/document "My-Online-Judge/document at master · Algorit-loop/My-Online-Judge · GitHub"
