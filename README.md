# FPL Edge — Modern FPL Analytics & Decision-Support Platform

**FPL Edge** is a Fantasy Premier League decision-support application built with React, FastAPI, PuLP optimisation, and a grounded plan explainer.

## Architecture & Principles
- **Decision Support System**: Helps managers make transfer, captaincy, and chip decisions while leaving total control in the user's hands.
- **Role-aware Forecasting**: Team-reconciled expected minutes, sample-size shrinkage, and component expected points distributions.
- **Patient Transfer Planning**: Values saved transfers, rejects marginal moves, prevents short-horizon churn, and treats rolling as a first-class recommendation.
- **Strict Captaincy Guardrails**: Only credible, available outfield starters can enter the captain shortlist.
- **Grounded Plan Notes**: The language model explains the exact saved recommendation and cannot create a separate plan.
- **Mini-league Intelligence**: Imports current classic leagues, standings, effective ownership, differentials, and rank threats.
- **Timestamp Transparency**: Every projection and recommendation displays model version, data timestamp, and deadline timestamp.

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js v18+

### Setup Python Virtual Environment
```bash
python3 -m venv venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Start Backend API Server
```bash
cd /Users/miguelpolijerez/.gemini/antigravity/scratch/fpl-edge
source .venv/bin/activate
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
source .venv/bin/activate
pytest tests/
```
