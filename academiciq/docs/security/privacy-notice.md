# AcademicIQ Privacy Notice and Data Governance

**Regulation:** India DPDP Act 2023 (default). Configurable for FERPA / GDPR.  
**Version:** 1.0

---

## 1. Data Collected

| Data | Purpose | Lawful Basis |
|---|---|---|
| Student register number, name, department | Student identification and result matching | Legitimate educational interest |
| Examination marks and grades | Analytics and academic intelligence | Legitimate educational interest |
| User email and hashed password | Authentication | Contractual necessity |
| IP address, login timestamps | Security audit | Legitimate interest (security) |
| Uploaded PDF files | Result data extraction | Legitimate educational interest |

## 2. Data NOT Collected

- Health, medical, or psychological data
- Financial or family circumstances
- Social media or communication data
- Biometric data

## 3. AI Processing Privacy

External LLMs receive **only pseudonymized, aggregated data**:
- No student names
- No register numbers
- Entity tokens only (e.g., `ENTITY_a3b4c5d6`)
- Metric values only (e.g., `{"type": "semester_average", "value": 67.4}`)

Guardrail G2 actively rejects any AI output containing register number patterns.

## 4. Data Retention

| Data type | Retention period |
|---|---|
| Examination results | 7 years (or per institutional policy) |
| Uploaded PDF files | 7 years |
| Audit logs | 7 years |
| User accounts (inactive) | 2 years after last login, then soft-delete |
| What-if scenarios | 1 year |
| AI insight logs | 1 year |

## 5. Correction and Erasure

Students may request correction of their academic data. Corrections create a new result version — the original is never overwritten. Erasure requests are handled per the runbook Section 14 process.

## 6. Breach Response

1. Identify and contain the breach within 72 hours.
2. Notify the Data Protection Board of India (DPBI) if the breach is likely to cause harm.
3. Notify affected data principals.
4. Document in `audit_logs` with action=`SECURITY_BREACH`.
5. Conduct post-incident review.
