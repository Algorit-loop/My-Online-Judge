# BKDNOJ - Bách Khoa Đà Nẵng Online Judge

## Mục Lục

1. [Kiến Trúc Hệ Thống](#kien-truc-he-thong)
2. [Yêu Cầu Hệ Thống](#yeu-cau-he-thong)
3. [Build Dự Án (Từ Đầu)](#build-du-an-tu-dau)
4. [Run Dự Án (Khởi Động)](#run-du-an-khoi-dong)
5. [Cài Đặt Máy Chấm (Judge)](#cai-dat-may-cham-judge)
6. [Cập Nhật Dự Án](#cap-nhat-du-an)
7. [Rebuild CodeMirror 6 (Chỉ khi cần)](#rebuild-codemirror-6)

---

<a id="kien-truc-he-thong"></a>
## Kiến Trúc Hệ Thống

```
                         +-------------------+
                         |    Nginx (:80)    |
                         |  Reverse Proxy    |
                         +--------+----------+
                                  |
              +-------------------+-------------------+
              |                   |                   |
    +---------v------+  +--------v--------+  +-------v--------+
    |  Site (uWSGI)  |  | WSEvent (Node)  |  |  Static Files  |
    |  Django :8000  |  | WS :15100-15102 |  |  /assets/      |
    +-------+--------+  +-----------------+  +----------------+
            |
    +-------+--------+
    |                |
+---v---+    +-------v-------+
|  DB   |    | Redis (Cache) |
|MariaDB|    |   + Celery    |
+-------+    +---------------+

    +-------------------+
    | Bridge (:9998/99) |<------>  Judge Server(s)
    +-------------------+
```

**7 Docker containers:**

| Container | Image | Port | Chức năng |
|-----------|-------|------|-----------|
| `bkdnoj_mysql` | mariadb | 3306 (internal) | Database |
| `bkdnoj_redis` | redis:alpine | 6379 (internal) | Cache + Celery broker |
| `bkdnoj_site` | bkdnoj/bkdnoj-site | 8000 (internal) | Django web app (uWSGI) |
| `bkdnoj_celery` | bkdnoj/bkdnoj-celery | - | Background tasks |
| `bkdnoj_bridged` | bkdnoj/bkdnoj-bridged | 9998, 9999 | Judge connection bridge |
| `bkdnoj_wsevent` | bkdnoj/bkdnoj-wsevent | 15100-15102 (internal) | WebSocket live updates |
| `bkdnoj_nginx` | nginx:alpine | **80** | Reverse proxy + static |

**Luồng chấm bài:**
```
User Submit -> Site -> Bridge (:9998) -> Judge (:9999) -> Kết quả -> WebSocket -> Browser
```

---

<a id="yeu-cau-he-thong"></a>
## Yêu Cầu Hệ Thống

| Thành phần | Tối thiểu | Khuyến nghị |
|------------|-----------|-------------|
| OS | Ubuntu 20.04 LTS | Ubuntu 22.04+ |
| CPU | 2 Cores | 4+ Cores |
| RAM | 4 GB | 8 GB |
| Disk | 60 GB SSD | 100 GB SSD |
| Software | Docker, Docker Compose | - |

### Cài Docker

```bash
# Cập nhật hệ thống
sudo apt-get update && sudo apt-get upgrade -y

# Cài Docker
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Cho phép chạy Docker không cần sudo
sudo usermod -aG docker $USER
newgrp docker

# Kiểm tra
docker --version
docker compose version
```

> **Ghi chú về lệnh Docker Compose:**
> - **Docker mới (v2+):** dùng `docker compose` (có khoảng trắng, tích hợp sẵn vào Docker CLI)
>   ```bash
>   docker compose up -d
>   ```
> - **Docker cũ (v1, cài riêng `docker-compose`):** dùng `docker-compose` (có dấu gạch ngang)
>   ```bash
>   docker-compose up -d
>   ```
> Kiểm tra phiên bản: `docker compose version` (bản mới) hoặc `docker-compose --version` (bản cũ).  
> Tài liệu này sử dụng cú pháp bản mới (`docker compose`). Nếu bạn dùng bản cũ, thay `docker compose` thành `docker-compose` trong tất cả các lệnh.

---

<a id="build-du-an-tu-dau"></a>
## Build Dự Án (Từ Đầu)

### Bước 1: Clone Repository

```bash
git clone --recursive <repo-url> bkdnoj-docker
cd bkdnoj-docker/dmoj
```

### Bước 2: Cấu hình môi trường

```bash
# Khởi tạo config (copy local_settings.py, uwsgi.ini, config.js vào repo/)
./scripts/initialize

# Tạo file environment từ example
cp environment/mysql.env.example environment/mysql.env
cp environment/mysql-admin.env.example environment/mysql-admin.env
cp environment/site.env.example environment/site.env
```

Chỉnh sửa các file:

**`environment/mysql.env`** - đổi `<password>` thành mật khẩu thật:
```env
MYSQL_HOST=db
MYSQL_DATABASE=dmoj
MYSQL_USER=dmoj
MYSQL_PASSWORD=<mat-khau-manh>
```

**`environment/mysql-admin.env`** - đổi `<password>` thành mật khẩu root:
```env
MYSQL_ROOT_PASSWORD=<mat-khau-root>
```

**`environment/site.env`** - đổi `localhost` thành IP/domain thật, đổi `<secret key>`:
```env
HOST=<ip-hoac-domain>
SITE_FULL_URL=http://<ip-hoac-domain>/
MEDIA_URL=http://<ip-hoac-domain>/
DEBUG=0
SECRET_KEY=<tao-key-ngau-nhien>

# Các dòng còn lại giữ nguyên giá trị mặc định
EVENT_DAEMON_POST=ws://wsevent:15101/
REDIS_CACHING_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1
BRIDGED_HOST=bridged
```

Tạo Secret Key (chọn 1 trong 2 cách):
```bash
# Cách 1: Dùng Python có sẵn trên máy
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Cách 2: Dùng openssl
openssl rand -base64 50
```

> **Ghi chú:** Nginx config mặc định (`nginx/conf.d/nginx.conf`) dùng `server_name _;` (chấp nhận mọi domain/IP), nên **không cần sửa** nếu chỉ truy cập qua IP. Nếu muốn giới hạn cho domain cụ thể, đổi `_` thành tên domain.

### Bước 3: Build Docker images

```bash
docker compose build base
docker compose build
```

> Lần đầu build mất khoảng 10-15 phút do tải Python packages, Node.js, v.v.

### Bước 4: Khởi động Database + Migrate

```bash
# Khởi động DB và Redis trước, đợi DB sẵn sàng
docker compose up -d db redis

# Đợi MariaDB khởi động xong (lần đầu có thể mất 15-30 giây)
# Kiểm tra bằng: docker compose logs db | tail -5
# Khi thấy "ready for connections" là được
sleep 15

# Khởi động Site
docker compose up -d site

# Đợi site container khởi động
sleep 5

# Chạy migration để tạo bảng trong database
./scripts/migrate
```

> **Lưu ý:** Nếu `migrate` báo lỗi kết nối DB, đợi thêm vài giây rồi chạy lại. MariaDB lần đầu cần thời gian khởi tạo.

### Bước 5: Build Static Files

```bash
./scripts/copy_static
```

> Bước này chạy bên trong site container và thực hiện:
> 1. `make_style.sh` - Compile Sass thành CSS
> 2. `collectstatic` - Thu thập tất cả static files (CodeMirror 6, Ace, jQuery, v.v.) vào `/assets/static/`
> 3. `compilemessages` + `compilejsi18n` - Compile file đa ngôn ngữ (i18n)
> 4. Copy `resources/`, `502.html`, `logo.png`, `robots.txt` vào `/assets/`

### Bước 6: Load dữ liệu khởi tạo

```bash
# Navbar menu
./scripts/manage.py loaddata navbar

# Ngôn ngữ lập trình: C++, Python, Java, v.v.
./scripts/manage.py loaddata language_small

# Bài mẫu: A+B, v.v.
./scripts/manage.py loaddata demo

# Tạo tài khoản admin
./scripts/manage.py createsuperuser
```

### Bước 7: Khởi động tất cả services

```bash
docker compose up -d
```

### Bước 8: Kiểm tra

```bash
# Kiểm tra trạng thái containers
docker compose ps

# Phải thấy 7 container ở trạng thái "Up":
#   bkdnoj_mysql, bkdnoj_redis, bkdnoj_site, bkdnoj_celery,
#   bkdnoj_bridged, bkdnoj_wsevent, bkdnoj_nginx
# (base chỉ là build image, sẽ hiện "Exited" - đây là bình thường)

# Truy cập: http://<ip-hoac-domain>/
```

> **Xử lý lỗi thường gặp:**
> - **502 Bad Gateway**: Site container chưa khởi động xong, đợi 10-20 giây rồi refresh.
> - **Trang trắng / thiếu CSS**: Chưa chạy `./scripts/copy_static`, chạy lại bước 5.
> - **Lỗi DB connection**: MariaDB chưa sẵn sàng, kiểm tra `docker compose logs db`.

---

<a id="run-du-an-khoi-dong"></a>
## Run Dự Án (Khởi Động)

### Khởi động bình thường sau khi đã build

```bash
cd bkdnoj-docker/dmoj
docker compose up -d
```

### Dừng tất cả services

```bash
docker compose down
```

### Restart một service cụ thể

```bash
docker compose restart site      # Restart web app
docker compose restart nginx     # Restart proxy
docker compose restart bridged   # Restart judge bridge
```

### Xem logs

```bash
# Tất cả logs
docker compose logs -f

# Logs của site
docker compose logs -f site

# Logs của bridge để debug judge connection
docker compose logs -f bridged
```

### Vào shell của site container

```bash
./scripts/enter_site
# Hoặc:
docker compose exec site /bin/bash
```

### Chạy Django management command

```bash
./scripts/manage.py <command>

# Ví dụ:
./scripts/manage.py shell          # Django shell
./scripts/manage.py dbshell        # MySQL shell
./scripts/manage.py showmigrations # Kiểm tra migration
```

---

<a id="cai-dat-may-cham-judge"></a>
## Cài Đặt Máy Chấm (Judge)

### Bước 1: Tạo Judge trong Admin Panel

1. Truy cập: `http://<domain>/admin/judge/`
2. Click "Add Judge"
3. Nhập **Name**. Ví dụ: `judge01`
4. Lưu lại, sau đó ghi nhớ **ID** và **Key**

### Bước 2: Clone Judge Server Source và Copy Custom Files

```bash
cd ~
git clone https://github.com/VNOI-Admin/judge-server.git

# Copy 3 file custom (judge.py, packet.py, result.py) vào judge-server
cp ~/bkdnoj-docker/judge_update/judge.py  ~/judge-server/dmoj/
cp ~/bkdnoj-docker/judge_update/packet.py ~/judge-server/dmoj/
cp ~/bkdnoj-docker/judge_update/result.py ~/judge-server/dmoj/
```

> **Ghi chú:** 3 file trong `bkdnoj-docker/judge_update/` chứa tính năng custom như partial testcase scoring.
> Sau khi copy vào `judge-server/`, các file này sẽ được mount read-only vào Judge container ở bước 4.

### Bước 3: Tạo file config judge

Tạo file `bkdnoj-docker/dmoj/problems/judge01.yml`:
```yaml
id: 'judge01'
key: '<key-tu-admin-panel>'
problem_storage_globs:
  - /problems/*
```

### Bước 4: Khởi động Judge container

```bash
sudo docker run \
    --name judge01 \
    --network="host" \
    -v ~/bkdnoj-docker/dmoj/problems:/problems \
    -v ~/judge-server/dmoj/judge.py:/judge/dmoj/judge.py:ro \
    -v ~/judge-server/dmoj/packet.py:/judge/dmoj/packet.py:ro \
    -v ~/judge-server/dmoj/result.py:/judge/dmoj/result.py:ro \
    --cap-add=SYS_PTRACE \
    -d \
    --restart=unless-stopped \
    vnoj/judge-tiervnoj:latest \
    run -p 9999 -c /problems/judge01.yml localhost -A 0.0.0.0 -a 9111
```

> **Tham số:**
> - `-p 9999`: Port kết nối tới Bridge (phải khớp với bridge port trong docker-compose)
> - `-c /problems/judge01.yml`: File config (đường dẫn bên trong container)
> - `localhost`: IP của site server, dùng `localhost` nếu judge cùng máy với site
> - `-A 0.0.0.0`: Bind API trên mọi interface
> - `-a 9111`: API port, đổi cho mỗi judge: `9111`, `9112`, v.v.

### Bước 5: Kiểm tra Judge

```bash
# Xem logs
sudo docker logs -f judge01

# Thành công khi thấy: "Judge is ready"

# Kiểm tra trong Admin Panel
# http://<domain>/admin/judge/ -> status màu xanh
```

### Thêm Judge thứ 2 (tùy chọn)

```bash
# Tạo judge02 trong Admin Panel, lấy key
# Tạo problems/judge02.yml
# Chạy với --name judge02 và -a 9112
```

### Judge Từ Xa (Remote)

```bash
# Trên máy remote, cài sshfs:
sudo apt-get install -y sshfs

# Mount thư mục problems từ site server
sudo mkdir -p /mnt/problems
sudo sshfs -o allow_other,IdentityFile=~/.ssh/id_rsa \
    user@<site-ip>:~/bkdnoj-docker/dmoj/problems /mnt/problems

# Copy 3 file custom judge vào máy remote
scp user@<site-ip>:~/bkdnoj-docker/judge_update/{judge.py,packet.py,result.py} ~/

# Chạy judge với mount path tương ứng
sudo docker run \
    --name judge01 \
    --network="host" \
    -v /mnt/problems:/problems \
    -v ~/judge.py:/judge/dmoj/judge.py:ro \
    -v ~/packet.py:/judge/dmoj/packet.py:ro \
    -v ~/result.py:/judge/dmoj/result.py:ro \
    --cap-add=SYS_PTRACE \
    -d --restart=unless-stopped \
    vnoj/judge-tiervnoj:latest \
    run -p 9999 -c /problems/judge01.yml <site-ip> -A 0.0.0.0 -a 9111
```

---

<a id="cap-nhat-du-an"></a>
## Cập Nhật Dự Án

### Khi thay đổi source code: templates, Python, CSS, JS

```bash
cd bkdnoj-docker/dmoj

# Rebuild static files
./scripts/copy_static

# Restart site để nhận thay đổi
docker compose restart site
```

### Khi thay đổi requirements.txt, ví dụ thêm Python package

```bash
# Rebuild base image
docker compose build base

# Rebuild các image phụ thuộc
docker compose build site celery bridged

# Restart
docker compose down && docker compose up -d
```

### Khi thay đổi database schema, ví dụ Django models

```bash
./scripts/migrate
docker compose restart site
```

### Khi thay đổi Dockerfile

```bash
docker compose build
docker compose down && docker compose up -d
```

---

<a id="rebuild-codemirror-6"></a>
## Rebuild CodeMirror 6

IDE editor sử dụng CodeMirror 6, pre-built bundle tại `repo/resources/aloj/codemirror6/`.

**Bình thường không cần rebuild** vì file bundle đã được commit sẵn.

Chỉ rebuild khi cần **thêm ngôn ngữ, cập nhật phiên bản CM6, hoặc sửa autocomplete**:

```bash
# Cần Node.js >= 18
cd bkdnoj-docker/dmoj/repo/_build/codemirror6

# Cài dependencies
npm install

# Build bundle -> output tại resources/aloj/codemirror6/codemirror-ide.min.js
node build.mjs

# Sau đó chạy lại copy_static trong Docker
cd ../../..    # về lại dmoj/
./scripts/copy_static
docker compose restart site
```

**Cấu trúc file CodeMirror 6:**

```
repo/
  _build/codemirror6/           # Build tools, không cần trong production
    entry.js                    # Entry point - import CM6 modules
    build.mjs                   # esbuild script
    package.json                # Dependencies
  resources/aloj/codemirror6/   # Output, được serve bởi Django/Nginx
    codemirror-ide.min.js       # CM6 bundle (~1MB, ~346KB gzipped)
    cm6-completions.js          # Autocomplete word lists (C++/Python/Java)
```

**Sửa autocomplete, ví dụ thêm/bớt từ khóa:**
- Sửa trực tiếp file `repo/resources/aloj/codemirror6/cm6-completions.js`
- Không cần rebuild bundle
- Chạy `./scripts/copy_static && docker compose restart site`

---

## Cấu Trúc Thư Mục

```
bkdnoj-docker/
  dmoj/
    base/                # Dockerfile base image (Python 3.11, Node 18)
    site/                # Dockerfile site (uWSGI)
    celery/              # Dockerfile celery worker
    bridged/             # Dockerfile bridge daemon
    wsevent/             # Dockerfile websocket daemon
    nginx/conf.d/        # Nginx config
    config/              # Template configs (local_settings.py, uwsgi.ini, config.js)
    environment/         # Environment files (.env)
    scripts/             # Management scripts
      initialize         # Copy config files lần đầu
      migrate            # Chạy Django migrations
      copy_static        # Build CSS + collect static files
      manage.py          # Django management wrapper
      enter_site         # Shell vào site container
    repo/                # Django source code
      dmoj/              # Django settings
      judge/             # Models, views, forms
        fixtures/        # Dữ liệu khởi tạo (navbar, language, demo)
      templates/         # HTML templates
      resources/         # Static files (JS, CSS, images)
        aloj/ace/        # Ace Editor cho trang submit thường
        aloj/codemirror6/# CodeMirror 6 cho IDE
        aloj/jquery/     # jQuery
        aloj/select2/    # Select2
      _build/            # Build tools (codemirror6)
    problems/            # Judge problem data + judge config (.yml)
    media/               # User uploads
    database/            # MariaDB data (auto-generated)
    generate_testcase/   # Test case generation
    docker-compose.yml   # Docker orchestration
  judge_update/          # Custom judge files (judge.py, packet.py, result.py)
  document/              # Documentation
```

---

## Lệnh Nhanh

Tất cả lệnh chạy từ thư mục `bkdnoj-docker/dmoj/`:

| Mục đích | Lệnh |
|----------|------|
| Build lần đầu | `docker compose build` |
| Start tất cả | `docker compose up -d` |
| Stop tất cả | `docker compose down` |
| Xem trạng thái | `docker compose ps` |
| Xem logs | `docker compose logs -f [service]` |
| Migration | `./scripts/migrate` |
| Collect static | `./scripts/copy_static` |
| Django command | `./scripts/manage.py <cmd>` |
| Vào shell site | `./scripts/enter_site` |
| Restart site | `docker compose restart site` |
| Judge logs | `sudo docker logs -f judge01` |
