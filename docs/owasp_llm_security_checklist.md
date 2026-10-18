<!--
OWASP Top 10 for LLMs: Production Security Architecture Checklist
=================================================================
Description: Comprehensive enterprise AppSec checklist and threat modeling guide for production
             deployments of Large Language Models (LLMs), RAG systems, and autonomous agent swarms.
Enterprise Mapping: Primary reference for Security Architects, DevSecOps leads, and AI Engineers
                    securing generative AI applications against adversarial exploitation.

Official Documentation References:
- OWASP Top 10 for LLMs (2025 Standard): https://owasp.org/www-project-top-10-for-large-language-model-applications/
- MITRE ATLAS (Adversarial Threat Landscape for AI Systems): https://atlas.mitre.org/
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- CISA & UK NCSC Guidelines for Secure AI System Development: https://www.cisa.gov/resources-tools/resources/guidelines-secure-ai-system-development
-->

# OWASP Top 10 for LLMs: Enterprise Production Security Checklist

This document provides a hardening checklist mapping directly to the official OWASP Top 10 for Large Language Model Applications.

---

## The OWASP Top 10 for LLMs Threat Matrix

| Threat ID | Vulnerability Category | Primary Attack Vector | Enterprise Mitigation Strategy |
|---|---|---|---|
| **LLM01** | **Prompt Injection** | Direct user prompts or indirect malicious content in RAG documents overriding system behavior. | XML boundary tags (`<user_data>`), heuristic WAF filters, separate LLM calls for untrusted data analysis. |
| **LLM02** | **Sensitive Information Disclosure** | Model leaking internal PII, API secrets, or confidential context during generation. | Egress DLP filters, automated PII redaction, cryptographic canary token exfiltration traps. |
| **LLM03** | **Supply Chain Vulnerabilities** | Poisoned third-party models, compromised training weights, malicious Pickle files. | Use Safetensors over Pickle (`torch.load`), verify model cryptographic checksums, lock dependency versions. |
| **LLM04** | **Data and Model Poisoning** | Adversarial manipulation of training corpora or RAG vector databases. | Cryptographically sign knowledge base documents, enforce RBAC on vector DB upsert endpoints. |
| **LLM05** | **Improper Output Handling** | Downstream execution of un-sanitized LLM completions (XSS, SSRF, SQL Injection). | Treat all LLM output as untrusted user input; contextual HTML entity encoding, parameterized SQL queries. |
| **LLM06** | **Excessive Agency** | Autonomous agents performing destructive real-world actions without human oversight. | Human-in-the-loop (HITL) approvals for state-altering actions, granular read-only scopes on API tools. |
| **LLM07** | **System Prompt Leakage** | Extraction of proprietary business logic, prompt IP, or hidden guardrails. | Canary tokens in prompt memory, output filtering blocking prompt reproduction, defense-in-depth isolation. |
| **LLM08** | **Vector and Embedding Weaknesses** | Embedding inversion reconstructing original text; poisoning vector search results. | Encrypt vector database collections at rest, restrict embedding dimensions and API endpoints. |
| **LLM09** | **Misinformation & Hallucination** | Fabricated technical details, fictitious citations, security vulnerabilities. | Groundedness validation (RAG Triad), citation provenance tracking, temperature $\le 0.2$ for factual queries. |
| **LLM10** | **Unbounded Consumption** | Denial of Wallet (DoW) and Denial of Service (DoS) through runaway token loops. | Hard token ceilings per request, semantic caching (Redis), rate-limiting via Token Bucket algorithm. |

---

## Production Security Hardening Verification Checklist

### Phase 1: Inbound Input Hardening (LLM01, LLM07)
- [ ] **Structural Boundary Enforcement**: Untrusted user inputs are wrapped inside explicit XML or markdown boundary envelopes (e.g., `<user_query>`) with synthetic tag escaping.
- [ ] **Heuristic WAF Filtering**: Inbound requests are scanned for known jailbreak patterns (`"ignore previous instructions"`, `"DAN mode"`, `"developer mode"`) before hitting the LLM API.
- [ ] **Canary Token Tripwires**: Dynamic, single-session cryptographic canary tokens are embedded into system instructions to detect prompt leakage instantly.

### Phase 2: Agent Tools & Agency Constraints (LLM06, LLM05)
- [ ] **Principle of Least Privilege**: Tool call permissions are restricted to minimal required operations (e.g., `SELECT` queries only; no raw `DROP` or `DELETE` capabilities).
- [ ] **Strict Pydantic Argument Validation**: Every tool function validates input parameters against rigid Pydantic v2 schemas before execution.
- [ ] **Human-in-the-Loop (HITL) Gateways**: Destructive actions (e.g., balance transfers > \$1,000, database schema migrations, sending external customer emails) require explicit signed operator approval.
- [ ] **Recursion Circuit Breakers**: Autonomous loops enforce hard caps (e.g. `max_iterations = 5`) to prevent runaway infinite tool-calling loops.

### Phase 3: Outbound Egress & Data Loss Prevention (LLM02, LLM05)
- [ ] **Output DLP Redaction**: Model completions pass through regular expression masking for Social Security Numbers, Payment Cards, and API tokens.
- [ ] **Contextual Output Encoding**: Generated Markdown/HTML text rendered on client UIs is processed through `html.escape()` to prevent Stored XSS attacks.
- [ ] **Parameterized Query Execution**: Any SQL queries generated by LLMs are strictly executed using parameterized placeholders (`?` or `$1`), never direct string formatting.

### Phase 4: Model Supply Chain & Infrastructure (LLM03, LLM10)
- [ ] **Safe Serialization Formats**: Model artifacts are stored and loaded strictly using `safetensors` or validated `joblib` pipelines; arbitrary `pickle.load()` on untrusted streams is banned.
- [ ] **Token Quota Envelopes**: Request timeouts and maximum output token budgets (`max_tokens`) are enforced at the API gateway layer to prevent resource exhaustion attacks.
