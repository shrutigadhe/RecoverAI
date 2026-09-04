# RecoverAI — Autonomous AI Revenue Recovery Agent

> **Razorpay AI / Agentic Commerce Buildathon — Track 03: AI Revenue Recovery**  
> *Detect revenue at risk, diagnose root causes, execute policy-bounded recovery actions, and measure money recovered with an immutable audit trail.*

[![Live Dashboard](https://img.shields.io/badge/Live%20Dashboard-Vercel-6366f1?style=for-the-badge&logo=vercel)](https://recover-ai-snowy.vercel.app)
[![Live Backend API](https://img.shields.io/badge/Live%20Backend-Render-00e599?style=for-the-badge&logo=render)](https://recoverai-backend-ej3i.onrender.com)
[![Pytest Coverage](https://img.shields.io/badge/Pytest-25%20PASSED-emerald?style=for-the-badge&logo=pytest)](./backend/tests)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776ab?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb?style=for-the-badge&logo=react)](https://react.dev)

---

## 🌐 Live Hackathon Links

- 🖥️ **Live Web Dashboard (Vercel)**: [https://recover-ai-snowy.vercel.app](https://recover-ai-snowy.vercel.app)
- ⚙️ **Live Backend API (Render)**: [https://recoverai-backend-ej3i.onrender.com](https://recoverai-backend-ej3i.onrender.com)
- 📚 **Interactive Swagger API Docs**: [https://recoverai-backend-ej3i.onrender.com/docs](https://recoverai-backend-ej3i.onrender.com/docs)
- 🔐 **Register Merchant Account**: [https://recover-ai-snowy.vercel.app/register](https://recover-ai-snowy.vercel.app/register)

---

## 1. Problem Statement

Businesses lose **15% to 30% of potential revenue** due to failed payments, checkout drop-offs, temporary banking server timeouts, and expired payment details. 

Standard retry mechanisms fail because they treat every failure identically—either retrying blindly (risking spammed customers or duplicate charges) or failing silently without recovering money.

---

## 2. Solution: RecoverAI

**RecoverAI** is an autonomous AI agent built on **LangGraph** and a **Deterministic Policy Engine**. It intercepts payment failures, diagnoses root causes, recommends bounded recovery interventions, validates every financial decision against strict merchant policy guardrails, and executes safe recoveries with an immutable audit trail.

### 🛡️ Core Security Principle
> **"AI recommends. Policy authorizes. Backend executes. Verification confirms. Audit records."**  
> The AI agent **NEVER** has direct, unchecked control over payment APIs. Every automated action must be authorized by a deterministic policy engine.

---

## 3. Closed-Loop System Architecture

```
+-----------------------------------------------------------------------------------+
|                              CLOSED LOOP RECOVERY FLOW                            |
+-----------------------------------------------------------------------------------+

 Razorpay Webhook Event / Synthetic Payment Failure
                     │
                     ▼
       [ Webhook Handler & Signature Verification ]
                     │ (HMAC SHA256 & Idempotency Check)
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
        - Evaluates proposed action against merchant guardrails:
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
  - RETRY payment             - Store Policy Rejection Reason
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
      [ Dashboard Metrics & Analytics Update ]
```

---

## 4. Key Features

- ⚡ **Idempotent Webhook Listener**: Intercepts `payment.failed`, `payment.authorized`, and `payment.captured` with HMAC SHA256 signature verification.
- 🧠 **LangGraph AI Diagnosis**: Diagnoses root causes (bank timeouts, network errors, insufficient funds, expired cards, unknown errors) and predicts explainable recovery scores.
- 🛡️ **Bounded Policy Guardrails**: Enforces non-negotiable financial limits (`MAX_AUTO_RETRY=1`, `MAX_AUTO_RECOVERY_AMOUNT=₹5,000`, `MIN_AI_CONFIDENCE=80%`).
- 🔒 **Duplicate Charge Protection**: Verifies real-time payment status before any retry action. Stops processing if payment is already captured.
- 🔐 **Argon2id & PyJWT Security**: Passwords are hashed using **Argon2id** (`argon2-cffi`); all endpoints enforce **PyJWT** Bearer authentication with isolated merchant data scoping.
- 👤 **Human-in-the-Loop Dashboard**: Merchant approval and escalation overrides for high-value or low-confidence payments.
- 📜 **Immutable Audit Trail**: Logs every single event (`PAYMENT_FAILED`, `AI_DIAGNOSIS`, `POLICY_APPROVED`, `POLICY_REJECTED`, `RETRY_EXECUTED`, `PAYMENT_RECOVERED`, `ESCALATED`, `STOPPED`).
- 📊 **Dynamic SaaS Dashboard**: Modern React + Vite + Tailwind CSS dashboard with Recharts visualizations and **4-second real-time auto-refresh polling**.
- 🧪 **100-Case Batch Evaluation**: Benchmarks recovery algorithms over a 100-record synthetic payment dataset (`data/synthetic_payments.csv`).

---

## 5. Five Interactive Demo Scenarios

The live dashboard includes a 1-click **Simulate Live Demo Scenarios** panel:

| Scenario | Details | AI Recommendation | Policy Result | Final Status |
|---|---|---|---|---|
| **1. Successful Recovery** | ₹3,500 • Temporary Bank Error • 0 Retries | `RETRY` (Confidence: 89%) | **APPROVED** | **RECOVERED** (+₹3,500) |
| **2. Retry Blocked** | ₹2,000 • Temporary Failure • Retry Count = 1 | `RETRY` | **REJECTED** (Max Retry = 1) | **ESCALATED** |
| **3. Low Confidence** | ₹3,200 • Unknown Gateway Error Code 999 | `ESCALATE` (Confidence: 61%) | **REJECTED** (< 80% Confidence) | **ESCALATED** |
| **4. High-Value Payment** | ₹25,000 • Temporary Bank Error | `RETRY` | **REJECTED** (> ₹5,000 Limit) | **ESCALATED** |
| **5. Already Captured** | Webhook for payment already captured | `STOP` | **STOPPED** | **STOPPED** (+₹0) |

---

## 6. Tech Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, PostgreSQL (with SQLite dev fallback).
- **Security**: Argon2id (`argon2-cffi`), PyJWT, HMAC SHA256.
- **AI Engine**: LangGraph, LangChain, Google Gemini API (with fallback scoring engine).
- **Frontend**: React 18, Vite, Tailwind CSS, Recharts, Axios, React Router, Lucide Icons.
- **Infrastructure**: Render (Backend & Postgres), Vercel (Frontend), Docker & Docker Compose.

---

## 7. Quick Start & Local Setup

### Prerequisites
- Python 3.11+
- Node.js v18+ & npm

### Step 1: Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
```

Start Backend Server:
```bash
python -m uvicorn app.main:app --reload --port 8000
```
*API docs will be available at:* `http://localhost:8000/docs`

### Step 2: Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```
*Dashboard will be available at:* `http://localhost:3000`

---

## 8. Running Automated Pytest Suite

Run the full suite of **25 automated backend unit tests**:
```bash
cd backend
python -m pytest tests/ -v
```

Output:
```
============================= 25 passed in 9.94s =============================
```

---

## 9. Environment Variables Configuration

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

## 10. Docker Deployment

Deploy full stack using Docker Compose:
```bash
docker compose up -d --build
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

---

## 11. Razorpay Webhook Configuration Guide

To receive live Razorpay webhooks:
1. Log in to [Razorpay Dashboard](https://dashboard.razorpay.com/) (Test or Live Mode).
2. Go to **Settings** → **Webhooks** → **Add New Webhook**.
3. Set Webhook URL: `https://recoverai-backend-ej3i.onrender.com/api/webhook/razorpay`
4. Set Secret: `your_webhook_secret` (must match `RAZORPAY_WEBHOOK_SECRET` in backend `.env`).
5. Select Events: `payment.failed`, `payment.authorized`, `payment.captured`.
