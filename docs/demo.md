# RecoverAI — Hackathon Demo Guide

## Quick Demo Checklist

1. Start Backend: `uvicorn app.main:app --reload` (Port 8000)
2. Start Frontend: `npm run dev` (Port 3000)
3. Open Browser at `http://localhost:3000`

---

## Demonstrating the 5 Core Scenarios

From the Overview page dashboard, click the 1-click simulation buttons in the **Simulate Live Demo Scenarios** panel:

### Scenario 1 — Successful Auto Recovery
- **Input**: ₹3,500 payment failure due to temporary bank server error.
- **AI Recommendation**: `RETRY` (Confidence: 89%).
- **Policy Check**: `APPROVED` (Amount ≤ ₹5,000, Retry = 0).
- **Result**: `RECOVERED` (₹3,500 captured).

### Scenario 2 — Retry Limit Reached
- **Input**: ₹2,000 payment failure with previous retry count = 1.
- **AI Recommendation**: `RETRY`.
- **Policy Check**: `REJECTED` (Rule: `MAX_RETRY_LIMIT`).
- **Result**: `ESCALATED` to merchant.

### Scenario 3 — Low AI Confidence
- **Input**: ₹3,200 payment failure due to unknown error code 99.
- **AI Recommendation**: `ESCALATE` (Confidence: 61%).
- **Policy Check**: `REJECTED` (Rule: `MIN_CONFIDENCE_THRESHOLD`).
- **Result**: `ESCALATED` to merchant.

### Scenario 4 — High-Value Payment
- **Input**: ₹25,000 payment failure.
- **AI Recommendation**: `RETRY`.
- **Policy Check**: `REJECTED` (Rule: `MAX_AMOUNT_LIMIT` > ₹5,000).
- **Result**: `ESCALATED` to merchant.

### Scenario 5 — Duplicate Payment Prevention
- **Input**: Webhook received for payment already marked `captured`/`RECOVERED`.
- **Policy Check**: `STOP` (Rule: `DUPLICATE_PAYMENT_PROTECTION`).
- **Result**: `STOPPED` (₹0 additional charge).

---

## Demonstrating Batch Evaluation

1. Navigate to **Batch Evaluation** in the sidebar.
2. Click **Run Batch Evaluation (100 Cases)**.
3. Observe real-time dynamic metrics calculated over `data/synthetic_payments.csv`.
