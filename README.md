# 🦾 EZYerrScanner: Cyber-Neural Data Integrity Platform

[![Powered by Groq](https://img.shields.io/badge/Powered%20by-Groq-00f2fe?style=for-the-badge&logo=ai)](https://groq.com/)
[![React 18](https://img.shields.io/badge/Frontend-React%2018-4facfe?style=for-the-badge&logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009485?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange?style=for-the-badge&logo=langchain)](https://github.com/langchain-ai/langgraph)

**EZYerrScanner** is a next-generation, multi-agent AI framework designed to audit, clean, and synthesize complex datasets with surgical precision. Built on a "Cyber-Dark" glassmorphism UI, it leverages a neural network of specialist agents to detect anomalies, business logic violations, and data decay in real-time.

<img width="1919" height="961" alt="Image" src="https://github.com/user-attachments/assets/d52e8b95-8c27-41b5-9902-ef0a4c1f93bc" />

<img width="1919" height="948" alt="Image" src="https://github.com/user-attachments/assets/f7df9bc1-e6f2-4bba-a2e6-b6c62c6bc2e6" />

<img width="1919" height="964" alt="Image" src="https://github.com/user-attachments/assets/2969f109-29d3-4344-a5a5-70f6e710e04d" />

<img width="1916" height="954" alt="Image" src="https://github.com/user-attachments/assets/7556ad0e-540d-4841-b003-154bde01dd3b" />

<img width="1919" height="962" alt="Image" src="https://github.com/user-attachments/assets/89fb6aab-9b21-490a-8d49-0256884e4c4e" />

<img width="1917" height="954" alt="Image" src="https://github.com/user-attachments/assets/4c56b978-c6d4-4b49-a104-91b9c2ee13ad" />

---

## 🧠 The Neural Architecture

EZYerrScanner uses a **LangGraph-orchestrated Multi-Agent State Machine**. Unlike linear scripts, our agents operate in a dynamic, stateful environment where a central **Orchestrator (Supervisor)** meticulously plans the audit roadmap before any specialist agent is deployed.

### 👥 Meet the Specialist Agents
| Agent | Designation | Core Capability |
| :--- | :--- | :--- |
| **🔍 Schema AI** | Intelligence | Auto-detects domain (HR, Finance, etc.) and deep-scans column types. |
| **🕹️ Orchestrator** | Supervisor | Construct a parallel execution plan based on data complexity. |
| **👯 Duplicate Hunter** | Specialist | Performs fuzzy matching and exact duplicate row identification. |
| **💎 Quality Audit** | Specialist | Analyzes null-density, type-mismatches, and format inconsistencies. |
| **📏 Logic Validator** | Specialist | Cross-references column relationships against business constraints. |
| **📈 Anomaly AI** | Specialist | Uses statistical distributions to flag outliers and Z-score deviations. |
| **🧟 Stale Detector** | Specialist | Identifies overdue tasks, zombie records, and temporal data decay. |
| **✍️ AI Summarizer** | Synthesizer | Compiles specialist findings into a Chief Data Officer-level executive briefing. |

---

## 🤝 Human-In-The-Loop (HITL) Workflow

We believe AI should be a co-pilot, not a black box. EZYerrScanner implements a high-fidelity **HITL sequence**:

1.  **Ingestion & Parsing**: Upload your `CSV`, `XLSX`, or `JSON`. The Schema Agent analyzes structure.
2.  **Roadmap Generation**: The Supervisor Agent creates a "Proposed Analysis Plan" detailing which specialists will run and why.
3.  **Human Approval**: The system pauses. **YOU** review the plan in a futuristic modal and click `APPROVE & EXECUTE`.
4.  **Neural Execution**: Specialist agents swarm the data in parallel, updating a real-time **Neural Progress Graph**.
5.  **Executive Synthesis**: Findings are distilled into a health score and top-priority action items.

---

## 🚀 Quick Start

### 1. Environment Configuration
Create a `.env` file in the `backend/` directory:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

### 2. Backend Setup (Powering the Neural Engine)
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### 3. Frontend Setup (Cyber-Dark Interface)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5174` (or your local Vite port) to begin the scan.

---

## 📂 Sample Data
The repository includes a `backend/sample_data/` directory with 8 pre-configured datasets spanning Project Management, HR, Finance, and Sales. Use these to test the **Neural Agent Progress Trace**.

---

## 🛠️ Technical Approach

*   **LLM Engine**: Powered by **Groq** for sub-second inference speeds, enabling agents to "think" and "react" instantly.
*   **State Management**: LangGraph manages the shared state, ensuring `file_bytes` and `dataframe` context are never lost across HITL transitions.
*   **Futuristic UI**: A custom-built Vanilla CSS design system utilizing `Orbitron` and `Outfit` fonts, glassmorphism, and SVG neural path animations.
*   **Resiliency**: Multi-layered error handling prevents graph crashes even with messy or malformed data inputs.

---

## 📜 License
The EZYerrScanner is proprietary software. All rights reserved. 🦾
