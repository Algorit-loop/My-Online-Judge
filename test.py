#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BKDNOJ Sanity Test — kiểm tra sức khỏe toàn hệ thống.

Cách chạy:   python3 test.py
Đặc điểm:    100% READ-ONLY — không ghi database, không tạo file,
             không thay đổi bất kỳ trạng thái nào của hệ thống.
             Kết quả in ra terminal, exit code != 0 nếu có check FAIL.

Chỉ dùng Python stdlib, không cần cài thêm gì.
"""

import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE_URL = 'http://localhost'
HTTP_TIMEOUT = 15  # giây

EXPECTED_CONTAINERS = [
    'bkdnoj_mysql',
    'bkdnoj_redis',
    'bkdnoj_site',
    'bkdnoj_celery',
    'bkdnoj_bridged',
    'bkdnoj_wsevent',
    'bkdnoj_nginx',
]

# Các trang public quan trọng — chỉ GET, không đăng nhập, không POST.
HTTP_PAGES = [
    ('/', 'Trang chủ'),
    ('/problems/', 'Danh sách bài tập'),
    ('/contests/', 'Danh sách contest'),
    ('/submissions/', 'Danh sách submission'),
    ('/users/', 'Bảng xếp hạng user'),
    ('/organizations/', 'Danh sách tổ chức'),
    ('/status/', 'Trạng thái judge'),
    ('/accounts/login/', 'Trang đăng nhập'),
]

# ---------------------------------------------------------------------------
# Tiện ích chung
# ---------------------------------------------------------------------------

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
RESET = '\033[0m'

results = []  # list of (name, ok, detail, seconds)


def check(name):
    """Decorator: chạy 1 check, đo thời gian, gom kết quả, in ngay ra terminal."""
    def wrap(fn):
        def run():
            start = time.time()
            try:
                detail = fn() or ''
                ok = True
            except Exception as e:
                detail = str(e).strip() or type(e).__name__
                ok = False
            elapsed = time.time() - start
            results.append((name, ok, detail, elapsed))
            mark = f'{GREEN}PASS{RESET}' if ok else f'{RED}FAIL{RESET}'
            line = f'  [{mark}] {name} ({elapsed:.2f}s)'
            if detail:
                line += f'\n         → {detail}'
            print(line, flush=True)
        return run
    return wrap


def sh(cmd, timeout=30):
    """Chạy lệnh shell, trả stdout; raise nếu lỗi."""
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip()[:300] or f'exit code {p.returncode}')
    return p.stdout.strip()


def http_get(path, expect=(200,)):
    """GET một URL, trả (status, body). Raise nếu status không như mong đợi."""
    req = urllib.request.Request(BASE_URL + path, headers={'User-Agent': 'bkdnoj-sanity-test'})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            status, body = resp.status, resp.read()
    except urllib.error.HTTPError as e:
        status, body = e.code, b''
    except Exception as e:
        raise RuntimeError(f'{path}: không kết nối được ({e})')
    if status not in expect:
        raise RuntimeError(f'{path}: HTTP {status} (mong đợi {expect})')
    return status, body


def django_eval(code):
    """Chạy đoạn python READ-ONLY bên trong container site (Django ORM)."""
    full = (
        'import os, django\n'
        "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dmoj.settings')\n"
        'django.setup()\n' + code
    )
    return sh(f'docker exec bkdnoj_site python -c {shell_quote(full)}', timeout=60)


def shell_quote(s):
    return "'" + s.replace("'", "'\\''") + "'"


# ---------------------------------------------------------------------------
# Các check
# ---------------------------------------------------------------------------

@check('Docker: 7 container BKDNOJ đang chạy')
def check_containers():
    out = sh("docker ps --format '{{.Names}}'")
    running = set(out.splitlines())
    missing = [c for c in EXPECTED_CONTAINERS if c not in running]
    if missing:
        raise RuntimeError(f'Container không chạy: {", ".join(missing)}')
    return f'{len(EXPECTED_CONTAINERS)}/7 container Up'


@check('Docker: có ít nhất 1 judge container đang chạy')
def check_judge_container():
    out = sh("docker ps --format '{{.Names}}'")
    judges = [n for n in out.splitlines() if 'judge' in n.lower()]
    if not judges:
        raise RuntimeError('Không thấy container judge nào (vd: ultra_speed_judge_01)')
    return ', '.join(judges)


@check('Redis: phản hồi PING')
def check_redis():
    out = sh('docker exec bkdnoj_redis redis-cli ping', timeout=15)
    if out != 'PONG':
        raise RuntimeError(f'Redis trả về "{out}" thay vì PONG')
    return 'PONG'


@check('Database: kết nối MariaDB qua Django ORM')
def check_database():
    out = django_eval(
        'from django.db import connection\n'
        'with connection.cursor() as c:\n'
        "    c.execute('SELECT 1')\n"
        "print('OK')\n"
    )
    if 'OK' not in out:
        raise RuntimeError(out[:200])
    return 'SELECT 1 thành công'


@check('Django: dữ liệu đọc được (Problem / User / Submission)')
def check_django_data():
    out = django_eval(
        'from judge.models import Problem, Profile, Submission\n'
        "print(f'{Problem.objects.count()} problems, "
        "{Profile.objects.count()} users, "
        "{Submission.objects.count()} submissions')\n"
    )
    return out.splitlines()[-1]


@check('Judge: có judge đang online (kết nối qua bridge)')
def check_judge_online():
    out = django_eval(
        'from judge.models import Judge\n'
        "names = list(Judge.objects.filter(online=True).values_list('name', flat=True))\n"
        "print('|'.join(names) if names else 'NONE')\n"
    )
    last = out.splitlines()[-1]
    if last == 'NONE':
        raise RuntimeError('Không có judge nào online — kiểm tra judge container và bridged')
    return f'Online: {last.replace("|", ", ")}'


@check('Celery: worker phản hồi ping')
def check_celery():
    out = sh('docker exec bkdnoj_celery celery -A dmoj_celery inspect ping -t 10', timeout=40)
    if 'pong' not in out:
        raise RuntimeError(out[:200])
    nodes = [l for l in out.splitlines() if 'node' in l and 'online' in l]
    return nodes[-1].strip() if nodes else 'pong'


@check('Bridge: cổng 9998 (site→bridge) và 9999 (judge→bridge) mở')
def check_bridge_ports():
    for port in (9998, 9999):
        try:
            with socket.create_connection(('localhost', port), timeout=5):
                pass
        except OSError as e:
            raise RuntimeError(f'Cổng {port} không kết nối được: {e}')
    return 'TCP 9998, 9999 OK'


@check('HTTP: các trang chính trả về 200')
def check_http_pages():
    slow = []
    for path, label in HTTP_PAGES:
        start = time.time()
        http_get(path)
        t = time.time() - start
        if t > 5:
            slow.append(f'{path} ({t:.1f}s)')
    detail = f'{len(HTTP_PAGES)} trang OK'
    if slow:
        detail += f' — CHẬM: {", ".join(slow)}'
    return detail


@check('HTTP: static file được nginx phục vụ')
def check_static():
    # Lấy 1 file css/js thật từ HTML trang chủ rồi thử tải — không hardcode tên file.
    _, body = http_get('/')
    html = body.decode('utf-8', errors='replace')
    import re
    m = re.search(r'["\'](/static/[^"\']+\.(?:css|js))["\']', html)
    if not m:
        raise RuntimeError('Không tìm thấy link /static/ nào trong trang chủ')
    path = m.group(1)
    http_get(path)
    return path


@check('WebSocket: endpoint /event/ hoạt động')
def check_websocket():
    # GET thường vào endpoint WS sẽ bị từ chối upgrade (HTTP 426) — thế là server sống.
    # 502/504 hoặc không kết nối được mới là chết.
    http_get('/event/', expect=(400, 405, 426))
    return 'wsevent phản hồi (HTTP 426 Upgrade Required là bình thường)'


@check('Polling fallback: /channels/ tới được wsevent daemon')
def check_polling_fallback():
    # Daemon (websocket/daemon.js) yêu cầu path bắt đầu bằng /channels/:
    # GET /channels/ (không có tên channel) phải trả 400 Bad Request từ daemon.
    # Nếu trả 404 nghĩa là nginx proxy_pass đang cắt mất prefix /channels/
    # trước khi chuyển tới daemon -> polling fallback (khi WebSocket fail) bị hỏng.
    status, _ = http_get('/channels/', expect=(400,))
    return 'daemon nhận đúng path /channels/ (HTTP 400 khi thiếu tên channel)'


@check('Nginx: không trả trang lỗi 502')
def check_no_502():
    _, body = http_get('/')
    if b'502' in body[:500] and b'Bad Gateway' in body:
        raise RuntimeError('Trang chủ đang là trang 502')
    return 'Trang chủ render bình thường'


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

ALL_CHECKS = [
    check_containers,
    check_judge_container,
    check_redis,
    check_database,
    check_django_data,
    check_judge_online,
    check_celery,
    check_bridge_ports,
    check_http_pages,
    check_static,
    check_websocket,
    check_polling_fallback,
    check_no_502,
]


def main():
    print(f'{BOLD}=== BKDNOJ Sanity Test ==={RESET}')
    print(f'Target: {BASE_URL}  |  {len(ALL_CHECKS)} checks  |  read-only\n')
    start = time.time()

    for fn in ALL_CHECKS:
        fn()

    total = time.time() - start
    passed = sum(1 for _, ok, _, _ in results if ok)
    failed = len(results) - passed

    print(f'\n{BOLD}=== Kết quả ==={RESET}')
    if failed == 0:
        print(f'{GREEN}{BOLD}✔ {passed}/{len(results)} checks PASS{RESET} — hệ thống khỏe ({total:.1f}s)')
    else:
        print(f'{RED}{BOLD}✘ {failed}/{len(results)} checks FAIL{RESET} ({total:.1f}s):')
        for name, ok, detail, _ in results:
            if not ok:
                print(f'  {RED}- {name}{RESET}: {detail}')
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
