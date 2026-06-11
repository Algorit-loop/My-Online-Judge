# TAI LIEU THAM KHAO VIET BAO CAO DO AN TOT NGHIEP
# DU AN: ALOJ - ALGORIT ONLINE JUDGE
# ====================================

> File nay cung cap day du thong tin chinh xac tu source code de viet bao cao do an tot nghiep.
> Moi thong tin duoi day deu duoc trích xuat truc tiep tu ma nguon du an.

---

# MUC LUC

1. [TONG QUAN DU AN](#1-tong-quan-du-an)
2. [DONG LUC VA VAN DE CAN GIAI QUYET](#2-dong-luc-va-van-de-can-giai-quyet)
3. [CONG NGHE SU DUNG (TECH STACK)](#3-cong-nghe-su-dung)
4. [KIEN TRUC HE THONG](#4-kien-truc-he-thong)
5. [CO SO DU LIEU](#5-co-so-du-lieu)
6. [CAC CHUC NANG CHINH](#6-cac-chuc-nang-chinh)
7. [DIEM MOI - DONG GOP CUA TAC GIA](#7-diem-moi---dong-gop-cua-tac-gia)
8. [CHUC NANG AI CHI TIET](#8-chuc-nang-ai-chi-tiet)
9. [CHUC NANG IDE CHI TIET](#9-chuc-nang-ide-chi-tiet)
10. [SRS - DAC TA YEU CAU PHAN MEM (TOM TAT)](#10-srs---dac-ta-yeu-cau-phan-mem)
11. [DIAGRAM VA FLOW](#11-diagram-va-flow)
12. [TRIEN KHAI VA DEPLOYMENT](#12-trien-khai-va-deployment)
13. [BAO MAT](#13-bao-mat)
14. [SO SANH VOI DMOJ / VNOJ / BKDNOJ](#14-so-sanh-voi-dmoj--vnoj--bkdnoj)
15. [HUONG PHAT TRIEN TUONG LAI](#15-huong-phat-trien-tuong-lai)
16. [DANH SACH FILE QUAN TRONG](#16-danh-sach-file-quan-trong)

---

# 1. TONG QUAN DU AN

## 1.1. Thong tin co ban

| Thong tin | Chi tiet |
|-----------|---------|
| **Ten du an** | ALOJ - Algorit Online Judge |
| **Ten day du** | Algorit Online Judge |
| **Domain** | algoritoj.id.vn |
| **Loai** | He thong cham bai tu dong (Online Judge) |
| **Tham khao tu** | DMOJ (dmoj.ca) va VNOJ (oj.vnoi.info) |
| **Muc dich** | Thay the BKDNOJ, cai thien chuc nang va tich hop AI |
| **Ngon ngu giao dien** | Tieng Viet (vi), ho tro Tieng Anh (en) |
| **Timezone mac dinh** | Asia/Ho_Chi_Minh |

## 1.2. DMOJ la gi?

DMOJ (Don Mills Online Judge) la mot he thong cham bai tu dong ma nguon mo, duoc phat trien boi cong dong Canada. DMOJ ho tro nhieu ngon ngu lap trinh, nhieu dang contest, va co kien truc microservice voi judge server rieng biet.

## 1.3. VNOJ la gi?

VNOJ (Vietnam Online Judge - oj.vnoi.info) la phien ban fork tu DMOJ, duoc tuy chinh boi VNOI-Admin cho cong dong Competitive Programming Viet Nam. VNOJ bo sung them cac tinh nang nhu: Polygon import, organization subdomain, contest format VNOJ, v.v.

## 1.4. ALOJ la gi?

ALOJ (Algorit Online Judge) la phien ban fork tu VNOJ, duoc tac gia phat trien nhu do an tot nghiep. ALOJ ke thua tat ca chuc nang cua DMOJ/VNOJ va bo sung them:
- **He thong IDE truc tuyen** (kieu LeetCode)
- **Tich hop AI da nha cung cap** (OpenAI, Google Gemini, Anthropic Claude, DeepSeek)
- **AI Code Review** - Phan tich code tu dong
- **AI Problem Creator** - Tao de bai tu anh/PDF
- **He thong quan ly API Key ma hoa**
- **He thong Contribution Points**
- **Nhieu cau hinh tuy chinh khac**

---

# 2. DONG LUC VA VAN DE CAN GIAI QUYET

## 2.1. Van de cua BKDNOJ

BKDNOJ (Bach Khoa Da Nang Online Judge) co nhieu han che:
- Giao dien cu, chua than thien voi nguoi dung
- Khong co IDE truc tuyen de test code truoc khi nop
- Khong tich hop cong nghe AI de ho tro nguoi hoc
- Han che ve kha nang mo rong va tuy chinh
- Khong co he thong goi y, phan tich code tu dong

## 2.2. Muc tieu cua ALOJ

1. **Xay dung he thong OJ hien dai** - Giao dien dep, than thien, responsive
2. **Tich hop AI** - Giup nguoi hoc duoc goi y, phan tich code, tao de tu dong
3. **IDE truc tuyen** - Cho phep viet code, chay thu ngay tren trinh duyet
4. **Kien truc microservice** - De mo rong, de bao tri, deploy bang Docker
5. **Ho tro nhieu loai contest** - IOI, ICPC, AtCoder, ECOO, VNOJ format
6. **Cong dong** - Blog, comment, ticket, organization, contribution points

## 2.3. Doi tuong su dung

- **Sinh vien** - Luyen tap, thi contest, hoc thuat toan
- **Giang vien** - Tao de bai, quan ly contest, theo doi tien do sinh vien
- **Admin** - Quan ly he thong, nguoi dung, bai tap
- **Organization** - Nhom/lop hoc/CLB co the quan ly rieng

---

# 3. CONG NGHE SU DUNG

## 3.1. Backend

| Cong nghe | Phien ban | Muc dich |
|-----------|-----------|---------|
| **Python** | 3.11 | Ngon ngu chinh |
| **Django** | 4.2+ | Web framework |
| **Django Jinja2** | - | Template engine |
| **uWSGI** | - | WSGI application server (8 workers) |
| **Celery** | - | Async task queue (2 workers) |
| **MariaDB** | latest | Co so du lieu (MySQL-compatible) |
| **Redis** | alpine | Cache, session, message broker |
| **Node.js** | 18.x | WebSocket event daemon |

## 3.2. Frontend

| Cong nghe | Phien ban | Muc dich |
|-----------|-----------|---------|
| **jQuery** | 3.4.1 | DOM manipulation |
| **SCSS/SASS** | 1.66.1 | CSS preprocessing |
| **ACE Editor** | 1.4.14 | Code editor (30+ ngon ngu) |
| **Select2** | 4.0.3 | Enhanced select dropdowns |
| **Chart.js** | - | Bieu do thong ke |
| **MathJax** | - | Hien thi cong thuc toan |
| **Diff2HTML** | - | So sanh source code |
| **Font Awesome** | 4.3.0 | Icon |
| **Martor** | - | Markdown editor |
| **WebSocket (ws)** | 8.14.0 | Real-time updates |
| **Featherlight** | - | Modal/Lightbox |
| **Clipboard.js** | - | Copy to clipboard |
| **PostCSS + Autoprefixer** | 8.4.29 | CSS vendor prefixes |

## 3.3. Infrastructure

| Cong nghe | Muc dich |
|-----------|---------|
| **Docker** | Container hoa |
| **Docker Compose** | 3.7 | Orchestration |
| **Nginx** | alpine | Reverse proxy, static files |
| **SSHFS** | Remote judge mount |
| **TCP/IP Socket + Zlib** | Judge protocol |

## 3.4. AI Providers

| Provider | Models ho tro |
|----------|--------------|
| **OpenAI** | gpt-5.5, gpt-5.4, gpt-5.4-mini, gpt-5.4-nano, gpt-4.1, gpt-4o, gpt-4o-mini |
| **Google Gemini** | gemini-3.1-pro-preview, gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite |
| **Anthropic Claude** | claude-opus-4-8, claude-opus-4-7, claude-sonnet-4-6, claude-haiku-4-5 |
| **DeepSeek** | deepseek-v4-flash, deepseek-v4-pro, deepseek-chat, deepseek-reasoner |

## 3.5. Thu vien Python quan trong

| Thu vien | Muc dich |
|----------|---------|
| mysqlclient | Ket noi MySQL/MariaDB |
| django-redis | Redis cache backend |
| django-compressor | CSS/JS minification |
| social-auth-core | OAuth2 authentication |
| webauthn | 2FA WebAuthn/FIDO2 |
| celery | Distributed task queue |
| cryptography (Fernet) | Ma hoa API keys |
| lxml, Pygments | XML, Code highlighting |
| mistune, markdown2 | Markdown rendering |
| bleach | HTML sanitization |
| qrcode | 2FA QR code |
| pika | RabbitMQ client |
| requests | HTTP client |
| matplotlib | Bieu do |

---

# 4. KIEN TRUC HE THONG

## 4.1. Tong quan kien truc Microservice

He thong ALOJ gom **8 container Docker** giao tiep qua **3 mang noi bo**:

```
+------------------------------------------------------------------+
|                        INTERNET                                   |
|                           |                                       |
|                      Port 80 (HTTP)                               |
|                           |                                       |
|               +-----------v-----------+                           |
|               |    Nginx (aloj_nginx) |  <-- Reverse Proxy        |
|               |    - Static files     |                           |
|               |    - WebSocket proxy  |                           |
|               +-----------+-----------+                           |
|                           |                                       |
|          +----------------+----------------+                      |
|          |                                 |                      |
|  +-------v-------+               +--------v--------+             |
|  | Site (Django)  |               | WSEvent (Node)  |             |
|  | aloj_site      |               | aloj_wsevent    |             |
|  | Port 8000      |               | Port 15100-15102|             |
|  | uWSGI 8 worker |               | WebSocket daemon|             |
|  +-------+-------+               +-----------------+             |
|          |                                                        |
|  +-------v-------+    +------------------+                       |
|  |  Redis Cache   |    | Celery Worker    |                       |
|  |  aloj_redis    |    | aloj_celery      |                       |
|  |  Port 6379     |    | 2 workers        |                       |
|  +---------------+    +------------------+                       |
|          |                                                        |
|  +-------v-------+    +------------------+    +-----------+      |
|  | MariaDB        |    | Bridge Daemon    |    | External  |      |
|  | aloj_mysql     |    | aloj_bridged     |<-->| Judge     |      |
|  | Port 3306      |    | Port 9998, 9999  |    | Servers   |      |
|  +---------------+    +------------------+    +-----------+      |
+------------------------------------------------------------------+
```

## 4.2. Chi tiet cac Service

### Service 1: aloj_mysql (Database)
- **Image:** mariadb (official)
- **Muc dich:** Co so du lieu trung tam
- **Network:** db (isolated)
- **Volume:** ./database/ -> /var/lib/mysql/
- **Charset:** UTF8MB4, STRICT_TRANS_TABLES
- **Port noi bo:** 3306

### Service 2: aloj_redis (Cache)
- **Image:** redis:alpine
- **Muc dich:** Session cache, Django cache, Celery broker
- **Network:** site
- **DB 0:** Django caching
- **DB 1:** Celery broker + result backend
- **Port noi bo:** 6379

### Service 3: aloj_site (Web Application)
- **Build tu:** aloj/aloj-base -> aloj/aloj-site
- **Muc dich:** Django web app chinh
- **Network:** site, nginx, db
- **uWSGI:** 8 workers, reload tai 512MB RSS
- **Port noi bo:** 8000
- **Volumes:** assets, media, problems, repo

### Service 4: aloj_celery (Task Queue)
- **Build tu:** aloj/aloj-base -> aloj/aloj-celery
- **Muc dich:** Xu ly task bat dong bo
- **Command:** `celery -A dmoj_celery worker -l info --concurrency=2`
- **Network:** site, db
- **Tasks:** Rejudge, export data, email, PDF generation

### Service 5: aloj_bridged (Judge Bridge)
- **Build tu:** aloj/aloj-base -> aloj/aloj-bridged
- **Muc dich:** Cau noi giua Site va Judge Server
- **Command:** `python3 manage.py runbridged`
- **Port 9998:** Django <-> Bridge communication
- **Port 9999:** Bridge <-> Judge communication
- **Network:** site, nginx, db

### Service 6: aloj_wsevent (WebSocket)
- **Build tu:** Node.js alpine
- **Muc dich:** Real-time event broadcasting
- **Command:** `node /app/site/websocket/daemon.js`
- **Port 15100:** Client nhan event (WebSocket)
- **Port 15101:** Server gui event (POST)
- **Port 15102:** HTTP long-polling fallback
- **Network:** site, nginx
- **Message queue:** Max 50 messages, filter support

### Service 7: aloj_nginx (Reverse Proxy)
- **Image:** nginx:alpine
- **Port:** 80 (HTTP)
- **Routes:**
  - `/` -> site:8000 (uWSGI)
  - `/static/` -> /assets/static/ (local)
  - `/event/` -> wsevent:15100 (WebSocket upgrade)
  - `/channels/` -> wsevent:15102 (HTTP polling)
  - `/media/` -> /media/ (uploads)
- **Max body size:** 64MB
- **Security headers:** X-Content-Type-Options, X-XSS-Protection

### Service 8: External Judge Servers
- **Image:** vnoj/judge-tiervnoj:latest
- **Muc dich:** Bien dich va chay code cua nguoi dung
- **Ket noi:** Port 9999 den Bridge
- **Sandbox:** SYS_PTRACE capability
- **Ho tro:** C/C++, Python, Java, Pascal, va 30+ ngon ngu khac

## 4.3. Docker Networks

| Network | Services | Muc dich |
|---------|----------|---------|
| **site** | site, celery, bridged, redis, wsevent | Giao tiep noi bo ung dung |
| **db** | mysql, site, celery, bridged | Truy cap database |
| **nginx** | nginx, site, wsevent | HTTP/WebSocket proxy |

## 4.4. Luong xu ly nop bai (Submission Flow)

```
1. User nop bai qua web (HTTP POST)
        |
2. Nginx:80 -> Site:8000 (uWSGI/Django)
        |
3. Django luu Submission vao DB (status='QU')
        |
4. Django goi judge_submission() -> gui packet den Bridge
        |
5. Bridge (port 9998) nhan request, chuyen den Judge (port 9999)
        |
6. Judge Server nhan packet:
   - Bien dich source code
   - Chay tung test case voi resource limits
   - Gui ket qua tung test case ve Bridge
        |
7. Bridge xu ly ket qua:
   - Luu SubmissionTestCase vao DB
   - Tinh diem tong
   - Cap nhat status='D' (Done)
        |
8. Bridge post event den WSEvent daemon (port 15101)
        |
9. WSEvent broadcast qua WebSocket (port 15100) den browser
        |
10. Browser cap nhat UI real-time (khong can reload)
```

### Packet Protocol
- **Format:** JSON + Zlib compression
- **Header:** 4 bytes (length) + compressed data
- **Cac loai packet:** submission-request, submission-acknowledged, grading-begin, test-case-status, grading-end, compile-error

### Status Codes
```
QU - Queued (dang doi cham)
P  - Processing (dang xu ly)
G  - Grading (dang cham)
D  - Done (hoan tat)

Result Codes:
AC  - Accepted (Dung)
WA  - Wrong Answer (Sai)
TLE - Time Limit Exceeded
MLE - Memory Limit Exceeded
RTE - Runtime Error
CE  - Compile Error
IE  - Internal Error
OLE - Output Limit Exceeded
```

---

# 5. CO SO DU LIEU

## 5.1. Database Engine
- **DBMS:** MariaDB (MySQL-compatible)
- **Charset:** UTF8MB4 (ho tro Unicode day du, bao gom emoji)
- **SQL Mode:** STRICT_TRANS_TABLES, NO_ENGINE_SUBSTITUTION
- **Storage Engine:** InnoDB

## 5.2. Danh sach Models chinh (Entity)

### A. Nhom User / Profile

| Model | Mo ta | Truong chinh |
|-------|-------|-------------|
| **User** (Django built-in) | Tai khoan nguoi dung | username, password, email, is_staff |
| **Profile** | Thong tin mo rong | user (1:1), timezone, language, points, rating, display_rank, contribution_points, about, organizations |
| **Organization** | Nhom/to chuc | name, slug, short_name, about, admins, members, logo_override_image |
| **OrganizationRequest** | Yeu cau tham gia | user, organization, state, reason |
| **OrganizationMonthlyUsage** | Credit su dung | organization, month, credit_used |
| **Badge** | Huy hieu | name, mini |

### B. Nhom Problem

| Model | Mo ta | Truong chinh |
|-------|-------|-------------|
| **Problem** | Bai tap | code, name, description, time_limit, memory_limit, points, partial, authors, curators, testers, types, group, allowed_languages, is_public, enable_new_ide |
| **ProblemGroup** | Nhom bai tap | name |
| **ProblemType** | Loai bai tap | name, full_name |
| **ProblemData** | Du lieu test | problem, zipfile, generator, output_prefix, output_limit |
| **ProblemTestCase** | Test case | dataset, order, type, input_file, output_file, points, is_pretest, **is_sample** (ALOJ moi) |
| **ProblemTranslation** | Da ngon ngu | problem, language, name, description |
| **ProblemClarification** | Lam ro de bai | problem, description, date |
| **Solution** (Editorial) | Loi giai mau | problem, is_public, publish_on, authors, content |
| **LanguageLimit** | Gioi han rieng | problem, language, time_limit, memory_limit |

### C. Nhom Submission

| Model | Mo ta | Truong chinh |
|-------|-------|-------------|
| **Submission** | Bai nop | user, problem, date, time, memory, points, language, status, result, source, case_points, case_total, judged_on |
| **SubmissionSource** | Ma nguon | submission (1:1), source |
| **SubmissionTestCase** | Ket qua test | submission, case, status, time, memory, points, total, batch, output |
| **RunSubmission** (ALOJ moi) | IDE Run | user, problem, language, source, status, result, time, memory, case_results (JSON) |

### D. Nhom Contest

| Model | Mo ta | Truong chinh |
|-------|-------|-------------|
| **Contest** | Cuoc thi | key, name, description, start_time, end_time, time_limit, authors, curators, testers, problems, format_name, is_rated |
| **ContestParticipation** | Tham gia thi | contest, user, real_start, score, cumtime, is_disqualified |
| **ContestProblem** | Bai trong contest | contest, problem, points, partial, order, output_prefix |
| **ContestSubmission** | Bai nop trong contest | submission, participation, problem, points |
| **ContestTag** | Tag contest | name, color, description |
| **ContestAnnouncement** | Thong bao | contest, title, description, date |
| **ContestMoss** | Chong gian lan | contest, problem, language, url |
| **Rating** | Xep hang | user, contest, rating, volatility, rank |

### E. Nhom Comment / Blog / Ticket

| Model | Mo ta | Truong chinh |
|-------|-------|-------------|
| **Comment** | Binh luan (MPTT tree) | author, page, body, score, parent |
| **CommentVote** | Vote binh luan | voter, comment, score |
| **CommentLock** | Khoa binh luan | page |
| **BlogPost** | Bai viet | title, slug, content, authors, publish_on, visible |
| **BlogPostTag** | Tag bai viet | name |
| **BlogVote** | Vote bai viet | voter, post, score |
| **Ticket** | Phieu ho tro | title, user, content, object_id, is_open |
| **TicketMessage** | Nhan tin ticket | ticket, user, body |

### F. Nhom AI (ALOJ MOI - Dong gop cua tac gia)

| Model | Mo ta | Truong chinh |
|-------|-------|-------------|
| **AICodeReview** | AI review code | submission, user, provider, model, review_text, output_language, created_at |
| **AIPromptTemplate** | Mau prompt AI | key, name, prompt_text, description |
| **AIAPIKey** | API key ma hoa | user, provider, key_ciphertext, key_last4, status, default_model, last_used_at |
| **AIAPIKeyTestLog** | Log test API | api_key, provider, model_tested, success, detail, response_time_ms |

### G. Nhom khac

| Model | Mo ta | Truong chinh |
|-------|-------|-------------|
| **Language** | Ngon ngu lap trinh | key, name, short_name, common_name, ace, pygments |
| **Judge** | May cham | name, created, online, start_time, load, description |
| **RuntimeVersion** | Phien ban runtime | judge, language, name, version |
| **NavigationBar** | Menu dieu huong | key, label, path, order, regex, parent |
| **MiscConfig** | Cau hinh he thong | key, value |
| **Tag** | Tag bai ngoai | name, code |
| **TagGroup** | Nhom tag | name |
| **TagProblem** | Bai tap ngoai | code, name, url, oj |
| **URLShortener** | Rut gon link | short_code, url, user, click_count |

## 5.3. Quan he giua cac Model (Relationships)

```
User (Django) <-- 1:1 --> Profile
Profile <-- N:M --> Organization (thanh vien + admin)
Profile <-- 1:N --> Submission, Comment, BlogPost, Ticket
Problem <-- 1:N --> Submission, ProblemTestCase, ProblemClarification
Problem <-- N:M --> Language (allowed_languages)
Problem <-- N:M --> ProblemType, ProblemGroup
Problem <-- 1:1 --> ProblemData
Contest <-- N:M --> Problem (qua ContestProblem)
Contest <-- N:M --> Profile (qua ContestParticipation)
Contest <-- 1:N --> ContestSubmission
Submission <-- 1:N --> SubmissionTestCase
Submission <-- 1:1 --> SubmissionSource
Comment <-- Self-referencing --> Comment (parent, cay MPTT)
AIAPIKey <-- 1:N --> AIAPIKeyTestLog
AICodeReview <-- N:1 --> Submission
AICodeReview <-- N:1 --> Profile
```

## 5.4. So luong Migration

Tong cong **231 migration files** trong `judge/migrations/`, bao gom:
- Migration goc tu DMOJ/VNOJ: 0001 -> 0224
- **Migration ALOJ moi:**
  - `0225_problem_enable_new_ide_problemtestcase_is_sample.py` - IDE feature
  - `0226_run_submission.py` - RunSubmission model
  - `0227_aiapikey.py` - AI API Key + Test Log models
  - `0229_ai_code_review.py` - AI Code Review model
  - `0230_ai_prompt_template.py` - AI Prompt Template model
  - `0231_seed_ai_prompts.py` - Khoi tao prompt mac dinh

---

# 6. CAC CHUC NANG CHINH

## 6.1. Chuc nang ke thua tu DMOJ/VNOJ

### A. Quan ly bai tap (Problem Management)
- Tao, sua, xoa bai tap voi Markdown editor
- Ho tro da ngon ngu (dich de bai)
- Quan ly test case (upload zip, tung file)
- Scoring modes: Standard, Partial (by testcase)
- Cau hinh time limit, memory limit rieng tung ngon ngu
- Editorial/loi giai mau
- Problem PDF generation
- Import bai tu Polygon format

### B. He thong cham bai (Judge System)
- Cham bai tu dong voi 30+ ngon ngu lap trinh
- Real-time status update qua WebSocket
- Ho tro batch grading, interactive problems
- Rejudge (cham lai) don le hoac hang loat
- Multiple judge server (scale horizontal)
- Custom checker, interactive grader

### C. Contest (Cuoc thi)
- **6 dinh dang contest:**
  - Default (DMOJ standard)
  - IOI (International Olympiad in Informatics)
  - ICPC (International Collegiate Programming Contest)
  - AtCoder format
  - ECOO format
  - VNOJ format
  - Legacy IOI format
- Dang ky tham gia, virtual participation
- Leaderboard real-time (auto-refresh 10s)
- Announcements trong contest
- Freeze scoreboard
- MOSS plagiarism detection (chong gian lan)
- Contest rating system
- Calendar view

### D. Nguoi dung & Xac thuc
- Dang ky, dang nhap, doi mat khau
- OAuth2: Google, Facebook, GitHub
- Two-Factor Authentication (TOTP + WebAuthn/FIDO2)
- User profile voi avatar (Gravatar)
- Rating, points, contribution tracking
- User data export (GDPR-ready)
- Admin impersonation (debug)

### E. Organization (To chuc)
- Tao va quan ly nhom
- Subdomain routing (vd: clb.algoritoj.id.vn)
- Organization-scoped problems va contests
- Join requests (yeu cau tham gia)
- Organization ranking
- Logo override

### F. Blog & Community
- Blog posts voi Markdown
- Comment system (hierarchical, MPTT tree)
- Comment voting (+1/-1)
- Ticket system (bao loi, yeu cau)
- RSS/Atom feeds

### G. Khac
- Dark mode / Light mode toggle
- Responsive design
- Full-text search
- URL shortener
- Language/Runtime status page
- Statistics va charts
- Sitemap generation
- Flatpages
- Email notifications (Gmail SMTP)
- Discord webhooks

## 6.2. URL Routing tong hop

| URL Pattern | Chuc nang |
|-------------|----------|
| `/` | Trang chu (Blog list) |
| `/problems/` | Danh sach bai tap |
| `/problem/<code>/` | Xem bai tap |
| `/problem/<code>/submit` | Nop bai |
| `/problem/<code>/run` | **IDE Run (ALOJ moi)** |
| `/submissions/` | Danh sach bai nop |
| `/submission/<id>/` | Chi tiet bai nop |
| `/src/<id>/` | Xem source code |
| `/src/<id>/ai-review/` | **AI Code Review (ALOJ moi)** |
| `/contests/` | Danh sach contest |
| `/contest/<code>/` | Xem contest |
| `/users/` | Bang xep hang |
| `/user/<username>/` | Profile nguoi dung |
| `/organizations/` | Danh sach to chuc |
| `/accounts/api-keys/` | **Quan ly AI API Keys (ALOJ moi)** |
| `/admin/judge/problem/ai-create/` | **AI Problem Creator (ALOJ moi)** |
| `/runtimes/` | Trang thai ngon ngu |
| `/status/` | Trang thai judge |
| `/posts/` | Blog |
| `/tickets/` | He thong ticket |
| `/tags/` | Tag problems |
| `/api/v2/` | REST API |

---

# 7. DIEM MOI - DONG GOP CUA TAC GIA

Day la phan QUAN TRONG NHAT cua bao cao - the hien nhung gi tac gia da lam duoc.

## 7.1. Tong hop cac dong gop

| STT | Chuc nang | Loai | Mo ta |
|-----|----------|------|-------|
| 1 | **AI Code Review** | Moi hoan toan | Phan tich code tu dong bang AI |
| 2 | **AI Problem Creator** | Moi hoan toan | Tao de bai tu anh/PDF bang AI |
| 3 | **AI API Key Management** | Moi hoan toan | Quan ly API key ma hoa |
| 4 | **AI Prompt Templates** | Moi hoan toan | Mau prompt tuy chinh |
| 5 | **Online IDE** | Moi hoan toan | Viet code + chay thu truc tuyen |
| 6 | **RunSubmission** | Moi hoan toan | Model cho IDE run (tach khoi Submission) |
| 7 | **Sample TestCase** | Cai tien | Danh dau test case lam sample cho IDE |
| 8 | **Contribution Points** | Tuy chinh | He thong diem dong gop |
| 9 | **Organization Credits** | Tuy chinh | He thong tin dung to chuc |
| 10 | **Cheating Management** | Tuy chinh | Tu dong ban khi gian lan nhieu lan |
| 11 | **Low Power Mode** | Tuy chinh | Toi uu hieu nang khi tai nguyen han che |
| 12 | **Comment Validation** | Tuy chinh | Kiem soat chat luong binh luan |
| 13 | *(Du kien) Generate Testcase with AI* | Chua implement | Sinh test case tu dong bang AI |

## 7.2. So luong code moi

### Models moi (6 models):
- `AICodeReview` - 31 dong
- `AIPromptTemplate` - 31 dong
- `AIAPIKey` - 142 dong (bao gom encryption logic)
- `AIAPIKeyTestLog` - 158 dong
- `RunSubmission` - 56 dong
- `URLShortener` - (urlshortener app)

### Views moi (5 files):
- `ai_code_review.py` - 249 dong
- `ai_problem_creator.py` - 239 dong
- `api_key.py` - ~300 dong
- `run.py` - 219 dong
- Cac thay doi trong views khac

### Templates moi:
- `problem-ide.html` - Full IDE layout
- `user/api-keys.html` - Quan ly API keys
- `admin/judge/problem/ai_create.html` - AI problem creator
- Sua doi `submission/source.html` - Them AI review modal

### Migrations moi: 6 files (0225 -> 0231)

### Settings moi: 40+ cau hinh ALOJ_* rieng

---

# 8. CHUC NANG AI CHI TIET

## 8.1. AI Code Review

### Mo ta
Cho phep nguoi dung yeu cau AI phan tich submission cua minh. AI se danh gia:
1. **Thuat toan & Cau truc du lieu** - Nhan dien thuat toan chinh
2. **Luong thuc thi** - Giai thich tung buoc code hoat dong
3. **Do phuc tap thoi gian** - Voi giai thich
4. **Do phuc tap bo nho** - Voi giai thich
5. **Chat luong code** - Doc duoc, edge cases, cai thien

### Luong hoat dong
```
1. User xem source code tai /src/<id>/
2. Click "Review with AI" -> Mo modal
3. Chon Provider, Model, Output Language
4. Click "Analyze" -> POST /src/<id>/ai-review/
5. Server:
   a. Kiem tra quyen so huu submission
   b. Lay API key da ma hoa tu DB, giai ma
   c. Tao prompt tu template (hoac default)
   d. Goi API cua provider (timeout 120s)
   e. Parse response theo format cua provider
   f. Luu AICodeReview vao DB
   g. Tra ve JSON response
6. Frontend hien thi ket qua trong modal
7. Lan sau GET -> tra ve cached review
```

### File lien quan
- Model: `judge/models/ai_code_review.py`
- View: `judge/views/ai_code_review.py`
- Template: `templates/submission/source.html` (modal section)
- URL: `path('src/<int:submission>/ai-review/', ...)`

### System Prompt (mac dinh)
```
You are an expert competitive programming analyst.
Analyze the following code submission.

Problem: "{problem_name}"
Language: {language_name}
Submission result: {result} ({points}/{total_points} points)

Provide analysis covering:
1. Algorithm & Data Structures
2. Execution Flow
3. Time Complexity
4. Space Complexity
5. Code Quality

Output language: {output_language}
```

## 8.2. AI Problem Creator

### Mo ta
Cho phep admin upload anh hoac PDF cua de bai, AI se tu dong chuyen thanh Markdown format chuan cho OJ.

### Luong hoat dong
```
1. Admin vao /admin/judge/problem/ai-create/
2. Upload file (PDF, PNG, JPG, WEBP) - max 10MB
3. Chon Provider (chi openai, gemini, claude - co vision)
4. Chon Model va Output Language
5. Click "Process" -> POST voi multipart form data
6. Server:
   a. Validate file (loai, kich thuoc)
   b. Encode file sang base64
   c. Build payload theo provider (khac nhau)
   d. Goi vision API (timeout 120s)
   e. Parse response, strip code fences
   f. Tra ve markdown content
7. Admin xem preview, chinh sua
8. Apply vao form tao problem moi
```

### Providers ho tro Vision
- **OpenAI:** input_image / input_file (PDF)
- **Gemini:** inline_data (base64)
- **Claude:** image/document block (base64)
- **DeepSeek:** KHONG ho tro vision

### File lien quan
- View: `judge/views/ai_problem_creator.py`
- Template: `templates/admin/judge/problem/ai_create.html`
- Admin URL: `/admin/judge/problem/ai-create/`

## 8.3. AI API Key Management

### Mo ta
He thong quan ly API key an toan voi ma hoa Fernet. Moi nguoi dung co the luu tru 1 key cho moi provider.

### Bao mat
- **Ma hoa:** Fernet symmetric encryption
- **Key derivation:** SHA-256 tu Django SECRET_KEY
- **Luu tru:** Chi luu ciphertext + 4 ky tu cuoi
- **Giai ma:** Chi khi goi API that su
- **Xoa ngay:** Plaintext bi xoa khoi memory sau khi dung

### Cac endpoint
| Method | URL | Chuc nang |
|--------|-----|----------|
| GET | `/accounts/api-keys/` | Trang quan ly |
| GET | `/accounts/api-keys/list/` | Danh sach keys (JSON) |
| POST | `/accounts/api-keys/add/` | Them key moi |
| POST | `/accounts/api-keys/<id>/test/` | Test ket noi |
| POST | `/accounts/api-keys/<id>/delete/` | Xoa key |
| GET | `/accounts/api-keys/<id>/logs/` | Xem log test |

### Trang thai API Key
- **pending** - Moi them, chua test
- **verified** - Test thanh cong (mau xanh)
- **failed** - Test that bai (mau do)

### File lien quan
- Model: `judge/models/api_key.py`
- View: `judge/views/api_key.py`
- Template: `templates/user/api-keys.html`

## 8.4. AI Prompt Templates

### Mo ta
He thong prompt co the tuy chinh tu Admin panel, cho phep thay doi cach AI xu ly ma khong can sua code.

### 3 Prompt mac dinh
1. **ai_code_review** - Prompt phan tich code
2. **ai_problem_creator** - Prompt trich xuat de bai tu anh
3. **api_key_test** - Prompt test ket noi ("Reply exactly: OK")

### Variable substitution
Su dung format `{variable}` trong prompt text. Vi du:
- `{problem_name}` - Ten bai tap
- `{language_name}` - Ngon ngu lap trinh
- `{output_language}` - Ngon ngu dau ra

### File lien quan
- Model: `judge/models/ai_prompt.py`
- Admin: `judge/admin/ai_prompt.py`
- Migration seed: `judge/migrations/0231_seed_ai_prompts.py`

---

# 9. CHUC NANG IDE CHI TIET

## 9.1. Mo ta

Online IDE cho phep nguoi dung viet code va chay thu ngay tren trinh duyet, tuong tu LeetCode. Giao dien chia 2 cot co the keo thay doi kich thuoc.

## 9.2. Giao dien

```
+-----------------------------------------------------------+
|  ALOJ Navbar                                               |
+---------------------------+-------------------------------+
|                           |                               |
|  PROBLEM STATEMENT        |  CODE EDITOR (ACE)            |
|                           |                               |
|  - Ten bai                |  [Language selector]          |
|  - Time/Memory limit      |  +-------------------------+ |
|  - De bai (Markdown)      |  | #include <iostream>     | |
|  - Sample I/O             |  | using namespace std;    | |
|  - Constraints            |  | int main() {            | |
|  - Notes                  |  |   int a, b;             | |
|                           |  |   cin >> a >> b;        | |
|  [Admin Actions]          |  |   cout << a+b << endl;  | |
|  [Problem Stats]          |  | }                       | |
|                           |  +-------------------------+ |
|                           |                               |
|  <-- keo -->              |  [Run] [Submit]               |
|                           |                               |
|                           |  RESULTS:                     |
|                           |  Test 1: AC (15ms, 2MB)       |
|                           |  Test 2: AC (12ms, 2MB)       |
|                           |  > Passed 2/2                 |
+---------------------------+-------------------------------+
```

## 9.3. Dac diem ky thuat

- **Layout:** CSS Flexbox voi draggable divider
- **Min width:** 280px (left), 350px (right)
- **Code editor:** ACE Editor voi 30+ ngon ngu syntax
- **Run mode:** Chi chay sample test cases (khong luu vao submission history)
- **Submit mode:** Nop bai chinh thuc (luu vao Submission)
- **Real-time:** WebSocket events cho ca Run va Submit
- **Custom inputs:** Ho tro toi da 3 custom test inputs

## 9.4. RunSubmission vs Submission

| Thuoc tinh | Submission | RunSubmission |
|-----------|-----------|---------------|
| Luu vao lich su | Co | Khong |
| Anh huong diem | Co | Khong |
| Chay tat ca test | Co | Chi sample tests |
| Custom input | Khong | Co (toi da 3) |
| WebSocket channel | `sub_<id>` | `run_<id>` |
| Packet type | `submission-request` | `run-request` |

## 9.5. Luong hoat dong IDE Run

```
1. User viet code trong ACE Editor
2. Click "Run"
3. Frontend POST /problem/<code>/run voi {source, language, custom_inputs}
4. Server (RunSubmitView):
   a. Validate: quyen truy cap, rate limit, source length
   b. Lay sample test cases (ProblemTestCase.is_sample=True)
   c. Tao RunSubmission (status='QU')
   d. Goi judge_run_submission() -> gui den Bridge
5. Bridge gui den Judge voi meta: sample-testcase-only=True
6. Judge chay chi sample tests + custom inputs
7. Ket qua tra ve qua WebSocket hoac polling
8. Frontend hien thi ket qua tung test case
```

## 9.6. Model moi

### ProblemTestCase.is_sample (Boolean)
- Them truong `is_sample` vao ProblemTestCase
- Admin danh dau test case nao la sample
- Chi nhung test co is_sample=True duoc chay khi IDE Run

### Problem.enable_new_ide (Boolean)
- Toggle bat/tat IDE cho tung bai
- Khi True: render `problem-ide.html` thay vi `problem.html`
- Khi False: giao dien truyen thong

### RunSubmission
- Model rieng, khong lien quan den Submission chinh thuc
- Case results luu trong JSONField (khong tao SubmissionTestCase rieng)
- HMAC-SHA512 id_secret cho WebSocket channel

## 9.7. File lien quan
- Model: `judge/models/run_submission.py`
- View: `judge/views/run.py` (3 views: RunSubmitView, RunPollView, SampleTestCaseView)
- Template: `templates/problem/problem-ide.html`
- Judge API: `judge/judgeapi.py` (ham judge_run_submission)
- Migration: `0225_...`, `0226_...`

---

# 10. SRS - DAC TA YEU CAU PHAN MEM

## 10.1. Yeu cau chuc nang (Functional Requirements)

### FR01: Quan ly tai khoan
- FR01.1: Dang ky tai khoan (email, username, password)
- FR01.2: Dang nhap/Dang xuat
- FR01.3: Dang nhap qua OAuth2 (Google, Facebook, GitHub)
- FR01.4: Two-Factor Authentication (TOTP, WebAuthn)
- FR01.5: Doi mat khau, reset mat khau
- FR01.6: Chinh sua profile (avatar, about, timezone, language)
- FR01.7: Quan ly AI API Keys

### FR02: Quan ly bai tap
- FR02.1: Xem danh sach bai tap (loc theo difficulty, tag, status)
- FR02.2: Xem chi tiet bai tap (de bai, constraints, sample I/O)
- FR02.3: Tao/sua/xoa bai tap (admin/problem setter)
- FR02.4: Upload test data (zip file hoac tung file)
- FR02.5: Cau hinh scoring mode, time/memory limit
- FR02.6: Import bai tu Polygon format
- FR02.7: **Tao de bai tu anh/PDF bang AI (ALOJ moi)**

### FR03: Nop bai va cham bai
- FR03.1: Nop bai giai (chon ngon ngu, paste/upload code)
- FR03.2: Xem ket qua real-time (WebSocket)
- FR03.3: Xem chi tiet tung test case
- FR03.4: Xem source code bai nop
- FR03.5: **Chay thu code qua IDE (ALOJ moi)**
- FR03.6: **AI Code Review (ALOJ moi)**

### FR04: Contest
- FR04.1: Xem danh sach contest
- FR04.2: Dang ky/tham gia contest
- FR04.3: Nop bai trong contest
- FR04.4: Xem leaderboard real-time
- FR04.5: Virtual participation
- FR04.6: Tao/quan ly contest (6 formats)
- FR04.7: MOSS plagiarism detection

### FR05: Community
- FR05.1: Blog posts (tao, doc, vote)
- FR05.2: Comment (hierarchical, vote)
- FR05.3: Ticket system (bao loi)
- FR05.4: Organization management

### FR06: AI Features
- FR06.1: Quan ly AI API Keys (them, xoa, test, xem log)
- FR06.2: AI Code Review (phan tich code tu dong)
- FR06.3: AI Problem Creator (tao de tu anh/PDF)
- FR06.4: Tuy chinh AI Prompt tu admin panel
- FR06.5: *(Tuong lai) Generate Testcase with AI*

## 10.2. Yeu cau phi chuc nang (Non-Functional Requirements)

### NFR01: Hieu nang
- uWSGI 8 workers xu ly dong thoi
- Redis caching giam tai database
- Celery 2 workers cho task bat dong bo
- WebSocket thay cho polling (giam tai server)
- Nginx gzip compression cho static files
- Lazy image loading

### NFR02: Bao mat
- Ma hoa API key bang Fernet
- CSRF protection
- XSS protection (Bleach sanitization, security headers)
- SQL injection prevention (Django ORM)
- Network isolation (3 Docker networks)
- Database khong expose ra ngoai
- Session management qua Redis

### NFR03: Kha nang mo rong
- Microservice architecture (Docker containers)
- Horizontal scaling cho Judge servers
- Scale Celery workers khi can
- Docker Compose orchestration

### NFR04: Kha dung
- Docker restart policy: unless-stopped
- Judge auto-reconnect
- WebSocket fallback to HTTP long-polling
- Error pages (502/504)

### NFR05: Kha nang bao tri
- Container hoa toan bo
- Environment variables cho cau hinh
- Database migration system
- Git version control

## 10.3. Actors (Tac nhan)

| Actor | Mo ta | Quyen |
|-------|-------|------|
| **Guest** | Khach chua dang nhap | Xem bai tap, xem contest, xem ranking |
| **User** | Nguoi dung da dang nhap | Nop bai, tham gia contest, comment, blog, AI review |
| **Problem Setter** | Nguoi tao de | Tao/sua bai tap, upload test data |
| **Contest Admin** | Nguoi tao contest | Tao/quan ly contest, xem moss |
| **Organization Admin** | Quan tri nhom | Quan ly thanh vien, bai tap, contest cua nhom |
| **Staff** | Nhan vien | Quan ly ticket, impersonate user |
| **Admin** | Quan tri vien | Toan quyen, AI problem creator |
| **Judge Server** | May cham tu dong | Nhan bai, bien dich, chay, tra ket qua |

---

# 11. DIAGRAM VA FLOW

## 11.1. Use Case Diagram (mo ta bang text)

### User Use Cases:
```
User
  |-- Dang ky / Dang nhap
  |-- Xem danh sach bai tap
  |-- Xem chi tiet bai tap
  |-- Nop bai giai
  |-- Chay thu code (IDE) [ALOJ moi]
  |-- Xem ket qua submission
  |-- Yeu cau AI Code Review [ALOJ moi]
  |-- Quan ly AI API Keys [ALOJ moi]
  |-- Tham gia contest
  |-- Xem leaderboard
  |-- Viet blog post
  |-- Binh luan & vote
  |-- Tao ticket
  |-- Tham gia organization
  |-- Chinh sua profile
```

### Admin Use Cases:
```
Admin
  |-- Toan quyen cua User
  |-- Quan ly bai tap (CRUD)
  |-- Upload test data
  |-- Tao de bang AI [ALOJ moi]
  |-- Quan ly contest
  |-- Quan ly user
  |-- Quan ly judge
  |-- Cau hinh he thong
  |-- Tuy chinh AI prompts [ALOJ moi]
  |-- Xem AI code review logs [ALOJ moi]
  |-- MOSS plagiarism check
```

## 11.2. Sequence Diagram: AI Code Review

```
User           Frontend        Server          AI Provider     Database
 |                |               |                |              |
 |-- Click Review |               |                |              |
 |                |-- POST /ai-review/             |              |
 |                |               |                |              |
 |                |               |-- Check ownership             |
 |                |               |-- Get API Key  |              |
 |                |               |                |<-- Decrypt --|
 |                |               |                |              |
 |                |               |-- Build prompt |              |
 |                |               |-- Call API --->|              |
 |                |               |                |-- Process -->|
 |                |               |<-- Response ---|              |
 |                |               |                |              |
 |                |               |-- Save review  |              |
 |                |               |                |-- INSERT --->|
 |                |               |                |              |
 |                |<-- JSON response               |              |
 |<-- Show result |               |                |              |
```

## 11.3. Sequence Diagram: IDE Run

```
User           Frontend        Server          Bridge          Judge
 |                |               |               |              |
 |-- Click Run    |               |               |              |
 |                |-- POST /run   |               |              |
 |                |               |-- Validate    |              |
 |                |               |-- Create RunSubmission       |
 |                |               |-- judge_run()  |              |
 |                |               |--------------->|              |
 |                |               |               |-- Send job -->|
 |                |               |               |              |
 |                |<-- run_id + id_secret          |              |
 |                |               |               |              |
 |                |-- Subscribe WebSocket(run_<id>)|              |
 |                |               |               |              |
 |                |               |               |<-- Results --|
 |                |               |               |-- Update DB  |
 |                |               |               |-- Post event |
 |                |               |               |              |
 |                |<-- WebSocket event             |              |
 |<-- Show results|               |               |              |
```

## 11.4. Component Diagram (text)

```
+------------------+     +------------------+     +------------------+
|   Presentation   |     |   Application    |     |     Data         |
|     Layer        |     |     Layer        |     |     Layer        |
|                  |     |                  |     |                  |
| - Nginx          |     | - Django Views   |     | - MariaDB        |
| - Templates      |     | - URL Routing    |     | - Redis Cache    |
| - Static Files   |     | - Middleware     |     | - File Storage   |
| - JavaScript     |     | - Models/ORM     |     | - Problem Data   |
| - WebSocket      |     | - Celery Tasks   |     |                  |
|                  |     | - AI Integration |     |                  |
+------------------+     +------------------+     +------------------+
         |                       |                        |
         v                       v                        v
+------------------+     +------------------+     +------------------+
|  Judge Layer     |     |  Event Layer     |     |  External APIs   |
|                  |     |                  |     |                  |
| - Bridge Daemon  |     | - WSEvent Node   |     | - OpenAI API     |
| - Judge Server   |     | - WebSocket      |     | - Gemini API     |
| - Sandbox        |     | - HTTP Polling   |     | - Claude API     |
|                  |     |                  |     | - DeepSeek API   |
+------------------+     +------------------+     +------------------+
```

---

# 12. TRIEN KHAI VA DEPLOYMENT

## 12.1. Yeu cau he thong

### May chu (Server)
- **OS:** Ubuntu 20.04 LTS tro len
- **CPU:** 2+ Cores
- **RAM:** 4 GB tro len
- **Storage:** 60 GB SSD
- **Docker + Docker Compose**

### May cham (Judge Server - tuy chon)
- **OS:** Ubuntu 20.04 LTS
- **CPU:** 1+ Core
- **RAM:** 2 GB tro len
- **Storage:** 60 GB SSD

## 12.2. Quy trinh deploy

```
1. Clone repository
2. Tao environment files (.env)
3. Chay scripts/initialize (copy config)
4. docker-compose build (build images)
5. docker-compose up -d db redis (khoi dong DB)
6. scripts/migrate (tao database schema)
7. scripts/copy_static (compile CSS/JS)
8. Tao admin account
9. docker-compose up -d (khoi dong tat ca)
10. Cau hinh Judge server
11. Test submission
```

## 12.3. Docker Images

| Image | Base | Size (uoc tinh) |
|-------|------|-----------------|
| aloj/aloj-base | python:3.11-slim-bullseye | ~500MB |
| aloj/aloj-site | aloj-base + Pandoc | ~600MB |
| aloj/aloj-celery | aloj-base | ~500MB |
| aloj/aloj-bridged | aloj-base | ~500MB |
| aloj/aloj-wsevent | node:alpine | ~100MB |
| mariadb | official | ~400MB |
| redis:alpine | official | ~30MB |
| nginx:alpine | official | ~30MB |
| vnoj/judge-tiervnoj | custom | ~2-10GB (tuy tier) |

---

# 13. BAO MAT

## 13.1. Authentication & Authorization
- Django built-in auth + Custom middleware
- OAuth2 (Google, Facebook, GitHub)
- 2FA: TOTP (Google Authenticator) + WebAuthn (YubiKey)
- Session-based auth voi Redis backend
- Permission system: user, setter, staff, admin, teacher
- IP-based authentication (tuy chon)

## 13.2. Data Protection
- **API Key encryption:** Fernet (AES-128-CBC) derived tu SECRET_KEY
- **Password hashing:** Django default (PBKDF2-SHA256)
- **CSRF protection:** Django middleware
- **XSS prevention:** Bleach HTML sanitization + Security headers
- **SQL injection:** Django ORM parameterized queries
- **Clickjacking:** X-Frame-Options middleware

## 13.3. Network Security
- Database khong expose port ra ngoai (chi noi bo Docker network)
- Redis khong expose port
- Judge ports (9998, 9999) chi cho internal communication
- Nginx la diem duy nhat tiep xuc internet (port 80)
- Max upload size: 64MB

## 13.4. Code Execution Security
- Judge server chay trong Docker container
- SYS_PTRACE capability cho sandbox
- Resource limits: time, memory, output
- Isolated execution environment

---

# 14. SO SANH VOI DMOJ / VNOJ / BKDNOJ

## 14.1. Bang so sanh chuc nang

| Chuc nang | DMOJ | VNOJ | BKDNOJ | **ALOJ** |
|-----------|------|------|--------|----------|
| Cham bai tu dong | Co | Co | Co | **Co** |
| Multi-language | 30+ | 30+ | Han che | **30+** |
| Contest formats | 4 | 6 | 1-2 | **7** |
| Real-time updates | Co | Co | Han che | **Co** |
| Dark mode | Co | Co | Khong | **Co** |
| Organization | Co | Co | Han che | **Co + subdomain** |
| 2FA | Co | Co | Khong | **Co (TOTP + WebAuthn)** |
| Plagiarism (MOSS) | Co | Co | Khong | **Co** |
| **Online IDE** | Khong | Khong | Khong | **Co** |
| **AI Code Review** | Khong | Khong | Khong | **Co** |
| **AI Problem Creator** | Khong | Khong | Khong | **Co** |
| **AI API Key Mgmt** | Khong | Khong | Khong | **Co** |
| **Multi AI Provider** | Khong | Khong | Khong | **4 providers** |
| **Contribution Points** | Khong | Co (co ban) | Khong | **Co (mo rong)** |
| **IDE Run (sample only)** | Khong | Khong | Khong | **Co** |
| API v2 | Co | Co | Han che | **Co** |
| Responsive design | Co | Co | Khong | **Co** |
| Vietnamese | Khong | Co | Co | **Co (mac dinh)** |
| Blog system | Co | Co | Khong | **Co** |
| Ticket system | Co | Co | Khong | **Co** |
| URL Shortener | Khong | Khong | Khong | **Co** |

## 14.2. Diem noi bat cua ALOJ

1. **AI-first approach:** Tich hop AI xuyen suot (review, tao de, prompt tuy chinh)
2. **Modern IDE:** Giong LeetCode, khong can IDE ngoai
3. **Multi-provider AI:** Khong phu thuoc 1 nha cung cap AI duy nhat
4. **Bao mat API key:** Ma hoa Fernet, khong luu plaintext
5. **Customizable prompts:** Admin tuy chinh hanh vi AI tu database
6. **Contribution system:** Khuyen khich dong gop cong dong

---

# 15. HUONG PHAT TRIEN TUONG LAI

1. **Generate Testcase with AI** - Tu dong sinh test case tu de bai (DA DU KIEN, CHUA IMPLEMENT)
2. **AI Hint System** - Goi y giai thuat khi user bi ket
3. **AI Plagiarism Detection** - Phat hien gian lan bang AI (bo sung MOSS)
4. **HTTPS (Let's Encrypt)** - Bao mat SSL/TLS
5. **CI/CD Pipeline** - Tu dong test va deploy
6. **Mobile Responsive** - Toi uu cho mobile
7. **Performance Monitoring** - Grafana, Prometheus
8. **Multi-language support** - Them nhieu ngon ngu giao dien
9. **Organization Credits** - Hoan thien he thong tin dung
10. **Contest Analytics** - Phan tich sau ve ket qua thi

---

# 16. DANH SACH FILE QUAN TRONG

## 16.1. Configuration
| File | Mo ta |
|------|-------|
| `dmoj/docker-compose.yml` | Docker orchestration |
| `dmoj/repo/dmoj/settings.py` | Django settings (700+ dong) |
| `dmoj/repo/dmoj/local_settings.py` | Local deployment config |
| `dmoj/repo/dmoj/urls.py` | URL routing (543 dong) |
| `dmoj/config/uwsgi.ini` | uWSGI config (8 workers) |
| `dmoj/nginx/conf.d/nginx.conf` | Nginx reverse proxy |
| `dmoj/environment/site.env` | Environment variables |

## 16.2. AI Features (ALOJ moi)
| File | Dong | Mo ta |
|------|------|-------|
| `judge/models/ai_code_review.py` | 31 | Model AI review |
| `judge/models/ai_prompt.py` | 31 | Model prompt template |
| `judge/models/api_key.py` | 158 | Model API key + encryption |
| `judge/views/ai_code_review.py` | 249 | AI review logic |
| `judge/views/ai_problem_creator.py` | 239 | AI problem creation |
| `judge/views/api_key.py` | ~300 | API key management |
| `judge/admin/ai_api_key.py` | - | Admin AI key |
| `judge/admin/ai_code_review.py` | - | Admin AI review |
| `judge/admin/ai_prompt.py` | - | Admin prompt |

## 16.3. IDE Feature (ALOJ moi)
| File | Dong | Mo ta |
|------|------|-------|
| `judge/models/run_submission.py` | 56 | RunSubmission model |
| `judge/views/run.py` | 219 | IDE Run views (3 views) |
| `templates/problem/problem-ide.html` | - | IDE template |
| `judge/migrations/0225_*.py` | - | IDE migration |
| `judge/migrations/0226_*.py` | - | RunSubmission migration |

## 16.4. Core Application
| File | Dong (uoc tinh) | Mo ta |
|------|-----------------|-------|
| `judge/models/problem.py` | ~500 | Problem model |
| `judge/models/submission.py` | ~300 | Submission model |
| `judge/models/contest.py` | ~1000 (41KB) | Contest model |
| `judge/models/profile.py` | ~600 (24KB) | Profile model |
| `judge/views/problem.py` | ~1200 (48KB) | Problem views |
| `judge/views/contests.py` | ~1600 (64KB) | Contest views |
| `judge/views/submission.py` | ~1000 (40KB) | Submission views |
| `judge/views/organization.py` | ~800 (33KB) | Organization views |

## 16.5. Templates
| Directory | So file | Mo ta |
|-----------|---------|-------|
| `templates/problem/` | 22 | Problem pages |
| `templates/submission/` | 8 | Submission pages |
| `templates/contest/` | 23 | Contest pages |
| `templates/user/` | 18 | User pages |
| `templates/organization/` | ~10 | Organization pages |
| `templates/admin/` | ~15 | Admin overrides |
| **Tong cong** | **~232** | **Tat ca templates** |

---

# PHU LUC

## A. Cac ALOJ Settings rieng (trong settings.py)

```python
# Community
ALOJ_CP_COMMENT = 1              # Diem/comment vote
ALOJ_CP_TICKET = 10              # Diem/ticket tot
ALOJ_CP_PROBLEM = 20             # Diem/bai tap goi y

# Gioi han
ALOJ_ORGANIZATION_ADMIN_LIMIT = 3
ALOJ_PROBLEM_TIMELIMIT_LIMIT = 5  # giay
ALOJ_CONTEST_DURATION_LIMIT = 14  # ngay
ALOJ_TESTCASE_HARD_LIMIT = 100
ALOJ_TESTCASE_SOFT_LIMIT = 50
ALOJ_INTERACT_MIN_PROBLEM_COUNT = 5
ALOJ_BLOG_MIN_PROBLEM_COUNT = 10

# Comment
ALOJ_COMMENT_MIN_CONTRIBUTION = -20
ALOJ_COMMENT_MIN_LENGTH = 10
ALOJ_COMMENT_MAX_LENGTH = 10000

# Chong gian lan
ALOJ_SHOULD_BAN_FOR_CHEATING_IN_CONTESTS = False
ALOJ_MAX_DISQUALIFICATIONS_BEFORE_BANNING = 3

# Organization
ALOJ_IGNORED_ORGANIZATION_SUBDOMAINS = ['oj', 'www', 'localhost']
ALOJ_ENABLE_ORGANIZATION_CREDIT_LIMITATION = False

# Performance
ALOJ_LOW_POWER_MODE = False
ALOJ_LONG_QUEUE_ALERT_THRESHOLD = 10

# IDE
DMOJ_IDE_MAX_CUSTOM_TESTCASES = 3
DMOJ_IDE_MAX_CUSTOM_INPUT_LENGTH = 8192
DMOJ_IDE_MAX_OUTPUT_DISPLAY_LENGTH = 8192
DMOJ_IDE_MAX_SOURCE_LENGTH = 8192

# AI
AI_PROBLEM_CREATOR_MAX_FILE_SIZE = 10485760  # 10MB
AI_PROBLEM_CREATOR_ALLOWED_EXTS = {'pdf', 'png', 'jpg', 'jpeg', 'webp'}
```

## B. Contest Formats ho tro

| Format | File | Mo ta |
|--------|------|-------|
| Default | `judge/contest_format/default.py` | DMOJ standard |
| IOI | `judge/contest_format/ioi.py` | IOI format |
| ICPC | `judge/contest_format/icpc.py` | ICPC format |
| AtCoder | `judge/contest_format/atcoder.py` | AtCoder format |
| ECOO | `judge/contest_format/ecoo.py` | ECOO format |
| VNOJ | `judge/contest_format/vnoj.py` | Vietnam OJ format |
| Legacy IOI | `judge/contest_format/legacy_ioi.py` | IOI cu |

## C. Ngon ngu lap trinh ho tro

He thong ho tro 30+ ngon ngu thong qua Judge Server, bao gom:
C, C++ (11/14/17/20), Python (2/3), Java, Pascal, Ruby, Go, PHP, Perl, Haskell, Kotlin, Rust, C#, JavaScript, TypeScript, Swift, Scala, Lua, R, Assembly, va nhieu ngon ngu khac.

---

> **Luu y:** File nay duoc tao tu dong bang cach phan tich source code truc tiep.
> Tat ca thong tin la chinh xac tai thoi diem tao (2026-06-10).
> Khi viet bao cao, hay dien dat lai bang ngon ngu hoc thuat phu hop.
