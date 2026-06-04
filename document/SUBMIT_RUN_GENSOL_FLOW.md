# Tài liệu luồng SUBMIT / RUN / GENSOL (AI Generate Testcase)

> Tài liệu mô tả chi tiết 3 luồng chấm bài của hệ thống: **Submit** (nộp bài chính thức),
> **Run** (chạy thử trên IDE mới), và **GenSol** (sinh testcase bằng AI).
> Phạm vi code: `aloj-docker/dmoj/repo` (site Django + bridge) và `judge-server` (judge daemon).
>
> Nhánh hiện tại: `AI-feature-v1.1` — đang phát triển tính năng **Generate Testcase with AI**.

---

## 0. Bức tranh tổng thể (kiến trúc)

Hệ thống gồm 4 thành phần chạy trong Docker Compose:

```mermaid
flowchart LR
    Browser["Trình duyệt (site UI / IDE)"]
    Site["Site Django<br/>(views + judgeapi.py)"]
    Bridge["Bridge<br/>(DjangoHandler + JudgeList + JudgeHandler)"]
    Judge["Judge-server<br/>(packet.py + judge.py + cptbox sandbox)"]
    Celery["Celery worker<br/>(tasks/generate_testcase.py)"]
    Redis[("Redis<br/>broker + signal")]
    WS["wsevent daemon<br/>(WebSocket realtime)"]

    Browser -- HTTP POST --> Site
    Site -- "TCP packet (zlib)" --> Bridge
    Bridge -- "TCP packet (zlib)" --> Judge
    Judge -- "kết quả từng case (TCP)" --> Bridge
    Bridge -- "ghi DB + event.post" --> WS
    WS -- "WebSocket push" --> Browser
    Browser -. "fallback: polling HTTP" .-> Site
    Site -- "run_generate_testcase.delay()" --> Celery
    Celery -- "judgeapi → Bridge" --> Bridge
    Bridge -- "signal_gensol_done (LPUSH)" --> Redis
    Celery -- "BLPOP chờ tín hiệu" --> Redis
```

**Nguyên tắc chung của giao thức bridge ↔ judge:**

- Mọi packet được serialize bằng `json.dumps`, nén `zlib`, đóng khung bằng 4 byte độ dài (`struct '!I'`).
- Site → Bridge dùng kết nối TCP ngắn (request/reply) qua `judge_request()` trong
  [judgeapi.py](dmoj/repo/judge/judgeapi.py#L27).
- Bridge → Judge dùng kết nối TCP dài (persistent) do judge daemon chủ động mở tới bridge.
- Kết quả chấm đi **ngược** về: Judge → Bridge (`JudgeHandler`) → ghi DB + bắn `event.post` lên wsevent → trình duyệt.

---

## 1. Luồng SUBMIT (nộp bài chính thức)

Đây là luồng gốc của DMOJ, dùng làm nền cho 2 luồng còn lại.

### 1.1. Gửi đi — ai gửi, gửi gì, gửi đến đâu

| Bước | Thành phần | Hành động |
|------|-----------|-----------|
| 1 | Browser | `POST` form nộp bài (source + language) đến view nộp bài |
| 2 | Site `judge_submission()` | Reset trạng thái về `QU`, xoá `SubmissionTestCase` cũ, gửi packet `submission-request` tới bridge |
| 3 | Bridge `DjangoHandler.on_submission()` | Đẩy vào `JudgeList.judge()`, trả về `submission-received` |
| 4 | Bridge `JudgeHandler.submit()` | Gửi `submission-request` cho judge daemon |
| 5 | Judge `packet._receive_packet()` | Nhận, gọi `judge.begin_grading()` với `Submission(...)` |

Packet `submission-request` (Site → Bridge), xem
[judge_submission()](dmoj/repo/judge/judgeapi.py#L55):

```jsonc
{
  "name": "submission-request",
  "submission-id": 123,
  "problem-id": "aplusb",
  "language": "CPP17",
  "source": "<mã nguồn>",
  "judge-id": null,
  "banned-judges": ["judge2"],
  "priority": 0            // DEFAULT / CONTEST / REJUDGE / BATCH_REJUDGE
}
```

### 1.2. Nhận về — ai nhận, nhận gì

Judge daemon bắn các packet ngược về bridge. Bridge xử lý trong
[judge_handler.py](dmoj/repo/judge/bridge/judge_handler.py):

| Packet từ judge | Handler bridge | Tác động |
|-----------------|----------------|----------|
| `submission-processing` | `on_submission_processing` | `status='P'`, gán `judged_on` |
| `grading-begin` | `on_grading_begin` | `status='G'`, xoá `SubmissionTestCase`, `current_testcase=1` |
| `batch-begin` / `batch-end` | `on_batch_begin/end` | đánh dấu batch |
| `test-case-status` | `on_test_case` | tạo `SubmissionTestCase` cho từng case |
| `grading-end` | `on_grading_end` | tính điểm, `status='D'` |
| `compile-error` | `on_compile_error` | `status='CE'`, lưu log |
| `compile-message` | `on_compile_message` | lưu warning compiler |
| `internal-error` | `on_internal_error` | `status='IE'` |
| `submission-terminated` | `on_submission_terminated` | `status='AB'` |

Mỗi bước bridge `event.post('sub_<id_secret>', {...})` để trình duyệt cập nhật realtime; kết quả **lưu thẳng vào DB** (`Submission` + `SubmissionTestCase`).

---

## 2. Luồng RUN (chạy thử trên IDE mới)

Luồng RUN cho phép người dùng chạy code với **sample testcase** và **custom input** mà **không** lưu vào bảng `Submission` chính. Dùng model riêng `RunSubmission`.

### 2.1. Gửi đi

```mermaid
sequenceDiagram
    participant B as Browser (IDE)
    participant V as RunSubmitView
    participant API as judge_run_submission()
    participant DH as DjangoHandler
    participant JL as JudgeList
    participant JH as JudgeHandler
    participant J as Judge-server

    B->>V: POST /problem/{code}/run {source, language, custom_inputs[]}
    V->>V: Validate (login, enable_new_ide, quyền, ban, rate-limit, độ dài)
    V->>API: judge_run_submission(run_sub, sample_input_files, custom_inputs)
    API->>DH: packet "run-request"
    DH->>JL: judge_run(...)
    DH-->>API: "run-received"
    JL->>JH: run_submit(...)
    JH->>J: packet "submission-request" (meta đặc biệt)
    J-->>JH: submission-received
```

**View** [RunSubmitView.post()](dmoj/repo/judge/views/run.py#L16) kiểm tra:

- Đăng nhập (`LoginRequiredMixin`).
- `prob.enable_new_ide` phải bật, nếu không → `403`.
- `prob.is_accessible_by(user)`; user không bị `banned_users`.
- **Rate limit**: tổng số `Submission` pending + `RunSubmission` pending `< DMOJ_SUBMISSION_LIMIT`, nếu không → `429`.
- `source` ≤ `DMOJ_IDE_MAX_SOURCE_LENGTH`.
- Ngôn ngữ hợp lệ và nằm trong `allowed_languages`.
- Problem phải có **sample testcase** (`is_sample=True, type='C'`), nếu không → `400`.
- `custom_inputs` là list, tối đa `DMOJ_IDE_MAX_CUSTOM_TESTCASES`, mỗi phần tử ≤ `DMOJ_IDE_MAX_CUSTOM_INPUT_LENGTH`.

Packet `run-request` (Site → Bridge), xem
[judge_run_submission()](dmoj/repo/judge/judgeapi.py#L115):

```jsonc
{
  "name": "run-request",
  "submission-id": 45,
  "problem-id": "aplusb",
  "language": "CPP17",
  "source": "<mã nguồn>",
  "judge-id": null,
  "banned-judges": [],
  "priority": 0,
  "sample-input-files": ["aplusb/1.in", ...],   // tên file input của sample
  "custom-inputs": ["3 5\n", "10 20\n", ...]      // input người dùng tự nhập
}
```

Bridge `JudgeHandler.run_submit()` gửi tới judge bằng packet **`submission-request`** (tái dùng giao thức gốc) với `meta` đặc biệt:

```jsonc
"meta": {
  "sample-testcase-only": true,
  "sample-input-files": [...],
  "custom-inputs": [...],
  "run-output-limit": N      // giới hạn độ dài output bắt về IDE
}
```

### 2.2. Xử lý phía judge-server

Trong [judge.py `_grade_cases()`](../judge-server/dmoj/judge.py#L489):

- Nếu `sample-testcase-only=true`: lọc `flattened_cases`, chỉ giữ case có `config['in']` nằm trong `sample-input-files`.
- Với mỗi `custom-inputs`: tạo **virtual TestCase trong RAM** — `virtual_case._input_data_io = MemoryIO(prefill=..., seal=True)` (không ghi đĩa).
- `run-output-limit > 0` → ghi đè `output_prefix_length` để IDE lấy được output đầy đủ.

### 2.3. Nhận về

Bridge phát hiện `self._is_run = True` và xử lý song song với submit, nhưng:

- **Không** ghi `SubmissionTestCase`; thay vào đó gom kết quả vào list `self._run_test_cases` rồi lưu JSON vào `RunSubmission.case_results`.
- `event.post('run_<id_secret>', {...})` ở từng giai đoạn: `processing`, `grading-begin`, `test-case`, `grading-end`, `compile-error`, `compile-message`, `internal-error`, `aborted`.

Mỗi phần tử trong `case_results`:

```jsonc
{
  "case": 1,
  "status": "AC",            // AC/WA/TLE/MLE/OLE/RTE/IR/SC
  "time": 0.01,
  "memory": 1234,
  "feedback": "...",
  "extended_feedback": "...",
  "output": "<stdout thực tế>"
}
```

### 2.4. Frontend nhận kết quả

- Ưu tiên **wsevent**: `event_dispatcher.on('run_' + runSecret, onRunEvent)`.
- Fallback **polling**: `GET /run/poll/{run_id}` → [RunPollView](dmoj/repo/judge/views/run.py#L112) trả JSON:

| Trường | Ý nghĩa |
|--------|---------|
| `status` | `PENDING` / `done` / `CE` / `IE` |
| `grading_status` | trạng thái nội bộ khi đang chạy (`QU`/`P`/`G`) |
| `result` | kết quả tổng (khi `D`) |
| `time`, `memory` | tài nguyên |
| `passed`, `total_cases` | số case đúng / tổng |
| `testcases[]` | danh sách case như trên |
| `error` | log compile/internal error |

---

## 3. Luồng GENSOL (Generate Testcase with AI) — luồng đang phát triển

Mục tiêu: sinh testcase tự động bằng cách (1) gọi AI sinh **generator code**, (2) chạy generator trên judge để tạo input, (3) chạy **solution code** để tạo output đúng, (4) đóng gói thành zip Themis và import vào problem.

> ⚠️ Trạng thái hiện tại (nhánh `AI-feature-v1.1`): các bước **(4) zip + (6) import đang bị comment** lại
> (chờ thêm popup xác nhận ở frontend). Output cũng **chưa được dọn** (`cleanup_output_files()` bị comment để debug).
> Đây là **MVP đang dev**, không phải bản hoàn chỉnh.

### 3.1. Tổng quan các bước

```mermaid
sequenceDiagram
    participant B as Browser
    participant V as ai_testcase_generator (view)
    participant AI as AI Provider (OpenAI/Gemini/Claude/DeepSeek)
    participant C as Celery: run_generate_testcase
    participant API as judge_gensol_submission()
    participant BR as Bridge
    participant J as Judge-server
    participant R as Redis

    B->>V: POST .../ai_generate/process {provider, model, num_cases}
    V->>AI: _call_text_api(system_prompt, problem.description)
    AI-->>V: generator_code
    V-->>B: {generator_code, job_id} (status=Draft)
    B->>V: POST .../ai_generate/apply {generator_code, solution_code, langs}
    V->>C: run_generate_testcase.delay(job_id)
    V-->>B: {job_id, id_secret}

    Note over C: Bước GEN
    C->>API: GenSolSubmission(type=GEN, custom_inputs=[''*num_cases])
    API->>BR: packet "gensol-request"
    BR->>J: packet "gensol-request" (meta gensol-stop-on-error)
    J-->>BR: kết quả từng case (output = input đề bài)
    BR->>R: signal_gensol_done(id, 'D')
    C->>R: BLPOP chờ tín hiệu
    C->>C: đọc output từ file → test_inputs[]

    Note over C: Bước SOL
    C->>API: GenSolSubmission(type=SOL, custom_inputs=test_inputs)
    API->>BR: packet "gensol-request"
    BR->>J: packet "gensol-request"
    J-->>BR: kết quả (output = đáp án)
    BR->>R: signal_gensol_done(id, 'D')
    C->>C: đọc output → test_outputs[]
    C->>B: event "done" (qua wsevent gentc_<id_secret>)
```

### 3.2. Giai đoạn AI (gọi LLM)

[ai_testcase_generator.py](dmoj/repo/judge/views/ai_testcase_generator.py):

- `ai_generate_testcase_process` (POST): kiểm tra `is_editable_by(user)`, lấy `AIAPIKey` đã `verified`, giải mã key (Fernet),
  gọi `_call_text_api()` với `GENERATOR_SYSTEM_PROMPT` + mô tả problem. Lưu job `status='DR'` (Draft).
- `ai_generate_testcase_apply` (POST): nhận `generator_code` + `solution_code` + ngôn ngữ → tạo job mới và gọi
  `run_generate_testcase.delay(job.id)` (Celery).
- `ai_generate_testcase_poll` (GET): fallback poll trạng thái job.

**Giới hạn AI:**

- `num_cases`: kẹp trong `[1, MAX_CASES_LIMIT=40]`.
- Timeout gọi API: `_AI_TIMEOUT = 120s`.
- Prompt yêu cầu generator: không đọc stdin, in đúng 1 testcase ra stdout, mỗi case < 1MB, random theo thời gian.
- API key được mã hoá bằng **Fernet** dẫn xuất từ `SECRET_KEY` (`key_ciphertext`), plaintext không lưu lại; chỉ lưu `last4`.

### 3.3. Celery task — orchestrator

[run_generate_testcase()](dmoj/repo/judge/tasks/generate_testcase.py#L153) chạy tuần tự:

| Status job | Giai đoạn |
|------------|-----------|
| `CG` | Compiling Generator |
| `RG` | Running Generator (`num_cases` lần, mỗi lần input rỗng) |
| `CS` | Compiling Solution |
| `RS` | Running Solution (input = output của generator) |
| `ZP` | Zipping *(đang comment)* |
| `IM` | Importing *(đang comment)* |
| `DN` | Done |
| `ER` | Error (kèm `error_stage`, `error_log`) |

Mỗi giai đoạn `event.post('gentc_<id_secret>', {...})` để frontend cập nhật.

**Cơ chế chờ kết quả (điểm mấu chốt):** task dùng **Redis BLPOP** thay vì poll DB —
xem [gensol_signal.py](dmoj/repo/judge/utils/gensol_signal.py):

- Bridge khi chấm xong gọi `signal_gensol_done(id, status)` → `LPUSH gensol_done:<id>`.
- Celery gọi `wait_for_gensol(id, timeout=300)` → `BLPOP` (race-free: nếu signal đã đẩy trước thì trả ngay).
- Hết timeout (`WAIT_TIMEOUT=300s`) → coi như judge treo, fail giai đoạn.

### 3.4. Packet GENSOL

`judge_gensol_submission()` gửi packet `gensol-request` (Site → Bridge):

```jsonc
{
  "name": "gensol-request",
  "submission-id": 78,
  "problem-id": "aplusb",
  "language": "CPP17",
  "source": "<generator hoặc solution code>",
  "type": "GEN",                 // hoặc "SOL"
  "custom-inputs": ["", "", ...] // GEN: rỗng; SOL: các input do generator sinh
}
```

Bridge `gensol_submit()` chuyển thành packet `gensol-request` cho judge với `meta` giống RUN
(`sample-testcase-only=true`, `custom-inputs`, `run-output-limit` = `output_limit` problem hoặc mặc định 2MB).

Judge-server [packet.py](../judge-server/dmoj/packet.py#L280) xử lý `gensol-request`:

- Inject `meta['gensol-stop-on-error'] = True`.
- `short_circuit=False`, `scoring_mode='partial_testcase'`.
- Trong [_grade_cases()](../judge-server/dmoj/judge.py#L616): **dừng ngay** khi gặp `TLE | MLE | OLE | RTE`
  (khác RUN — RUN chạy hết mọi case).

### 3.5. Lưu kết quả GENSOL

Khác RUN/Submit: output **không lưu DB** mà ghi **file** để tránh phình DB.
Xem [_on_gensol_grading_end()](dmoj/repo/judge/bridge/judge_handler.py#L754):

- Output mỗi case ghi vào `/problems/generate_testcase/<gensol_id>/case_<n>.out`
  (thư mục chia sẻ giữa site, celery, bridge).
- DB chỉ lưu metadata nhẹ `case_statuses` (JSON list): `{case, status, time, memory}`.
- `GenSolSubmission.read_case_output(case_num)` để Celery đọc lại output.

Sau khi chấm xong, bridge bắn signal + event ở mọi nhánh kết thúc:

| Tình huống | status signal | event wsevent |
|-----------|---------------|---------------|
| Chấm xong | `D` | `grading-end` |
| Compile error | `CE` | `compile-error` |
| Internal error / ghi file lỗi | `IE` | `internal-error` |
| Abort | `AB` | `aborted` |
| Bridge shutdown khi đang chấm | `IE` | — |

### 3.6. Celery đọc kết quả & kiểm tra lỗi

[_check_gensol_result()](dmoj/repo/judge/tasks/generate_testcase.py#L95):

- `status='CE'` → "Compile error"; `status='IE'` → "Internal error"; khác `'D'` → "Unexpected status".
- Duyệt `case_statuses`: nếu có `TLE/MLE/OLE/RTE/IR/SC` → fail kèm số thứ tự case.
- Nếu số kết quả < số case kỳ vọng → "short-circuited?".
- Đọc output từng file qua `read_case_output`; thiếu file → fail.

---

## 4. Bảng tổng hợp giới hạn & mã trạng thái

### 4.1. Settings giới hạn (settings.py)

| Setting | Giá trị | Áp dụng |
|---------|---------|---------|
| `DMOJ_IDE_MAX_CUSTOM_TESTCASES` | 3–5 | Số custom input tối đa (RUN) |
| `DMOJ_IDE_MAX_CUSTOM_INPUT_LENGTH` | 8192–65536 | Độ dài 1 custom input |
| `DMOJ_IDE_MAX_OUTPUT_DISPLAY_LENGTH` | 8192 | Độ dài output hiển thị |
| `DMOJ_IDE_MAX_SOURCE_LENGTH` | 8192–65536 | Độ dài source (RUN) |
| `DMOJ_SUBMISSION_LIMIT` | — | Số bài pending tối đa / user |
| `MAX_CASES_LIMIT` / `MAX_CASES` | 40 | Số testcase AI sinh tối đa |
| `MAX_ZIP_SIZE` | 128 MB | Zip testcase tối đa *(chưa dùng)* |
| `WAIT_TIMEOUT` | 300s | Chờ judge cho 1 GenSol |
| `_AI_TIMEOUT` | 120s | Timeout gọi LLM |
| `run-output-limit` | 2 MB mặc định | Độ dài output bắt về (RUN/GENSOL) |
| `GenSolSubmission.source` | 65536 | max_length cột source |

### 4.2. Mã trạng thái (status) submission

`QU` Queued · `P` Processing · `G` Grading · `D` Done · `CE` Compile Error ·
`IE` Internal Error · `AB` Aborted.
`IN_PROGRESS_GRADING_STATUS = ('QU', 'P', 'G')`.

### 4.3. Mã kết quả testcase (result_flag → chữ)

Bitmask trong [on_test_case](dmoj/repo/judge/bridge/judge_handler.py#L964):

| Bit | Chữ | Ý nghĩa |
|-----|-----|---------|
| `&4` | TLE | Time Limit Exceeded |
| `&8` | MLE | Memory Limit Exceeded |
| `&64` | OLE | Output Limit Exceeded |
| `&2` | RTE | Runtime Error |
| `&16` | IR | Invalid Return |
| `&1` | WA | Wrong Answer |
| `&32` | SC | Short Circuited (case trước fail) |
| `0` | AC | Accepted |

### 4.4. Status job GenerateTestcaseJob

`DR` Draft · `QU` Queued · `AI` AI Generating · `CG` Compiling Generator · `RG` Running Generator ·
`CS` Compiling Solution · `RS` Running Solution · `ZP` Zipping · `IM` Importing · `DN` Done · `ER` Error.

### 4.5. Kênh wsevent

| Luồng | Kênh | Sinh secret |
|-------|------|-------------|
| Submit | `sub_<id_secret>` | `Submission.get_id_secret` |
| Run | `run_<id_secret>` | HMAC-SHA512(`EVENT_DAEMON_RUN_KEY`, `run_<id>`) |
| GenSol | `gensol_<id_secret>` | HMAC-SHA512(`EVENT_DAEMON_RUN_KEY`, `gensol_<id>`) |
| GenTC job | `gentc_<id_secret>` | UUID4 (`GenerateTestcaseJob.id_secret`) |

### 4.6. Định tuyến packet ở bridge (`JudgeList`)

Để tránh đụng ID giữa 3 loại, `submission_map` dùng key qua
[`_key()`](dmoj/repo/judge/bridge/judge_list.py#L36):

- Submit → `id` (số nguyên)
- Run → `('run', id)`
- GenSol → `('gensol', id)`

Cờ phân biệt trên `JudgeHandler`: `_is_run`, `_is_gensol` (không dùng cache).

---

## 5. Phân tích nhánh & hướng đi

### 5.1. Tình trạng git

- Nhánh hiện tại: **`AI-feature-v1.1`** (đã push lên `origin`).
- Lịch sử: `AI-feature-v1` (MVP Create Problem + Create Testcase) → `AI-feature-v1.1` (cập nhật Generate Testcase).
- File đang sửa dở (chưa commit):
  - `judge/bridge/judge_handler.py` — thêm `signal_gensol_done` ở mọi điểm kết thúc, đổi RUN-style `submission-request` sang packet `gensol-request` riêng.
  - `judge/tasks/generate_testcase.py` — chuyển từ poll DB sang chờ Redis BLPOP; comment tạm bước zip + import.
  - `judge/utils/gensol_signal.py` *(file mới, chưa add)* — tiện ích signal Redis.

→ Đang phát triển: **chấm generator/solution trên judge sandbox thật để sinh testcase**, dùng Redis làm tín hiệu hoàn tất.

### 5.2. Những điểm ĐÃ ỔN 👍

1. **Tách model rõ ràng.** `RunSubmission` và `GenSolSubmission` tách khỏi `Submission` → không làm bẩn dữ liệu nộp bài thật, không ảnh hưởng bảng xếp hạng.
2. **Tái dùng giao thức judge.** GenSol/Run đi qua đúng pipeline cptbox sandbox → code AI sinh chạy trong môi trường cô lập, an toàn.
3. **Bỏ polling DB, dùng Redis BLPOP.** Race-free, ít tải DB, phản hồi nhanh hơn vòng lặp `sleep`.
4. **Output ra file thay vì DB.** Tránh phình bảng với output lớn (đúng hướng cho 40 case × tới ~MB).
5. **`gensol-stop-on-error`.** Dừng sớm khi generator/solution TLE/MLE/RTE → tiết kiệm tài nguyên judge.
6. **Bảo mật cơ bản tốt.** API key mã hoá Fernet, kiểm tra `is_editable_by`, chỉ dùng key `verified`, `_safe_json` chống XSS, plaintext key không lưu.
7. **Có cơ chế signal ở mọi nhánh kết thúc** (CE/IE/AB/shutdown) → Celery không bị treo vô hạn nhờ timeout.

### 5.3. RỦI RO / cần lưu ý ⚠️

| Mức | Rủi ro | Vị trí |
|-----|--------|--------|
| 🔴 Cao | **Phụ thuộc judge-server đã được sửa.** `gensol-request` chỉ tồn tại trong thư mục `judge-server/`. Nếu container judge đang chạy là bản DMOJ gốc (không có nhánh này), packet sẽ rơi vào `Unknown packet` và **không bao giờ chấm** → Celery treo tới 300s rồi fail. Cần đảm bảo build/deploy đúng image judge. | [packet.py#L280](../judge-server/dmoj/packet.py#L280) |
| 🔴 Cao | **Rò rỉ đĩa.** `cleanup_output_files()` bị comment → mỗi job để lại file output trong `/problems/generate_testcase/`. Chạy nhiều sẽ đầy đĩa shared volume. | [generate_testcase.py](dmoj/repo/judge/tasks/generate_testcase.py) |
| 🟠 TB | **Chiếm judge lâu.** Mỗi job nối tiếp 2 lần chấm (GEN rồi SOL), mỗi lần tối đa 40 case, block một judge slot. Nhiều người dùng đồng thời có thể làm nghẽn hàng đợi chấm bài thật. Chưa thấy ưu tiên/giới hạn riêng cho GenSol. | task + `priority=DEFAULT_PRIORITY` |
| 🟠 TB | **Source AI có thể vượt 65536.** View `apply` không kiểm tra độ dài `generator_code`/`solution_code` trước khi lưu cột `source` (max 65536) → có thể lỗi DB. | view apply |
| 🟠 TB | **`custom-inputs` lớn qua packet.** SOL gửi toàn bộ input do generator sinh (tới 40 × ~MB) trong 1 packet zlib qua TCP. Payload lớn có thể chậm/đầy bộ nhớ bridge. | `judge_gensol_submission` |
| 🟠 TB | **Không xác thực generator độc hại logic.** Generator/solution là code do LLM sinh nhưng vẫn do người dùng (editor problem) cung cấp/sửa. Sandbox chặn được phá hoại hệ thống, nhưng output sai/vô nghĩa vẫn được đóng gói thành testcase nếu bật bước import. | toàn luồng |
| 🟡 Thấp | **Timeout cứng 300s** không tỉ lệ theo `num_cases` × time-limit. Bài có TL lớn + 40 case có thể vượt 300s dù judge vẫn chạy đúng. | `WAIT_TIMEOUT` |
| 🟡 Thấp | **`_get_redis()` mặc định DB index 1** trùng broker Celery. Lẫn key `gensol_done:*` với dữ liệu Celery (ít rủi ro nhưng nên tách DB/namespace). | gensol_signal.py |
| 🟡 Thấp | **Bước import chưa bật** → tính năng hiện chỉ sinh + xem, chưa thực sự ghi testcase vào problem. Cần hoàn thiện popup xác nhận. | task (comment) |

### 5.4. GỢI Ý hướng đi (mức "đủ tốt", không cần hoàn hảo)

Ưu tiên theo thứ tự:

1. **Chốt việc deploy judge-server có `gensol-request`** (rủi ro cao nhất). Thêm 1 test khói: gửi `gensol-request` và assert nhận `gensol-received`. Nếu judge cũ, fallback rõ ràng (báo lỗi "judge không hỗ trợ GenSol") thay vì treo 300s.
2. **Bật lại `cleanup_output_files()`** sau khi Celery đọc xong output (hoặc thêm cron dọn thư mục cũ > N giờ). Tránh đầy đĩa.
3. **Validate độ dài `generator_code`/`solution_code`** ở view `apply` (ví dụ ≤ 65536) trước khi tạo `GenSolSubmission`.
4. **Giới hạn đồng thời cho GenSol**: hàng đợi/priority riêng hoặc khoá "1 job GenSol đang chạy / user" để không nuốt judge của chấm bài thật. Đơn giản nhất: kiểm tra user đã có job `status` đang chạy thì chặn.
5. **Timeout động**: `WAIT_TIMEOUT = base + num_cases * time_limit * hệ_số`. Tránh false-timeout.
6. **Tách Redis DB/namespace** cho signal (ví dụ key prefix riêng + DB index riêng) để không lẫn với Celery.
7. **Hoàn thiện bước import có xác nhận**: giữ đúng kế hoạch popup, đóng gói zip Themis, dùng `transaction.atomic` (code mẫu đã có sẵn dạng comment — chỉ cần bật và test).
8. **Giới hạn kích thước mỗi case sinh ra** (kiểm tra độ dài output trước khi nhận làm input cho SOL), thay vì chỉ "nhờ" prompt AI giữ < 1MB.

Tóm lại: kiến trúc đang đi **đúng hướng** (tách model, tái dùng sandbox, signal Redis). Việc còn lại chủ yếu là **đóng kín các đầu hở vận hành** (dọn file, giới hạn tài nguyên, đảm bảo judge tương thích) và **bật nốt bước import có xác nhận** để hoàn thiện MVP.

---

## 6. Tham chiếu nhanh file

| Vai trò | File |
|---------|------|
| View RUN | [judge/views/run.py](dmoj/repo/judge/views/run.py) |
| View AI GenTC | [judge/views/ai_testcase_generator.py](dmoj/repo/judge/views/ai_testcase_generator.py) |
| Celery task GenSol | [judge/tasks/generate_testcase.py](dmoj/repo/judge/tasks/generate_testcase.py) |
| Tín hiệu Redis | [judge/utils/gensol_signal.py](dmoj/repo/judge/utils/gensol_signal.py) |
| API gửi tới bridge | [judge/judgeapi.py](dmoj/repo/judge/judgeapi.py) |
| Bridge nhận từ site | [judge/bridge/django_handler.py](dmoj/repo/judge/bridge/django_handler.py) |
| Bridge điều phối | [judge/bridge/judge_list.py](dmoj/repo/judge/bridge/judge_list.py) |
| Bridge ↔ judge | [judge/bridge/judge_handler.py](dmoj/repo/judge/bridge/judge_handler.py) |
| Judge nhận packet | [judge-server/dmoj/packet.py](../judge-server/dmoj/packet.py) |
| Judge chấm case | [judge-server/dmoj/judge.py](../judge-server/dmoj/judge.py) |
| Model RunSubmission | judge/models/run_submission.py |
| Model GenSolSubmission | [judge/models/gensol_submission.py](dmoj/repo/judge/models/gensol_submission.py) |
| Model GenerateTestcaseJob | [judge/models/generate_testcase.py](dmoj/repo/judge/models/generate_testcase.py) |
