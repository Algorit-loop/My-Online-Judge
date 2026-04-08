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

### NOT yet fixed
- WebSocket realtime on paginated pages (page 2+) for `/submissions/`, `/contest/.../submissions/`
- Organization submissions pages have no realtime at all
