# EZYerrScanner — Multi-Agent Data Integrity Platform

OptiScan is a production-grade AI system using an architecture of 7 distinct LangGraph AI Agents that autonomously run data quality, anomaly detection, business logic bounds, and stale state aggregation across CSV, XLSX, and JSON structured data. The system operates autonomously mimicking a Chief Data Officer.

## Architecture

- **7 AI agents powered by Google Gemini 1.5 Flash (free tier)**
- **LangGraph** stateful orchestration with parallel execution mapping
- **LangChain** tool wrappers passing raw pandas/numpy statistics
- **FastAPI** backend + React 18 frontend

## Agents

| Agent | Role | AI Used |
|---|---|---|
| Schema Intelligence | Domain detection + column typing | Gemini |
| Supervisor | Smart routing decisions | Gemini |
| Duplicate Hunter | Exact + fuzzy duplicate detection | Gemini |
| Data Quality | Null + type + format analysis | Gemini |
| Business Logic | Rule violation detection | Gemini |
| Anomaly Detector | Statistical outlier analysis | Gemini |
| Stale Records | Overdue + zombie record detection | Gemini |
| Report Synthesizer | Executive summary generation | Gemini |

## Quick Start
1. Get a free Gemini API key: https://aistudio.google.com/app/apikey
2. Add it to `backend/.env`: `GROQ_API_KEY=your_key_here`
3. Launch the Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
4. Launch the Frontend:
```bash
cd frontend
npm install
npm run dev
```
5. Open http://localhost:5173 and upload `backend/sample_data/test_projects.csv`.

## Deploy to Render (Free Tier)
- **Backend**: New Web Service → connect GitHub → build command: `pip install -r requirements.txt`
- **Frontend**: New Static Site → build command: `npm run build` → publish dir: `dist`

## Docker Deployment

To run the full stack simultaneously:
```bash
docker-compose up --build
```
