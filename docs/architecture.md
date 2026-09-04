# RecoverAI — Architecture & Design Document

## System Closed Loop Flow

```
+-------------------------------------------------------------------------------+
|                               RECOVERAI ARCHITECTURE                          |
+-------------------------------------------------------------------------------+

 Razorpay Webhook Event / Synthetic Failure Event
                     │
                     ▼
       [ Webhook Handler & Signature Verification ]
                     │ (Idempotency Check)
                     ▼
       [ PostgreSQL DB: Payment & Customer Record ]
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
          * Confidence Level
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

## Core Architectural Guardrail Principle

> **"The AI Agent MUST NEVER have direct, unmitigated access to payment APIs."**

All financial actions flow through a 2-stage verification:
1. **AI Layer (LangGraph)**: Probabilistic reasoning, scoring, and recommendation.
2. **Policy Engine**: Deterministic boolean logic rules that reject unauthorized or risky actions.
