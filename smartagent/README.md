# SmartAgent — AI-Powered Smartsheet Data Auditing Agent

**SmartAgent** is a sophisticated, LangGraph-powered auditing suite integrated into the EZYerrScanner ecosystem. It automates the detection of data quality issues across Smartsheet sheets, proposes AI-driven corrective actions, and executes them with a **Human-in-the-Loop (HITL)** approval step.

---

<img width="1009" height="553" alt="Image" src="https://github.com/user-attachments/assets/859c1a27-b7a9-4acf-94d4-d4a758b63b8d" />

<img width="927" height="645" alt="Image" src="https://github.com/user-attachments/assets/a03ad3a4-3f37-4af1-85cd-1cfdaab57a5a" />

<img width="1919" height="971" alt="Image" src="https://github.com/user-attachments/assets/ea32ba1b-ba71-40c0-8e6a-e4f09f25be5e" />

<img width="1919" height="966" alt="Image" src="https://github.com/user-attachments/assets/b1343180-279c-4710-b621-1891a546958c" />

<img width="1919" height="967" alt="Image" src="https://github.com/user-attachments/assets/bac0f0f6-fc27-4d6a-829e-88077c7af1a9" />

<img width="1919" height="970" alt="Image" src="https://github.com/user-attachments/assets/2240244e-43bf-487f-83c5-6da575168783" />

<img width="1919" height="968" alt="Image" src="https://github.com/user-attachments/assets/d83fadea-1732-4e54-b258-dee53ca052e8" />

<img width="1919" height="968" alt="Image" src="https://github.com/user-attachments/assets/ab41d9e1-ddf2-4882-9985-672277aed009" />

<img width="1917" height="963" alt="Image" src="https://github.com/user-attachments/assets/b72430bf-9ef5-4966-bf33-2eb001bcb56c" />

<img width="1369" height="648" alt="Image" src="https://github.com/user-attachments/assets/2f38107f-b4d6-42d3-91ac-51da2e362605" />

## 🏗️ System Architecture

SmartAgent operates as a specialized module within the unified EZYerrScanner platform. It leverages a centralized FastAPI backend and a custom LangGraph "Brain" to process complex auditing tasks.

```mermaid
graph TD
    subgraph "Frontend (React + Vite)"
        UI["Unified Dashboard"]
        Tab1["File Scanner Tab"]
        Tab2["Smartsheet Audit Tab"]
    end

    subgraph "Consolidated Backend (FastAPI)"
        Router["Analyze Router (Port 8000)"]
        Brain["LangGraph Brain"]
        Simulator["Smartsheet Simulator"]
    end

    subgraph "Data Layer"
        SDK["Official Smartsheet SDK"]
        MOCK["WireMock Server"]
        LIVE["Live Smartsheet API"]
        CSV["all_agents_dataset.csv"]
    end

    UI --> Router
    Router --> Brain
    Brain --> SDK
    SDK --> Simulator
    Simulator --> CSV
    SDK -.-> MOCK
    SDK -.-> LIVE
```

---

## 🧠 The LangGraph "Brain" (How it Thinks)

The auditing process is managed by a **Stateful Multi-Agent Workflow**. Instead of a simple linear script, SmartAgent uses a supervisor-specialist pattern to analyze data from multiple dimensions.

### The Audit Pipeline

```mermaid
graph LR
    START((Start)) --> Load[Load Sheet]
    Load --> Schema[Schema Intelligence]
    Schema --> Super[Supervisor]
    
    subgraph "Specialist Agents"
        Super --> Dup[Duplicate Hunter]
        Super --> Qual[Data Quality]
        Super --> Logi[Business Logic]
        Super --> Stal[Stale Detector]
        Super --> Anom[Anomaly Detector]
    end
    
    Dup --> Agg[Aggregator]
    Qual --> Agg
    Logi --> Agg
    Stal --> Agg
    Anom --> Agg
    
    Agg --> Synth[Synthesizer]
    Synth --> END((Report Ready))
```

### Node Explanations:
- **Supervisor**: Analyzes the sheet metadata and decides which specialist agents are relevant (e.g., skips "Anomaly Detector" if no numeric columns are present).
- **Specialist Agents**: Industry-specific logic designed to find duplicates, missing values, status conflicts, and budget overruns.
- **Aggregator**: Deduplicates findings and calculates an overall **Health Score**.
- **Synthesizer**: Generates the executive summary and top priorities for the final report.

---

## 🔄 The 5-Step Auditing Workflow

SmartAgent follow a rigorous Step-by-Step execution process to ensure data integrity and user control.

1.  **Connect**: Initializes the link with the Smartsheet API or the local Simulator.
2.  **Select Sheet**: Displays a list of accessible sheets for scanning.
3.  **Analyze**: Triggers the LangGraph Brain. This is a **read-only** phase that generates AI findings.
4.  **Review Actions (HITL)**: **Crucial Step.** The AI proposes specific changes (Comments, Cell Updates). You review, approve, or discard each one.
5.  **Execute**: The system uses the **Official Smartsheet SDK** to apply only the **approved** actions back to the sheet.

---

## 🚀 How to Run

### One-Click Startup (Recommended)
From the project root, run the unified launcher:
```powershell
.\run_scanner.ps1
```

### Manual Execution
If you prefer running components separately:

**Backend:**
```powershell
cd smartagent/backend
.\venv\Scripts\python.exe -m uvicorn main:app --port 8000 --reload
```

**Frontend:**
```powershell
cd frontend
npm run dev
```

---

## 🧪 Simulation Mode vs Live Mode

SmartAgent includes a **Local Simulator** that allows you to test the full lifecycle without a Smartsheet account.

- **Simulator Mode**: Set `USE_SIMULATOR=true` in `.env`. It reads from `all_agents_dataset.csv`.
- **Live Mode**: Set `USE_SIMULATOR=false` and provide your `SMARTSHEET_ACCESS_TOKEN`.

> [!IMPORTANT]
> **Developer Note on Connectivity**: Every write operation in SmartAgent (like adding comments or updating cells) is routed through the **Official Smartsheet Python SDK**. Even in simulator mode, the SDK thinks it is talking to a real API, ensuring production-ready reliability.
