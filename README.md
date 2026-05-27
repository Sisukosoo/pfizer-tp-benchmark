# pfizer-tp-benchmark

Transfer Pricing benchmarking study for Pfizer Pharma GmbH using Orbis exports and OECD TNMM methodology.

**Status:** Work in progress -- portfolio project for Big 4 TP applications.

Data files (Orbis exports) are not included in this repository due to licensing restrictions from TU Munich's Bureau van Dijk subscription. The analysis can be reproduced with equivalent Orbis exports placed in `data/raw/`.

## Setup

```powershell
git clone https://github.com/Sisukosoo/pfizer-tp-benchmark.git
cd pfizer-tp-benchmark
py -3.14 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Place the Orbis exports in `data/raw/`:

- `Final_Pfizer_testedparty.xlsx`
- `Export_27_05_2026_13_13.xlsx`

Run the Streamlit app:

```powershell
.\venv\Scripts\streamlit.exe run streamlit_app.py
```

Run tests:

```powershell
.\venv\Scripts\python.exe -m pytest -v
```

## Methodology

The project applies the Transactional Net Margin Method (TNMM), following the OECD Transfer Pricing Guidelines, to benchmark Pfizer Pharma GmbH against independent EU/EFTA pharmaceutical distributors selected from Orbis. The rejection cascade starts from 55 NACE 4646 candidates and applies functional comparability criteria to exclude entities whose functions, assets, risks, product segment, ownership model, or data quality differ materially from the tested party. This reflects the OECD TPG comparability focus, including paragraph 3.24 on practical comparability considerations in narrow markets. The current baseline leaves 10 accepted comparables for later PLI and arm's length range analysis.

Rejection categories:

- `MANUFACTURER`: manufacturing functions and production assets are not comparable to a limited-risk distributor.
- `COOPERATIVE`: pharmacy-owned cooperatives and consortia have structurally different economics.
- `RETAIL`: retail pharmacies and online B2C channels perform consumer-facing functions.
- `WRONG_SEGMENT`: non-pharma, veterinary, diagnostics, device, dental, packaging, or rehabilitation focus.
- `HOLDING`: no relevant operating distribution activity.
- `LOGISTICS`: service-provider logistics profile rather than principal distributor profile.
- `BRAND_OWNER`: own-brand or IP-bearing pharmaceutical profile.
- `MIXED_PORTFOLIO`: pharma distribution materially mixed with cosmetics, perfumes, devices, or own-marketed specialties.
- `LOW_DATA_QUALITY`: insufficient evidence to validate functional comparability.

## Project Structure

```text
pfizer-tp-benchmark/
├── streamlit_app.py
├── src/
│   ├── config.py
│   ├── data_loader.py
│   ├── default_decisions.py
│   ├── comparables.py
│   ├── pli_calculator.py
│   ├── benchmarking.py
│   └── visualizations.py
├── tests/
├── data/
│   ├── raw/
│   ├── processed/
│   └── synthetic/
├── output/
│   ├── figures/
│   └── reports/
├── docs/
└── notebooks/
```

## License

MIT License.

Author: Sisu Kosoo, TU Munich. Year: 2026.
