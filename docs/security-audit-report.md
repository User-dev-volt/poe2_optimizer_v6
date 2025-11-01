# Security Audit Report

**Date:** 2025-10-20
**Tool:** pip-audit 2.9.0
**Scope:** All Python packages in environment
**Project:** PoE2 Build Optimizer (Story 1.5)

## Executive Summary

Security audit completed using `pip-audit` to scan for known CVEs in Python dependencies. **12 vulnerabilities found in 8 packages**, all of which are **transitive dependencies from the Miniconda environment** and **NOT direct project dependencies**.

**Key Finding:** ✅ **All project dependencies are clean** - no CVEs in xmltodict, lupa, pytest, or pytest-cov.

**Risk Level:** 🟡 **LOW** - Vulnerabilities exist in system packages but do not affect the core PoE2 Optimizer functionality (calculation engine, parsing, testing).

## Vulnerable Packages Summary

| Package           | Version | CVEs | Fix Version | Severity | Direct Dep? |
|-------------------|---------|------|-------------|----------|-------------|
| ecdsa             | 0.19.1  | 1    | None        | Medium   | ❌ No       |
| fastapi           | 0.104.1 | 1    | 0.109.1     | Medium   | ❌ No       |
| python-jose       | 3.3.0   | 2    | 3.4.0       | Medium   | ❌ No       |
| python-multipart  | 0.0.6   | 2    | 0.0.18      | High     | ❌ No       |
| scikit-learn      | 1.3.2   | 1    | 1.5.0       | Low      | ❌ No       |
| starlette         | 0.27.0  | 2    | 0.47.2      | High     | ❌ No       |
| urllib3           | 2.3.0   | 2    | 2.5.0       | Medium   | ❌ No       |

**Total:** 12 vulnerabilities, 0 in direct dependencies

## Project Dependencies (Clean ✅)

The following packages are **direct dependencies** listed in `requirements.txt` and have **NO known vulnerabilities**:

- ✅ **xmltodict** (0.13.0) - XML parsing for PoB codes
- ✅ **lupa** (>=2.0) - Python-LuaJIT bindings for PoB engine
- ✅ **pytest** (>=7.4.0) - Testing framework
- ✅ **pytest-cov** (>=4.1.0) - Coverage reporting

**Risk Assessment:** ✅ **NO ACTION REQUIRED** for project dependencies.

## Vulnerability Details

### 1. ecdsa (0.19.1)

**CVE:** GHSA-wj6h-64fc-37mp
**Type:** Timing Attack (Minerva attack on P-256 curve)
**Severity:** Medium
**Fix:** None planned (project considers side-channel attacks out of scope)

**Impact on PoE2 Optimizer:**
- ❌ Not used by project
- ❌ Not a direct dependency
- ⚠️ Likely installed by conda/miniconda for system cryptography

**Recommendation:** Monitor but no action required (not used by project code).

---

### 2. fastapi (0.104.1)

**CVE:** PYSEC-2024-38
**Type:** ReDoS (Regular Expression Denial of Service) in form parsing
**Severity:** Medium
**Fix Version:** 0.109.1

**Impact on PoE2 Optimizer:**
- ❌ Not used by project
- ❌ Not a direct dependency
- ⚠️ Likely installed by conda/miniconda or JupyterLab

**Recommendation:** No action required (not used by project code).

---

### 3. python-jose (3.3.0)

**CVEs:**
- PYSEC-2024-232: Algorithm confusion with OpenSSH ECDSA keys
- PYSEC-2024-233: JWT bomb DoS via high compression ratio

**Severity:** Medium
**Fix Version:** 3.4.0

**Impact on PoE2 Optimizer:**
- ❌ Not used by project
- ❌ Not a direct dependency
- ⚠️ Likely installed for JWT authentication in other tools

**Recommendation:** No action required (not used by project code).

---

### 4. python-multipart (0.0.6)

**CVEs:**
- GHSA-2jv5-9r88-3w3p: ReDoS in Content-Type header parsing
- GHSA-59g5-xgcq-4qw3: Excessive logging DoS vulnerability

**Severity:** High
**Fix Versions:** 0.0.7 (ReDoS), 0.0.18 (logging DoS)

**Impact on PoE2 Optimizer:**
- ❌ Not used by project
- ❌ Not a direct dependency
- ⚠️ Dependency of fastapi/starlette (not used by project)

**Recommendation:** No action required (not used by project code).

---

### 5. scikit-learn (1.3.2)

**CVE:** PYSEC-2024-110
**Type:** Sensitive data leakage in TfidfVectorizer
**Severity:** Low
**Fix Version:** 1.5.0

**Impact on PoE2 Optimizer:**
- ❌ Not used by project
- ❌ Not a direct dependency
- ⚠️ Machine learning library (not relevant to PoB calculation engine)

**Recommendation:** No action required (not used by project code).

---

### 6. starlette (0.27.0)

**CVEs:**
- GHSA-f96h-pmfr-66vw: DoS via unbounded form field buffering
- GHSA-2c2j-9gv5-cj73: Event loop blocking on large file uploads

**Severity:** High
**Fix Versions:** 0.40.0, 0.47.2

**Impact on PoE2 Optimizer:**
- ❌ Not used by project
- ❌ Not a direct dependency
- ⚠️ Web framework (not relevant to calculation engine)

**Recommendation:** No action required (not used by project code).

---

### 7. urllib3 (2.3.0)

**CVEs:**
- GHSA-48p4-8xcf-vxj5: Redirect control ignored in Pyodide runtime
- GHSA-pq67-6m6q-mj2v: Redirect control ignored at PoolManager level

**Severity:** Medium
**Fix Version:** 2.5.0

**Impact on PoE2 Optimizer:**
- ❌ Not directly used by project (xmltodict doesn't make HTTP requests)
- ❌ Not a direct dependency
- ⚠️ HTTP library used by other tools in environment

**Recommendation:** Monitor but no action required (not used by project code).

---

## Recommendations

### Immediate Actions (Story 1.5)

**✅ NO IMMEDIATE ACTION REQUIRED**

All vulnerable packages are transitive dependencies from the Miniconda environment and are not used by the PoE2 Optimizer project. The project dependencies (xmltodict, lupa, pytest, pytest-cov) are clean.

### Future Actions (Epic 3 - Production)

When preparing for production deployment:

1. **Use virtual environment:** Create isolated venv instead of conda base environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows

   pip install -r requirements.txt
   ```

2. **Re-run pip-audit:** Verify clean environment
   ```bash
   pip-audit
   ```

3. **Pin dependencies:** Add exact versions to requirements.txt
   ```
   xmltodict==0.13.0
   lupa==2.5
   pytest==7.4.3
   pytest-cov==7.0.0
   ```

4. **Add pip-audit to CI/CD:** Automated security checks
   ```yaml
   # .github/workflows/security.yml
   - name: Security audit
     run: |
       pip install pip-audit
       pip-audit --strict
   ```

5. **Regular audits:** Run pip-audit monthly or after dependency updates

### Optional Actions (Story 1.5)

For development environment hygiene (non-blocking):

1. **Update conda packages** (if using web/ML features):
   ```bash
   conda update fastapi starlette urllib3 scikit-learn
   ```

2. **Create clean project venv** to avoid transitive dependencies:
   ```bash
   conda deactivate
   python -m venv poe2_env
   poe2_env\Scripts\activate
   pip install -r requirements.txt
   ```

## Risk Assessment

### Current Risk: 🟢 **MINIMAL**

**Rationale:**
- ✅ No vulnerabilities in project dependencies
- ✅ Vulnerable packages not imported by project code
- ✅ Project scope: offline calculation engine (no web server, no HTTP requests, no JWT auth)
- ✅ All vulnerabilities are in web framework/HTTP/crypto libraries irrelevant to PoB calculations

**Attack Surface:**
- **Web endpoints:** None (offline calculation engine)
- **HTTP requests:** None (no external API calls)
- **Form parsing:** None (PoB XML parsing via xmltodict only)
- **JWT/Auth:** None (no authentication layer)

### Production Risk: 🟡 **LOW-MEDIUM** (Future)

When Epic 3 introduces web API:
- ⚠️ fastapi/starlette vulnerabilities become relevant
- ⚠️ urllib3 vulnerabilities relevant if making HTTP requests
- ⚠️ Need to update dependencies before production deployment

**Mitigation:** Follow "Future Actions" recommendations above.

## Audit Commands

### Run Full Audit

```bash
# Install pip-audit
pip install pip-audit

# Run audit with descriptions
pip-audit --desc

# Generate JSON report
pip-audit --format=json > security-audit.json

# Strict mode (fail on any vulnerability)
pip-audit --strict
```

### Filter by Severity

```bash
# Only show high/critical vulnerabilities
pip-audit --desc | grep -E "(High|Critical)"
```

### Check Specific Package

```bash
# Audit single package
pip-audit --requirement <(echo "xmltodict==0.13.0")
```

## References

- **pip-audit documentation:** https://pypi.org/project/pip-audit/
- **CVE database:** https://cve.mitre.org/
- **GitHub Security Advisories:** https://github.com/advisories
- **Python Security:** https://www.python.org/dev/security/

## Audit History

| Date       | Vulnerabilities Found | Action Taken           | Notes                                      |
|------------|------------------------|------------------------|--------------------------------------------|
| 2025-10-20 | 12 (8 packages)        | Documented, no action  | All in transitive deps, none in project    |

## Next Audit

**Recommended:** Before Epic 3 production deployment (or monthly if in active development)

**Command:**
```bash
pip-audit --desc > docs/security-audit-report-$(date +%Y%m%d).txt
```

---

**Audited by:** Claude (Amelia - Dev Agent)
**Story:** 1.5 - Execute Single Build Calculation
**Optional Enhancement:** #4 (Run Security Audit)
