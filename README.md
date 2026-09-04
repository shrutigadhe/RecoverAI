# RecoverAI — AI Revenue Recovery Agent

> **Autonomous, Policy-Bounded AI Revenue Recovery Agent for Agentic Commerce**

[![Backend Tests](https://img.shields.io/badge/pytest-18%20passed-emerald)](./backend/tests)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-blue)](https://react.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38bdf8)](https://tailwindcss.com)

---

## 1. Problem Statement

Businesses lose up to **15-30% of potential revenue** due to failed payments, checkout abandonment, temporary banking disruptions, and expired cards. Standard retry mechanisms fail because they treat every failure identically—either retrying blindly (risking customer frustration or duplicate charges) or failing silently.

---

## 2. Solution: RecoverAI

**RecoverAI** is an intelligent revenue recovery agent built on **LangGraph** and a **Deterministic Policy Engine**. It intercepts payment failures, diagnoses root causes, recommends bounded recovery actions, validates every financial decision against merchant guardrails, and executes safe recoveries with an immutable audit trail.

---

## 3. Core Architecture

```
+-----------------------------------------------------------------------------------+
|                              CLOSED LOOP RECOVERY FLOW                            |
+-----------------------------------------------------------------------------------+

 Razorpay Webhook Event / Synthetic Failure Event
                     │
                     ▼
       [ Webhook Handler & Idempotency Check ]
                     │
                     ▼
       [ PostgreSQL Database: Payment & Customer History ]
                     │
                     ▼
         [ Recovery Case Created ]
                     │
                     ▼
      [ LangGraph AI Agent Diagnosis & Recommendation ]
        - Structured JSON Output:
          * Diagnosis (Root cause)
          * Recovery Score (0.0 to 1.0)
          * Recommended Action (RETRY, REMINDER, ESCALATE, STOP)
          * Confidence Level (0.0 to 1.0)
                     │
                     ▼
      [ Deterministic Policy / Guardrail Engine ]
        - Checks:
          * MAX_AUTO_RETRY (1)
          * MAX_AUTO_RECOVERY_AMOUNT (₹5,000)
          * MIN_AI_CONFIDENCE (80%)
          * Duplicate Charge Protection
                     │
        +------------+------------+
        │                         │
     [APPROVED]              [REJECTED]
        │                         │
        ▼                         ▼
 [Execute Bounded Action]   [Escalate Case to Merchant]
  - RETRY payment             - Store Escalation Reason
  - REMINDER message          - Human-in-the-Loop Override
        │                         │
        +------------+------------+
                     │
                     ▼
        [ Verify Payment Outcome ]
                     │
                     ▼
         [ Immutable Audit Log Entry ]
                     │
                     ▼
      [ Dashboard & Analytics Metrics Update ]
```

---

## 4. Key Features

- ⚡ **Failed Payment Interception**: Idempotent Razorpay webhook listener for `payment.failed`, `payment.authorized`, and `payment.captured`.
- 🧠 **LangGraph AI Diagnosis**: Diagnoses failure root causes and predicts explainable recovery scores.
- 🛡️ **Bounded Policy Guardrails**: Enforces non-negotiable financial limits (`MAX_AUTO_RETRY=1`, `MAX_AUTO_RECOVERY_AMOUNT=₹5,000`, `MIN_AI_CONFIDENCE=80%`).
- 🔒 **Duplicate Charge Prevention**: Verifies real-time payment status before any retry action.
- 👤 **Human-in-the-Loop Escalation**: Provides merchant manual override and approval for escalated high-value or low-confidence payments.
- 📜 **Immutable Audit Trail**: Logs every event, policy evaluation, action, and outcome with timestamped metadata.
- 📊 **Real-time Analytics Dashboard**: Modern SaaS React frontend with Recharts visualization.
- 🧪 **Batch Evaluation**: Benchmarks recovery algorithms over a 100-case synthetic payment dataset.

---

## 5. Tech Stack

- **Frontend**: React, Vite, Tailwind CSS, Recharts, Axios, React Router, Lucide Icons.
- **Backend**: Python, FastAPI, Pydantic v2, SQLAlchemy 2.0, PostgreSQL (with SQLite dev fallback).
- **AI Engine**: LangGraph, LangChain, Google Gemini / OpenAI (with fallback scoring engine).
- **Payments**: Razorpay Test Mode API & Webhook integration.

---

## 6. Quick Start & Setup

### Prerequisites
- Python 3.11+
- Node.js v18+ & npm
- PostgreSQL (Optional; falls back to local SQLite if PostgreSQL is not running)

### Step 1: Clone & Setup Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
```

Run Backend Server:
```bash
uvicorn app.main:app --reload --port 8000
```
Backend API interactive docs will be available at: `http://localhost:8000/docs`

### Step 2: Setup Frontend
```bash
cd ../frontend
npm install
npm run dev
```
Dashboard will be available at: `http://localhost:3000`

---

## 7. Environment Variables Configuration

Refer to `backend/.env.example`:

```ini
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/recoverai
DEMO_MODE=true
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
LLM_PROVIDER=gemini
LLM_API_KEY=your_gemini_api_key
MAX_AUTO_RETRY=1
MAX_AUTO_RECOVERY_AMOUNT=5000.0
MIN_AI_CONFIDENCE=0.80
```

---

## 8. Running Automated Tests

Run backend pytest suite (18 unit tests):
```bash
cd backend
python -m pytest tests/ -v
```

---

## 9. Batch Evaluation Results

Run batch evaluation over `data/synthetic_payments.csv` (100 synthetic payment failure records):

Endpoint: `POST /api/evaluation/run` or via UI at `http://localhost:3000/evaluation`.
