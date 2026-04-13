# ALOJ Frontend – AI Agent Reference

> Concise reference for AI agents working on the ALOJ (DMOJ-based) online judge frontend.

## Project Stack

| Layer | Tech |
|-------|------|
| Backend | Django (Jinja2 templates) |
| CSS | SCSS → sass → postcss/autoprefixer → CSS |
| JS | jQuery 3.4.1, vanilla JS (no bundler) |
| Realtime | WebSocket via `wsevent` service |
| Charts | Chart.js |
| Icons | FontAwesome 4 |
| i18n | Django gettext (`_('...')`) – Vietnamese / English |
| Docker | nginx → site (Django) → db (MariaDB) + redis + celery + bridged + wsevent |

## Key Paths

```
/home/algoritonlinejudge/aloj-docker/dmoj/          ← Docker project root
├── docker-compose.yml
├── repo/                                            ← Django source (mounted into site container at /site)
│   ├── resources/                                   ← SCSS, JS, static assets
│   │   ├── submission.scss                          ← ** Submission page styles **
│   │   ├── base.scss, style.scss, navbar.scss       ← Global styles
│   │   ├── vars-common.scss, vars-default.scss      ← SCSS variables (light)
│   │   ├── vars-dark.scss                           ← SCSS variables (dark)
│   │   ├── common.js                                ← Shared JS utilities
│   │   ├── event.js                                 ← WebSocket event dispatcher
│   │   └── libs/                                    ← Third-party JS (jQuery, Chart.js, Select2, etc.)
│   ├── templates/
│   │   ├── base.html                                ← Root template (loads jQuery, common.js, event.js)
│   │   ├── common-content.html                      ← Content wrapper (extends base.html)
│   │   └── submission/
│   │       ├── list.html                            ← ** Submission list page (JS + WebSocket logic) **
│   │       ├── row.html                             ← ** Single submission row template **
│   │       ├── status.html                          ← Submission detail/judgment page
│   │       ├── status-testcases.html                ← Test case breakdown
│   │       ├── source.html                          ← Source code viewer
│   │       └── submission-list-tabs.html            ← Tab navigation
│   ├── judge/views/submission.py                    ← View logic (context, permissions, pagination)
│   ├── judge/models/submission.py                   ← Submission model
│   ├── make_style.sh                                ← SCSS build script
│   └── locale/                                      ← Translation .po files
```

## Build & Deploy

```bash
cd /home/algoritonlinejudge/aloj-docker/dmoj && \
docker compose exec site bash -c "cd /site && bash make_style.sh 2>&1 | tail -3 && python manage.py collectstatic --noinput 2>&1 | tail -2" && \
docker compose restart site 2>&1 | tail -2
```

**Build pipeline**: `vars-{default,dark}.scss` → copied as `vars.scss` → `sass` compiles all `.scss` → `postcss + autoprefixer` → output to `resources/` (light) and `resources/dark/` (dark).

## Submission Page Architecture

### Template inheritance
```
base.html → common-content.html → submission/list.html
                                       ↳ includes submission/row.html (per row)
```

### list.html structure
- **Blocks**: `js_media` (inline JS + WebSocket), `body` (toolbar + table), `media` (extra CSS)
- **Toolbar**: Filter dropdown (status/language/org selects) + Statistics dropdown (Chart.js pie)
- **Table**: `<table class="submissions-table">` with `<tbody id="submissions-table">`
- **WebSocket**: `load_dynamic_update()` listens to `submissions` channel, calls `/api/submission_single_query?id=X` to get updated row HTML

### row.html structure (columns in order)
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

### Result bar states
| State | CSS class on `.result-bar-fill` | Visual |
|-------|---------------------------------|--------|
| Graded (normal) | `.result-bar-{AC,WA,TLE,MLE,...}` | Colored bar, width = score %, text "X / Y" |
| Error (IE/CE/AB) | `.result-bar-error` | Full-width gray bar, text = short status |
| Grading | `.result-bar-grading` | Full-width #6C6DFF pulsing, spinner + "Case #N" |

### Sub-actions (below result bar)
Icons: eye (view) → file-code (source) / download → refresh (rejudge, admin only) → cog (admin, superuser only). Wrapped in `.sub-actions` flex container.

### WebSocket update logic (in list.html)
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

## CSS Architecture (submission.scss)

**~470 lines.** Key sections:

| Section | What it styles |
|---------|----------------|
| Toolbar | `.submission-toolbar`, `.toolbar-btn` (#2196F3 blue), `.dropdown-box` |
| Table | `.submissions-table` (headers 1.05em, hover rows, column widths) |
| Result bar | `.result-bar` (#111 bg, 22px, rounded 8px), `.result-bar-fill`, `.result-text` |
| Bar colors | `.result-bar-AC` (green gradient), `-WA` (red), `-TLE/-MLE` (gray), `-RTE/-OLE/-IR` (orange) |
| Grading | `.result-bar-grading` (#6C6DFF, `grading-pulse` animation) |
| Sub-actions | `.sub-actions` (flex, space-evenly, 1.0em icons) |
| State column | Uses existing `.case-*` classes (`.case-AC` green, `.case-WA` red, etc.) |
| Responsive | `@media (max-width: 700px)` shrinks font, adjusts padding |

**SCSS variables**: Defined in `vars-common.scss` / `vars-default.scss`. Used as `$color_primary10`, `$color_primary25`, `$color_primary50`, `$color_primary75`, `$color_primary100`.

## Past Modifications (Summary)

### Submission list page (list.html + submission.scss + row.html)
1. **Toolbar buttons** – Added `.toolbar-btn` with blue bg (#2196F3), white text, dropdown toggle JS
2. **Table headers** – Increased to `font-size: 1.05em`, `font-weight: 600`
3. **State column** – Added `col-state` before `col-result`, uses `.case-{result_class}` for colored bold text
4. **Result bar** – Black (#111) background, 8px rounded, centered white text via absolute positioning
5. **Result bar colors** – Gradient fills per status (AC=green, WA=red, TLE/MLE=gray, RTE/OLE=orange)
6. **Grading bar** – #6C6DFF background, `grading-pulse` animation, spinner + "Case #N" text
7. **Vietnamese i18n** – Fixed result bar rendering to be language-independent; translated column headers
8. **State colors** – Removed custom state-color section; reuses existing `.case-*` classes
9. **Sub-actions** – `space-evenly` layout, 1.0em font size, padded clickable area
10. **WebSocket smart update** – Grading animation preserved when case # changes (only text + state updated)
11. **WS disconnection banner** – `.ws-closed` styled with yellow bg, visible text color (#7d5a00)
12. **Performance** – `$temp` DOM parse deferred to grading-only path to reduce overhead
13. **Partial Testcase Scoring Mode** – Replaced `partial`/`short_circuit` checkboxes with a 3-option dropdown (`short_circuit`, `partial_batch`, `partial_testcase`). In `partial_testcase`, the Judge doesn't short-circuit inside batches on WA.
14. **Custom Checkers vs Standard Checkers Normalization** – Fixed a major batch scoring bug. Standard checkers return `case.points` equal to `case.total`, but Custom Checkers return a `0..1` coefficient. 
    * Normalized coefficient: `coeff = case.points if case.points <= 1 else (case.points / case.total)`.
    * Batch score logic: `(sum(coeff) / batch_case_count) * batch.total`.
    * This applies to both the Python backend `judge_handler.py` and the Django view `submission.py` (`make_batch()`).
15. **Per-Testcase Point Display** – `status-testcases.html` displays individual test case points. Non-batched cases use `(points/total)`. Batched cases output normalized coefficient `(coeff/1)` (e.g., `0.924/1`) instead of confusing it with the whole batch score.

## Recent Session Notes (Apr 2026)

### Submission detail page UI redesign (status.html / status-testcases.html)

**Objective**: Redesign submission detail page at `/submission/<id>/` from table-based layout to modern card-based UI with modal popups for test case details.

**Files Modified**:
1. `repo/templates/submission/status.html` - Main submission page template
2. `repo/templates/submission/status-testcases.html` - Test case breakdown template
3. `repo/resources/submission.scss` - All styling for submission detail page

**Key Changes**:

**Template Changes (status.html)**:
- Action bar redesigned with flex layout, groups buttons: View source, Resubmit, Rejudge (admin), Diff (admin)
- Result section wrapped in `.submission-results-card` with shadow and rounded corners
- Added modal system with JS functions: `showCaseModal(caseId)`, `hideCaseModal(caseId)`
- ESC key listener closes all modals and restores scroll

**Template Changes (status-testcases.html)**:
- Replaced `<table class="submissions-status-table">` with `.test-cases-grid` (CSS Grid)
- Each test case now rendered as `.test-case-card` with flex layout
  - Card header: Title + status badge
  - Card body: Time/memory/points in single line with `flex-wrap: wrap`
  - Card footer: "Click to view details" hint
- Added modal structure per case: `.case-modal` with overlay, header (closeable), body (input/answer/output/feedback sections)
- **Test-cases-overview section commented out** (icon row above grid - can be re-enabled if needed)
- Batch headers wrapped in `.batch-header` with pink background (#cb3158)
- Submission summary converted to flex layout with orange background (#ffe6bb)

**SCSS Changes (submission.scss)**:
- ~550 lines of new CSS added
- Key classes:
  - `.submission-detail-container` - 100% width, max styling
  - `.submission-action-bar` - flex, gradient bg, button groups
  - `.submission-results-card` - white bg, rounded, shadow
  - `.test-cases-grid` - CSS Grid: `repeat(auto-fill, minmax(220px, 1fr))`
  - `.test-case-card` - base white card with border, hover animation (translateY -4px)
  - `.case-modal` - fixed positioning, flex centering, z-index 9999
  - `.batch-header` - solid pink #cb3158
  - `.submission-summary` - light orange background, summary items with flex space-between

**Color Scheme** (per test case status):
| Status | Border | Gradient |
|--------|--------|----------|
| AC | #2ecc71 (green) | white → #f0fff4 |
| _AC | #BBCC00 (yellow) | white → #fffef0 |
| WA | #e74c3c (red) | white → #fff5f5 |
| TLE, SC | #888 (gray) | white → #f5f5f5 |
| MLE, OLE, RTE, IR | #f39c12 (orange) | white → #fff8f0 |
| CE, IE, AB | #aaa (light gray) | white → #f7f7f7 |
| None (QU/P/G) | #6C6DFF (purple) | white → #f3f3ff |

**Issues Fixed During Development**:
1. ✅ Test case info split across lines → fixed with `flex-wrap: wrap; gap: 0.3em 1em;`
2. ✅ Batch cases not displaying as grid → removed conflicting `display: inline-block` CSS
3. ✅ Modal not centered vertically → changed JS from `display='block'` to `display='flex'`
4. ✅ Container width too narrow → expanded from 1200px to 100%
5. ✅ Test-cases-overview disappeared → restored with clickable modal support
6. ✅ Color consistency → mapped all 12 status types to appropriate colors

**Deployment Status**: ✅ All changes built successfully
- SCSS compiled via `make_style.sh`
- Static files collected via `manage.py collectstatic --noinput`
- Site container restarted

**Backend Impact**: ✅ ZERO - This is purely UI/UX redesign
- No model changes
- No view logic changes
- No permission/visibility flag changes
- Data flow unchanged (output_prefix_override, can_view_* flags still work as before)
- Safe for concurrent admin changes

**Future Agent Notes**:
- Modal system uses vanilla JS with fixed positioning and ESC key support
- Grid uses `auto-fill` and `minmax(220px, 1fr)` for responsive layout
- Color scheme locked in for consistency with status badges
- Test-cases-overview currently commented out in template (remove comment to re-enable)
- Responsive design implemented via media query `@768px` (single column grid, full-width modal)
- All SCSS variables use existing `$color_primary*` naming convention from vars.scss

---

### Partial testcase scoring incident (submission 1825)
- Symptom: batched case showed `0.092/1` instead of `0.92/1`, and batch score looked wrong.
- Root causes:
  1. Problem was still set to `scoring_mode = partial_batch` (so batch display used `min(case.points)`).
  2. Mixed checker formats:
     - Standard checker stores scaled points (`case.points = case.total` on full AC).
     - Custom checker stores coefficient (`case.points in [0,1]`).
- Final normalization rule used consistently:
  - `coeff = case.points if case.points <= 1 else case.points / case.total`
- Final batch formula (partial_testcase mode):
  - `batch_score = (sum(coeff) / testcase_count_in_batch) * batch_points`

### Files verified and aligned
- `repo/judge/bridge/judge_handler.py`:
  - Uses normalized `coeff` for batched `partial_testcase` scoring.
  - Computes `points += mean(coeff) * batch_points`.
- `repo/judge/views/submission.py`:
  - `make_batch()` mirrors backend formula for UI consistency.
- `repo/templates/submission/status-testcases.html`:
  - Batched testcase displays coefficient `(coeff/1)`.
  - Non-batched testcase keeps `(points/total)`.
- `repo/judge/views/api/api_v2.py`:
  - Uses `group_test_cases(..., scoring_mode)` so API batch points match UI.

### Operational caveats for future agents
- If UI shows batch points inconsistent with expected partial-testcase behavior, **check problem scoring mode first**:
  - `judge_problem.scoring_mode` must be `partial_testcase`.
- Changing scoring mode does not automatically rewrite old `submission.points` unless a rescore/rejudge path is triggered.
- Quick DB sanity query used in this session:
  - `SELECT case, batch, status, points, total FROM judge_submissiontestcase WHERE submission_id = ? ORDER BY case;`
  - Useful to detect whether values are scaled (`points ~= total`) or coefficient-style (`points <= 1`).

### Code verification status
- Checked diagnostics on:
  - `repo/judge/bridge/judge_handler.py`
  - `repo/judge/views/submission.py`
  - `repo/templates/submission/status-testcases.html`
  - `repo/judge/views/api/api_v2.py`
- Result: no syntax/lint errors reported by editor diagnostics in this session.

### NOT yet fixed
- WebSocket realtime on paginated pages (page 2+) for `/submissions/`, `/contest/.../submissions/`
- Organization submissions pages have no realtime at all
