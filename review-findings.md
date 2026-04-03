# EquityMA Code Review Findings

**Date:** 2026-04-03
**File:** equity-ma.html (1,774 lines)
**Tests:** 50/50 PASS

## P0 (Critical)

### P0-1: CSV export lacks formula injection sanitization
**Lines:** 1568-1587 (`exportCsvData`)
Study names, subgroup labels, and dimensions are written directly to CSV without checking for formula injection characters (`=`, `+`, `@`, `\t`, `\r`). A malicious study name like `=CMD("calc")` would execute in Excel.
**Status:** FIXED

### P0-2: Missing closing `</html>` tag
**Line:** 1773
File ends with `</script></body>` but no `</html>`.
**Status:** FIXED

## P1 (Important)

### P1-1: DerSimonian-Laird Q division by zero when k=1
**Lines:** 770-779
When k=1, the single-study path returns correctly. But the `dlMeta` function calculates `Q` and `W2/W` which could be NaN if a single study has SE=0 (variance=0, weight=Infinity).

### P1-2: I2 calculation can produce NaN when Q=0
**Line:** 799
`I2 = Math.max(0, (Q-df)/Q*100)` — when Q=0 (perfect homogeneity), this is 0/0 = NaN. Should guard with `Q > 0 ? ... : 0`.
**Status:** FIXED

### P1-3: CSV import does not validate effect type
**Lines:** 705-749
CSV import accepts any string for `effectType` without validation. Invalid types like "XYZ" would pass through silently.

### P1-4: `prompt()` usage for editing is not accessible
Functions like `editIntervention` in EvidenceMap use `prompt()` which blocks the UI and is not keyboard-accessible in some screen readers.

### P1-5: Interaction test uses Q_total - Q_within which can be negative
**Lines:** 813-833
`Qbetween = Qtotal - Qwithin` can be slightly negative due to floating point. The `Math.max(0, Qbetween)` on line 857 handles this correctly.

## P2 (Minor)

### P2-1: Heatmap canvas colors use undefined `tc.surface2`
**Line:** 1438
`ctx.fillStyle = hasDim ? DIM_COLORS[dim] : tc.surface2` — `tc` object doesn't have `surface2` property; it has `bg`, `text`, `text2`, `border`, `teal`, `coral`, `amber`, `grid`. Should use `tc.bg` or similar.

### P2-2: `studyIdCounter` resets on page reload with non-empty localStorage
**Line:** 557
`studyIdCounter = 1` at init, but loaded studies may have IDs > 1. New studies could get duplicate IDs.

### P2-3: No feedback when CSV has header row
The CSV format documentation mentions no header row, but users may paste with headers.

### P2-4: Forest plot axis labels overlap for small studies
When study names are long (>15 chars), they overlap with the plot area margin.

---

**Summary:** 2 P0 fixed, 5 P1 found (1 fixed), 4 P2 found
