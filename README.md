# Data Pilot

A **production‑quality** data‑cleaning web application built with **Streamlit**, **Pandas**, **Plotly**, and **ReportLab**.

## Features
- Upload CSV/Excel files (drag‑and‑drop or browse)
- Automatic data profiling & visualisation
- Interactive cleaning operations (duplicates, missing values, outliers, type conversion, etc.)
- Before‑/After comparison dashboard
- PDF report generation (Project title, dataset summary, cleaning steps, charts)
- Download cleaned CSV/Excel and cleaning logs
- Activity log, data‑quality score, smart recommendations
- Light/Dark theme toggle, undo, pipeline save/load, column search & profiling, script export

## Tech Stack
- **Frontend**: Streamlit, custom CSS, Plotly
- **Backend**: Python, Pandas, NumPy, OpenPyXL, Scikit‑learn, ReportLab

## Project Structure
```
DataPilot/
│   app.py
│   requirements.txt
│   .gitignore
│   README.md
│
├─ pages/
│   ├─ Dashboard.py
│   ├─ Upload.py
│   ├─ Analysis.py
│   ├─ Cleaning.py
│   ├─ BeforeAfter.py
│   ├─ Reports.py
│   ├─ Download.py
│   └─ Settings.py
│
├─ utils/
│   ├─ cleaner.py
│   ├─ analyzer.py
│   ├─ charts.py
│   ├─ report.py
│   ├─ exporter.py
│   └─ helpers.py
│
├─ assets/
│   ├─ logo.png
│   └─ styles.css
│
├─ uploads/          # uploaded datasets (empty, .gitkeep)
├─ cleaned_files/    # cleaned datasets (empty, .gitkeep)
└─ reports/          # generated PDF reports (empty, .gitkeep)
```

## Getting Started
```bash
# Clone the repo (if hosted remotely) or simply navigate to the folder
cd DataPilot

# Create a virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

---
*Built for a portfolio showcase – clean, modular, and scalable.*
