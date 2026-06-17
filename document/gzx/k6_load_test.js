import http from 'k6/http';
import { sleep, check } from 'k6';
import { Trend, Counter, Rate } from 'k6/metrics';

// Custom metrics
const homeLatency = new Trend('home_latency', true);
const problemsLatency = new Trend('problems_latency', true);
const contestsLatency = new Trend('contests_latency', true);
const errorRate = new Rate('error_rate');

const BASE = 'http://localhost';

export const options = {
    scenarios: {
        light: {
            executor: 'constant-vus',
            vus: __ENV.VUS ? parseInt(__ENV.VUS) : 50,
            duration: __ENV.DURATION || '1m',
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<10000'],
    },
};

export default function () {
    // Trang chủ
    let r1 = http.get(`${BASE}/`);
    homeLatency.add(r1.timings.duration);
    let ok1 = check(r1, { 'home 2xx': (r) => r.status >= 200 && r.status < 400 });
    errorRate.add(!ok1);

    // Danh sách bài tập
    let r2 = http.get(`${BASE}/problems/`);
    problemsLatency.add(r2.timings.duration);
    let ok2 = check(r2, { 'problems 2xx': (r) => r.status >= 200 && r.status < 400 });
    errorRate.add(!ok2);

    // Danh sách contest
    let r3 = http.get(`${BASE}/contests/`);
    contestsLatency.add(r3.timings.duration);
    let ok3 = check(r3, { 'contests 2xx': (r) => r.status >= 200 && r.status < 400 });
    errorRate.add(!ok3);

    sleep(1);
}
