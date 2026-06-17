# CHƯƠNG 5. THỰC NGHIỆM VÀ ĐÁNH GIÁ

Các chương trước đã trình bày quá trình phân tích, thiết kế và triển khai hệ thống BKDNOJ. Chương này tập trung kiểm thử các chức năng chính của hệ thống trên môi trường triển khai thực tế nhằm xác nhận hệ thống hoạt động đúng theo thiết kế, đồng thời ghi nhận các hạn chế cần cải thiện.

## 5.1. Mục tiêu thực nghiệm

Thực nghiệm trong chương này được thực hiện nhằm kiểm tra bốn nhóm chức năng chính của BKDNOJ:

- **Luồng nộp bài và chấm bài**: Xác nhận toàn bộ vòng đời bài nộp — từ khi người dùng nộp mã nguồn, hệ thống gửi đến máy chấm qua bridge, thực thi chương trình, so sánh kết quả với test case cho đến khi trạng thái và điểm số được cập nhật trên giao diện theo thời gian thực qua WebSocket.
- **IDE trực tuyến và luồng chạy thử**: Xác nhận luồng xử lý RunSubmission hoạt động độc lập với luồng chấm chính thức, cho phép người dùng chạy thử chương trình với các test case mẫu và nhận kết quả trực tiếp.
- **Các chức năng AI**: Kiểm tra bốn tính năng AI mới — phân tích mã nguồn, hỗ trợ tạo đề bài từ ảnh, sinh chương trình tạo test case, và gợi ý dạng bài — xác nhận khả năng kết nối với dịch vụ AI bên ngoài, xử lý kết quả trả về và lưu trữ đúng.
- **Cơ chế khóa tập trung**: Xác nhận cơ chế Focus Lock trong kỳ thi hoạt động đúng — chuyển hướng thí sinh vào trang wrapper, yêu cầu toàn màn hình, theo dõi và ghi nhận vi phạm, chặn các phím tắt thoát.

Các kịch bản kiểm thử được thiết kế theo hướng kiểm thử chức năng (functional testing), tập trung vào tính đúng đắn của từng luồng xử lý thay vì đo hiệu năng tải lớn.

## 5.2. Thiết lập môi trường thực nghiệm

### 5.2.1. Cấu hình hệ thống

Hệ thống BKDNOJ được triển khai bằng Docker Compose với bảy dịch vụ chạy thường trực trên một máy chủ.

| Dịch vụ | Container | Vai trò |
|---|---|---|
| `db` | `bkdnoj_mysql` | Cơ sở dữ liệu MariaDB |
| `redis` | `bkdnoj_redis` | Bộ nhớ đệm, phiên đăng nhập, broker Celery |
| `site` | `bkdnoj_site` | Ứng dụng Django, xử lý nghiệp vụ qua uWSGI (8 worker, cổng 8000) |
| `celery` | `bkdnoj_celery` | Xử lý tác vụ bất đồng bộ |
| `bridged` | `bkdnoj_bridged` | Bridge trung gian kết nối máy chấm qua cổng 9998–9999 |
| `wsevent` | `bkdnoj_wsevent` | WebSocket server, đẩy cập nhật thời gian thực (cổng 15100–15102) |
| `nginx` | `bkdnoj_nginx` | Reverse proxy, tiếp nhận request từ bên ngoài qua cổng 80 |

Máy chấm (Judge) chạy độc lập bên ngoài Docker Compose và kết nối vào `bridged` qua cổng 9999. Dữ liệu bài toán và test case được chia sẻ qua volume dùng chung (`./problems/`, `./generate_testcase/`).

### 5.2.2. Dữ liệu kiểm thử

Để phục vụ thực nghiệm, hệ thống được chuẩn bị với:

- **Bài toán kiểm thử**: Các bài toán có độ khó khác nhau, có đầy đủ test case, hỗ trợ nhiều ngôn ngữ lập trình (C++, Python, Java), bao gồm bài có subtask và bài không có subtask.
- **Tài khoản người dùng**: Tài khoản thường (để kiểm thử nộp bài, AI code review, IDE) và tài khoản quản trị (để kiểm thử tạo đề, sinh test case, gợi ý dạng bài).
- **Kỳ thi kiểm thử**: Một kỳ thi có bật Focus Lock, chứa các bài toán kiểm thử, để kiểm tra cơ chế khóa tập trung.
- **API key AI**: API key đã được thêm và xác minh cho ít nhất một nhà cung cấp (ví dụ: Google Gemini hoặc OpenAI).

## 5.3. Kịch bản thực nghiệm

### 5.3.1. Kiểm thử luồng nộp bài và chấm bài

Mục tiêu: Xác nhận bài nộp đi qua đầy đủ vòng đời xử lý và trả về kết quả chính xác.

**Kịch bản 1 — Nộp bài đúng (AC)**

| Bước | Hành động | Kết quả mong đợi |
|------|-----------|------------------|
| 1 | Đăng nhập và chọn bài toán | Trang bài toán hiển thị đề bài, ràng buộc, ví dụ |
| 2 | Chọn ngôn ngữ C++ và dán mã nguồn lời giải đúng | Mã nguồn hiển thị đúng trong editor |
| 3 | Nhấn nút Submit | Hệ thống chuyển sang trang trạng thái bài nộp |
| 4 | Quan sát quá trình chấm | Trạng thái chuyển từ Queued → Processing → Grading → Done |
| 5 | Kiểm tra kết quả | Kết quả hiển thị AC, điểm đầy đủ, thời gian và bộ nhớ cho từng test case |

**Kịch bản 2 — Nộp bài sai (WA)**

| Bước | Hành động | Kết quả mong đợi |
|------|-----------|------------------|
| 1 | Nộp mã nguồn cho ra output sai | Hệ thống tiếp nhận bài nộp |
| 2 | Chờ chấm hoàn tất | Kết quả hiển thị WA, điểm < tổng điểm |
| 3 | Kiểm tra chi tiết từng test case | Các test case sai hiển thị trạng thái WA |

**Kịch bản 3 — Nộp bài lỗi biên dịch (CE)**

| Bước | Hành động | Kết quả mong đợi |
|------|-----------|------------------|
| 1 | Nộp mã nguồn có lỗi cú pháp | Hệ thống tiếp nhận bài nộp |
| 2 | Chờ xử lý | Kết quả hiển thị CE, thông báo lỗi biên dịch |

**Kịch bản 4 — Nộp bài vượt giới hạn (TLE/MLE)**

| Bước | Hành động | Kết quả mong đợi |
|------|-----------|------------------|
| 1 | Nộp mã nguồn có vòng lặp vô hạn (TLE) hoặc cấp phát bộ nhớ lớn (MLE) | Hệ thống tiếp nhận bài nộp |
| 2 | Chờ chấm hoàn tất | Kết quả hiển thị TLE hoặc MLE, chương trình bị dừng đúng giới hạn |

<<Hình kết quả chấm bài hiển thị trên giao diện — bao gồm trạng thái, điểm, thời gian và bộ nhớ từng test case>>

### 5.3.2. Kiểm thử IDE trực tuyến và luồng chạy thử

Mục tiêu: Xác nhận luồng RunSubmission hoạt động đúng, độc lập với luồng chấm chính thức, kết quả trả về theo từng test case mẫu.

**Kịch bản 5 — Chạy thử qua IDE**

| Bước | Hành động | Kết quả mong đợi |
|------|-----------|------------------|
| 1 | Mở bài toán có bật IDE (`enable_new_ide = true`) | Giao diện IDE hiển thị editor, chọn ngôn ngữ và nút Run |
| 2 | Viết mã nguồn lời giải đúng | Mã nguồn hiển thị trong ACE editor |
| 3 | Nhấn nút Run | Hệ thống gửi RunSubmission, trạng thái chuyển sang Processing |
| 4 | Chờ kết quả | Kết quả hiển thị theo từng test case mẫu (`is_sample = true`), bao gồm trạng thái, thời gian, bộ nhớ |
| 5 | Kiểm tra kết quả không ảnh hưởng bài nộp chính thức | Danh sách Submission của bài toán không có bản ghi RunSubmission |

**Kịch bản 6 — Chạy thử bài lỗi qua IDE**

| Bước | Hành động | Kết quả mong đợi |
|------|-----------|------------------|
| 1 | Viết mã nguồn có lỗi biên dịch và nhấn Run | Kết quả hiển thị lỗi CE, kèm thông báo lỗi biên dịch |
| 2 | Sửa thành mã nguồn cho ra kết quả sai và nhấn Run | Kết quả hiển thị WA cho các test case mẫu |

<<Hình giao diện IDE trực tuyến với kết quả chạy thử theo từng test case mẫu>>

### 5.3.3. Kiểm thử các chức năng AI

Mục tiêu: Xác nhận các tính năng AI kết nối đúng dịch vụ AI bên ngoài, xử lý phản hồi và lưu trữ kết quả vào cơ sở dữ liệu.

**Kịch bản 7 — Quản lý API key**

| Bước | Hành động | Kết quả mong đợi |
|------|-----------|------------------|
| 1 | Vào trang AI API Keys, chọn nhà cung cấp và dán API key | Key được thêm, trạng thái Pending, giao diện hiển thị 4 ký tự cuối |
| 2 | Chọn model và nhấn Test | Hệ thống gửi prompt thử nghiệm; trạng thái chuyển thành Verified (hoặc Failed nếu key sai) |
| 3 | Kiểm tra Test Logs | Nhật ký hiển thị thời gian kiểm tra, model, kết quả, thời gian phản hồi (ms) |
| 4 | Nhấn nút xóa | API key và nhật ký kiểm tra bị xóa |

**Kịch bản 8 — AI phân tích mã nguồn**

| Bước | Hành động | Kết quả mong đợi |
|------|-----------|------------------|
| 1 | Nộp một bài và chờ chấm xong | Có bài nộp với kết quả (AC, WA, ...) |
| 2 | Vào trang chi tiết bài nộp, chọn nhà cung cấp AI và model, nhấn Review with AI | Hệ thống gửi mã nguồn kèm prompt đến dịch vụ AI |
| 3 | Chờ kết quả | Phần phân tích hiển thị 5 mục: thuật toán, luồng thực thi, độ phức tạp thời gian, độ phức tạp không gian, chất lượng mã |
| 4 | Kiểm tra tag dạng bài | Hệ thống tự động trích tag từ phản hồi AI và lưu vào UserProblemTag |
| 5 | Tải lại trang bài nộp | Kết quả phân tích được hiển thị từ cache (không gọi lại AI) |

<<Hình kết quả AI phân tích mã nguồn trên trang chi tiết bài nộp>>

**Kịch bản 9 — AI hỗ trợ tạo đề bài từ ảnh**

| Bước | Hành động | Kết quả mong đợi |
|------|-----------|------------------|
| 1 | Vào trang tạo/chỉnh sửa bài toán (quyền quản trị) | Giao diện hiển thị form tạo bài |
| 2 | Tải lên file ảnh (PNG/JPG/WebP) chứa đề bài, chọn nhà cung cấp AI (OpenAI/Gemini/Claude) và ngôn ngữ đầu ra | File được chấp nhận (không hỗ trợ PDF và DeepSeek) |
| 3 | Nhấn nút tạo đề | Hệ thống mã hóa ảnh base64, gửi kèm prompt đến dịch vụ AI |
| 4 | Chờ kết quả | Nội dung Markdown được điền vào form, bao gồm: mô tả bài, định dạng Input/Output, subtask (nếu có), ví dụ minh họa |
| 5 | Kiểm tra và chỉnh sửa nội dung | Người ra đề tự cấu hình giới hạn thời gian, bộ nhớ, điểm số, quyền truy cập |

<<Hình giao diện AI tạo đề bài từ ảnh — trước và sau khi AI trả về kết quả>>

**Kịch bản 10 — AI sinh chương trình tạo test case**

| Bước | Hành động | Kết quả mong đợi |
|------|-----------|------------------|
| 1 | Vào trang Generate Testcase của bài toán có đề bài đầy đủ | Giao diện hiển thị form với 2 editor (generator, solution) |
| 2 | Chọn nhà cung cấp AI, model, số lượng test case (1–50), nhấn Generate | AI trả về mã nguồn C++ cho chương trình sinh input, điền vào editor generator |
| 3 | Viết hoặc dán mã nguồn lời giải chuẩn vào editor solution, chọn ngôn ngữ | Mã nguồn hiển thị đúng |
| 4 | Nhấn Start | Hệ thống tạo GensolJob, gửi tác vụ đến máy chấm |
| 5 | Theo dõi tiến trình | Trạng thái chuyển: PENDING → GENERATING_INPUT → GENERATING_OUTPUT → UPLOADING → DONE |
| 6 | Kiểm tra kết quả | Bộ test case mới được lưu vào bài toán; nếu bài đã có test case, hệ thống yêu cầu xác nhận ghi đè trước |

<<Hình giao diện sinh test case — chương trình generator do AI tạo và tiến trình sinh>>

**Kịch bản 11 — AI gợi ý dạng bài**

| Bước | Hành động | Kết quả mong đợi |
|------|-----------|------------------|
| 1 | Chọn bài toán đã có ít nhất 3 bài nộp AC | Bài toán đủ điều kiện |
| 2 | Chọn nhà cung cấp AI, model, nhấn nút gợi ý tag | Hệ thống lấy 3 bài nộp AC nhanh nhất, gửi kèm đề bài và danh sách ProblemType cho AI |
| 3 | Chờ kết quả | AI trả về mảng JSON tên tag; hệ thống đối chiếu với cơ sở dữ liệu, hiển thị tag hợp lệ |
| 4 | Kiểm tra với bài toán chưa đủ 3 bài AC | Hệ thống từ chối và hiển thị thông báo thiếu dữ liệu |

<<Hình giao diện gợi ý dạng bài — danh sách tag được AI đề xuất>>

### 5.3.4. Kiểm thử cơ chế khóa tập trung trong kỳ thi

Mục tiêu: Xác nhận cơ chế Focus Lock hoạt động đúng — chuyển hướng, theo dõi vi phạm, chặn phím tắt, ghi nhận số lần vi phạm.

**Kịch bản 12 — Tham gia kỳ thi có Focus Lock**

| Bước | Hành động | Kết quả mong đợi |
|------|-----------|------------------|
| 1 | Vào trang kỳ thi có bật Focus Lock và nhấn Join | Hộp thoại cảnh báo hiển thị thông tin về cơ chế khóa tập trung |
| 2 | Xác nhận tham gia | Chuyển hướng đến trang wrapper, hiển thị lớp phủ "Click to enter fullscreen" |
| 3 | Nhấp vào lớp phủ | Trình duyệt vào chế độ toàn màn hình, lớp phủ ẩn, giao diện thi hiển thị trong iframe |
| 4 | Kiểm tra thanh điều hướng | Thanh navigation bị ẩn hoàn toàn |

**Kịch bản 13 — Ghi nhận vi phạm**

| Bước | Hành động | Kết quả mong đợi |
|------|-----------|------------------|
| 1 | Thoát toàn màn hình (nhấn Escape hoặc F11) | Hệ thống ghi nhận 1 vi phạm, lớp phủ hiển thị lại |
| 2 | Nhấp lớp phủ để vào lại toàn màn hình | Giao diện thi tiếp tục |
| 3 | Chuyển sang tab khác (Alt+Tab hoặc nhấp ngoài cửa sổ) | Hệ thống ghi nhận 1 vi phạm (không hiển thị lớp phủ thêm) |
| 4 | Kiểm tra số vi phạm trong cơ sở dữ liệu | Trường `focus_violations` trong ContestParticipation tăng đúng số lần |

**Kịch bản 14 — Chặn phím tắt**

| Bước | Hành động | Kết quả mong đợi |
|------|-----------|------------------|
| 1 | Nhấn Ctrl+R hoặc F5 trong chế độ toàn màn hình | Trang không bị tải lại |
| 2 | Nhấn F11 | Không thoát toàn màn hình |
| 3 | Nhấn Escape (trên Chrome/Edge có Keyboard Lock) | Phím bị khóa, không thoát toàn màn hình |

**Kịch bản 15 — Nộp bài trong chế độ Focus Lock**

| Bước | Hành động | Kết quả mong đợi |
|------|-----------|------------------|
| 1 | Xem đề bài trong iframe | Đề bài hiển thị đầy đủ |
| 2 | Viết mã và nộp bài | Bài nộp được tiếp nhận, kết quả chấm cập nhật bình thường |
| 3 | Sử dụng IDE chạy thử (nếu bài có bật IDE) | IDE hoạt động bình thường trong iframe |

<<Hình giao diện Focus Lock — lớp phủ yêu cầu toàn màn hình, giao diện thi trong iframe, và bảng hiển thị số vi phạm>>

### 5.3.5. Kiểm thử tải đọc API

Mục tiêu: Đánh giá khả năng phục vụ đồng thời của hệ thống khi nhiều người dùng truy cập cùng lúc, xác định ngưỡng chịu tải và điểm bắt đầu suy giảm.

**Công cụ**: K6 v0.56.0 — công cụ kiểm thử tải mã nguồn mở của Grafana Labs. Mỗi virtual user (VU) đại diện cho một phiên người dùng hoạt động liên tục, thực hiện tuần tự 3 request (trang chủ, danh sách bài tập, danh sách kỳ thi), nghỉ 1 giây rồi lặp lại.

**Thiết kế kiểm thử**: 4 mức tải, mỗi mức chạy trong 1 phút.

| Mức | VU | Mục đích |
|-----|-----|----------|
| Nhẹ | 50 | Tải bình thường — lớp học, luyện tập hằng ngày |
| Trung bình | 100 | Kỳ thi quy mô nhỏ |
| Nặng | 200 | Kỳ thi quy mô lớn |
| Stress | 300 | Vượt ngưỡng — tìm giới hạn hệ thống |

## 5.4. Kết quả thực nghiệm

### 5.4.1. Kết quả kiểm thử luồng nộp bài và chấm bài

| Kịch bản | Mô tả | Kết quả | Ghi chú |
|----------|-------|---------|---------|
| 1 | Nộp bài đúng (AC) | Đạt | Trạng thái cập nhật thời gian thực qua WebSocket |
| 2 | Nộp bài sai (WA) | Đạt | Điểm và trạng thái từng test case hiển thị đúng |
| 3 | Lỗi biên dịch (CE) | Đạt | Thông báo lỗi biên dịch hiển thị chi tiết |
| 4 | Vượt giới hạn (TLE/MLE) | Đạt | Chương trình bị dừng đúng giới hạn |

<<Hình kết quả từng kịch bản — AC, WA, CE, TLE>>

### 5.4.2. Kết quả kiểm thử IDE trực tuyến

| Kịch bản | Mô tả | Kết quả | Ghi chú |
|----------|-------|---------|---------|
| 5 | Chạy thử bài đúng qua IDE | Đạt | Kết quả theo từng test mẫu, không tạo bản ghi Submission |
| 6 | Chạy thử bài lỗi qua IDE | Đạt | CE và WA hiển thị đúng |

<<Hình kết quả IDE — chạy thử thành công và chạy thử lỗi>>

### 5.4.3. Kết quả kiểm thử các chức năng AI

| Kịch bản | Mô tả | Kết quả | Ghi chú |
|----------|-------|---------|---------|
| 7 | Quản lý API key | Đạt | Thêm, kiểm tra, xóa API key hoạt động đúng; key mã hóa Fernet |
| 8 | AI phân tích mã nguồn | Đạt | 5 mục phân tích đầy đủ, tag được trích và lưu tự động |
| 9 | AI tạo đề bài từ ảnh | Đạt | Markdown đúng cấu trúc; DeepSeek bị từ chối do không hỗ trợ ảnh |
| 10 | AI sinh chương trình tạo test case | Đạt | Generator C++ hợp lệ, bộ test case được lưu vào bài toán |
| 11 | AI gợi ý dạng bài | Đạt | Tag hợp lệ được đề xuất; bài chưa đủ 3 AC bị từ chối đúng |

<<Hình kết quả từng chức năng AI>>

### 5.4.4. Kết quả kiểm thử cơ chế khóa tập trung

| Kịch bản | Mô tả | Kết quả | Ghi chú |
|----------|-------|---------|---------|
| 12 | Tham gia kỳ thi Focus Lock | Đạt | Cảnh báo, wrapper, toàn màn hình, ẩn navbar đều hoạt động đúng |
| 13 | Ghi nhận vi phạm | Đạt | `focus_violations` tăng đúng; lớp phủ hiện lại khi thoát fullscreen |
| 14 | Chặn phím tắt | Đạt | Ctrl+R, F5, F11 bị chặn; Escape bị khóa trên Chrome/Edge |
| 15 | Nộp bài trong Focus Lock | Đạt | Xem đề, nộp bài, IDE đều hoạt động bình thường trong iframe |

<<Hình kết quả Focus Lock — giao diện wrapper, vi phạm được ghi nhận, nộp bài trong iframe>>

### 5.4.5. Kết quả kiểm thử tải đọc API

Kiểm thử được thực hiện bằng K6 với 4 mức tải trên hệ thống triển khai thực tế (Docker Compose, uWSGI 8 worker, MariaDB, Redis, Nginx). Mỗi mức tải chạy trong 1 phút. Kết quả được tổng hợp trong bảng sau:

| Chỉ số | 50 VU | 100 VU | 200 VU | 300 VU |
|--------|-------|--------|--------|--------|
| Tổng request | 6.684 | 6.642 | 6.804 | 6.777 |
| Request/s | 108,1 | 104,4 | 90,1 | 77,9 |
| Error rate | 0,00% | 0,00% | 0,19% | 1,63% |
| P50 tổng thể (ms) | 101 | 588 | 1.040 | 1.110 |
| P95 tổng thể (ms) | 246 | 735 | 3.800 | 6.760 |
| Max (ms) | 1.180 | 1.410 | 61.000 | 61.000 |

**Chi tiết theo endpoint:**

| Endpoint | Chỉ số | 50 VU | 100 VU | 200 VU | 300 VU |
|----------|--------|-------|--------|--------|--------|
| Trang chủ (`/`) | P50 (ms) | 82 | 566 | 1.870 | 2.150 |
| | P95 (ms) | 204 | 675 | 5.320 | 17.720 |
| Bài tập (`/problems/`) | P50 (ms) | 79 | 570 | 978 | 1.020 |
| | P95 (ms) | 209 | 669 | 1.960 | 3.130 |
| Kỳ thi (`/contests/`) | P50 (ms) | 143 | 638 | 1.050 | 1.100 |
| | P95 (ms) | 291 | 964 | 1.820 | 2.470 |

<<Hình biểu đồ P95 response time theo mức tải — 4 cột cho 4 mức VU, mỗi cột chia 3 màu cho 3 endpoint>>

**Phân tích kết quả:**

Ở mức **50 VU**, hệ thống phản hồi nhanh với P95 tổng thể dưới 250 ms và error rate 0%. Đây là mức tải phù hợp với sử dụng hằng ngày (lớp học, luyện tập cá nhân).

Ở mức **100 VU**, P95 tăng lên 735 ms nhưng vẫn dưới 1 giây, error rate vẫn 0%. Hệ thống đáp ứng tốt cho kỳ thi quy mô nhỏ.

Ở mức **200 VU**, bắt đầu xuất hiện lỗi (0,19%) và P95 tăng lên 3,8 giây. Trang chủ chịu ảnh hưởng nhiều nhất với P95 đạt 5,3 giây. Đây là ngưỡng bắt đầu suy giảm đáng kể.

Ở mức **300 VU** (stress test), error rate tăng lên 1,63%, P95 tổng thể đạt 6,7 giây và trang chủ có P95 lên đến 17,7 giây. Request tối đa đạt timeout 61 giây. Hệ thống vẫn phục vụ được nhưng trải nghiệm người dùng suy giảm rõ rệt.

**Throughput** giảm dần khi tải tăng: từ 108 req/s (50 VU) xuống 78 req/s (300 VU), cho thấy hệ thống bắt đầu bão hòa ở khoảng 100–200 VU.

### 5.4.6. Tổng hợp kết quả

| Nhóm chức năng | Số kịch bản | Đạt | Không đạt |
|----------------|-------------|-----|-----------|
| Luồng nộp bài và chấm bài | 4 | 4 | 0 |
| IDE trực tuyến | 2 | 2 | 0 |
| Các chức năng AI | 5 | 5 | 0 |
| Cơ chế khóa tập trung | 4 | 4 | 0 |
| **Tổng cộng** | **15** | **15** | **0** |

Đối với kiểm thử tải, hệ thống duy trì error rate 0% đến mức 100 VU đồng thời và bắt đầu xuất hiện lỗi từ 200 VU trở lên. Nếu lấy ngưỡng P95 dưới 1 giây làm tiêu chí, cấu hình hiện tại đáp ứng tốt cho khoảng 100 người dùng truy cập đồng thời.

## 5.5. Đánh giá hệ thống

### 5.5.1. Kết quả đạt được

**Về luồng chấm bài**, hệ thống xử lý đúng toàn bộ vòng đời bài nộp với các loại kết quả khác nhau (AC, WA, CE, TLE, MLE). Kiến trúc Django Site → Bridge → Judge hoạt động ổn định, kết quả chấm được cập nhật theo thời gian thực qua WebSocket đến trình duyệt mà không cần người dùng tải lại trang.

**Về IDE trực tuyến**, luồng RunSubmission hoạt động độc lập với luồng chấm chính thức. Người dùng có thể chạy thử chương trình với test case mẫu (`is_sample`) và nhận kết quả nhanh mà không tạo bản ghi Submission. Kết quả được lưu dạng JSON trong trường `case_results` thay vì tạo nhiều bản ghi `SubmissionTestCase`, giúp giảm tải cơ sở dữ liệu.

**Về các chức năng AI**, bốn tính năng AI đều kết nối thành công với dịch vụ bên ngoài thông qua API key do người dùng tự quản lý:

- Phân tích mã nguồn trả về nhận xét có cấu trúc và tự động trích tag dạng bài vào `UserProblemTag`, tích lũy thành dữ liệu tiến độ kỹ năng trên trang Progress.
- Tạo đề bài từ ảnh trích xuất chính xác nội dung và trả về Markdown đúng cấu trúc (Input, Output, Subtask, Example).
- Sinh chương trình tạo test case tạo ra mã C++ hợp lệ; hệ thống máy chấm biên dịch và thực thi trọn vẹn luồng generator → solution → đóng gói test case.
- Gợi ý dạng bài phân tích bài nộp AC và đề bài để đề xuất tag phù hợp, có bước kiểm tra điều kiện tiên quyết (cần ít nhất 3 bài nộp AC).

API key được mã hóa bằng Fernet, chỉ giải mã tạm thời khi gọi API và xóa ngay khỏi bộ nhớ sau khi sử dụng.

**Về cơ chế khóa tập trung**, Focus Lock hoạt động đúng theo thiết kế: chuyển hướng thí sinh vào trang wrapper, yêu cầu toàn màn hình, tải giao diện thi trong iframe, ẩn thanh điều hướng, chặn các phím tắt (Ctrl+R, F5, F11, Escape), theo dõi và ghi nhận vi phạm khi thoát toàn màn hình hoặc chuyển tab. Thí sinh vẫn sử dụng được đầy đủ chức năng xem đề, nộp bài và chạy thử trong iframe. Middleware phía server chặn truy cập URL ngoài trang wrapper, ngăn thí sinh thoát khỏi môi trường kiểm soát bằng cách truy cập trực tiếp URL khác.

### 5.5.2. Hạn chế còn tồn tại

**Về khả năng chịu tải**, kết quả kiểm thử cho thấy hệ thống bắt đầu xuất hiện lỗi từ 200 VU đồng thời và suy giảm rõ rệt ở 300 VU. Với cấu hình hiện tại (uWSGI 8 worker trên một máy chủ duy nhất), ngưỡng phục vụ ổn định nằm ở khoảng 100 người dùng đồng thời. Để mở rộng, cần tăng số worker uWSGI, bổ sung cache cho các trang có tải truy vấn nặng (danh sách bài tập, trang chủ), hoặc triển khai nhiều instance site phía sau load balancer. Ngoài ra, kiểm thử tải mới đo luồng đọc trang; chưa đo tải nộp bài đồng thời do cần nhiều tài khoản và bài toán kiểm thử.

**Về chức năng AI**, chất lượng phản hồi phụ thuộc hoàn toàn vào dịch vụ AI bên ngoài và model được chọn. Hệ thống không kiểm soát được độ chính xác của nội dung phân tích, tag gợi ý, hay chương trình generator do AI tạo ra. Người dùng luôn cần kiểm tra lại kết quả trước khi sử dụng chính thức. Ngoài ra, thời gian phản hồi từ dịch vụ AI có thể kéo dài (đến 120 giây đối với model reasoning), ảnh hưởng đến trải nghiệm người dùng.

**Về cơ chế khóa tập trung**, Focus Lock hoạt động ở tầng trình duyệt nên có thể bị vô hiệu hóa nếu thí sinh sử dụng công cụ can thiệp vào DOM hoặc trình duyệt không hỗ trợ đầy đủ API (Keyboard Lock chỉ hoạt động trên Chrome/Edge). Hệ thống chỉ ghi nhận số lần vi phạm mà không tự động xử lý hay loại thí sinh, việc đánh giá gian lận vẫn phụ thuộc vào người quản trị.

**Về kiến trúc triển khai**, máy chấm chạy độc lập bên ngoài Docker Compose, việc theo dõi trạng thái và khởi động lại máy chấm khi gặp sự cố cần thực hiện thủ công. Chưa có cơ chế tự phát hiện và phục hồi khi máy chấm mất kết nối.

## 5.6. Tổng kết chương

Chương này đã kiểm thử hệ thống BKDNOJ trên môi trường triển khai thực tế thông qua hai phương pháp: kiểm thử chức năng (15 kịch bản) và kiểm thử tải (4 mức tải bằng K6).

Về kiểm thử chức năng, toàn bộ 15 kịch bản đều đạt yêu cầu. Luồng chấm bài xử lý đúng toàn bộ vòng đời bài nộp với các loại kết quả khác nhau (AC, WA, CE, TLE, MLE). IDE trực tuyến hoạt động độc lập với luồng chấm chính thức. Bốn chức năng AI kết nối thành công với dịch vụ bên ngoài, xử lý và lưu trữ kết quả đúng. Cơ chế khóa tập trung theo dõi và ghi nhận vi phạm đúng trong môi trường kỳ thi.

Về kiểm thử tải, hệ thống duy trì error rate 0% và P95 dưới 250 ms ở mức 50 VU, P95 dưới 735 ms ở mức 100 VU. Từ 200 VU trở lên bắt đầu xuất hiện lỗi và P95 vượt ngưỡng 3 giây. Ngưỡng phục vụ ổn định của cấu hình hiện tại (uWSGI 8 worker, một máy chủ) nằm ở khoảng 100 người dùng đồng thời.

Các hạn chế bao gồm: chưa đo tải nộp bài đồng thời, chất lượng AI phụ thuộc dịch vụ bên ngoài, Focus Lock có giới hạn kỹ thuật ở tầng trình duyệt, và máy chấm chưa có cơ chế tự phục hồi. Các hạn chế này là cơ sở để định hướng cải tiến trong tương lai.
