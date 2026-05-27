# pfizer-tp-benchmark

Transfer Pricing benchmarking study scaffold for Pfizer Pharma GmbH using Orbis exports and OECD TNMM methodology.

**Status:** Work in progress -- portfolio project for Big 4 TP applications.

Data files (Orbis exports) are not included in this repository due to licensing restrictions from TU München's Bureau van Dijk subscription. The analysis can be reproduced with equivalent Orbis exports placed in `data/raw/`.

## Setup

```powershell
git clone https://github.com/SisuKosoo/pfizer-tp-benchmark.git
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

## Methodology Overview

The project applies the Transactional Net Margin Method (TNMM), following the OECD Transfer Pricing Guidelines, to benchmark Pfizer Pharma GmbH against independent EU pharmaceutical distributors selected from Orbis. The application will support a rejection cascade, profitability level indicators, interquartile arm's length range analysis, sensitivity checks, and reporting.

## Project Structure

```text
pfizer-tp-benchmark/
├── streamlit_app.py
├── src/
│   ├── config.py
│   ├── data_loader.py
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

Author: Sisu Kosoo, TU München. Year: 2026.
