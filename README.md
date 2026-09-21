# FPL Edge — Modern FPL Analytics & Decision-Support Platform

**FPL Edge** is an advanced Fantasy Premier League decision-support application built with Next.js, FastAPI, PuLP MILP Optimization, and a grounded AI explainer.

## Architecture & Principles
- **Decision Support System**: Helps managers make transfer, captaincy, and chip decisions while leaving total control in the user's hands.
- **Deterministic Analytics Pipeline**: Decoupled xMinutes, component expected points (xP), and Mixed Integer Linear Programming (MILP) optimization.
- **Grounded AI Assistant**: The LLM is an explainer that works strictly on deterministic `DECISION_CONTEXT` payloads without hallucinating predictions.
- **Timestamp Transparency**: Every projection and recommendation displays model version, data timestamp, and deadline timestamp.

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js v18+

### Setup Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Start Backend API Server
```bash
cd /Users/miguelpolijerez/.gemini/antigravity/scratch/fpl-edge
source venv/bin/activate
python3 -m uvicorn services.api.main:app --reload --port 8000
```

### Start Frontend Application
```bash
cd /Users/miguelpolijerez/.gemini/antigravity/scratch/fpl-edge/apps/web
npm install
npm run dev
```

### Running Tests & Evaluation
```bash
source venv/bin/activate
pytest tests/
```
