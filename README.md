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
| `aloj_mysql` | mariadb | 3306 (internal) | Database |
| `aloj_redis` | redis:alpine | 6379 (internal) | Cache + Celery broker |
| `aloj_site` | aloj/aloj-site | 8000 (internal) | Django web app |
| `aloj_celery` | aloj/aloj-celery | - | Background tasks |
| `aloj_bridged` | aloj/aloj-bridged | 9998, 9999 | Judge connection bridge |
| `aloj_wsevent` | aloj/aloj-wsevent | 15100-15102 (internal) | WebSocket live updates |
| `aloj_nginx` | nginx:alpine | **80** | Reverse proxy + static |

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

---

<a id="build-du-an-tu-dau"></a>
## Build Dự Án (Từ Đầu)

### Bước 1: Clone Repository

```bash
git clone --recursive <repo-url> aloj-docker
cd aloj-docker/dmoj
```

### Bước 2: Cấu hình môi trường

```bash
# Khởi tạo config
./scripts/initialize

# Tạo file environment
cp environment/mysql.env.example environment/mysql.env
cp environment/mysql-admin.env.example environment/mysql-admin.env
cp environment/site.env.example environment/site.env
```

Chỉnh sửa các file:

**`environment/mysql.env`**
```env
MYSQL_HOST=db
MYSQL_DATABASE=dmoj
MYSQL_USER=dmoj
MYSQL_PASSWORD=<mat-khau-manh>
```

**`environment/mysql-admin.env`**
```env
MYSQL_ROOT_PASSWORD=<mat-khau-root>
```

**`environment/site.env`**
```env
HOST=<ip-hoac-domain>
SITE_FULL_URL=http://<ip-hoac-domain>/
MEDIA_URL=http://<ip-hoac-domain>/
DEBUG=0
SECRET_KEY=<tao-key-ngau-nhien>
```

Tạo Secret Key:
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

**`nginx/conf.d/nginx.conf`** - đổi `server_name`:
```nginx
server_name <ip-hoac-domain>;
```

### Bước 3: Build Docker images

```bash
docker compose build
```

> Lần đầu build mất khoảng 10-15 phút do tải Python packages, Node.js, v.v.

### Bước 4: Khởi động Database + Migrate

```bash
# Khởi động DB và Redis trước
docker compose up -d db redis
sleep 10

# Khởi động Site
docker compose up -d site

# Chạy migration để tạo bảng trong database
./scripts/migrate
```

### Bước 5: Build Static Files

```bash
./scripts/copy_static
```

> Bước này sẽ:
> 1. Compile Sass thành CSS (`make_style.sh`)
> 2. `collectstatic` - thu thập tất cả static files, bao gồm CodeMirror 6, Ace, jQuery, v.v. vào `/assets/static/`
> 3. Compile i18n messages
> 4. Copy resources vào `/assets/`

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

# Tất cả 7 container phải ở trạng thái "Up"
# Truy cập: http://<ip-hoac-domain>/
```

---

<a id="run-du-an-khoi-dong"></a>
## Run Dự Án (Khởi Động)

### Khởi động bình thường sau khi đã build

```bash
cd aloj-docker/dmoj
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
cp ~/aloj-docker/judge_update/judge.py  ~/judge-server/dmoj/
cp ~/aloj-docker/judge_update/packet.py ~/judge-server/dmoj/
cp ~/aloj-docker/judge_update/result.py ~/judge-server/dmoj/
```

> **Ghi chú:** 3 file trong `aloj-docker/judge_update/` chứa các bản custom như partial testcase scoring, v.v.
> Các file này sẽ được mount read-only vào Judge container ở bước 4.

### Bước 3: Tạo file config judge

**`problems/judge01.yml`**
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
    -v /path/to/aloj-docker/dmoj/problems:/problems \
    -v /path/to/judge-server/dmoj/judge.py:/judge/dmoj/judge.py:ro \
    -v /path/to/judge-server/dmoj/packet.py:/judge/dmoj/packet.py:ro \
    -v /path/to/judge-server/dmoj/result.py:/judge/dmoj/result.py:ro \
    --cap-add=SYS_PTRACE \
    -d \
    --restart=unless-stopped \
    vnoj/judge-tiervnoj:latest \
    run -p 9999 -c /problems/judge01.yml <site-ip> -A 0.0.0.0 -a 9111
```

> **Tham số:**
> - `-p 9999`: Port kết nối tới Bridge
> - `-c /problems/judge01.yml`: File config
> - `<site-ip>`: IP của site server, dùng `localhost` nếu cùng máy
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
# Trên máy remote:
sudo apt-get install -y sshfs

# Mount thư mục problems từ site server
sudo sshfs -o allow_other,IdentityFile=~/.ssh/id_rsa \
    user@<site-ip>:/path/to/dmoj/problems /mnt/problems

# Chạy judge với -v /mnt/problems:/problems
```

---

<a id="cap-nhat-du-an"></a>
## Cập Nhật Dự Án

### Khi thay đổi source code: templates, Python, CSS, JS

```bash
cd aloj-docker/dmoj

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
cd aloj-docker/dmoj/repo/_build/codemirror6

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
aloj-docker/
  dmoj/
    base/                # Dockerfile base image
    site/                # Dockerfile site (uWSGI)
    celery/              # Dockerfile celery worker
    bridged/             # Dockerfile bridge daemon
    wsevent/             # Dockerfile websocket daemon
    nginx/conf.d/        # Nginx config
    config/              # Template configs (local_settings.py, uwsgi.ini, config.js)
    environment/         # Environment files (.env)
    scripts/             # Management scripts
      initialize         # Khởi tạo config lần đầu
      migrate            # Chạy Django migrations
      copy_static        # Build CSS + collect static files
      manage.py          # Django management wrapper
      enter_site         # Shell vào site container
    repo/                # Django source code
      dmoj/              # Django settings
      judge/             # Models, views, forms
      templates/         # HTML templates
      resources/         # Static files (JS, CSS, images)
        aloj/ace/        # Ace Editor cho trang submit thường
        aloj/codemirror6/# CodeMirror 6 cho IDE
        aloj/jquery/     # jQuery
        aloj/select2/    # Select2
      _build/            # Build tools, gitignored
    problems/            # Judge problem data + judge configs
    media/               # User uploads
    docker-compose.yml   # Docker orchestration
  document/              # Documentation
  judge_partial_testcase.patch  # Custom judge patch
```

---

## Lệnh Nhanh

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
