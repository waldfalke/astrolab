# Report templates

Client-facing deliverable formats. De-identified, git-tracked. **Filled instances carry PII and
must go to `.private/charts/<id>/packs/` — never commit a filled copy.**

## `grand-report.html` — canonical grand client report

Self-contained, print-to-PDF (A4) astrological report: cover with embedded chart wheel, then
Portrait → Strengths → Growth edges → Year ahead (with a timing-windows table) → Supports → data
footer. Russian-facing copy, English scaffolding. All `{{TOKENS}}` and content rules are documented
in the leading HTML comment of the file.

### Render pipeline

```powershell
# 1. Build the chart project (recipes → .private), then render the wheel
pwsh artifacts/mcp-recipes/run_renderer.ps1 -ChartId <id> -ChartsRoot .private/charts
# → artifacts/results/renderer_<id>_*/01_chart_wheel.svg

# 2. Clean the wheel SVG for embedding:
#    - remove  <text ...>CATMEastrolab Renderer MVP</text>
#    - root tag: keep viewBox, drop width/height, add preserveAspectRatio="xMidYMid meet"

# 3. Fill {{TOKENS}} (incl. inline cleaned SVG into {{WHEEL_SVG}}) → save filled HTML to
#    .private/charts/<id>/packs/grand_report_<date>.html

# 4. Render PDF (self-contained, fonts/CSS/SVG all inline):
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu `
  --no-pdf-header-footer --print-to-pdf="<...>/packs/grand_report_<date>.pdf" `
  "file:///<...>/packs/grand_report_<date>.html"
```

### Quality rules (enforce on every fill)

- **Re-present, don't re-analyze.** Content traces to the validated working reading
  (`reading_full_*.md`); no fresh delineation in the warming-up pass.
- **Tendencies & invitations, not verdicts & events** — valence stays open.
- **Words, not glyphs, in body prose** (the wheel carries the symbols); avoids font-gap tofu on print.
- **Self-contained for print:** inline CSS + inline SVG; `print-color-adjust:exact` is already in the
  template (else colored boxes/headers print as white blanks).
- Keep the approximate-time note and the "verify against biography" line, gracefully worded.

First filled instance (reference): `novosibirsk_19880609_1430` (in `.private`).

## `rising-clock-mundane.html` — natal-free rising-sign clock (mundane day forecast)

The quality of a **day for a place**, with no personal chart — a "космограмма качества времени дня". Two
layers in fixed order: **I. Астрологический слой** (12 watches as paragraph pairs + начкары, objects on the
rising degree, Moon hand, retro climate) → **II. По-человечески**. All `{{TOKENS}}` and the full quality
rules (12 watches not 13; header bold/no period; достоинство ≠ фаза; phase = archetype, never the formula;
"восходящий градус" not "горизонт"; aspect cases НА квадрате / В оппозиции; high planets are not background)
live in the leading HTML comment of the file — that comment **is** the standard.

### Data source & render

Data comes from `run_rising_hands.ps1` in **general mode** (no `-NatalPointsCsv`). Fill the template against
a twin (read-as-system first — twin before prose), then render to PDF:

```powershell
python D:/Temp/claude/h2pdf_day.py <filled>.html <out>.pdf
```

First filled instance (reference): `general_20260623_krasnodar` (in `.private/charts/_transit_days/`).
