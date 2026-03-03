# Everest Region Tourism Data Analysis

Analysis and forecasting of tourist arrivals in the Everest region (Namche Bazar area) of Nepal, spanning 1995–2025.

## Project Overview

This project provides:
- **Data cleaning** and validation pipeline
- **Exploratory analysis** with visualizations
- **Outlier detection** and crisis-event analysis (2015 Earthquake, COVID-19)
- **2026 monthly forecasts** by gender, country, age, and purpose of visit
- **Interactive Streamlit dashboard**

## Project Structure

```
├── data/                    # Data files
│   ├── entry_data.csv       # Raw visitor data
│   ├── entry_data_cleaned.csv
│   ├── yearly_summary.csv
│   ├── country_summary.csv
│   └── PROJECT_DOCUMENTATION.txt   # Full technical docs
├── scripts/
│   └── data_prep.py         # Data cleaning pipeline
├── notebooks/
│   ├── 1_exploration.ipynb  # Initial exploration
│   └── 2_data_analysis_and_visualization.ipynb
├── app.py                   # Streamlit dashboard
├── test_setup.py            # Environment check
└── requirements.txt
```

## Setup

1. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate          # Windows
   # source venv/bin/activate     # Linux/Mac
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify setup**
   ```bash
   python test_setup.py
   ```

## Usage

### 1. Prepare data (cleaned CSVs and summaries)
```bash
python scripts/data_prep.py
```

### 2. Run analysis notebooks
Open `notebooks/1_exploration.ipynb` and `2_data_analysis_and_visualization.ipynb` in Jupyter and run all cells.

### 3. Launch Streamlit dashboard
```bash
streamlit run app.py
```
Open the URL shown (usually http://localhost:8501).

## Key Dependencies

| Library   | Purpose                        |
|----------|---------------------------------|
| pandas   | Data handling & aggregation     |
| matplotlib, seaborn | Notebook visualizations |
| altair   | Dashboard charts                |
| streamlit| Interactive dashboard           |

See `requirements.txt` for full list.

## Documentation

Full technical documentation (algorithms, methods, libraries, data flow) is in:
**`data/PROJECT_DOCUMENTATION.txt`**

## Data

- **Source:** `data/entry_data.csv`
- **Records:** ~169,000 visitors (1995–2025)
- **Columns:** Visitor_ID, Name, Visit_Date, Nationality, Purpose_of_Visit, Age, Gender, Expedition_Duration_Days, Permit_Fee_USD, Year, Month
