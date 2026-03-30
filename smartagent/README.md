# SmartAgent — AI-Powered Smartsheet Data Quality Agent

**Round 2 Submission** for the SSPM AI Agent Challenge.

SmartAgent is a LangGraph-powered agentic system that audits Smartsheet data quality, proposes corrective actions, and applies them through the official Smartsheet Python SDK — with a Human-in-the-Loop approval step before anything is written back.

---

## Architecture

```
Browser (React)
    │
    ▼
FastAPI Backend (Python 3.11)
    │
    ├─ GET  /api/analyze/connect   → list sheets
    ├─ POST /api/analyze/start     → run LangGraph pipeline
    └─ POST /api/actions/execute   → apply approved actions
         │
         ▼
LangGraph Pipeline:
  load_sheet → schema_intelligence → supervisor
    → duplicate_hunter → quality_auditor → logic_validator → stale_detector
    → aggregator → synthesizer
         │
         ▼
Smartsheet Python SDK (official)
    │
    ├─ Dev/Demo:  WireMock (http://localhost:8082)  ← no real account needed
    └─ Prod:      api.smartsheet.com                ← real Smartsheet API
```

---

## Quickstart (Docker Compose — Recommended)

```bash
git clone https://github.com/your-org/smartagent
cd smartagent

# Start WireMock + Backend + Frontend together
docker compose up

# Open the app
open http://localhost:5173

# WireMock admin (see what SDK calls were made)
open http://localhost:8082/__admin
```

---

## Quickstart (Local Dev — No Docker for backend)

```bash
# 1. Start WireMock (Docker required for this step only)
cd smartsheet-sdk-tests && docker compose up -d
cd ..

# 2. Set up Python environment
cd backend
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
cp .env.example .env     # edit if needed

# 3. Start backend
uvicorn main:app --reload --port 8000

# 4. Start frontend (separate terminal)
cd ../frontend
npm install
npm run dev

# 5. Open http://localhost:5173
```

---

## Smartsheet Integration

SmartAgent uses the **official Smartsheet Python SDK** for all API operations.

### Development — WireMock Mock Server

Uses the official Smartsheet contract testing server so you can develop and demo without a real Smartsheet account.

```bash
# Clone the official mock server (already in repo as submodule)
git clone https://github.com/smartsheet/smartsheet-sdk-tests.git

# Start WireMock (requires Docker)
cd smartsheet-sdk-tests && docker compose up -d

# Admin UI: http://localhost:8082/__admin
# → Shows all 198 loaded mappings
# → Shows every request the SDK sent (MATCHED vs UNMATCHED)
```

**Proof of real SDK integration:**

```bash
python scripts/wiremock_admin.py
```

This shows WireMock's request log. Every call SmartAgent makes goes through the official Smartsheet Python SDK which makes **actual HTTP requests** to WireMock. The log shows:
- The exact endpoint called (e.g. `POST /sheets/{id}/discussions`)
- The `Api-Scenario` header we sent
- Whether WireMock matched it to a mapping
- The response returned

This is **identical** to how the SDK behaves against the real Smartsheet API — only the base URL changes.

### Production — Real Smartsheet API

1. Get a Personal Access Token: **Smartsheet → Account → Personal Settings → API Access**
2. Set in `backend/.env`:
   ```
   SMARTSHEET_ACCESS_TOKEN=your_token_here
   USE_MOCK_SERVER=false
   ```
3. Restart the backend. No code changes required.

### Environment Modes

| Variable | Dev (default) | Docker | Production |
|---|---|---|---|
| `USE_MOCK_SERVER` | `true` | `true` | `false` |
| `SMARTSHEET_MOCK_URL` | `http://localhost:8082` | `http://wiremock:8080` | _(not used)_ |
| `SMARTSHEET_ACCESS_TOKEN` | _(not used)_ | _(not used)_ | `your_real_token` |

---

## What SmartAgent Does

### Analysis (read-only, safe)
- **Duplicate Hunter** — finds exact duplicate rows
- **Quality Auditor** — detects empty/missing cell values
- **Logic Validator** — flags unrecognised status values
- **Stale Detector** — identifies stale/overdue date records

### Corrective Actions (write — requires your approval)
When you approve, SmartAgent can:
- **Add row comments** explaining each issue (SAFE)
- **Flag cells** with quality notes without changing values (SAFE)
- **Update status columns** to "Needs Review" (REVIEW)
- **Create an audit report sheet** with all findings (REVIEW)

All write operations use the official Smartsheet Python SDK and go through the HITL approval step in the UI.

---

## Environment Variables

See `backend/.env.example` for the full list.

```env
# Switch between mock and live
USE_MOCK_SERVER=true

# WireMock URL (local dev)
SMARTSHEET_MOCK_URL=http://localhost:8082

# Real Smartsheet token (production only)
SMARTSHEET_ACCESS_TOKEN=your_token_here
```

---

## Project Structure

```
smartagent/
├── docker-compose.yml          ← starts everything
├── backend/
│   ├── main.py                 ← FastAPI app
│   ├── config.py               ← environment switcher
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── graph/
│   │   ├── state.py            ← GraphState TypedDict
│   │   ├── nodes.py            ← all 9 LangGraph nodes
│   │   └── graph_builder.py   ← pipeline wiring
│   ├── routers/
│   │   ├── analyze.py          ← /api/analyze/*
│   │   └── actions.py          ← /api/actions/execute
│   └── smartsheet_client/
│       ├── mock_client.py      ← SDK → WireMock routing
│       ├── reader.py           ← list_sheets, read_sheet
│       └── writer.py           ← add_comment, flag_cell, create_audit_sheet
├── frontend/
│   └── src/
│       ├── App.jsx             ← 5-step SmartAgent UI
│       └── api/client.js       ← API calls
├── smartsheet-sdk-tests/       ← official WireMock mappings (198 scenarios)
├── scripts/
│   ├── add_custom_mappings.py  ← inject missing WireMock scenarios
│   └── wiremock_admin.py       ← debug WireMock request log
└── tests/
    ├── test_reader_writer.py   ← Phase 2 integration tests
    └── test_end_to_end.py      ← Phase 3 full flow test
```

---

## Submission Checklist

- [x] `docker compose up` starts cleanly (wiremock + backend + frontend)
- [x] `GET /api/analyze/connect` returns sheets list from WireMock
- [x] `POST /api/analyze/start` returns issues + proposed_actions
- [x] `POST /api/actions/execute` runs approved actions via SDK → WireMock
- [x] `python scripts/wiremock_admin.py` shows requests received by WireMock
- [x] Frontend shows 5-step flow: Connect → Select → Analyze → Review → Execute
- [x] HITL approval panel with SAFE / REVIEW / DESTRUCTIVE badges
- [x] Execution log showing per-action results
- [x] `.env.example` committed (no real tokens in git)
- [x] WireMock section in README with both modes explained
