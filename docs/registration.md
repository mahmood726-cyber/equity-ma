# EquityMA Protocol Registration

## Registration Details

| Field | Value |
|-------|-------|
| **Registration ID** | EQM-2026-001 |
| **Title** | EquityMA: A Browser-Based Tool for Equity-Stratified Meta-Analysis Using the PROGRESS-Plus Framework |
| **Version** | 1.0 |
| **Registration Date** | 2026-03-31 |
| **Author** | Mahmood Alhusseini |
| **License** | MIT |

## Repository

- **GitHub**: https://github.com/mahmood726-cyber/equity-ma
- **GitHub Pages**: https://mahmood726-cyber.github.io/equity-ma/

## Scope

EquityMA is a browser-based tool for equity-stratified meta-analysis. It implements:

- DerSimonian-Laird random-effects pooling within PROGRESS-Plus equity strata
- Q-between interaction test for equity dimension comparisons
- 11 PROGRESS-Plus dimensions (8 core + Age, Disability, Other)
- Stratified forest plots, equity gap charts, and reporting heatmap (Canvas)
- 12-item PRISMA-Equity 2012 auto-fill checklist
- CSV import/export and localStorage persistence

## Effect Types Supported

- Relative Risk (RR)
- Odds Ratio (OR)
- Hazard Ratio (HR)
- Mean Difference (MD)
- Standardised Mean Difference (SMD)

## Example Datasets

1. Statins by SES (k=6, N=46,380)
2. Vaccines by Country Income (k=15, N=800,861)
3. Antihypertensives by Sex (k=6, N=68,964)

## Safety Checks (Pre-Ship)

- [x] Div balance: PASS
- [x] Script integrity: PASS
- [x] Function uniqueness: PASS
- [x] ID uniqueness: PASS
- [x] Event listener cleanup: PASS

## Changelog

### v1.0.0 (2026-03-31)
- Initial release
- 1,774-line single HTML file
- All safety checks passed
