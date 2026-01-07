# 🧪 Evaluation Scenarios: Vendor Spend & Compliance Agent

This document serves as the "Golden Dataset" for verifying the reasoning, tool-calling, and cross-referencing capabilities of the Multi-Search Agent.

---

## 🏗️ 1. Multi-Source Discovery (The "Apex Trap")
**Goal:** Verify the agent can identify data integrity failures between BigQuery (SQL) and Vertex AI Search (RAG).

**Prompt:**
> "Check all vendors with over $100M in spend. Compare their BigQuery renewal dates with the termination dates in their contract PDFs. Are there any critical risks or discrepancies?"

**✅ Success Criteria:**
* Calls `get_high_value_vendors` tool.
* Calls `search_contracts` tool for high-value targets.
* Identifies **Apex Logistics** specifically.
* Correcty flags the **2024 (Contract) vs. 2027 (Database)** mismatch.

---

## 🔍 2. Deep-Dive Legal Analysis
**Goal:** Verify accuracy in document grounding and specific clause extraction.

**Prompt:**
> "For Apex Logistics, can you explain exactly which page of the contract you found the termination date on and summarize the 'Termination for Convenience' clause so I know how quickly we can exit?"

**✅ Success Criteria:**
* Cites **Section 2: TERM AND TERMINATION**.
* Correctly identifies the **90-day written notice** requirement.
* Recognizes that the contract is already technically expired.

---

## 🤖 3. Reasoning & Hypothesis Testing
**Goal:** Test the agent's ability to "think" beyond retrieval and hypothesize root causes.

**Prompt:**
> "Why do you think the database shows 2027 while the contract says 2024? Look for any 'Auto-renewal' or 'Evergreen' clauses in the PDF that might explain the discrepancy."

**✅ Success Criteria:**
* Specifically searches for "Auto-renewal" or "Evergreen" terminology.
* Confirms **no such clause exists**.
* Hypothesizes a data integrity failure (e.g., SOW vs. MSA confusion).

---

## 📈 4. Productivity & Actionable Output
**Goal:** Test the agent's ability to format data (CSV/Email) and prioritize financial risk.

**Prompt A (Drafting):**
> "Draft an urgent email to the Procurement Lead for Apex Logistics. Summarize the discrepancy, cite the specific contract end date, and request a meeting to discuss the $200M uncontracted spend."

**Prompt B (Structuring):**
> "Create a CSV-ready list of all 19 expired vendors, including their name, their contract expiration date, and a recommended 'Next Action' based on the spend level."

**✅ Success Criteria:**
* Generates a professional, high-stakes email draft.
* Produces a valid, comma-separated table.
* Prioritizes **Apex Logistics** as "Critical."

---

## 🛡️ 5. Systemic Risk Assessment
**Goal:** Higher-level executive reasoning and process improvement recommendations.

**Prompt:**
> "Based on these findings, what are the top 3 systemic risks to our procurement process? Is this a failure of data entry, or a lack of legal oversight?"

**✅ Success Criteria:**
* Identifies the "Green Dashboard Illusion."
* Connects expired contracts to "Zombie Spend" liability.
* Suggests a "No Contract, No PO" technical control.

---

## 🔮 6. Predictive Risk (Future Reasoning)
**Goal:** Use temporal reasoning to identify upcoming lapses.

**Prompt:**
> "If we don't renew Alpha Systems Inc by January 15th, what legal protections (like Indemnification or SLAs) do we lose on January 16th based on the contract language?"

**✅ Success Criteria:**
* Identifies the **January 15, 2026** hard stop.
* Explains the loss of SLA penalties and new incident indemnification.