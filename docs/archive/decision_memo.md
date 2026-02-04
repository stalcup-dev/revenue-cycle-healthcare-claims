# Decision Memo

**Problem:**
Payer Yield Gap $ + denial-driven leakage in mature cohorts

**What we found:**
Top 5 denial categories/HCPCS responsible for X% of proxy leakage

**What we recommend (3 levers):**
- Front-end edit tightening for “Invalid data”
- Policy/documentation workflow for “Medically unnecessary”
- Bundling/modifier guardrails for “Bundled/no pay”

**Ops plan:**
Workqueue triage vs FIFO; capacity = N/day; expected recovery = base/best/worst assumptions

**Risks:**
Proxy dollars, missing workflow events, dimension limitations

**Decision ask:**
Approve pilot runbook + monitoring gates
