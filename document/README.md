# ALOJ - Algorit Online Judge

## Muc Luc

1. [Kien Truc He Thong](#kien-truc-he-thong)
2. [Yeu Cau He Thong](#yeu-cau-he-thong)
3. [Build Du An (Tu Dau)](#build-du-an-tu-dau)
4. [Run Du An (Khoi Dong)](#run-du-an-khoi-dong)
5. [Cai Dat May Cham (Judge)](#cai-dat-may-cham-judge)
6. [Cap Nhat Du An](#cap-nhat-du-an)
7. [Rebuild CodeMirror 6 (Chi khi can)](#rebuild-codemirror-6)

---

## Kien Truc He Thong

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

| Container | Image | Port | Chuc nang |
|-----------|-------|------|-----------|
| `aloj_mysql` | mariadb | 3306 (internal) | Database |
| `aloj_redis` | redis:alpine | 6379 (internal) | Cache + Celery broker |
| `aloj_site` | aloj/aloj-site | 8000 (internal) | Django web app |
| `aloj_celery` | aloj/aloj-celery | - | Background tasks |
| `aloj_bridged` | aloj/aloj-bridged | 9998, 9999 | Judge connection bridge |
| `aloj_wsevent` | aloj/aloj-wsevent | 15100-15102 (internal) | WebSocket live updates |
| `aloj_nginx` | nginx:alpine | **80** | Reverse proxy + static |

**Luong cham bai:**
```
User Submit -> Site -> Bridge (:9998) -> Judge (:9999) -> Ket qua -> WebSocket -> Browser
```

---

## Yeu Cau He Thong

| Thanh phan | Toi thieu | Khuyen nghi |
|------------|-----------|-------------|
| OS | Ubuntu 20.04 LTS | Ubuntu 22.04+ |
| CPU | 2 Cores | 4+ Cores |
| RAM | 4 GB | 8 GB |
| Disk | 60 GB SSD | 100 GB SSD |
| Software | Docker, Docker Compose | - |

### Cai Docker

```bash
# Cap nhat he thong
sudo apt-get update && sudo apt-get upgrade -y

# Cai Docker
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

# Cho phep chay Docker khong can sudo
sudo usermod -aG docker $USER
newgrp docker

# Kiem tra
docker --version
docker compose version
```

---

## Build Du An (Tu Dau)

### Buoc 1: Clone Repository

```bash
git clone --recursive <repo-url> aloj-docker
cd aloj-docker/dmoj
```

### Buoc 2: Cau hinh moi truong

```bash
# Khoi tao config
./scripts/initialize

# Tao file environment
cp environment/mysql.env.example environment/mysql.env
cp environment/mysql-admin.env.example environment/mysql-admin.env
cp environment/site.env.example environment/site.env
```

Chinh sua cac file:

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

Tao Secret Key:
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

**`nginx/conf.d/nginx.conf`** - doi `server_name`:
```nginx
server_name <ip-hoac-domain>;
```

### Buoc 3: Build Docker images

```bash
docker compose build
```

> Lan dau build mat khoang 10-15 phut (tai Python packages, Node.js, etc.)

### Buoc 4: Khoi dong Database + Migrate

```bash
# Khoi dong DB va Redis truoc
docker compose up -d db redis
sleep 10

# Khoi dong Site
docker compose up -d site

# Chay migration (tao bang trong database)
./scripts/migrate
```

### Buoc 5: Build Static Files

```bash
./scripts/copy_static
```

> Buoc nay se:
> 1. Compile Sass thanh CSS (`make_style.sh`)
> 2. `collectstatic` - thu thap tat ca static files (bao gom CodeMirror 6, Ace, jQuery, etc.) vao `/assets/static/`
> 3. Compile i18n messages
> 4. Copy resources vao `/assets/`

### Buoc 6: Load du lieu khoi tao

```bash
# Navbar menu
./scripts/manage.py loaddata navbar

# Ngon ngu lap trinh (C++, Python, Java, etc.)
./scripts/manage.py loaddata language_small

# Bai mau (A+B, etc.)
./scripts/manage.py loaddata demo

# Tao tai khoan admin
./scripts/manage.py createsuperuser
```

### Buoc 7: Khoi dong tat ca services

```bash
docker compose up -d
```

### Buoc 8: Kiem tra

```bash
# Kiem tra trang thai containers
docker compose ps

# Tat ca 7 container phai la "Up"
# Truy cap: http://<ip-hoac-domain>/
```

---

## Run Du An (Khoi Dong)

### Khoi dong binh thuong (sau khi da build)

```bash
cd aloj-docker/dmoj
docker compose up -d
```

### Dung tat ca services

```bash
docker compose down
```

### Restart mot service cu the

```bash
docker compose restart site      # Restart web app
docker compose restart nginx     # Restart proxy
docker compose restart bridged   # Restart judge bridge
```

### Xem logs

```bash
# Tat ca logs
docker compose logs -f

# Logs cua site
docker compose logs -f site

# Logs cua bridge (de bug judge connection)
docker compose logs -f bridged
```

### Vao shell cua site container

```bash
./scripts/enter_site
# Hoac:
docker compose exec site /bin/bash
```

### Chay Django management command

```bash
./scripts/manage.py <command>

# Vi du:
./scripts/manage.py shell          # Django shell
./scripts/manage.py dbshell        # MySQL shell
./scripts/manage.py showmigrations # Kiem tra migration
```

---

## Cai Dat May Cham (Judge)

### Buoc 1: Tao Judge trong Admin Panel

1. Truy cap: `http://<domain>/admin/judge/`
2. Click "Add Judge"
3. Nhap **Name** (vd: `judge01`)
4. Luu lai -> ghi nho **ID** va **Key**

### Buoc 2: Clone Judge Server Source va Copy Custom Files

```bash
cd ~
git clone https://github.com/VNOI-Admin/judge-server.git

# Copy 3 file custom (judge.py, packet.py, result.py) vao judge-server
cp ~/aloj-docker/judge_update/judge.py  ~/judge-server/dmoj/
cp ~/aloj-docker/judge_update/packet.py ~/judge-server/dmoj/
cp ~/aloj-docker/judge_update/result.py ~/judge-server/dmoj/
```

> **Ghi chu:** 3 file trong `aloj-docker/judge_update/` chua cac ban custom (partial_testcase scoring, etc.).
> Cac file nay se duoc mount read-only vao Judge container o buoc 4.

### Buoc 3: Tao file config judge

**`problems/judge01.yml`**
```yaml
id: 'judge01'
key: '<key-tu-admin-panel>'
problem_storage_globs:
  - /problems/*
```

### Buoc 4: Khoi dong Judge container

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

> **Tham so:**
> - `-p 9999`: Port ket noi toi Bridge
> - `-c /problems/judge01.yml`: File config
> - `<site-ip>`: IP cua site server (`localhost` neu cung may)
> - `-a 9111`: API port (doi cho moi judge: 9111, 9112, ...)

### Buoc 5: Kiem tra Judge

```bash
# Xem logs
sudo docker logs -f judge01

# Thanh cong khi thay: "Judge is ready"

# Kiem tra trong Admin Panel
# http://<domain>/admin/judge/ -> status mau xanh
```

### Them Judge thu 2 (tuy chon)

```bash
# Tao judge02 trong Admin Panel, lay key
# Tao problems/judge02.yml
# Chay voi --name judge02 va -a 9112
```

### Judge Tu Xa (Remote)

```bash
# Tren may remote:
sudo apt-get install -y sshfs

# Mount thu muc problems tu site server
sudo sshfs -o allow_other,IdentityFile=~/.ssh/id_rsa \
    user@<site-ip>:/path/to/dmoj/problems /mnt/problems

# Chay judge voi -v /mnt/problems:/problems
```

---

## Cap Nhat Du An

### Khi thay doi source code (templates, Python, CSS, JS)

```bash
cd aloj-docker/dmoj

# Rebuild static files
./scripts/copy_static

# Restart site de nhan thay doi
docker compose restart site
```

### Khi thay doi requirements.txt (them Python package)

```bash
# Rebuild base image
docker compose build base

# Rebuild cac image phu thuoc
docker compose build site celery bridged

# Restart
docker compose down && docker compose up -d
```

### Khi thay doi database schema (Django models)

```bash
./scripts/migrate
docker compose restart site
```

### Khi thay doi Dockerfile

```bash
docker compose build
docker compose down && docker compose up -d
```

---

## Rebuild CodeMirror 6

IDE editor su dung CodeMirror 6 (pre-built bundle tai `repo/resources/aloj/codemirror6/`).
**Binh thuong khong can rebuild** - file bundle da duoc commit san.

Chi rebuild khi can **them ngon ngu, cap nhat phien ban CM6, hoac sua autocomplete**:

```bash
# Can Node.js >= 18
cd aloj-docker/dmoj/repo/_build/codemirror6

# Cai dependencies
npm install

# Build bundle -> output tai resources/aloj/codemirror6/codemirror-ide.min.js
node build.mjs

# Sau do chay lai copy_static trong Docker
cd ../../..    # ve lai dmoj/
./scripts/copy_static
docker compose restart site
```

**Cau truc file CodeMirror 6:**

```
repo/
  _build/codemirror6/           # Build tools (khong can trong production)
    entry.js                    # Entry point - import CM6 modules
    build.mjs                   # esbuild script
    package.json                # Dependencies
  resources/aloj/codemirror6/   # Output (duoc serve boi Django/Nginx)
    codemirror-ide.min.js       # CM6 bundle (~1MB, ~346KB gzipped)
    cm6-completions.js          # Autocomplete word lists (C++/Python/Java)
```

**Sua autocomplete (them/bot tu khoa):**
- Sua truc tiep file `repo/resources/aloj/codemirror6/cm6-completions.js`
- Khong can rebuild bundle
- Chay `./scripts/copy_static && docker compose restart site`

---

## Cau Truc Thu Muc

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
      initialize         # Khoi tao config lan dau
      migrate            # Chay Django migrations
      copy_static        # Build CSS + collect static files
      manage.py          # Django management wrapper
      enter_site         # Shell vao site container
    repo/                # Django source code
      dmoj/              # Django settings
      judge/             # Models, views, forms
      templates/         # HTML templates
      resources/         # Static files (JS, CSS, images)
        aloj/ace/        # Ace Editor (cho trang submit thuong)
        aloj/codemirror6/# CodeMirror 6 (cho IDE)
        aloj/jquery/     # jQuery
        aloj/select2/    # Select2
      _build/            # Build tools (gitignored)
    problems/            # Judge problem data + judge configs
    media/               # User uploads
    docker-compose.yml   # Docker orchestration
  document/              # Documentation
  judge_partial_testcase.patch  # Custom judge patch
```

---

## Lenh Nhanh

| Muc dich | Lenh |
|----------|------|
| Build lan dau | `docker compose build` |
| Start tat ca | `docker compose up -d` |
| Stop tat ca | `docker compose down` |
| Xem trang thai | `docker compose ps` |
| Xem logs | `docker compose logs -f [service]` |
| Migration | `./scripts/migrate` |
| Collect static | `./scripts/copy_static` |
| Django command | `./scripts/manage.py <cmd>` |
| Vao shell site | `./scripts/enter_site` |
| Restart site | `docker compose restart site` |
| Judge logs | `sudo docker logs -f judge01` |
