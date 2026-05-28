# Pfizer TP Benchmark

Python + Streamlit portfolio project for a transfer pricing benchmarking study of Pfizer Pharma GmbH.

This is a student learning project by **Sisu Kosonen, TU München**. I built it to study transfer pricing more deeply, practice modelling financial indicators used in transfer pricing, and learn how tools such as Moody's Orbis, Python, OpenAI Codex, Claude, and Excel can be combined in an applied finance/tax workflow.

The project is not a statutory transfer pricing report or professional tax opinion. It is a reproducible educational workpaper and portfolio case.

## Project Purpose

The case benchmarks Pfizer Pharma GmbH as a tested party under the OECD Transactional Net Margin Method (TNMM). The app follows a realistic transfer pricing workflow:

- define the tested-party profile using FAR analysis context
- load confidential Orbis exports for the tested party and comparable candidates
- document a rejection cascade from raw candidate companies to accepted comparables
- calculate Profit Level Indicators (PLIs), especially Operating Margin
- determine an arm's-length range using the interquartile range
- run sensitivity scenarios
- present visualizations and generate an Excel workpaper

The main learning goal was to understand how transfer pricing methodology can be translated into transparent data modelling and reporting.

## AI-Assisted Development

This project was coded with the support of AI tools, especially **OpenAI Codex** and **Claude**. I used these tools to help design the project structure, implement Python modules, debug issues, improve Streamlit UI, and iterate on documentation.

The methodological choices, project direction, data interpretation, and final review remain part of the learning process. AI was used as a coding and reasoning assistant, not as a substitute for understanding the transfer pricing concepts.

## Data Notice

Real Orbis data files are not included in this repository.

The Orbis exports used in the project are confidential under TU München's Moody's / Bureau van Dijk subscription. To reproduce the analysis, equivalent Orbis exports must be placed locally in `data/raw/`:

- `Final_Pfizer_testedparty.xlsx`
- `Export_27_05_2026_13_13.xlsx`

The `.gitignore` is configured so raw Orbis files, processed decision state, generated reports, and generated figures are not committed.

The repository includes a synthetic public-demo dataset in `data/synthetic/`. It is structurally similar to the Orbis exports used by the app, but the company names and financial values are artificial. Public screenshots and demos should use this synthetic mode, not real Orbis-derived outputs.

## Public Demo Mode

Before recording screenshots, running a public demo, or making the repository public, launch the app in synthetic mode:

```powershell
$env:APP_DATA_MODE = "synthetic"
.\venv\Scripts\streamlit.exe run streamlit_app.py
```

The sidebar should show `Data mode: Synthetic (public demo)`. Do not use screenshots from private real-data mode in public materials. Generated screenshots and workpapers under `output/` are gitignored because they may be derived from local confidential data.

## Methodology Summary

The analysis applies TNMM to a limited-risk distributor with sales and marketing functions (LRD-SM). Operating Margin, defined as EBIT / Sales, is the primary PLI. Berry Ratio and ROCE are used only as diagnostic sensitivity checks, not as alternative primary conclusions.

The comparable-company workflow starts from 55 EU/EFTA Orbis candidates selected around NACE 4646, wholesale of pharmaceutical goods. The rejection cascade excludes candidates with materially different functions, assets, risks, product-market exposure, ownership models, or data quality. The current baseline leaves 10 accepted comparables and 45 rejected candidates.

Multi-year Operating Margin is calculated as a weighted ratio:

```text
sum(EBIT over selected years) / sum(Sales over selected years)
```

The base case uses FY22-FY24, consistent with the FAR memo's view that FY20-FY21 do not fully represent the entity's current operational scope. The arm's-length range is calculated as the interquartile range of accepted comparable PLIs using linear quartiles. Sensitivity scenarios test period choice, PLI choice, outlier exclusions, Italian regional distributor exclusions, and Pfizer's FY22 restructuring normalization.

## Current Features

- Orbis Excel data loader with handling for Orbis workbook quirks
- tested-party overview page
- interactive comparables rejection cascade
- accepted, rejected, and pending comparable pools
- Operating Margin, Berry Ratio, and ROCE calculation engine
- weighted multi-year PLI calculations
- arm's-length range and tested-party positioning
- sensitivity analysis
- Plotly visualizations
- methodology page
- contextual About page
- downloadable Excel workpaper
- pytest test suite

## Setup

```powershell
git clone https://github.com/Sisukosoo/pfizer-tp-benchmark.git
cd pfizer-tp-benchmark
py -3.14 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Place the Orbis exports in `data/raw/`:

```text
data/raw/Final_Pfizer_testedparty.xlsx
data/raw/Export_27_05_2026_13_13.xlsx
```

Run the Streamlit app:

```powershell
.\venv\Scripts\streamlit.exe run streamlit_app.py
```

The app automatically uses real data when both confidential Orbis files are present locally. If they are absent, it falls back to the synthetic public-demo dataset. You can also force synthetic mode:

```powershell
$env:APP_DATA_MODE = "synthetic"
.\venv\Scripts\streamlit.exe run streamlit_app.py
```

To force private real-data mode:

```powershell
$env:APP_DATA_MODE = "real"
.\venv\Scripts\streamlit.exe run streamlit_app.py
```

Run tests:

```powershell
.\venv\Scripts\python.exe -m pytest -v
```

Run linting and formatting checks:

```powershell
.\venv\Scripts\python.exe -m ruff check .
.\venv\Scripts\python.exe -m black --check .
```

Run the public-release safety audit:

```powershell
.\venv\Scripts\python.exe scripts\public_release_audit.py
```

## Project Structure

```text
pfizer-tp-benchmark/
+-- streamlit_app.py
+-- src/
|   +-- config.py
|   +-- data_loader.py
|   +-- default_decisions.py
|   +-- comparables.py
|   +-- pli_calculator.py
|   +-- benchmarking.py
|   +-- sensitivity.py
|   +-- reporting.py
|   +-- visualizations.py
+-- tests/
+-- data/
|   +-- raw/
|   +-- processed/
|   +-- synthetic/
+-- output/
|   +-- figures/
|   +-- reports/
+-- docs/
+-- assets/
+-- notebooks/
+-- scripts/
```

## Limitations

The comparable pool is small, and Pfizer Pharma GmbH is materially larger than the median accepted comparable. Independent multinational pharmaceutical distributors are scarce in Europe, so the analysis presents transparent assumptions and sensitivity checks rather than claiming mechanical certainty.

The project is intended to demonstrate learning, methodology, and analytical implementation. It should not be relied on for tax compliance or professional advice.

## License

MIT License.

Author: Sisu Kosonen, TU München. Year: 2026.
