# ALOJ – Algorit Online Judge · AI Agent Reference

> **Base platform**: [VNOJ Docker](https://github.com/VNOI-Admin/vnoj-docker) (fork của [DMOJ](https://github.com/DMOJ/online-judge))  
> **Stack**: Django · MariaDB · Redis · Celery · Nginx · Docker Compose  
> **Ngôn ngữ UI**: Tiếng Việt (`LANGUAGE_CODE = 'vi'`, timezone `Asia/Ho_Chi_Minh`)

---

## Mục Lục

1. [Kiến Trúc Tổng Quan](#1-kiến-trúc-tổng-quan)
2. [Project Stack (Frontend)](#2-project-stack-frontend)
3. [Cấu Trúc Thư Mục](#3-cấu-trúc-thư-mục)
4. [Docker Services](#4-docker-services)
5. [Luồng Chấm Bài](#5-luồng-chấm-bài)
6. [Cấu Hình Chính](#6-cấu-hình-chính)
7. [Judge Servers](#7-judge-servers)
8. [Networking & Ports](#8-networking--ports)
9. [Frontend Architecture](#9-frontend-architecture)
10. [Build & Deploy](#10-build--deploy)
11. [Scripts Tiện Ích](#11-scripts-tiện-ích)
12. [Bài Tập (Problems)](#12-bài-tập-problems)
13. [Khởi Động & Vận Hành](#13-khởi-động--vận-hành)
14. [Past Modifications](#14-past-modifications)
15. [Known Open Issues](#15-known-open-issues)
16. [Tham Khảo](#16-tham-khảo)

---

## 1. Kiến Trúc Tổng Quan

```
User Browser
    │ HTTP/WS
    ▼
Nginx (:80)
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

**Quy trình nộp bài:**

```
Nộp bài → Site (lưu DB, status=QU)
        → Bridge (:9998) nhận request
        → Judge (:9999) biên dịch + chạy test
        → Bridge cập nhật DB (status D / result AC/WA/…)
        → wsevent broadcast WebSocket → Browser cập nhật UI
```

---

## 2. Project Stack (Frontend)

| Layer | Tech |
|-------|------|
| Backend | Django (Jinja2 templates) |
| CSS | SCSS → sass → postcss/autoprefixer → CSS |
| JS | jQuery 3.4.1, vanilla JS (no bundler) |
| Realtime | WebSocket via `wsevent` service |
| Charts | Chart.js |
| Icons | FontAwesome 4 |
| i18n | Django gettext (`_('...')`) – Vietnamese / English |

---

## 3. Cấu Trúc Thư Mục

```
aloj-docker/
├── AGENTS.md                  # File này
└── dmoj/
    ├── docker-compose.yml     # Định nghĩa toàn bộ services
    ├── base/Dockerfile        # Base image dùng chung
    ├── bridged/Dockerfile     # Bridge daemon
    ├── celery/Dockerfile      # Celery worker
    ├── site/                  # Dockerfile cho Django site
    ├── wsevent/               # WebSocket event server
    ├── config/
    │   ├── local_settings.py  # Django settings tuỳ chỉnh
    │   ├── config.js          # Cấu hình wsevent
    │   └── uwsgi.ini          # uWSGI config
    ├── environment/
    │   ├── mysql.env          # DB credentials (user)
    │   ├── mysql-admin.env    # DB credentials (root)
    │   └── site.env           # Biến môi trường cho site
    ├── nginx/conf.d/
    │   └── nginx.conf         # Nginx reverse proxy config
    ├── problems/              # Dữ liệu test + judge YML configs
    ├── database/              # MariaDB data volume (bind mount)
    ├── media/                 # File upload (submission_file, martor, pdf)
    ├── repo/                  # Source code VNOJ (git submodule)
    │   ├── resources/         # SCSS, JS, static assets
    │   │   ├── submission.scss
    │   │   ├── base.scss, style.scss, navbar.scss
    │   │   ├── vars-common.scss, vars-default.scss, vars-dark.scss
    │   │   ├── common.js
    │   │   ├── event.js
    │   │   └── libs/          # jQuery, Chart.js, Select2, etc.
    │   ├── templates/
    │   │   ├── base.html
    │   │   ├── common-content.html
    │   │   └── submission/
    │   │       ├── list.html
    │   │       ├── row.html
    │   │       ├── status.html
    │   │       ├── status-testcases.html
    │   │       ├── source.html
    │   │       └── submission-list-tabs.html
    │   ├── judge/views/submission.py
    │   ├── judge/models/submission.py
    │   ├── judge/bridge/judge_handler.py
    │   ├── judge/views/api/api_v2.py
    │   ├── judge/views/contests.py
    │   ├── judge/admin/contest.py
    │   ├── judge/contest_format/base.py
    │   ├── make_style.sh
    │   └── locale/
    └── scripts/               # CLI scripts tiện ích
        ├── initialize
        ├── migrate
        ├── copy_static
        ├── manage.py
        └── enter_site
```

**Judge Server (separate repo):**

```
judge-server/
├── dmoj/
│   ├── judge.py              # Judge orchestration (IPC, multiprocessing)
│   ├── packet.py             # TCP/SSL + zlib packet protocol
│   ├── problem.py            # Problem/test-case management
│   ├── result.py             # Result codes
│   ├── config.py             # Judge config loading
│   ├── judgeenv.py           # Environment settings
│   ├── control.py            # HTTP control server
│   ├── monitor.py            # Resource monitoring
│   ├── executors/            # Language executors (C++, Python, Java, etc.)
│   ├── graders/              # Grading strategies (standard, bridged, interactive)
│   ├── checkers/             # Output checkers
│   ├── cptbox/               # Sandbox (ptrace-based)
│   └── utils/                # Utilities
└── testsuite/                # Test cases for judge features
```

---

## 4. Docker Services

| Container | Image | Mô tả | Network |
|---|---|---|---|
| `db` (vnoj_mysql) | `mariadb` | Cơ sở dữ liệu chính | `db` |
| `redis` (vnoj_redis) | `redis:alpine` | Cache + Celery broker | `site` |
| `site` (vnoj_site) | `vnoj/vnoj-site` | Django app (uWSGI :8000) | `site`, `nginx`, `db` |
| `celery` (vnoj_celery) | `vnoj/vnoj-celery` | Celery async worker | `site`, `db` |
| `bridged` (vnoj_bridged) | `vnoj/vnoj-bridged` | Bridge daemon | `site`, `nginx`, `db` |
| `wsevent` (vnoj_wsevent) | `vnoj/vnoj-wsevent` | WebSocket event server | `site`, `nginx` |
| `nginx` (vnoj_nginx) | `nginx:alpine` | Reverse proxy (port **80**) | `nginx` |

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
| `./repo/` | Source code VNOJ (mount → `/site/`) |

### Docker Networks

| Network | Services |
|---|---|
| `db` | db, site, celery, bridged |
| `site` | site, celery, redis, bridged, wsevent |
| `nginx` | nginx, site, bridged, wsevent |

---

## 5. Luồng Chấm Bài

### Protocol

- **Transport**: TCP Socket + SSL + Zlib compression
- **Format**: JSON → `zlib.compress` → `[4-byte length header (struct '!I')][payload]`
- `PacketManager` class in `judge-server/dmoj/packet.py` handles serialization

### IPC Messages (Judge Internal)

```
HELLO, BYE, COMPILE_ERROR, COMPILE_MESSAGE,
RESULT, BATCH_BEGIN, BATCH_END,
GRADING_BEGIN, GRADING_END, GRADING_ABORTED,
UNHANDLED_EXCEPTION, REQUEST_ABORT
```

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

## 6. Cấu Hình Chính

### `environment/site.env`

```env
HOST=localhost
SITE_FULL_URL=http://localhost/
MEDIA_URL=http://localhost/
DEBUG=0
SECRET_KEY='algorit'
EVENT_DAEMON_POST=ws://wsevent:15101/
REDIS_CACHING_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1
BRIDGED_HOST=bridged
```

### `config/local_settings.py` (key settings)

```python
SITE_NAME        = 'Algorit Online Judge'
SITE_LONG_NAME   = 'ALOJ: Algorit Online Judge'
SITE_ADMIN_EMAIL = 'aloj@onlinejudge.com'
LANGUAGE_CODE    = 'vi'
DEFAULT_USER_TIME_ZONE = 'Asia/Ho_Chi_Minh'

# Database: MySQL (MariaDB) at host 'db', database 'dmoj', charset utf8mb4
# Cache: Redis django-redis at redis:6379/0
# Session: cached_db, TTL 4 days, save every request

BRIDGED_JUDGE_ADDRESS  = [('bridged', 9999)]
BRIDGED_DJANGO_ADDRESS = [('bridged', 9998)]

EVENT_DAEMON_USE  = True
EVENT_DAEMON_POST = 'ws://wsevent:15101/'
EVENT_DAEMON_GET  = '/event/'

CELERY_BROKER_URL = 'redis://redis:6379/1'

STATIC_ROOT = '/assets/static/'
MEDIA_ROOT  = '/media/'
DMOJ_PROBLEM_DATA_ROOT = '/problems/'

# Email: SMTP Gmail (smtp.gmail.com:587, TLS)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Features
ENABLE_FTS = False  # Full-text search disabled
# CSS/JS compressor enabled
```

### `config/config.js` (wsevent)

```javascript
{
    get_host: 'wsevent',   get_port: 15100,
    post_host: 'wsevent',  post_port: 15101,
    http_host: 'wsevent',  http_port: 15102,
    long_poll_timeout: 29000,
}
```

### `nginx/conf.d/nginx.conf` (key routes)

| Location | Proxy đến |
|---|---|
| `/` (default) | `uwsgi site:8000` |
| `/static` | `/assets/static/` (gzip, max cache) |
| `/martor` | `/media/martor/` |
| `/pdf` | `/media/pdf/` |
| `/submission_file` | `/media/submission_file/` |
| `/event/` | `ws://wsevent:15100/` (WebSocket upgrade) |
| `/channels/` | `http://wsevent:15102/` |
| `/502.html`, `/logo.png`, `/robots.txt` | Static files |

Client max body size: 64M.

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

| Judge | API Port | Config |
|---|---|---|
| judge01 | 9111 | `problems/judge01.yml` |
| judge02 | 9112 | `problems/judge02.yml` |
| judge03 | 9113 | `problems/judge03.yml` |
| judge04 | 9114 | `problems/judge04.yml` |
| ultra_speed_judge_01 | — | `problems/ultra_speed_judge_01.yml` |

**Judge config structure:**
```yaml
id: 'judge01'
key: '<auth_key>'
problem_storage_globs:
  - /problems/*
```

---

## 8. Networking & Ports

| Port (host) | Service | Mô tả |
|---|---|---|
| `80` | Nginx | HTTP web interface |
| `9998` | Bridged | Site → Bridge communication |
| `9999` | Bridged | Bridge → Judge communication |
| `15100` | wsevent | WebSocket proxy (qua Nginx `/event/`) |
| `15101` | wsevent | Internal post endpoint |
| `15102` | wsevent | Channels endpoint (`/channels/`) |
| `9111–9114` | Judge API | Management API từng judge |

> **Note**: DB (3306) và Redis (6379) ports chỉ expose internal, không ra host.

---

## 9. Frontend Architecture

### Template Inheritance

```
base.html → common-content.html → submission/list.html
                                       ↳ includes submission/row.html (per row)
```

### Submission List Page (list.html)

- **Blocks**: `js_media` (inline JS + WebSocket), `body` (toolbar + table), `media` (extra CSS)
- **Toolbar**: Filter dropdown (status/language/org selects) + Statistics dropdown (Chart.js pie)
- **Table**: `<table class="submissions-table">` with `<tbody id="submissions-table">`
- **WebSocket**: `load_dynamic_update()` listens to `submissions` channel, calls `/api/submission_single_query?id=X`

### Row Columns (row.html)

| Column | Class | Content |
|--------|-------|---------|
| Time | `.col-time` | `relative_time()` + contest icon |
| Username | `.col-user` | `link_user()` |
| Problem | `.col-problem` | Link (only if `show_problem`) |
| Language | `.col-lang` | `short_display_name` |
| State | `.col-state` | `<span class="case-{result_class}">` bold colored text |
| Result | `.col-result` | Result bar + sub-actions |
| Exec time | `.col-exectime` | milliseconds or `---` |
| Memory | `.col-memory` | KB formatted or `---` |

### Result Bar States

| State | CSS class | Visual |
|-------|-----------|--------|
| Graded | `.result-bar-{AC,WA,TLE,MLE,...}` | Colored bar, width = score %, text "X / Y" |
| Error (IE/CE/AB) | `.result-bar-error` | Full-width gray bar, text = short status |
| Grading | `.result-bar-grading` | Full-width #6C6DFF pulsing, spinner + "Case #N" |

### WebSocket Update Logic

```
event_dispatcher.on('submissions', callback)
  ├── 'update-submission' → AJAX fetch row HTML, smart-update:
  │     If currently grading AND new data also grading:
  │       → Update only .grading-case-text + .col-state (preserves CSS animation)
  │     Else:
  │       → Replace entire row.html(data)
  └── 'done-submission' → force full row replace + update stats chart
```

Throttle: `doing_ajax` flag + 1s cooldown between non-forced updates.

### Sub-actions (below result bar)

Icons: eye (view) → file-code (source) / download → refresh (rejudge, admin only) → cog (admin, superuser only). Wrapped in `.sub-actions` flex container.

### CSS Architecture (submission.scss)

~470+ lines. Key sections:

| Section | What it styles |
|---------|----------------|
| Toolbar | `.submission-toolbar`, `.toolbar-btn` (#2196F3 blue), `.dropdown-box` |
| Table | `.submissions-table` (headers 1.05em, hover rows) |
| Result bar | `.result-bar` (#111 bg, 22px, rounded 8px), `.result-bar-fill`, `.result-text` |
| Bar colors | `.result-bar-AC` (green), `-WA` (red), `-TLE/-MLE` (gray), `-RTE/-OLE/-IR` (orange) |
| Grading | `.result-bar-grading` (#6C6DFF, `grading-pulse` animation) |
| Sub-actions | `.sub-actions` (flex, space-evenly, 1.0em icons) |
| State column | `.case-*` classes (`.case-AC` green, `.case-WA` red, etc.) |
| Responsive | `@media (max-width: 700px)` |

### Submission Detail Page (status.html / status-testcases.html)

- Card-based UI with modal popups for test case details
- `.test-cases-grid` CSS Grid: `repeat(auto-fill, minmax(220px, 1fr))`
- `.test-case-card` with hover animation (translateY -4px)
- `.case-modal` with fixed positioning, z-index 9999, ESC key close
- `.batch-header` solid pink #cb3158
- `.submission-summary` light orange background

**Status color scheme:**

| Status | Border | Gradient |
|--------|--------|----------|
| AC | #2ecc71 (green) | white → #f0fff4 |
| _AC | #BBCC00 (yellow) | white → #fffef0 |
| WA | #e74c3c (red) | white → #fff5f5 |
| TLE, SC | #888 (gray) | white → #f5f5f5 |
| MLE, OLE, RTE, IR | #f39c12 (orange) | white → #fff8f0 |
| CE, IE, AB | #aaa (light gray) | white → #f7f7f7 |
| None (QU/P/G) | #6C6DFF (purple) | white → #f3f3ff |

**SCSS variables**: `$color_primary10`, `$color_primary25`, `$color_primary50`, `$color_primary75`, `$color_primary100` (defined in `vars-common.scss` / `vars-default.scss`).

---

## 10. Build & Deploy

```bash
cd /home/algoritonlinejudge/aloj-docker/dmoj && \
docker compose exec site bash -c "cd /site && bash make_style.sh 2>&1 | tail -3 && python manage.py collectstatic --noinput 2>&1 | tail -2" && \
docker compose restart site 2>&1 | tail -2
```

**Build pipeline**: `vars-{default,dark}.scss` → copied as `vars.scss` → `sass` compiles all `.scss` → `postcss + autoprefixer` → output to `resources/` (light) and `resources/dark/` (dark).

---

## 11. Scripts Tiện Ích

Tất cả trong `dmoj/scripts/`:

| Script | Mô tả |
|---|---|
| `./scripts/initialize` | Khởi tạo cấu hình lần đầu |
| `./scripts/migrate` | Chạy DB migrations (`manage.py migrate`) |
| `./scripts/copy_static` | Thu thập static files (`collectstatic`) |
| `./scripts/manage.py` | Django management CLI |
| `./scripts/enter_site` | Shell vào container site |

---

## 12. Bài Tập (Problems)

Dữ liệu test lưu tại `dmoj/problems/<problem_code>/`:

| Prefix | Mô tả |
|---|---|
| `prob_NNN` | Bài tập chung (001–021+) |
| `prob_icpc_NNN` | Bài ICPC (4 bài) |
| `icpc_prob_NNN` | Bài ICPC series (005–014) |
| `ksnl4_` → `ksnl12_` | Khoa học nhanh lẹ các khối 4–12 |
| `cpacademy_…` | CP Academy contests & problems (19 bài) |
| `hsg_thpt_qt_2025_…` | HSG THPT Quốc Tế 2025 |
| `lgcj2025_…` | LGCJ 2025 |
| `hpny_2026` | Happy New Year 2026 |
| `special_prob_01` | Bài đặc biệt |

---

## 13. Khởi Động & Vận Hành

### Lần đầu setup

```bash
cd aloj-docker/dmoj

# 1. Tạo env files
cp environment/mysql.env.example     environment/mysql.env
cp environment/mysql-admin.env.example environment/mysql-admin.env
cp environment/site.env.example      environment/site.env
# → Chỉnh sửa các file trên

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

---

## 14. Past Modifications

### Submission list page (list.html + submission.scss + row.html)
1. **Toolbar buttons** – `.toolbar-btn` with blue bg (#2196F3), dropdown toggle JS
2. **Table headers** – `font-size: 1.05em`, `font-weight: 600`
3. **State column** – Added `col-state` before `col-result`, uses `.case-{result_class}`
4. **Result bar** – Black (#111) background, 8px rounded, centered white text
5. **Result bar colors** – Gradient fills per status (AC=green, WA=red, TLE/MLE=gray, RTE/OLE=orange)
6. **Grading bar** – #6C6DFF background, `grading-pulse` animation, spinner + "Case #N"
7. **Vietnamese i18n** – Language-independent result bar rendering
8. **State colors** – Reuses existing `.case-*` classes
9. **Sub-actions** – `space-evenly` layout, 1.0em font
10. **WebSocket smart update** – Grading animation preserved when case # changes
11. **WS disconnection banner** – `.ws-closed` yellow bg (#7d5a00 text)
12. **Performance** – `$temp` DOM parse deferred to grading-only path

### Submission detail page (status.html / status-testcases.html)
- Table-based → card-based UI with modal popups
- CSS Grid test cases, hover animations, ESC key modal close
- Batch headers pink (#cb3158), summary orange (#ffe6bb)

### Partial Testcase Scoring
- Replaced `partial`/`short_circuit` checkboxes with 3-option dropdown (`short_circuit`, `partial_batch`, `partial_testcase`)
- **Normalization rule**: `coeff = case.points if case.points <= 1 else (case.points / case.total)`
- **Batch formula** (partial_testcase): `batch_score = (sum(coeff) / testcase_count) * batch_points`
- Applied in both `judge_handler.py` (backend) and `submission.py` → `make_batch()` (UI)
- Per-testcase point display: batched shows `(coeff/1)`, non-batched shows `(points/total)`

### Contest Format Change Auto-Rescore (Apr 2026)
- Added auto-rescore trigger to `EditContest.post()` in `judge/views/contests.py`
- Mirrors Django Admin behavior: format field changes → `rescore_contest.s(contest.key).delay()` via Celery

### Penalty Time Format (Apr 2026 — staged, pending commit)
- New `penalty_time_format` field on `Contest` model: `'hh:mm:ss'` (default) or `'mm'` (minutes only)
- `BaseContestFormat.format_time(seconds)` method added
- All contest formats (`atcoder`, `default`, `ecoo`, `icpc`, `legacy_ioi`, `vnoj`) use `self.format_time()`
- Migration: `0224_contest_penalty_time_format.py`
- Contest ranking CSS tweaks in `media-css.html`

### Operational Notes
- If batch points inconsistent → check `judge_problem.scoring_mode` = `partial_testcase`
- Changing scoring mode doesn't rewrite old `submission.points` (needs rejudge)
- DB sanity query: `SELECT case, batch, status, points, total FROM judge_submissiontestcase WHERE submission_id = ? ORDER BY case;`

---

## 15. Known Open Issues

- WebSocket realtime on paginated pages (page 2+) for `/submissions/`, `/contest/.../submissions/`
- Organization submissions pages have no realtime at all

---

## 16. Tham Khảo

| Link | Mô tả |
|---|---|
| https://github.com/VNOI-Admin/vnoj-docker | Repo gốc VNOJ Docker |
| https://github.com/VNOI-Admin/judge-server | Judge server source |
| https://docs.dmoj.ca/ | Tài liệu DMOJ |
| https://docs.djangoproject.com/ | Django docs |
| https://docs.docker.com/ | Docker docs |
