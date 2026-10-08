# Literature Review: AcademicIQ Research Grounding

**Version:** 1.0  
**Date:** 2026-10-07  
**Status:** Draft — requires peer review before publication

---

## 1. Purpose

This document compares AcademicIQ against related work before claiming any novelty. It is a requirement of spec Section 12: "Do not claim novelty without evidence."

---

## 2. Related Work

### 2.1 Learning Analytics and Early-Warning Systems

Siemens and Long (2011) established learning analytics as a field, focusing on using educational data to understand and optimize learning environments. Early-warning systems (EWS) in higher education have been studied extensively: systems like Purdue's Course Signals (Arnold & Pistilli, 2012) and EAB Navigate use engagement signals alongside grade data to flag at-risk students.

**What AcademicIQ does differently:** Existing EWS primarily use LMS engagement data (clicks, logins) or GPA thresholds. AcademicIQ is designed around *heterogeneous document-extracted result data* with explicit provenance to source PDFs — a different input domain.

### 2.2 Explainable AI in Education

The broader XAI-in-education literature (Khosravi et al., 2022) emphasizes the need for transparency in algorithmic recommendations. SHAP-based explanations for student success prediction have been explored (e.g., Banihashem et al., 2022), but most work assumes clean tabular data from institutional databases.

**What AcademicIQ does differently:** Explainability is built into the attention scoring factors (F1–F7) at the rule-engine level, not post-hoc. Each factor shows its raw values and evidence description. AI text is an explanation layer over verified metrics, not a primary computation.

### 2.3 Student Success Prediction

Machine learning for student success prediction is well-studied (Romero & Ventura, 2020; Hussain et al., 2019). Common models include logistic regression, random forest, and neural networks trained on historical grade data.

**Established practice that AcademicIQ adopts:**
- Temporal train/test splits (never random) to avoid data leakage.
- Logistic Regression as interpretable baseline before complex models.
- Reporting precision, recall, F1, and calibration curves.
- Honest reporting: ML is disabled if data thresholds are not met.

**What AcademicIQ adds:** Gating mechanism with independent ground truth requirement (not circular with rule-engine output), explicit subgroup performance checks.

### 2.4 Data Provenance and Lineage

Data lineage in analytics systems is studied in database literature (Buneman et al., 2001 on data provenance; W3C PROV model). Educational data provenance has received less attention.

**What AcademicIQ contributes:** An evidence graph directly linking every analytical insight to its source PDF page, with a typed node/edge model and recursive CTE traversal. This is a practical implementation of the provenance concept in an educational analytics context.

### 2.5 Document Intelligence for Tabular Records

PDF table extraction research (Camelot, Tabula, pdfplumber, PaddleOCR papers) focuses on general-purpose table detection. University result documents have specific structural patterns that benefit from institution-specific parsers.

**What AcademicIQ contributes:** A plugin parser architecture with confidence-scored fallback chain (UniversitySpecific → GenericPDF → OCR), staging/validation workflow, and golden-file testing framework for parser accuracy measurement.

---

## 3. Claimed Contribution

The working contribution (to be confirmed or revised after full literature review):

> An evidence-driven academic intelligence architecture combining:
> 1. Longitudinal student academic profiles built from document-extracted, provenance-tracked result data
> 2. Explainable and versioned attention scoring with configurable factors and sensitivity analysis
> 3. Source-traceable evidence graphs linking every insight to its source PDF
> 4. Academic intervention recommendations with a human-in-the-loop approval workflow
> 5. Clearly separated hypothetical what-if simulation reusing production deterministic engines
> 6. Honest reporting: metric labels, ML gating, partial score flags, and negative result documentation

The architecture integrates these elements into a coherent system designed for the specific challenge of heterogeneous university result documents in institutional settings.

---

## 4. What is NOT Claimed as Novel

- Attention scoring factor methodology — the specific weights and thresholds are initial defaults requiring calibration (Section 7.3 of spec). They are not validated predictors until H4 evaluation is completed.
- Machine learning models — logistic regression, random forest, XGBoost are established methods.
- PDF extraction — uses established libraries (PyMuPDF, pdfplumber, Tesseract).
- RBAC, JWT auth, audit logging — standard engineering practice.

---

## 5. References

*(Abbreviated — full BibTeX in `docs/references.bib`)*

- Arnold, K. E., & Pistilli, M. D. (2012). Course signals at Purdue. *LAK 2012*.
- Buneman, P., Khanna, S., & Tan, W. C. (2001). Why and where: A characterization of data provenance. *ICDT 2001*.
- Hussain, S., et al. (2019). Using machine learning to predict student difficulties. *Int. J. Information Technology*.
- Khosravi, H., et al. (2022). Explainable artificial intelligence in education. *Computers and Education: Artificial Intelligence*.
- Romero, C., & Ventura, S. (2020). Educational data mining and learning analytics. *WIREs Data Mining*.
- Siemens, G., & Long, P. (2011). Penetrating the fog: Analytics in learning and education. *EDUCAUSE Review*.
- W3C. (2013). PROV-Overview. https://www.w3.org/TR/prov-overview/

---

## 6. Gaps and Open Questions

1. **Validated attention score methodology:** The F1–F7 weights and thresholds are undocumented in the educational analytics literature at this specific configuration. They require calibration and predictive validation (H4) before the scoring methodology can be described as validated.
2. **"Academic Digital Twin" terminology:** Not sufficiently established in academic literature to use without qualification. Primary term is "Longitudinal Academic Profile" (ADR-003).
3. **OCR accuracy on real university result PDFs:** Not benchmarked yet. Required before claiming H1 accuracy target.
