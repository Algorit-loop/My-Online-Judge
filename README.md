# Hướng Dẫn Chi Tiết Thiết Lập Máy Chấm (Judge Server) - VNOJ

## Mục Lục
1. [Kiến Trúc Hệ Thống](#kiến-trúc-hệ-thống)
   - [Quy Trình Hoạt Động](#quy-trình-hoạt-động)
   - [Chi Tiết Quá Trình Chấm Bài](#chi-tiết-quá-trình-chấm-bài)
   - [Cấu Hình Khuyến Nghị](#cấu-hình-khuyến-nghị)
2. [Chuẩn Bị](#chuẩn-bị)
3. [Cài Đặt Docker và Docker-Compose](#cài-đặt-docker-và-docker-compose)
4. [Cài Đặt Máy Chủ (Local Server)](#cài-đặt-máy-chủ-local-server)
5. [Cài Đặt Máy Chấm](#cài-đặt-máy-chấm)
6. [Cài Đặt Máy Chấm Từ Xa](#cài-đặt-máy-chấm-từ-xa)
7. [Kiểm Tra và Khắc Phục Sự Cố](#kiểm-tra-và-khắc-phục-sự-cố)
   - [Kiểm Tra Trạng Thái Judge](#1-kiểm-tra-trạng-thái-judge)
   - [Theo Dõi Quá Trình Chấm Bài](#2-theo-dõi-quá-trình-chấm-bài-qua-logs)
   - [Vấn Đề Phổ Biến](#3-vấn-đề-phổ-biến)
   - [Monitoring](#4-monitoring)
8. [Tham Khảo](#tham-khảo)

---

## Kiến Trúc Hệ Thống

### Tổng Quan
Hệ thống VNOJ bao gồm 3 thành phần chính:
- **Site Server**: Máy chủ web chính chứa giao diện và logic quản lý
- **Bridge**: Daemon trung gian kết nối Judge với Site (chạy trong Docker)
- **Judge Server**: Máy chấm thực thi bài tập, có thể chạy cục bộ hoặc từ xa

### Quy Trình Hoạt Động
```
User Submit -> Site Server -> Bridge Daemon -> Judge Server -> Kết Quả
```

### Chi Tiết Quá Trình Chấm Bài

#### 1. **Giai Đoạn Nộp Bài (Submission)**

Khi người dùng nộp bài:

```
User (Web Browser)
  ↓
  Dữ liệu: source code, language, problem ID
  ↓
Site Server (Django) - route: /api/submit/
  ↓
  Lưu vào Database với status = 'QU' (Queued)
  ↓
  Gọi hàm: judge_submission(submission)
  ↓
Packet gửi đến Bridge Daemon:
{
  "name": "submission-request",
  "submission-id": 123,          # ID bài nộp
  "problem-id": "aplusb",        # Code bài tập
  "language": "cpp",              # Ngôn ngữ lập trình
  "source": "<code>...",         # Mã nguồn
  "time-limit": 1000,            # Giới hạn thời gian (ms)
  "memory-limit": 64,            # Giới hạn bộ nhớ (MB)
  "short-circuit": false,        # Dừng sớm khi fail
  "meta": {                       # Thông tin metadata
    "pretests-only": false,
    "in-contest": 0,
    "attempt-no": 1,
    "user": 42
  }
}
```

#### 2. **Giai Đoạn Truyền Dữ Liệu (Data Transmission)**

**Format Giao Tiếp**: TCP Socket + Zlib Compression

```
┌──────────────────────────────┐
│ Site Server (Port 9998)      │
│ Bridge Daemon                │
│ - Lắng nghe trên port 9998   │
│ - Nhận request từ Site       │
│ - Gửi request tới Judge      │
└──────────────────────────────┘
         ↓ (Port 9999)
┌──────────────────────────────┐
│ Judge Server (Port 9999)     │
│ - Nhận request từ Bridge     │
│ - Chấm bài                   │
│ - Gửi kết quả về Bridge      │
└──────────────────────────────┘
```

**Protocol Chi Tiết** (`/judge/judgeapi.py`):

```python
# Gửi request
1. JSON encode: {"name": "submission-request", ...}
2. Zlib compress: zlib.compress(json_bytes)
3. Thêm header: struct.pack('!I', length) + compressed_data
4. Gửi qua socket

# Nhận response
1. Đọc 4 bytes header để lấy độ dài
2. Đọc dữ liệu theo độ dài
3. Zlib decompress
4. JSON decode
```

**Cấu Trúc Packet Zlib**:
```
┌────────┬─────────────────────┐
│ 4 bytes│   Compressed Data   │
│ Length │   (Zlib Format)     │
└────────┴─────────────────────┘
  Header     Payload
```

#### 3. **Giai Đoạn Chấm Bài (Grading)**

Judge Server làm những việc sau:

```
Judge Server Process:
  1. Nhận packet từ Bridge
  2. Verify ID & xác thực
  3. Biên dịch source code
     ├─ Nếu lỗi → gửi 'compile-error' về
     └─ Nếu OK → tiếp tục
  4. Chạy binary với mỗi test case:
     ├─ Đọc input
     ├─ Chạy với resource limit (time, memory)
     ├─ So sánh output với expected output
     ├─ Gửi 'test-case-status' cho mỗi test
     └─ Cập nhật điểm
  5. Gửi 'grading-end' với kết quả cuối
```

**Các Packet Judge Gửi Về**:

```python
# 1. Submission Acknowledged
{"name": "submission-acknowledged", "submission-id": 123}

# 2. Grading Begin (bắt đầu chấm)
{"name": "grading-begin", "submission-id": 123, "pretested": false}

# 3. Test Case Status (từng test case)
{
  "name": "test-case-status",
  "submission-id": 123,
  "case": 1,                    # Test case số
  "status": "AC",               # AC/WA/TLE/MLE/RTE/etc
  "time": 15,                   # ms
  "memory": 2048,               # KB
  "points": 100,                # điểm
  "total": 100,                 # tổng điểm
  "batch": 0                    # batch ID (0 = không batch)
}

# 4. Compile Error (nếu lỗi compile)
{
  "name": "compile-error",
  "submission-id": 123,
  "log": "error: undefined reference to..."
}

# 5. Grading End (chấm xong)
{
  "name": "grading-end",
  "submission-id": 123
}
```

#### 4. **Giai Đoạn Xử Lý Kết Quả (Result Processing)**

Bridge Daemon nhận packets từ Judge:

```python
# File: /judge/bridge/judge_handler.py

handlers = {
    'grading-begin': self.on_grading_begin,      # Cập nhật status = 'G'
    'test-case-status': self.on_test_case,       # Lưu kết quả test case
    'grading-end': self.on_grading_end,          # Tính kết quả cuối
    'compile-error': self.on_compile_error,      # Lưu lỗi compile
    ...
}
```

**Xử Lý `test-case-status`**:
```python
# Lưu từng test case vào SubmissionTestCase table
SubmissionTestCase.objects.create(
    submission_id=123,
    case=1,
    status='AC',
    time=15,
    memory=2048,
    points=100,
    total=100,
    batch=0
)
```

**Xử Lý `grading-end`**:
```python
# Tính toán:
# 1. Tổng thời gian: sum(time of all test cases)
# 2. Bộ nhớ max: max(memory of all test cases)
# 3. Điểm: sum(points) / sum(total) * problem.points
# 4. Kết quả: 'AC' if all test 'AC' else worst status

submission.status = 'D'        # Done
submission.time = 450          # ms
submission.memory = 2048       # KB
submission.points = 100        # điểm
submission.result = 'AC'       # Kết quả
submission.save()
```

#### 5. **Giai Đoạn Cập Nhật Web (Event Broadcasting)**

WebSocket daemon (port 15101) broadcast kết quả:

```python
# File: /judge/event_poster_ws.py

# Bridge gửi event tới WebSocket daemon
event.post('sub_123', {
  'type': 'grading-end',
  'time': 450,
  'memory': 2048,
  'points': 100,
  'result': 'AC'
})

↓ (WebSocket)

# Browser client nhận event
WebSocket.onmessage = (event) => {
  if (event.data.type === 'grading-end') {
    updateUI(event.data);  // Cập nhật màn hình
  }
}
```

#### 6. **Luồng Dữ Liệu Toàn Bộ**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User nộp bài qua web                                     │
│    Source: C++, Python, Java, etc.                         │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│ 2. Site Server (Django)                                     │
│    - Lưu vào database (status='QU')                        │
│    - Gọi judge_submission()                               │
└─────────────────────────────┬───────────────────────────────┘
                              │
        ┌─────────────────────▼─────────────────────┐
        │ 3a. Tạo JSON packet (submission-request) │
        │     + Zlib compress                      │
        │     + Gửi qua socket (port 9998)        │
        └─────────────────────┬─────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│ 4. Bridge Daemon (Docker container vnoj_bridged)           │
│    - Port 9998: Lắng nghe từ Site                        │
│    - Port 9999: Kết nối tới Judge                        │
│    - Quản lý trạng thái: 'QU'→'P'→'G'→'D'               │
└─────────────────────────────┬───────────────────────────────┘
                              │
        ┌─────────────────────▼─────────────────────┐
        │ 5. Gửi packet tới Judge                  │
        │    (Zlib compressed JSON)                │
        │    (Port 9999)                          │
        └─────────────────────┬─────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│ 6. Judge Server (Docker: vnoj/judge-tier1:latest)          │
│    - Biên dịch source code                                 │
│    - Chạy với test cases                                  │
│    - Gửi từng test result qua port 9999                 │
└─────────────────────────────┬───────────────────────────────┘
                              │
        ┌─────────────────────▼─────────────────────┐
        │ 7. Gửi packets:                          │
        │    - test-case-status (mỗi test)       │
        │    - grading-end (kết thúc)            │
        │    - compile-error (nếu lỗi)          │
        └─────────────────────┬─────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│ 8. Bridge xử lý kết quả                                     │
│    - Lưu test cases to SubmissionTestCase table          │
│    - Tính toán điểm cuối                                  │
│    - Update status = 'D'                                   │
│    - Post event tới WebSocket daemon                      │
└─────────────────────────────┬───────────────────────────────┘
                              │
        ┌─────────────────────▼─────────────────────┐
        │ 9. WebSocket Daemon (port 15101)         │
        │    Broadcast event kết quả               │
        └─────────────────────┬─────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│ 10. Browser nhận qua WebSocket                             │
│     Cập nhật UI với kết quả                              │
│     Hiển thị: AC, WA, TLE, MLE, CE, IE, etc.            │
└─────────────────────────────────────────────────────────────┘
```

#### Status Codes:

```
QU - Queued (đợi chấm)
P  - Processing (đang xử lý)
G  - Grading (đang chấm)
D  - Done (hoàn tất)

Result Codes:
AC  - Accepted (Đúng)
WA  - Wrong Answer (Sai)
TLE - Time Limit Exceeded (Vượt thời gian)
MLE - Memory Limit Exceeded (Vượt bộ nhớ)
RTE - Runtime Error (Lỗi runtime)
CE  - Compile Error (Lỗi biên dịch)
IE  - Internal Error (Lỗi hệ thống)
OLE - Output Limit Exceeded (Vượt output limit)
```

---

### Cấu Hình Khuyến Nghị

#### Máy Chủ (Local Server)
- **OS**: Ubuntu 20.04 LTS trở lên
- **CPU**: 2+ Cores
- **RAM**: 4 GB trở lên
- **Storage**: 60 GB SSD
- **Mục đích**: Chạy Site, Redis, Database, và 2-3 Judge

#### Máy Chấm Từ Xa (Remote Judge) - Tùy Chọn
- **OS**: Ubuntu 20.04 LTS trở lên
- **CPU**: 1+ Core
- **RAM**: 2 GB trở lên
- **Storage**: 60 GB SSD
- **Mục đích**: Tăng tốc độ chấm, chia tải

---

## Chuẩn Bị

### Yêu Cầu Hệ Thống

1. **Cập Nhật Hệ Thống**
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

2. **Các Package Cần Thiết**
```bash
# Cài đặt Git
sudo apt-get install -y git

# Cài đặt Build Tools
sudo apt-get install -y build-essential curl wget

# Cho máy chấm: CÓ thể cần nhiều dependencies hơn
sudo apt-get install -y ca-certificates curl
```

### Lấy Mã Nguồn

Trên **Local Server**:

```bash
# Clone repository (nếu chưa có)
git clone --recursive https://github.com/VNOI-Admin/vnoj-docker.git
cd vnoj-docker/dmoj

# Hoặc nếu đã có, cập nhật:
cd vnoj-docker/dmoj
git pull origin master
```

---

## Cài Đặt Docker và Docker-Compose

### Cài Đặt Docker

#### Ubuntu/Debian

```bash
# 1. Chuẩn bị Repository Docker
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# 2. Thêm Docker Repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 3. Cài đặt Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

#### Kiểm Tra Cài Đặt
```bash
docker --version
docker run hello-world
```

### Cài Đặt Docker Compose

Docker Compose thường được cài với Docker plugin, nhưng cũng có thể cài standalone:

```bash
# Nếu chưa có plugin docker-compose:
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

### Cấu Hình Quyền Docker (Quan Trọng)

Để chạy Docker mà không cần `sudo`:

```bash
# Thêm user vào docker group
sudo usermod -aG docker $USER

# Áp dụng group mới
newgrp docker

# Kiểm tra
docker ps
```

> ⚠️ **Lưu Ý**: Để quyền `docker` hiệu lực, có thể cần đăng xuất và đăng nhập lại.

---

## Cài Đặt Máy Chủ (Local Server)

### Bước 1: Cấu Hình Môi Trường

Toàn bộ cài đặt thực hiện trong thư mục `/dmoj`.

#### 1.1. Khởi Tạo Cấu Hình
```bash
cd vnoj-docker/dmoj
./scripts/initialize
```

#### 1.2. Tạo File Môi Trường

```bash
# Tạo file mysql.env
cp environment/mysql.env.example environment/mysql.env

# Tạo file mysql-admin.env
cp environment/mysql-admin.env.example environment/mysql-admin.env

# Tạo file site.env
cp environment/site.env.example environment/site.env
```

#### 1.3. Chỉnh Sửa File Cấu Hình

**File: `environment/mysql.env`**
```env
MYSQL_HOST=db
MYSQL_DATABASE=dmoj
MYSQL_USER=dmoj
MYSQL_PASSWORD=your_strong_password_here  # GHI CHÚ: Thay đổi mật khẩu này
```

**File: `environment/mysql-admin.env`**
```env
MYSQL_ROOT_PASSWORD=your_root_password_here  # GHI CHÚ: Thay đổi mật khẩu root
```

**File: `environment/site.env`**
```env
# Cấu hình cơ bản
HOST=192.168.1.60                           # GHI CHÚ: Thay đổi thành IP của máy chủ
SITE_FULL_URL=http://192.168.1.60/          # Hoặc dùng domain name
MEDIA_URL=http://192.168.1.60/              # URL truy cập media files

# Cấu hình bảo mật
DEBUG=0                                      # Không dùng debug mode trên production
SECRET_KEY=your_secret_key_here             # GHI CHÚ: Tạo key ngẫu nhiên

# Nếu dùng HTTPS (tùy chọn)
# SITE_FULL_URL=https://yourdomain.com/
# MEDIA_URL=https://yourdomain.com/
```

**Tạo Secret Key ngẫu nhiên (Python):**
```bash
# Chạy câu lệnh sau để tạo một secret key an toàn:
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

#### 1.4. Cấu Hình Nginx

**File: `nginx/conf.d/nginx.conf`**

Chỉnh sửa dòng `server_name`:
```nginx
server {
    listen 80;
    server_name 192.168.1.60;  # Thay đổi thành IP hoặc domain của bạn
    # ... phần cấu hình khác
}
```

#### 1.5. Cấu Hình Local Settings (Tùy Chọn)

**File: `repo/dmoj/local_settings.py`**

Một số cấu hình quan trọng đã được thiết lập:
```python
# DMOJ Site Display
SITE_NAME = 'ALGORIT'
SITE_LONG_NAME = 'Algorit Online Judge'
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "algoritoj.id.vn",  # Thay đổi domain
]

# Judge Server Configuration
BRIDGED_JUDGE_ADDRESS = [(os.environ.get('BRIDGED_HOST', 'bridged'), 9999)]
BRIDGED_DJANGO_ADDRESS = [(os.environ.get('BRIDGED_HOST', 'bridged'), 9998)]

# Event Daemon (Live Update)
EVENT_DAEMON_USE = True
EVENT_DAEMON_POST = os.environ.get('EVENT_DAEMON_POST', 'ws://wsevent:15101/')
```

### Bước 2: Build Docker Images

```bash
# Build tất cả images
docker-compose build

# Hoặc build một image cụ thể
docker-compose build site
docker-compose build db
docker-compose build redis
```

### Bước 3: Khởi Động Database và Tạo Schema

```bash
# Khởi động base services (Database, Redis)
docker-compose up -d db redis

# Chờ Database khởi động (khoảng 10 giây)
sleep 10

# Khởi động Site
docker-compose up -d site

# Chạy migration (tạo database schema)
./scripts/migrate

# Copy static files
./scripts/copy_static
```

### Bước 4: Load Dữ Liệu Khởi Tạo

```bash
# Load dữ liệu mẫu (navbar, language, demo problems)
./scripts/manage.py loaddata navbar
./scripts/manage.py loaddata language_small
./scripts/manage.py loaddata demo

# Tạo superuser (admin account)
./scripts/manage.py createsuperuser
# Hoặc dùng demo account: username=admin, password=admin (không nên dùng trên production)
```

### Bước 5: Khởi Động Tất Cả Services

```bash
# Khởi động tất cả containers
docker-compose up -d

# Kiểm tra status
docker-compose ps

# Xem logs
docker-compose logs -f site
```

### Bước 6: Truy Cập Web

Mở trình duyệt và truy cập:
```
http://192.168.1.60/  # Thay đổi IP phù hợp
```

---

## Cài Đặt Máy Chấm

### Bước 1: Tạo Judge trong Admin Panel

1. Truy cập: `http://192.168.1.60/admin/judge/`
2. Thêm Judge (Add Judge): 
   - **Name**: `judge01` (hoặc tên khác)
   - **Lưu lại**: Sẽ tự tạo **ID** và **Authentication Key**

Ví dụ từ cấu hình hiện tại:
```
ID: judge01
Key: cTLqgCOG77KYgj2I/edX/Pt0MSyn+NtalIucB9jOSkNQEFBUdol8xoDQdbEnoAWtL7yt4+X2yoXHmddTxlBexyEohRSwQgb73N5T
```

### Bước 2: Build Judge Runtime Environment

Tải về judge-server repository và build Docker image:

```bash
# Tạo thư mục tạm
mkdir -p ~/judge-build
cd ~/judge-build

# Clone judge-server
git clone https://github.com/VNOI-Admin/judge-server.git
cd judge-server/.docker

# Cài đặt Make
sudo apt-get install -y make

# Build Judge Image (chọn một tier phù hợp)
# Tier 1: Python, C/C++, Java, Pascal (nhẹ - ~2GB)
sudo make judge-tier1

# Tier 2: Thêm Ruby, Go, PHP, Perl, Haskell... (~5GB)
# sudo make judge-tier2

# Tier 3: Đầy đủ (tất cả ngôn ngữ - ~10GB)
# sudo make judge-tier3

# TierVNOJ: Tùy chỉnh cho VNOJ (khuyến nghị)
# sudo make judge-tiervnoj
```

> **Lưu Ý**: 
> - `judge-tier1` đủ cho hầu hết bài tập cơ bản
> - Quá trình build mất 20-30 phút tùy ISP
> - Cần kết nối internet tốt

### Bước 3: Tạo File Cấu Hình Judge

Tạo file config cho mỗi judge. Ví dụ: `judge01.yml`

**File: `problems/judge01.yml`**
```yaml
id: 'judge01'
key: 'cTLqgCOG77KYgj2I/edX/Pt0MSyn+NtalIucB9jOSkNQEFBUdol8xoDQdbEnoAWtL7yt4+X2yoXHmddTxlBexyEohRSwQgb73N5T'
problem_storage_globs:
  - /problems/*
```

**File: `problems/judge02.yml`** (nếu cần chạy 2 judge)
```yaml
id: 'judge02'
key: 'second_judge_key_here'
problem_storage_globs:
  - /problems/*
```

> **GHI CHÚ**: ID và Key phải giống với những gì bạn tạo trong Admin Panel

### Bước 4: Khởi Động Judge Container

Trong thư mục `/dmoj`, chạy:

```bash
# Judge 1 (Port API: 9111)
sudo docker run \
    --name judge01 \
    --network="host" \
    -v /home/algorit/vnoj-docker/dmoj/problems:/problems \
    --cap-add=SYS_PTRACE \
    -d \
    --restart=always \
    vnoj/judge-tier1:latest \
    run -p 9999 -c /problems/judge01.yml 192.168.1.60 -A 0.0.0.0 -a 9111
```

**Giải thích các tham số:**
- `--name judge01`: Tên container
- `--network="host"`: Dùng network của host (cần thiết để kết nối)
- `-v /path/to/problems:/problems`: Mount thư mục chứa bài tập
- `--cap-add=SYS_PTRACE`: Cho phép trace process (cần cho sandbox)
- `--restart=always`: Tự khởi động khi Docker daemon restart
- `-p 9999`: Port dùng để liên lạc với judge
- `-c /problems/judge01.yml`: File cấu hình judge
- `192.168.1.60`: IP của site server
- `-A 0.0.0.0 -a 9111`: API port để quản lý judge

```bash
# Judge 2 (Port API: 9112) - nếu cần
sudo docker run \
    --name judge02 \
    --network="host" \
    -v /home/algorit/vnoj-docker/dmoj/problems:/problems \
    --cap-add=SYS_PTRACE \
    -d \
    --restart=always \
    vnoj/judge-tier1:latest \
    run -p 9999 -c /problems/judge02.yml 192.168.1.60 -A 0.0.0.0 -a 9112
```

### Bước 5: Kiểm Tra Judge

```bash
# Xem logs judge
sudo docker logs -ft judge01

# Kiểm tra container đang chạy
sudo docker ps | grep judge

# Kiểm tra kết nối
sudo docker exec judge01 netstat -tln | grep 9999
```

**Dấu Hiệu Thành Công:**
- Logs hiển thị: `Judge is ready`
- Container đang running
- Không có lỗi kết nối

---

## Cài Đặt Máy Chấm Từ Xa (Remote Judge)

### Kịch Bản Sử Dụng

- Máy chủ quá tải, cần chia tải
- Muốn scale up số judge
- Tăng tốc độ chấm

### Phần 1: Cài Đặt Docker trên Remote

```bash
# Thực hiện tương tự như Local Server (xem phần "Cài Đặt Docker")
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Thêm user vào docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Phần 2: Tảo Thư Mục Problems và Mount SSHFS

Trên **Remote Server**:

```bash
# Tạo thư mục để mount
sudo mkdir -p /mnt/problems
sudo chmod 755 -R /mnt/problems

# Cài đặt SSHFS
sudo apt-get install -y sshfs

# Thêm user vào docker group (nếu cần)
sudo usermod -aG fuse judger

# Mount problems từ Local Server
# (Thay đổi username, password, IP phù hợp)
sudo sshfs -o allow_other,IdentityFile=/home/judger/.ssh/id_rsa \
    username@192.168.1.60:/home/algorit/vnoj-docker/dmoj/problems \
    /mnt/problems
```

> **Setup SSH Key (Tùy chọn nhưng khuyến nghị):**
> ```bash
> # Trên Remote Server tạo SSH key
> ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
>
> # Copy public key đến Local Server
> ssh-copy-id -i ~/.ssh/id_rsa.pub username@192.168.1.60
> ```

### Phần 3: Build Judge Runtime

```bash
# Tương tự Local Server
git clone https://github.com/VNOI-Admin/judge-server.git
cd judge-server/.docker
sudo apt-get install -y make
sudo make judge-tier1
```

### Phần 4: Tạo File Cấu Hình Judge Remote

```bash
# Tạo file cấu hình
cat > /mnt/problems/judge03.yml << 'EOF'
id: 'judge03'
key: 'third_judge_key_from_admin'
problem_storage_globs:
  - /problems/*
EOF
```

### Phần 5: Khởi Động Judge Remote

```bash
sudo docker run \
    --name judge03 \
    --network="host" \
    -v /mnt/problems:/problems \
    --cap-add=SYS_PTRACE \
    -d \
    --restart=always \
    vnoj/judge-tier1:latest \
    run -p 9999 -c /problems/judge03.yml 192.168.1.60 -A 0.0.0.0 -a 9113
```

### Phần 6: Tự Động Mount SSHFS khi Reboot

Thêm vào `/etc/fstab` (hoặc dùng script startup):

```
username@192.168.1.60:/home/algorit/vnoj-docker/dmoj/problems /mnt/problems fuse.sshfs allow_other,IdentityFile=/home/judger/.ssh/id_rsa,reconnect,uid=1000,gid=1000 0 0
```

---

## Kiểm Tra và Khắc Phục Sự Cố

### 1. Kiểm Tra Trạng Thái Judge

#### 1.1. Trong Admin Panel
```
Site URL: http://192.168.1.60/admin/judge/
```
- Kiểm tra status của judge (xanh = online, đỏ = offline)

#### 1.2. Qua Command Line

```bash
# Xem tất cả container
docker ps -a

# Xem logs judge
docker logs -f judge01

# Kiểm tra network
docker exec judge01 netstat -tln

# Ping từ judge đến site
docker exec judge01 ping 192.168.1.60
```

### 2. Theo Dõi Quá Trình Chấm Bài Qua Logs

#### 2.1. Chuẩn Bị: Theo Dõi 3 Terminals Cùng Lúc

**Terminal 1: Xem Site logs**
```bash
docker-compose logs -f site
```

**Terminal 2: Xem Bridge logs**
```bash
docker-compose logs -f bridged
```

**Terminal 3: Xem Judge logs**
```bash
docker logs -f judge01
```

#### 2.2. Nộp Một Bài Tập Đơn Giản

1. Truy cập: `http://192.168.1.60/problems/aplusb/`
2. Tạo submission với code C++ đơn giản:
```cpp
#include <iostream>
using namespace std;
int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b << endl;
    return 0;
}
```
3. Nộp bài (Submit)

#### 2.3. Phân Tích Logs Theo Các Giai Đoạn

**Giai Đoạn 1: Site nhận request (Status: QU → P → G)**

Logs từ `site`:
```
[timestamp] Saving submission #123 with status='QU'
[timestamp] judge_submission() called for submission #123
[timestamp] Sending request to judge...
```

**Giai Đoạn 2: Bridge vận chuyển packet (Port 9998 → 9999)**

Logs từ `bridged`:
```
[timestamp] [judge01] Connected from: 192.168.1.xx:xxxxx
[timestamp] [judge01] Judge authenticated successfully
[timestamp] Submission #123 received from site
[timestamp] Forwarding submission #123 to judge
[timestamp] Bridge listening on port 9998
```

**Giai Đoạn 3: Judge chấm bài**

Logs từ `judge01`:
```
[timestamp] Received submission #123
[timestamp] Submission #123: Compiling...
[timestamp] Submission #123: Compilation successful
[timestamp] Submission #123: Running test case 1...
[timestamp] Test #1: AC (time=15ms, memory=2048KB)
[timestamp] Submission #123: Running test case 2...
[timestamp] Test #2: AC (time=12ms, memory=2048KB)
[timestamp] Submission #123: All tests completed
[timestamp] Sending grading-end for submission #123
```

**Giai Đoạn 4: Bridge xử lý kết quả (Status: D)**

Logs từ `bridged`:
```
[timestamp] [judge01] grading-end received for submission #123
[timestamp] Submission #123: Calculating final result...
[timestamp] Submission #123: Result = AC, Points = 100, Time = 27ms
[timestamp] Updating database: status='D'
[timestamp] Posting event to websocket daemon
```

**Giai Đoạn 5: Site cập nhật database**

Logs từ `site`:
```
[timestamp] Submission #123 status changed to 'D'
[timestamp] Result: AC, Points: 100
```

#### 2.4. Sử Dụng JSON Logs để Theo Dõi Chi Tiết

DMOJ có logger riêng cho JSON (structured logging):

```bash
# Tìm JSON logs từ bridged container
docker exec vnoj_bridged tail -f /var/log/judge-json.log

# Hoặc trong điểm mount logs (nếu có)
tail -f dmoj/logs/judge-json.log
```

**Ví dụ JSON log:**
```json
{
  "timestamp": "2026-03-05T14:30:45.123Z",
  "action": "submission",
  "submission_id": 123,
  "judge": "judge01",
  "problem": "aplusb",
  "language": "cpp",
  "status": "AC",
  "time_ms": 27,
  "memory_kb": 2048,
  "points": 100,
  "total_points": 100
}
```

#### 2.5. Lệnh Grep Hữu Ích

```bash
# Tìm lỗi compile
docker logs judge01 | grep -i "compile"

# Tìm timeout
docker logs judge01 | grep -i "timeout\|tle"

# Tìm memory exceeded
docker logs judge01 | grep -i "memory\|mle"

# Tìm runtime error
docker logs judge01 | grep -i "error\|runtime"

# Tìm tất cả sự kiện của submission #123
docker logs vnoj_bridged | grep "123"

# Xem number of submissions processed
docker logs judge01 | grep "grading-end" | wc -l
```

#### 2.6. Kiểm Tra Database Trực Tiếp

```bash
# Truy cập MySQL trong Docker
docker exec -it vnoj_mysql mysql -u dmoj -p dmoj

# Trong MySQL prompt:
# Xem submission vừa nộp
SELECT id, status, result, points, time, memory FROM judge_submission 
WHERE id = 123;

# Xem test case results
SELECT case, status, points, total, time, memory FROM judge_submissiontestcase 
WHERE submission_id = 123 
ORDER BY case;

# Thoát
exit
```

**Output ví dụ:**
```
+-----+--------+--------+--------+------+--------+
| id  | status | result | points | time | memory |
+-----+--------+--------+--------+------+--------+
| 123 | D      | AC     |    100 |   27 |   2048 |
+-----+--------+--------+--------+------+--------+

+------+--------+--------+-------+------+--------+
| case | status | points | total | time | memory |
+------+--------+--------+-------+------+--------+
|    1 | AC     |    100 |   100 |   15 |   2048 |
|    2 | AC     |    100 |   100 |   12 |   2048 |
+------+--------+--------+-------+------+--------+
```

#### 2.7. Real-time Monitoring Dashboard (Optional)

Tạo bash script để theo dõi realtime:

```bash
#!/bin/bash
# monitor-judge.sh

while true; do
    clear
    echo "=== VNOJ Judge Monitoring ==="
    echo "Time: $(date)"
    echo ""
    
    echo "Container Status:"
    docker ps --filter "name=judge\|bridge\|site" --format "table {{.Names}}\t{{.Status}}"
    echo ""
    
    echo "Judge Queue:"
    docker exec vnoj_mysql mysql -u dmoj -p dmoj -e "SELECT COUNT(*) as queued FROM judge_submission WHERE status='QU';" 2>/dev/null
    
    echo ""
    echo "Latest Submissions:"
    docker exec vnoj_mysql mysql -u dmoj -p dmoj -e "SELECT id, result, points FROM judge_submission ORDER BY id DESC LIMIT 5;" 2>/dev/null
    
    echo ""
    echo "Press Ctrl+C to stop"
    sleep 5
done
```

Chạy:
```bash
chmod +x monitor-judge.sh
./monitor-judge.sh
```

### 3. Vấn Đề Phổ Biến

#### Lỗi: "Cannot connect to socket"
```
Nguyên nhân: Judge không thể kết nối tới Site
Giải pháp:
- Kiểm tra IP trong cấu hình là đúng
- Kiểm tra firewall
- Kiểm tra bridge container đang running
```

#### Lỗi: "Permission denied"
```bash
# Nguyên nhân: Docker daemon không có quyền đủ
# Giải pháp:
sudo usermod -aG docker $USER
newgrp docker
sudo usermod -aG fuse $USER  # Nếu dùng SSHFS
```

#### Lỗi: "Disk quota exceeded"
```bash
# Nguyên nhân: Không gian ổ cứng hết
# Giải pháp:
df -h  # Kiểm tra dung lượng
docker system prune  # Dọn dẹp Docker
```

#### Judge Không Chấm Bài

1. **Kiểm tra trạng thái judge:**
```bash
docker logs -f judge01 | grep -i "error\|ready"
```

2. **Kiểm tra file cấu hình judge:**
```bash
cat problems/judge01.yml
```

3. **Kiểm tra quyền thư mục:**
```bash
ls -la problems/
# Cấp quyền nếu cần
sudo chmod 755 -R problems/
```

4. **Restart judge:**
```bash
docker restart judge01
```

### 3. Monitoring

#### Giám Sát Docker Resources

```bash
# Xem CPU, Memory, Network
docker stats

# Hoặc giám sát judge cụ thể
docker stats judge01
```

#### Giám Sát Logs Realtime

```bash
# Tất cả logs
docker-compose logs -f

# Logs của judge
docker logs -f judge01 --tail 50
```

---

## Tham Khảo

### Repository Chính

1. **VNOJ Docker**: https://github.com/VNOI-Admin/vnoj-docker
2. **Judge Server**: https://github.com/VNOI-Admin/judge-server
3. **Hướng Dẫn Deployment**: https://github.com/VietThienTran/DeploymentTools/tree/main/VNOJ

### Tài Liệu Liên Quan

- [Docker Documentation](https://docs.docker.com/)
- [DMOJ Judge Documentation](https://docs.dmoj.ca/)
- [Django Documentation](https://docs.djangoproject.com/)

### Các Tính Năng Thêm

#### Email Settings (Để gửi thông báo)
```python
# File: repo/dmoj/local_settings.py
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'app_password'  # Google App Password
EMAIL_PORT = 587
```

#### Bật Full-Text Search
```python
ENABLE_FTS = True  # Trong local_settings.py
```

#### Kiểm Soát Lượng Bài Nộp (Rate Limit)
```python
DMOJ_PASSWORD_RESET_LIMIT_COUNT = 5
DMOJ_PASSWORD_RESET_LIMIT_WINDOW = 3600
```

---

## Troubleshooting & FAQ

### Q: Làm sao biết judge đã kết nối thành công?

**A:** Kiểm tra:
1. Admin Panel: `/admin/judge/` - status màu xanh
2. Docker logs: `docker logs judge01` - không có error
3. Thử nộp bài đơn giản

### Q: Có thể chạy nhiều judge trên 1 máy không?

**A:** Có, cần đổi tên container, API port, file config:
```bash
# judge01: -a 9111
# judge02: -a 9112
# judge03: -a 9113
```

### Q: Docker restart mất bao lâu?

**A:** 
- Khởi động lần đầu: 1-2 phút
- Restart sau: 30 giây - 1 phút
- Tùy vào cấu hình máy

### Q: Cách sao lưu dữ liệu?

**A:** 
```bash
# Sao lưu database
docker exec vnoj_mysql mysqldump -uroot -p$MYSQL_ROOT_PASSWORD dmoj > backup.sql

# Sao lưu thư mục problems
tar -czf problems_backup.tar.gz problems/
```

### Q: Thay đổi cấu hình sau khi chạy?

**A:**
```bash
# Sửa file cấu hình
# Rồi:
docker-compose down
docker-compose build  # Nếu thay Dockerfile
docker-compose up -d
```

---

## Ghi Chú Quan Trọng

⚠️ **Production Deployment**:
- Luôn dùng HTTPS với Let's Encrypt
- Thay đổi mật khẩu default
- Bật 2FA nếu có thể
- Setup proper backup strategy
- Giám sát logs thường xuyên
- Update Docker images định kỳ

⚠️ **Security**:
- Không exposed port 9998, 9999 ra internet
- Dùng firewall để hạn chế access
- Thay secret key định kỳ
- Giữ container/OS luôn cập nhật

⚠️ **Performance**:
- Cập nhật Judge khi có version mới
- Monitor disk space (problems/ có thể lớn)
- Optimize database queries
- Cache static files

---

## Hỗ Trợ

Nếu gặp vấn đề:

1. Kiểm tra lại hướng dẫn từ đầu
2. Xem logs: `docker-compose logs` hoặc `docker logs <container>`
3. Tham khảo: GitHub Issues của VNOI-Admin
4. Liên hệ community VNOI

**Chúc bạn thành công!** 🎉

---

*Tài liệu này dựa trên:*
- VNOI-Admin/vnoj-docker
- VietThienTran/DeploymentTools
- DMOJ Judge Server Documentation
- Phiên bản: March 2026


Xóa DOCKER:
- Stop toàn bộ container: `docker stop $(docker ps -aq)`  
- Xoá toàn bộ container: `docker rm -f $(docker ps -aq)`
- Xoá image không dùng: `docker image prune [-a]`
- Xoá volume: docker `volume prune -a`
- Xoá TẤT CẢ (rất mạnh 💥): `docker system prune -a --volumes`

Kiểm tra lại:
```
docker ps -a
docker images
docker volume ls
```

