<!--
Application Security (AppSec) Engineer & DevSecOps Lead Syllabus
================================================================
Description: Comprehensive enterprise syllabus for Application Security (AppSec) Engineers
             and DevSecOps Leads. Covers OWASP PBKDF2 password hashing, AES-128 Fernet encryption,
             JWT RBAC route guards, OWASP Top 10 for LLMs defense, and Bandit static security auditing.
Enterprise Mapping: Translates web application security practices (Helmet.js, PHP password_hash,
                    OWASP Top 10) to Python backend security frameworks, cryptography, and modern AI AppSec.

Official Documentation References:
- Python Cryptography Library: https://cryptography.io/en/latest/
- Python Hashlib Module: https://docs.python.org/3/library/hashlib.html
- PyJWT Documentation: https://pyjwt.readthedocs.io/en/latest/
- OWASP Top 10 Web Application Security: https://owasp.org/www-project-top-ten/
- OWASP Top 10 for LLMs: https://owasp.org/www-project-top-10-for-large-language-model-applications/
- Bandit Security Linter for Python: https://bandit.readthedocs.io/en/latest/
- Pip-Audit Vulnerability Scanner: https://pypi.org/project/pip-audit/
-->

# Application Security (AppSec) Engineer & DevSecOps Lead

## 1. Role Overview & Strategic Positioning

The **Application Security (AppSec) Engineer / DevSecOps Lead** architects, audits, and enforces the security postures of enterprise applications, APIs, and AI-enabled platforms. This role ensures cryptographic confidentiality and integrity of data at rest and in transit, designs stateless zero-trust authentication and authorization protocols, neutralizes classical web injection attacks, and establishes defensive firewalls against emerging Generative AI attack vectors (such as prompt injection, jailbreaks, and sensitive data leakage).

### Enterprise Ecosystem Translation

| Security Domain | Node.js / TypeScript Ecosystem | PHP Enterprise (Laravel / Symfony) | Modern Python Production Standard |
|---|---|---|---|
| **Password Hashing** | `bcrypt`, `argon2` npm packages | `password_hash()` (Argon2id / Bcrypt) | **`hashlib.pbkdf2_hmac`** (600,000 rounds) or **Argon2** |
| **Symmetric Encryption** | `crypto.createCipheriv` (AES-256-GCM) | `openssl_encrypt()`, Laravel Encrypter | **`cryptography.fernet`** (AES-128-CBC + HMAC-SHA256) |
| **JWT Verification & RBAC** | `jsonwebtoken`, Passport.js | `firebase/php-jwt`, LexikJWT | **`PyJWT` / `python-jose`** + FastAPI `Security()` guards |
| **Constant-Time Compare** | `crypto.timingSafeEqual` | `hash_equals()` | **`hmac.compare_digest`** |
| **Static Security Scanning** | ESLint Security, Snyk, npm audit | PHPStan Security, Psalm, Composer audit | **Bandit SAST**, **Semgrep**, **pip-audit** |
| **LLM AppSec Guardrails** | Custom regex sanitizers | Custom middleware | **OWASP Top 10 for LLMs**, **NeMo Guardrails**, **Canary Tokens** |

---

## 2. Direct Hands-On Evidence Modules (Levels 1–8)

The following modules in this repository provide concrete, production-grade evidence of mastery required for this role:

1. [**`level_6_cybersecurity_appsec/01_cryptography_and_hashing.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_6_cybersecurity_appsec/01_cryptography_and_hashing.py)
   - *Evidence*: Cryptographic password hashing utilizing PBKDF2-HMAC-SHA256 with 600,000 iterations (OWASP compliance), constant-time signature verification (`hmac.compare_digest`), and authenticated symmetric AES-128 Fernet encryption for PII data at rest.
2. [**`level_6_cybersecurity_appsec/02_jwt_auth_and_rbac_middleware.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_6_cybersecurity_appsec/02_jwt_auth_and_rbac_middleware.py)
   - *Evidence*: Stateless JWT token lifecycle management, asymmetric signature verification, unique token identifier (JTI) revocation blacklisting, and FastAPI Role-Based Access Control (RBAC) dependency injection guards (`require_roles`).
3. [**`level_6_cybersecurity_appsec/03_sql_injection_and_input_sanitization.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_6_cybersecurity_appsec/03_sql_injection_and_input_sanitization.py)
   - *Evidence*: Side-by-side comparison demonstrating vulnerable string concatenation vs parameterized SQL prepared statements, and XSS sanitization neutralizing HTML tags and DOM events.
4. [**`level_6_cybersecurity_appsec/04_llm_prompt_injection_defense.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_6_cybersecurity_appsec/04_llm_prompt_injection_defense.py)
   - *Evidence*: Multi-layered defense neutralizing OWASP Top 10 for LLMs threats: heuristic jailbreak regex filters, XML boundary isolation (`<user_input>`), canary token leak detection, and PII DLP redaction.
5. [**`docs/owasp_llm_security_checklist.md`**](file:///P:/prabhu/projects/git_python/py_docs/docs/owasp_llm_security_checklist.md)
   - *Evidence*: Production hardening architectural whitepaper detailing mitigation controls, threat vectors, and verification gates for OWASP LLM01 through LLM10.

---

## 3. Comprehensive Core Syllabus

### Module 1: Cryptography, Key Derivation & Data at Rest
- **OWASP-Compliant Password Hashing**:
  Implementing PBKDF2-HMAC-SHA256 with cryptographically secure 16-byte random salts (`os.urandom(16)`) and a minimum of 600,000 iterations to withstand GPU-accelerated brute-force attacks (Hashcat).
- **Constant-Time Verification**:
  Using `hmac.compare_digest(a, b)` instead of standard equality operators (`==`) to eliminate timing side-channel attacks where an attacker infers byte matches based on microsecond latency differences.
- **Symmetric Authenticated Encryption with Fernet**:
  Using `cryptography.fernet.Fernet` to enforce AES-128 in CBC mode with PKCS7 padding, authenticated by an HMAC-SHA256 signature to guarantee both confidentiality and tamper resistance.

### Module 2: Identity, Access & Token Lifecycle Management
- **Stateless JWT Tokens with PyJWT**:
  Issuing JSON Web Tokens with standard claims: `sub` (Subject ID), `exp` (Expiration), `iat` (Issued At), `iss` (Issuer), and `jti` (JWT ID).
- **FastAPI Role-Based Access Control (RBAC)**:
  Designing decoupled security dependency injection guards that evaluate user roles against route permissions:
  ```python
  def require_roles(*allowed_roles: str):
      async def dependency(current_user: UserContext = Security(get_current_active_user)):
          if not any(role in current_user.roles for role in allowed_roles):
              raise HTTPException(status_code=403, detail="Insufficient operational role privileges.")
          return current_user
      return dependency
  ```
- **Token Revocation via Distributed Blacklisting**:
  Implementing distributed Redis bloom filters or TTL-expiring keys tracking revoked `jti` values to provide instant session termination without hitting relational databases.

### Module 3: Injection Defense & Input Sanitization
- **Parameterized SQL Prepared Statements**:
  Enforcing strict parameter binding in both SQLite (`sqlite3.Cursor.execute(sql, (param,))`) and SQLAlchemy 2.0 (`select(Model).where(Model.attr == bindparam("val"))`), ensuring user input is treated strictly as data literals and never parsed as executable SQL syntax.
- **XSS Sanitization & HTML Entity Encoding**:
  Using Python standard library `html.escape()` and stripping dangerous script elements and DOM event attributes (`onload`, `onerror`).

### Module 4: Generative AI & LLM Threat Defense (OWASP LLM01–LLM10)
- **Prompt Injection & Jailbreak Defense**:
  Isolating untrusted user text inside structured XML boundary delimiters (`<user_data>...</user_data>`) and explicitly instructing system prompts never to interpret content within boundary tags as operational instructions.
- **Canary Tokens**:
  Injecting randomized cryptographic canary strings into hidden system prompt context and validating completion text; if the canary appears in the output, the prompt has been leaked and the request is aborted immediately.
- **Data Loss Prevention (DLP)**:
  Scanning and redacting Social Security Numbers, credit cards, and API keys from both input prompts and completion responses before egress.

### Module 5: Automated Static Security Analysis (SAST) & Dependency Auditing
- **Bandit Linter**:
  Executing static AST-based vulnerability analysis across Python codebases to catch hardcoded secrets (`B105`), insecure cryptography (`B303`), unescaped shell execution (`B602`), and unsafe yaml loading (`B506`):
  ```bash
  bandit -r . -ll -ii --exclude ./tests,./venv
  ```
- **Pip-Audit & Vulnerability Scanning**:
  Scanning installed packages and `requirements.txt` against the PyPA and Google OSV vulnerability databases to detect known CVEs before deployment.

---

## 4. Supplemental Topics (Remaining 10% to 100% Mastery)

### 1. Dynamic Application Security Testing (DAST) with OWASP ZAP
Integrating automated penetration testing into CI/CD pipelines:
- Running automated DAST baseline scans against staging FastAPI endpoints using the official OWASP ZAP Docker container.
- Detecting missing Security Headers (HSTS, Content-Security-Policy, X-Frame-Options), CORS misconfigurations, and cookie flag omissions (`HttpOnly`, `Secure`, `SameSite=Strict`).
- *Official Docs*: [OWASP ZAP Documentation](https://www.zaproxy.org/docs/)

### 2. Software Bill of Materials (SBOM) Generation
Meeting enterprise federal and SOC2 supply chain security standards:
- Generating standardized CycloneDX or SPDX JSON manifests from Python virtual environments using tools like `syft` or `cyclonedx-python`.
- Tracking cryptographic hashes of all transitive dependencies to detect upstream supply chain tampering.
- *Official Docs*: [CycloneDX Python](https://github.com/CycloneDX/cyclonedx-python)

### 3. OpenID Connect (OIDC) & Enterprise SSO
- Integrating FastAPI with enterprise identity providers (IdPs) like Okta, Keycloak, or Auth0 using the OAuth 2.0 Authorization Code Flow with PKCE (Proof Key for Code Exchange).
- Validating JSON Web Key Sets (JWKS) dynamically with automated public key rotation.
- *Official Docs*: [Authlib Python OIDC Client](https://docs.authlib.org/en/latest/)

### 4. Secrets Management with HashiCorp Vault
- Eliminating long-lived environment variables and hardcoded credentials by integrating the `hvac` Python SDK to retrieve short-lived dynamic database credentials and automated rotating encryption keys.
- *Official Docs*: [HashiCorp Vault Python SDK (hvac)](https://hvac.readthedocs.io/en/stable/)

---

## 5. Curated Documentation & Reference Links

- **Python Cryptography Standard Library**: https://cryptography.io/en/latest/
- **Python Standard Library Hashlib**: https://docs.python.org/3/library/hashlib.html
- **PyJWT Documentation**: https://pyjwt.readthedocs.io/
- **OWASP Top 10 Web Application Security**: https://owasp.org/www-project-top-ten/
- **OWASP Top 10 for Large Language Models**: https://owasp.org/www-project-top-10-for-large-language-model-applications/
- **Bandit Security Linter**: https://bandit.readthedocs.io/en/latest/
- **Pip-Audit Vulnerability Scanner**: https://pypi.org/project/pip-audit/
- **OWASP ZAP (Zed Attack Proxy)**: https://www.zaproxy.org/
- **HackerOne OWASP SQL Injection Prevention Cheat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
- **HashiCorp Vault hvac SDK**: https://hvac.readthedocs.io/
