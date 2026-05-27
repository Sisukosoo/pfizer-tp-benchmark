# Methodology: TNMM Benchmarking Workflow

This project benchmarks Pfizer Pharma GmbH as a tested party under the Transactional Net Margin Method (TNMM). The tested party is characterized as a Limited-Risk Distributor with Sales and Marketing functions (LRD-SM). The comparables workflow therefore seeks independent companies whose observed activity is broadly consistent with routine pharmaceutical distribution, while excluding entities with materially different functions, assets, risks, or product-market exposure.

The starting population is a fixed Orbis export of 55 EU/EFTA candidates selected with NACE 4646, Wholesale of pharmaceutical goods, and independence filters. The rejection cascade records the manual functional review as a reproducible decision ledger. Defaults are stored in `src/default_decisions.py`; runtime overrides are stored separately in `data/processed/comparables_decisions.csv`, which is intentionally gitignored because it is generated state.

The cascade excludes candidates in the following categories:

- Manufacturer: manufacturing or production assets make the company unlike a routine distributor.
- Pharmacy cooperative: member-owned pharmacy networks and consortia have structurally different economics.
- Retail / B2C: pharmacy chains and online retailers perform consumer-facing retail functions.
- Wrong product segment: medical devices, dental, rehabilitation, veterinary, diagnostics, packaging, or other non-pharma focus.
- Holding company: no relevant operating activity.
- Logistics service provider: service-provider logistics profile rather than principal distributor profile.
- Brand owner / IP profile: entities that own, develop, register, or market proprietary pharmaceutical brands.
- Mixed portfolio: pharma activity materially mixed with cosmetics, perfumes, devices, parapharmaceuticals, or own-marketed specialties.
- Low data quality: insufficient financial or business-description evidence to validate comparability.

The baseline result is 10 accepted comparables, 45 rejected candidates, and 0 pending candidates. User edits in the Streamlit app support sensitivity scenarios without overwriting the immutable baseline logic. This follows the OECD Transfer Pricing Guidelines' emphasis on comparability analysis, including paragraph 3.24 on practical considerations where markets are narrow and perfect comparables are scarce.

## App Workflow

The Streamlit app presents the benchmarking study as a transparent workpaper rather than a black-box model. The Overview page identifies the tested party and summarizes the LRD-SM characterization. The Comparables page documents the rejection cascade from the raw Orbis population to the accepted comparable pool. The Analysis page then links the methodology to the quantitative result through an executive dashboard, base-case arm's-length range, sensitivity scenarios, and comparable-level PLI detail. The Report page converts the current benchmark state into an executive conclusion and downloadable Excel workpaper.

## PLI Selection

Operating Margin, defined as EBIT divided by Sales, is the primary Profit Level Indicator. It is appropriate for a sales and marketing distributor because it measures routine operating profitability relative to the sales base that the distributor manages. Pfizer Pharma GmbH is characterized as a Limited-Risk Distributor with Sales and Marketing functions (LRD-SM), so the analysis focuses on routine distributor returns rather than returns to manufacturing assets or pharmaceutical IP.

Berry Ratio, defined as Gross Profit divided by operating expenses, is retained as a secondary check. In this project, operating expenses are derived as Sales minus EBIT minus Material Costs because the Orbis export does not provide a direct Other Operating Expenses line. This captures personnel, depreciation/amortization, and other operating expenses from available income-statement lines. ROCE using P/L before tax is read from Orbis and used as an additional capital-return indicator, not as the primary tested PLI.

## Multi-Year Weighting

The base case uses a three-year period: FY22, FY23, and FY24, represented in Orbis as `Year - 2`, `Year - 1`, and `Last avail. yr`. Operating Margin and Berry Ratio are calculated as weighted multi-year ratios: sum(numerator) divided by sum(denominator). This avoids giving a small or anomalous year the same weight as a larger year. Missing or zero-denominator observations are excluded from the relevant weighted ratio rather than forcing a distorted result.

## Arm's-Length Range

The arm's-length range is constructed as the interquartile range of the accepted comparable companies' weighted PLIs. The calculation reports the minimum, Q1, median, Q3, maximum, and IQR width. Quartiles use NumPy's `percentile` implementation with method `linear`, which is a transparent interpolation method suitable for a small accepted pool. Pfizer's tested PLI is then positioned as below Q1, within the range, or above Q3. If the tested party falls outside the IQR, the tool reports the direction and distance to the nearest range edge and the median.

## Sensitivity and Limitations

The sensitivity tab tests period choice, PLI choice, outlier exclusions, exclusion of Italian regional distributors, and an optional Pfizer FY22 EBIT normalization for the EUR 71.9M restructuring charge described in the FAR memo. These scenarios are not separate conclusions; they are diagnostic checks on the robustness of the base case.

The current comparable pool is methodologically useful but not perfect. Pfizer Pharma GmbH is materially larger than the median comparable, and independent multinational pharmaceutical distributors are scarce in Europe. Several accepted comparables are Italian regional distributors, which may have lower margins than manufacturer-side distributors. The app therefore presents the result as a transparent TNMM benchmark with explicit limitations rather than as a mechanically definitive arm's-length conclusion.

## Reporting Output

The Excel workpaper is a presentation layer over the same calculation engine used in the app. It includes the tested-party overview, accepted comparables, rejected candidates, PLI detail, arm's-length range, sensitivity scenarios, and methodology notes. The report should be read as a reproducible portfolio workpaper based on the available Orbis export, not as a statutory transfer pricing report.
