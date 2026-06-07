# HouseSignal AI Agents

HouseSignal AI is organized as a routed multi-agent system for commercial real estate investment analysis. Agents should stay modular, auditable, and conservative: they summarize evidence, surface assumptions, and avoid guaranteeing investment outcomes.

## Core Rules

- Never hardcode API keys, database passwords, JWT secrets, or service-role keys.
- Never print secrets or include them in logs, exceptions, prompts, or Streamlit UI output.
- Use environment variables loaded from `.env` locally and platform secrets in deployment.
- Keep RentCast, OpenAI, and Supabase service keys backend-only.
- Cache paid/free-tier API responses before calling external services again.
- Log API usage metadata, not secret values or full sensitive payloads.
- Treat uploaded documents as private user data.
- Prefer structured outputs that can be reviewed and tested.

## Router Agent

Routes a user request to the right specialized agent. It should inspect the requested task, selected document type, available context, and current deal state.

Primary destinations:

- Lease Agreement Agent
- Rent Roll Agent
- Offering Memorandum Agent
- T12 Financial Statement Agent
- Property Condition Report Agent
- Financial Analysis Agent
- Risk Analysis Agent
- Market Data Agent
- Recommendation Agent

## Document Agents

Each document agent receives retrieved chunks from the RAG layer plus document metadata. It should return concise findings, extracted fields, red flags, and follow-up questions.

### Lease Agreement Agent

Focus:

- Lease term, renewal options, rent escalations
- Tenant obligations and landlord obligations
- Default clauses, assignment/subletting, termination language
- Unusual concessions or risk terms

### Rent Roll Agent

Focus:

- Unit mix, in-place rent, vacancy, lease expirations
- Rent concentration and tenant rollover risk
- Below-market/above-market rent signals
- Data quality issues and missing fields

### Offering Memorandum Agent

Focus:

- Broker assumptions versus supporting evidence
- Market positioning, comps, pro forma claims
- Cap rate, NOI, rent growth, occupancy assumptions
- Missing diligence items

### T12 Financial Statement Agent

Focus:

- Revenue, expenses, NOI, expense ratio
- One-time items versus recurring operations
- Debt service coverage and cash-flow quality
- Variance versus OM/pro forma assumptions

### Property Condition Report Agent

Focus:

- Immediate repairs, deferred maintenance, capex schedule
- Life-safety, roof, HVAC, plumbing, electrical risks
- Cost ranges and underwriting reserves
- Impact on recommendation and downside risk

## Analysis Agents

### Financial Analysis Agent

Combines extracted document facts with underwriting inputs to estimate NOI, cap rate, cash-on-cash return, debt service coverage, breakeven occupancy, and sensitivity scenarios.

### Risk Analysis Agent

Scores downside risk across market, tenant, lease, physical condition, financing, data quality, and concentration risk.

### Market Data Agent

Uses cached Zillow/FRED/RentCast/Supabase-backed data to summarize local trend, rent demand, affordability pressure, and comparable market behavior.

### Recommendation Agent

Combines valuation, financial metrics, risk scoring, market signals, and document evidence into a recommendation label. It must include assumptions and caveats.

## RAG Layer

Supported document types:

1. Lease agreements
2. Rent rolls
3. Offering memorandums
4. T12 financial statements
5. Property condition reports

Pipeline:

```text
Upload -> classify document type -> extract text/tables -> chunk -> embed or keyword-index -> retrieve -> specialized agent -> recommendation context
```

## Auditability

Every recommendation should be traceable to:

- Input assumptions
- Market data snapshot date
- External API cache status
- Retrieved document chunks
- Agent outputs
- Final score components
