# Documentation

This folder contains methodology notes for the Pfizer TP Benchmark learning project.

- `methodology.md` explains how the FAR memo, rejection cascade, PLI calculation, arm's-length range, sensitivity analysis, and reporting output fit together.

Public screenshots and demos should be produced in synthetic mode only:

```powershell
$env:APP_DATA_MODE = "synthetic"
.\venv\Scripts\streamlit.exe run streamlit_app.py
```

The sidebar should show `Data mode: Synthetic (public demo)`.
