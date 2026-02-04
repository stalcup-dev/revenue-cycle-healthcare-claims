# Interview Defense Sheet

**Why synthetic is OK:**
- Demonstrates system architecture, logic, and analytics without PHI or real dollars
- Enables rapid prototyping and sharing

**Why denied dollars are a proxy:**
- Submitted charges are not present in DE-SynPUF; must estimate using allowed-line medians
- Denied Potential Allowed $ is a ranking proxy for opportunity size, not guaranteed collectible cash; actual recovery depends on policy coverage, documentation, and appeal outcomes.

**Why “observed payer-paid” is payer-side and recoupments separated:**
- Only payer-side payments are visible in the Carrier file; patient liability is excluded
- Recoupments/negative payments are tracked separately to avoid distorting net paid

**Why cohort maturity is mandatory:**
- Ensures claims have had time to resolve; avoids bias from immature/unresolved claims

**What you’d validate in production:**
- Remit-level true paid amounts
- Appeal outcomes and overturn rates
- Contract terms and payer-specific rules

This sheet turns potential weaknesses into strengths and demonstrates readiness for real-world deployment.