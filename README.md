# RecoverAI — Autonomous AI Revenue Recovery Agent

> **Razorpay Buildathon — Track 03: AI Revenue Recovery**  
> *Find revenue that’s slipping away and win it back with a policy-bounded AI recovery agent.*

[![Live Web Dashboard](https://img.shields.io/badge/Live%20Dashboard-Vercel-6366f1?style=for-the-badge&logo=vercel)](https://recover-ai-snowy.vercel.app)
[![Live Backend API](https://img.shields.io/badge/Live%20API-Render-009688?style=for-the-badge&logo=render)](https://recoverai-backend-ej3i.onrender.com/docs)
[![Backend Tests](https://img.shields.io/badge/Pytest-25%20Passed%20(100%25)-emerald?style=for-the-badge&logo=pytest)](./backend/tests)
[![Security](https://img.shields.io/badge/Security-Argon2id%20%2B%20PyJWT-blue?style=for-the-badge&logo=jsonwebtokens)](./backend/app/utils/security.py)

---

## 🌐 Live Cloud Deployment Links

- 🖥️ **Live Web Dashboard (UI)**: [https://recover-ai-snowy.vercel.app](https://recover-ai-snowy.vercel.app)
- ⚙️ **Live Cloud Backend API**: [https://recoverai-backend-ej3i.onrender.com](https://recoverai-backend-ej3i.onrender.com)
- 📖 **Interactive Swagger Docs**: [https://recoverai-backend-ej3i.onrender.com/docs](https://recoverai-backend-ej3i.onrender.com/docs)

---

## 1. Problem Statement

Businesses lose **15% to 30% of potential revenue** to failed payments, checkout drop-offs, network timeouts, and expired cards. Naive automated retries are dangerous—they risk duplicate charges, customer frustration, spammed notifications, and compliance violations.

---

## 2. Solution: RecoverAI

**RecoverAI** is an autonomous revenue recovery agent built with **LangGraph** and a **Deterministic Policy Engine**. It detects failed payments, diagnoses root causes using AI, recommends bounded interventions, validates every decision against strict merchant guardrails, and executes safe recoveries with an immutable audit trail.

---

## 3. Core Closed-Loop System Architecture

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
          * diagnosis (Root cause)
          * recovery_score (0.0 to 1.0)
          * recommended_action (RETRY, REMINDER, ESCALATE, STOP)
          * confidence (0.0 to 1.0)
          * reason
        - Fallback: On LLM timeout / malformed output -> ESCALATE + AI_ERROR audit log
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
  - RETRY payment             - Store Policy Rejection Reason
  - REMINDER link             - Human-in-the-Loop Override
        │                         │
        +------------+------------+
                     │
                     ▼
        [ Payment Status Verification ]
                     │
                     ▼
         [ Immutable Audit Log Entry ]
                     │
                     ▼
      [ Real-Time 4s Auto-Refresh Dashboard Metrics ]
```

---

## 4. Key Features & Guardrails

- ⚡ **Failed Payment Interception**: Idempotent Razorpay webhook listener for `payment.failed`, `payment.authorized`, and `payment.captured` with HMAC SHA256 signature verification.
- 🧠 **LangGraph AI Agent**: Structured JSON output returning diagnosis, recovery score, recommended action, and confidence.
- 🛡️ **Non-Negotiable Policy Guardrails**:
  - `MAX_AUTO_RETRY = 1` (Prevents infinite retries or notification spamming)
  - `MAX_AUTO_RECOVERY_AMOUNT = ₹5,000` (High-value payments require merchant approval)
  - `MIN_AI_CONFIDENCE = 80%` (Low AI confidence escalates to merchant support)
  - `DUPLICATE_PAYMENT_PROTECTION` (Halts action if payment is already captured)
- 🔒 **Argon2id Password Security**: Password hashing using `argon2-cffi` + `PyJWT` Bearer authentication.
- 🏢 **Merchant-Level Data Isolation**: All data queries derive merchant identity from JWT tokens (cross-merchant access forbidden).
- 👤 **Human-in-the-Loop Overrides**: Merchant dashboard buttons for manual retry approval or escalation.
- 📜 **Immutable Audit Log**: Every event, policy check, actor, and outcome is logged with timestamps.
- 📊 **Real-Time Auto-Refresh Dashboard**: React SaaS UI with Recharts visualizations auto-refreshing every 4 seconds.
- 🧪 **Batch Evaluation Benchmark**: Evaluates 100 synthetic payment failure records (`data/synthetic_payments.csv`) to show measured revenue recovered across a batch.

---

## 5. The 5 Live Demo Scenarios

| Scenario | Input Case | AI Recommendation | Policy Check | Final Status | Outcome |
|---|---|---|---|---|---|
| **1. Successful Recovery** | ₹3,500 Bank Error (0 retries) | `RETRY` (89% conf) | **APPROVED** | **RECOVERED** | +₹3,500 Recovered |
| **2. Retry Blocked** | ₹2,000 Failure (retry_count=1) | `RETRY` | **REJECTED** (Max Retry) | **ESCALATED** | Sent to Merchant UI |
| **3. Low Confidence** | ₹3,200 Unknown Error Code 99 | `ESCALATE` (61% conf) | **REJECTED** (Low Conf) | **ESCALATED** | Sent to Merchant UI |
| **4. High Value Payment** | ₹25,000 Failure (> ₹5,000) | `RETRY` | **REJECTED** (Max Amount) | **ESCALATED** | Sent to Merchant UI |
| **5. Already Captured** | Webhook for completed payment | `STOP` | **STOPPED** | **STOPPED** | +₹0 Duplicate Charge |

---

## 6. Tech Stack

- **Frontend**: React, Vite, Tailwind CSS, Recharts, Axios, React Router, Lucide Icons.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, PostgreSQL (with SQLite dev fallback).
- **Security**: Argon2id (`argon2-cffi`), PyJWT, Passlib.
- **AI Agent**: LangGraph, LangChain, Google Gemini / OpenAI (with fallback scoring engine).
- **Payments**: Razorpay Test Mode API & Webhook handler.

---

## 7. Quick Start & Local Setup

### Prerequisites
- Python 3.11+
- Node.js v18+ & npm

### Step 1: Clone Repository
```bash
git clone https://github.com/shrutigadhe/RecoverAI.git
cd RecoverAI
```

### Step 2: Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
*Backend API Docs will be live at:* `http://localhost:8000/docs`

### Step 3: Frontend Setup (Open a New Terminal)
```bash
cd frontend
npm install
npm run dev
```
*Frontend Dashboard will be live at:* `http://localhost:3000`

---

## 8. Running Automated Test Suite

Run the backend pytest suite (**25 / 25 tests passing 100%**):
```bash
cd backend
python -m pytest tests/ -v
```

---

## 9. Docker Deployment

Deploy all services (PostgreSQL, Backend, Frontend) with Docker Compose:
```bash
docker compose up -d --build
```

---

## 10. License

Built for the **Razorpay Buildathon 2026** under the **AI Revenue Recovery** track.
