# 💰 Snowflake FinOps Dashboard with Cortex AI  
**Powered by Streamlit (Native in Snowflake) + ACCOUNT_USAGE + Snowflake Cortex LLMs**

![FinOps Architecture](./assets/finops_architecture.png)



---

This repository demonstrates how to build a **production-grade FinOps platform inside Snowflake**. Users gain interactive cost visibility, optimization insights, and natural language FinOps analysis with **a fully native Streamlit UI** and **Snowflake Cortex AI**.

No external BI tools.  
No external APIs.  
All processing and governance occur within Snowflake.

---

## 🚀 Key Capabilities

| Capability | Benefit |
|------------|---------|
| Curated FinOps tables | Fast, predictable usage & cost reporting |
| Warehouse-level cost breakdown | Identify waste and inefficiencies |
| Query performance analytics | Detect inefficient workloads |
| Storage growth tracking | Understand long-term storage cost drivers |
| Cortex AI executive insights | Business-ready narrative summaries |
| ChatGPT-style FinOps chat | Speak your questions, get actionable answers |
| Streamlit native in Snowflake | Secure, serverless dashboard |

---

## 🧱 High-Level Architecture

```text
     ┌─────────────────────────────┐
     │   Snowflake ACCOUNT_USAGE   │
     │ (Metering, Queries, Storage)│
     └─────────────┬───────────────┘
                   │ Curated Daily Aggregates
                   ▼
     ┌─────────────────────────────┐
     │ FINOPS.SNOWFLAKE_USAGE      │
     │ - DAILY_METERING            │
     │ - DAILY_WAREHOUSE_METERING  │
     │ - DAILY_QUERY_METRICS       │
     │ - DAILY_STORAGE             │
     │ - HOURLY_USAGE_HEATMAP      │
     └─────────────┬───────────────┘
                   │
                   ▼
     ┌─────────────────────────────┐
     │ Streamlit FinOps Dashboard  │
     │ (Native in Snowflake)       │
     │ - KPI Metrics               │
     │ - Cost Trends               │
     │ - Performance Charts        │
     │ - AI Insights               │
     │ - Cortex Chat               │
     └─────────────┬───────────────┘
                   │
                   ▼
     ┌─────────────────────────────┐
     │ Snowflake Cortex AI         │
     │ - Executive insights        │
     │ - Optimization guidance     │
     │ - Conversational FinOps     │
     └─────────────────────────────┘
