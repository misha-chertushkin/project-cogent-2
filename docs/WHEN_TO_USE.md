# 🧭 When to Use: Vendor Spend & Compliance Agent

This demonstration showcases a **Hybrid Search & Reasoning** pattern (often referred to as RAG + Structured Data). It is designed to solve the common enterprise challenge where **Systems of Record** (Databases) become decoupled from **Systems of Truth** (Legal Contracts).

---

## 🎯 Target Audience
* **Procurement Leadership:** Looking to automate the auditing of high-spend vendor relationships.
* **Legal & Compliance Teams:** Needing to verify contract clauses across heterogeneous document libraries.
* **IT/AI Architects:** Interested in "beyond-basic-RAG" architectures that combine SQL and Unstructured search.

---

## ✅ Ideal Use Cases

| Scenario | Strategic Value |
| :--- | :--- |
| **"Source of Truth" Reconciliation** | When a customer's database renewal dates frequently conflict with the physical PDFs. This is the core "Apex Logistics Trap" demo. |
| **Heterogeneous Contract Analysis** | When vendor contracts are on *vendor paper* (different layouts/phrasing) rather than a single standardized company template. |
| **High-Volume Risk Auditing** | Using BigQuery to filter "High-Value" or "High-Risk" vendors first, then using Vertex AI Search to perform a deep-dive legal audit on the subset. |
| **Legacy ERP Augmentation** | Providing an "Intelligent Layer" over a legacy system that is too difficult or expensive to modify directly. |

---

## 🚀 Key Technical Differentiators

### 1. The Reasoning Discrepancy Pattern
Unlike a standard search bot that just summarizes a document, this agent **cross-references** two disparate data sources. It identifies when the database is "lying" compared to the legal ground truth in the PDF.

### 2. Cost-Optimized Scaling
The architecture demonstrates how to use the right tool for the job:
* **BigQuery:** Handles massive scale structured filtering (Who are the vendors?).
* **Vertex AI Search:** Handles semantic retrieval (What does the contract actually say?).
* **Gemini:** Acts as the "Logic Layer" to synthesize the two.



---

## ❌ When *Not* to Use

* **Sub-Second Transactional Fraud:** If the use case requires microsecond latency for a high-volume transaction, an LLM-based agent is likely too slow. 
* **Homogeneous Form Processing:** If every single document is identical (e.g., a standard W-9 form), **Document AI (Form Parser)** is a more cost-effective and faster solution than Generative AI Search.
* **Public Web Data Only:** This demo is specifically for **Private Enterprise Data**. If the customer only wants to search the public web, use a standard Vertex AI Search web-indexing setup.

---

## 💡 Discovery Questions for Customers
Use these questions to qualify a lead before showing this demo:
1. *"How do you currently verify that the renewal dates in your database match the actual termination clauses in your legal PDFs?"*
2. *"When a contract is updated via an amendment, how long does it take for that change to be reflected in your spend reporting?"*
3. *"Are you looking for a way to let your procurement team ask natural language questions about vendor compliance without manual audits?"*

---

## 🛠️ Deployment Summary
* **Complexity:** Low (Single Makefile setup)
* **Cloud Costs:** Minimal (Uses pay-as-you-go BigQuery and Vertex Search tiers)
* **Time to Demo:** ~15 minutes (after 10-minute initial indexing)