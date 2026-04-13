# ALOJ – Algorit Online Judge · Project Overview

> **Base platform**: [VNOJ Docker](https://github.com/VNOI-Admin/vnoj-docker) (fork của [DMOJ](https://github.com/DMOJ/online-judge))  
> **Stack**: Django · MariaDB · Redis · Celery · Nginx · Docker Compose  
> **Ngôn ngữ UI**: Tiếng Việt (`LANGUAGE_CODE = 'vi'`, timezone `Asia/Ho_Chi_Minh`)

---

## Mục Lục

1. [Kiến Trúc Tổng Quan](#1-kiến-trúc-tổng-quan)
2. [Cấu Trúc Thư Mục](#2-cấu-trúc-thư-mục)
3. [Docker Services](#3-docker-services)
4. [Luồng Chấm Bài](#4-luồng-chấm-bài)
5. [Cấu Hình Chính](#5-cấu-hình-chính)
6. [Bài Tập (Problems)](#6-bài-tập-problems)
7. [Judge Servers](#7-judge-servers)
8. [Networking & Ports](#8-networking--ports)
9. [Scripts Tiện Ích](#9-scripts-tiện-ích)
10. [Khởi Động & Vận Hành](#10-khởi-động--vận-hành)

---

## 1. Kiến Trúc Tổng Quan

```
User Browser
    │ HTTP/WS
    ▼
Nginx (:8080)
    │ uWSGI / reverse-proxy
    ├──▶ Site (Django uWSGI :8000)
    │        │
    │        ├── DB (MariaDB)
    │        ├── Redis (cache + Celery broker)
    │        ├── Celery (async tasks)
    │        └── WebSocket Event Daemon (wsevent :15101)
    │
    └── wsevent (:15100/:15102) ◀── Bridge (:9998)
                                         │
                                         ▼
                                  Judge Server(s) (:9999)
```

**Quy trình nộp bài (tóm tắt):**

```
Nộp bài → Site (lưu DB, status=QU)
        → Bridge (:9998) nhận request
        → Judge (:9999) biên dịch + chạy test
        → Bridge cập nhật DB (status D / result AC/WA/…)
        → wsevent broadcast WebSocket → Browser cập nhật UI
```

---

## 2. Cấu Trúc Thư Mục

```
aloj-docker/
├── README.md                  # Hướng dẫn đầy đủ (tiếng Việt)
├── agents.md                  # File này
└── dmoj/
    ├── docker-compose.yml     # Định nghĩa toàn bộ services
    ├── base/Dockerfile        # Base image dùng chung
    ├── bridged/Dockerfile     # Bridge daemon
    ├── celery/Dockerfile      # Celery worker
    ├── site/                  # Dockerfile cho Django site
    ├── wsevent/               # WebSocket event server
    ├── config/
    │   ├── local_settings.py  # Django settings tuỳ chỉnh
    │   ├── config.js          # Cấu hình JS phía frontend
    │   └── uwsgi.ini          # uWSGI config
    ├── environment/
    │   ├── mysql.env          # DB credentials (user)
    │   ├── mysql-admin.env    # DB credentials (root)
    │   └── site.env           # Biến môi trường cho site
    ├── nginx/conf.d/
    │   └── nginx.conf         # Nginx reverse proxy config
    ├── problems/              # Dữ liệu test của từng bài + judge YML
    ├── database/              # MariaDB data volume (mount)
    ├── media/                 # File upload (submission, martor)
    ├── repo/                  # Source code VNOJ (git submodule)
    └── scripts/               # CLI scripts tiện ích
        ├── initialize
        ├── migrate
        ├── copy_static
        ├── manage.py
        └── enter_site
```

---

## 3. Docker Services

| Container | Image | Mô tả | Network |
|---|---|---|---|
| `vnoj_mysql` | `mariadb` | Cơ sở dữ liệu chính | `db` |
| `vnoj_redis` | `redis:alpine` | Cache + Celery broker | `site` |
| `vnoj_site` | `vnoj/vnoj-site` | Django app (uWSGI :8000) | `site`, `nginx`, `db` |
| `vnoj_celery` | `vnoj/vnoj-celery` | Celery async worker | `site`, `db` |
| `vnoj_bridged` | `vnoj/vnoj-bridged` | Bridge daemon | `site`, `nginx`, `db` |
| `vnoj_wsevent` | `vnoj/vnoj-wsevent` | WebSocket event server | `site`, `nginx` |
| `vnoj_nginx` | `nginx:alpine` | Reverse proxy (port **8080**) | `nginx` |

### Volumes Docker

| Volume | Dùng cho |
|---|---|
| `assets` | Static files (CSS/JS/fonts) |
| `userdatacache` | Cache download dữ liệu user |
| `contestdatacache` | Cache download dữ liệu contest |
| `cache` | Compressed static files |
| `./database/` | MariaDB data (bind mount) |
| `./media/` | File media upload |
| `./problems/` | Test data bài tập |
| `./repo/` | Source code VNOJ |

---

## 4. Luồng Chấm Bài

### Protocol

- **Transport**: TCP Socket + Zlib compression
- **Format**: JSON → `zlib.compress` → `[4-byte length header][payload]`

### Status Codes

| Code | Ý nghĩa |
|---|---|
| `QU` | Queued – đang đợi |
| `P` | Processing |
| `G` | Grading – đang chấm |
| `D` | Done – hoàn tất |

### Result Codes

| Code | Ý nghĩa |
|---|---|
| `AC` | Accepted |
| `WA` | Wrong Answer |
| `TLE` | Time Limit Exceeded |
| `MLE` | Memory Limit Exceeded |
| `RTE` | Runtime Error |
| `CE` | Compile Error |
| `IE` | Internal Error |
| `OLE` | Output Limit Exceeded |

### Packet Types (Judge → Bridge)

```
submission-acknowledged → grading-begin → test-case-status (×N) → grading-end
                                        ↘ compile-error
```

---

## 5. Cấu Hình Chính

### `environment/site.env` (các biến quan trọng)

```env
HOST=<IP hoặc domain>
SITE_FULL_URL=http://<host>/
MEDIA_URL=http://<host>/
DEBUG=0
SECRET_KEY=<random secret>
EVENT_DAEMON_POST=ws://wsevent:15101/
REDIS_CACHING_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
BRIDGED_HOST=bridged
```

### `config/local_settings.py` (key settings)

```python
SITE_NAME        = 'Algorit Online Judge'
SITE_LONG_NAME   = 'ALOJ: Algorit Online Judge'
LANGUAGE_CODE    = 'vi'
DEFAULT_USER_TIME_ZONE = 'Asia/Ho_Chi_Minh'

# Database: MySQL (MariaDB)
# Cache: Redis (django-redis)
# Session: cached_db, TTL 4 ngày

BRIDGED_JUDGE_ADDRESS  = [(bridged_host, 9999)]
BRIDGED_DJANGO_ADDRESS = [(bridged_host, 9998)]

EVENT_DAEMON_USE  = True
EVENT_DAEMON_POST = 'ws://wsevent:15101/'
EVENT_DAEMON_GET  = '/event/'

CELERY_BROKER_URL = 'redis://redis:6379/1'

# Email: SMTP Gmail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST    = 'smtp.gmail.com'
EMAIL_PORT    = 587
```

### `nginx/conf.d/nginx.conf` (key routes)

| Location | Proxy đến |
|---|---|
| `/` (default) | `uwsgi site:8000` |
| `/static` | `/assets/static/` |
| `/media/…` | bind-mount `/media/` |
| `/event/` | `ws://wsevent:15100/` |
| `/channels/` | `http://wsevent:15102/` |

---

## 6. Bài Tập (Problems)

Dữ liệu test lưu tại `dmoj/problems/<problem_code>/`, gồm các nhóm:

| Prefix | Mô tả |
|---|---|
| `prob_NNN` | Bài tập chung (001–021+) |
| `prob_icpc_NNN` | Bài ICPC |
| `icpc_prob_NNN` | Bài ICPC (series 005–014) |
| `ksnl4_` → `ksnl11_` | Khoa học nhanh lẹ các khối 4–11 |
| `cpacademy_…` | CP Academy contests & problems |
| `hsg_thpt_qt_2025_…` | HSG THPT Quốc Tế 2025 |
| `hpny_2026` | Happy New Year 2026 |
| `special_prob_01` | Bài đặc biệt |

**Judge config files**: `problems/judge01.yml` → `judge04.yml`

```yaml
# Ví dụ judge01.yml
id: 'judge01'
key: '<auth_key>'
problem_storage_globs:
  - /problems/*
```

---

## 7. Judge Servers

### Tiers Docker Image

| Tier | Ngôn ngữ hỗ trợ | Kích thước |
|---|---|---|
| `judge-tier1` | C/C++, Python, Java, Pascal | ~2 GB |
| `judge-tier2` | + Ruby, Go, PHP, Perl, Haskell | ~5 GB |
| `judge-tier3` | Đầy đủ | ~10 GB |
| `judge-tiervnoj` | Tuỳ chỉnh VNOJ | — |

### Chạy Judge Container

```bash
docker run --name judge01 \
  --network="host" \
  -v /path/to/problems:/problems \
  --cap-add=SYS_PTRACE \
  -d --restart=always \
  vnoj/judge-tier1:latest \
  run -p 9999 -c /problems/judge01.yml <SITE_IP> \
  -A 0.0.0.0 -a 9111
```

| Tham số | Ý nghĩa |
|---|---|
| `-p 9999` | Port kết nối Bridge |
| `-c /problems/judgeXX.yml` | File config |
| `<SITE_IP>` | IP máy chủ site |
| `-A 0.0.0.0 -a 91XX` | API management port |

### Judge hiện tại

| Judge | API Port |
|---|---|
| judge01 | 9111 |
| judge02 | 9112 |
| judge03 | 9113 |
| judge04 | 9114 |

---

## 8. Networking & Ports

| Port (host) | Service | Mô tả |
|---|---|---|
| `8080` | Nginx | HTTP web interface |
| `9998` | Bridged | Site → Bridge communication |
| `9999` | Bridged | Bridge → Judge communication |
| `15100` | wsevent | WebSocket proxy (qua Nginx `/event/`) |
| `15101` | wsevent | Internal post endpoint |
| `15102` | wsevent | Channels endpoint (`/channels/`) |
| `9111–9114` | Judge API | Management API từng judge |

### Docker Networks

| Network | Services |
|---|---|
| `db` | mysql, site, celery, bridged |
| `site` | site, celery, redis, bridged, wsevent |
| `nginx` | nginx, site, bridged, wsevent |

---

## 9. Scripts Tiện Ích

Tất cả trong `dmoj/scripts/`:

| Script | Tương đương | Mô tả |
|---|---|---|
| `./scripts/initialize` | — | Khởi tạo cấu hình lần đầu |
| `./scripts/migrate` | `manage.py migrate` | Chạy DB migrations |
| `./scripts/copy_static` | `collectstatic` | Thu thập static files |
| `./scripts/manage.py` | `python manage.py` | Django management CLI |
| `./scripts/enter_site` | `docker exec -it site bash` | Shell vào container site |

---

## 10. Khởi Động & Vận Hành

### Lần đầu setup

```bash
cd aloj-docker/dmoj

# 1. Tạo env files
cp environment/mysql.env.example     environment/mysql.env
cp environment/mysql-admin.env.example environment/mysql-admin.env
cp environment/site.env.example      environment/site.env
# → Chỉnh sửa các file trên với thông tin thực tế

# 2. Build images
docker compose build

# 3. Khởi động DB
docker compose up -d db redis
sleep 10

# 4. Migrate & static
docker compose up -d site
./scripts/migrate
./scripts/copy_static

# 5. Load dữ liệu mẫu + tạo admin
./scripts/manage.py loaddata navbar language_small demo
./scripts/manage.py createsuperuser

# 6. Chạy toàn bộ
docker compose up -d
```

### Hằng ngày

```bash
docker compose up -d          # Khởi động
docker compose down           # Dừng
docker compose ps             # Kiểm tra status
docker compose logs -f site   # Xem logs
docker compose logs -f bridged
docker logs -f judge01
```

### Backup

```bash
# Database
docker exec vnoj_mysql mysqldump -uroot -p$MYSQL_ROOT_PASSWORD dmoj > backup.sql

# Problems
tar -czf problems_backup.tar.gz problems/
```

### Dọn dẹp Docker

```bash
docker stop $(docker ps -aq)
docker rm -f $(docker ps -aq)
docker system prune -a --volumes  # ⚠️ Xoá toàn bộ
```

---

## Tham Khảo

| Link | Mô tả |
|---|---|
| https://github.com/VNOI-Admin/vnoj-docker | Repo gốc VNOJ Docker |
| https://github.com/VNOI-Admin/judge-server | Judge server source |
| https://docs.dmoj.ca/ | Tài liệu DMOJ |
| https://docs.djangoproject.com/ | Django docs |
| https://docs.docker.com/ | Docker docs |
