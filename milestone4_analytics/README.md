# SupportPilot — AI Performance & Analytics (Milestone 4)

## Overview
This is a **separate, independently runnable analytics, monitoring, escalation, and evaluation application** built for **SupportPilot / AeroAssist AI**.

It runs on its own dedicated port (**8501**) using **Streamlit, Pandas, and Plotly**, operating strictly in **read-only mode** against the production SQLite database (`aeroassist.db`). The existing Flask web dashboard on port **5000** remains completely intact, active, and unmodified.

---

## 📁 Application Structure

```
milestone4_analytics/
├── requirements.txt            # Dedicated dependencies (streamlit, pandas, plotly, scikit-learn, etc.)
├── app.py                      # Separate Streamlit analytics interface (Port 8501)
├── analytics.py                # Pure KPI aggregation, time-series, category, and priority calculations
├── escalation.py               # 5-Rule automatic escalation engine & human-intervention queue queries
├── evaluation.py               # Offline benchmark evaluations (Classifier F1/Accuracy, Confusion Matrix, RAG Quality)
├── monitoring.py               # System health checks, latency tracking, and true calculated uptime
├── tests/
│   └── test_analytics_app.py   # Complete unit and integration test suite
└── README.md                   # Setup, configuration, and execution instructions
```

---

## 🚀 Quickstart & Execution

### 1. Open Windows PowerShell
Navigate to the `milestone4_analytics` directory:

```powershell
cd "c:\Users\kolik\OneDrive\Documents\Project\aeroassist\milestone4_analytics"
```

### 2. Install Dependencies (if not already installed)
```powershell
python -m pip install -r requirements.txt
```

### 3. Run the Analytics Application
Launch Streamlit on port **8501**:

```powershell
streamlit run app.py --server.port 8501
```

### 4. Access the Dashboard
Open your web browser and navigate to:
```
http://localhost:8501
```

> **Note**: Your main SupportPilot application (`python app.py`) will continue running independently on `http://localhost:5000`.

---

## 📊 Features & Dashboard Pages

### 1. Executive KPIs & AI Performance Over Time
- **Live KPI Metrics**: Total Tickets, AI Resolution Rate %, Escalation Rate %, Average AI Confidence, Knowledge Base Coverage %, Resolution Success Rate %, and Average Resolution Time.
- **Interactive Multi-Line Chart (Plotly)**: Visualizes daily/weekly trends for:
  - 🟢 AI Resolution Rate (%)
  - 🔴 Escalation Rate (%)
  - 🔵 Average AI Confidence (%)
- **Date Presets**: All Time, Last 30 Days, Last 7 Days.
- **Missing Data Handling**: Displays `"Not available"` with clear explanations for unavailable metrics (e.g. CSAT surveys).

### 2. Category & Priority Analysis
- Stacked bar charts showing auto-resolved vs escalated volume per category.
- Donut chart highlighting AI Resolution vs Human Escalation ratio.
- Priority distribution highlighting Critical tickets routed to human intervention.

### 3. Confidence Score Distribution
- Histogram grouping processed decisions into 4 standardized confidence bands:
  - **Low** (< 0.50)
  - **Moderate** (0.50 - 0.69)
  - **Good** (0.70 - 0.84)
  - **High** (0.85 - 1.00)

### 4. Human Intervention Monitor & Rule Engine
- **Live Queue Table**: Displays escalated and unresolved tickets with Ticket ID, Category, Priority, AI Confidence, Status, Escalation Reason, Attempts, Jira Key, and Created Time.
- **Interactive Rule Tester**: Allows testing any custom ticket parameters against the **5 Automatic Escalation Rules**:
  1. *Priority is Critical*
  2. *AI Confidence < 0.70*
  3. *Resolution Failed / KB Similarity < 0.60*
  4. *Customer Explicitly Requests Human Support*
  5. *Repeated Resolution Attempts $\ge 3$*

### 5. Classifier & RAG Evaluation Benchmarks
- Offline testing against 40 ground-truth scenarios (`data/evaluation_dataset.json`).
- Reports Classification Accuracy, Precision, Recall, Macro-F1, Per-Category metrics, and Confusion Matrix heatmap.
- Reports Decision Accuracy, Solvable Auto-Resolution Rate, and Knowledge-Base Coverage.

### 6. System Health & Monitoring
- Real-time diagnostic probes for SQLite Database, Intent Classifier, RAG Retriever, and Jira Escalation Service.
- **True System Uptime**: Calculated from health check log history without hardcoding fake numbers.
- Agent pipeline stage latency breakdown.

---

## 🧪 Running the Test Suite

Run the full Milestone 4 test suite with:

```powershell
python -m unittest milestone4_analytics/tests/test_analytics_app.py -v
```
