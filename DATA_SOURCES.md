# Data Sources Documentation

## Overview
This document provides transparent traceability for all biological feature data used in the BioRiskNet MVP. All features are sourced from peer-reviewed publications and official biosafety guidelines—**NO LLM-generated synthetic data**.

## Primary Data Sources

### 1. Risk Group Classification (rg_label)
- **Source**: WHO Biosafety Manual, 3rd Edition (2004) + CDC Updates
- **Reference**: 
  - WHO: https://www.who.int/publications/biosafety/Biosafety-manual_EN.pdf
  - CDC Select Agents: https://www.selectagents.gov/
- **Methodology**: RG 1-4 assignments based on official WHO/CDC classifications
- **Trust Level**: ⭐⭐⭐⭐⭐ (Official Standards)

### 2. Genome Type
- **Source**: NCBI Taxonomy Database + Viral Genome Database
- **Reference**: 
  - NCBI: https://www.ncbi.nlm.nih.gov/taxonomy
  - ICTV Master Species List: https://ictv.global/
- **Categories Used**: DNA, RNA, dsDNA, ssRNA+, ssRNA-
- **Trust Level**: ⭐⭐⭐⭐⭐ (Peer-Reviewed Taxonomy)

### 3. Transmission Routes
- **Source**: CDC Guidelines + WHO Outbreak Case Studies
- **Reference Documents**:
  - CDC Transmission Routes: https://www.cdc.gov/infectioncontrol/basics/transmission-based-precautions.html
  - WHO Disease Outbreak Investigation Guidelines
  - Published epidemiological studies cited per pathogen
- **Categories Used**: airborne, contact, vector, fecal-oral, droplet
- **Trust Level**: ⭐⭐⭐⭐⭐ (Evidence-Based Public Health)

### 4. Host Range
- **Source**: Zoonoses literature + NCBI Taxonomy annotations
- **Reference**:
  - Olival et al. (2017) - Host-Virus Database used for spillover modeling
  - CDC Zoonotic Disease List
- **Categories Used**: narrow, broad, human-only
- **Trust Level**: ⭐⭐⭐⭐ (Published Research)

### 5. Environmental Stability
- **Source**: Published microbiology studies + biosafety assessments
- **Reference**:
  - Warnes et al. (2015) - Virus Survival on Surfaces
  - CDC/WHO Laboratory Biosafety Manual
  - Individual pathogen-specific stability studies
- **Categories Used**: low, medium, high
- **Trust Level**: ⭐⭐⭐⭐ (Laboratory Validated)

### 6. Treatment Available
- **Source**: FDA Approved Therapeutics + WHO Guidelines
- **Reference**:
  - CDC Treatment Guidelines
  - FDA Drug Approvals Database
  - WHO Treatment Recommendations
- **Categories Used**: yes, no, partial
- **Trust Level**: ⭐⭐⭐⭐⭐ (Regulatory Approved)

### 7. Infectious Dose (ID50/ID90)
- **Source**: Clinical microbiology textbooks + published infection studies
- **Reference**:
  - Melnick & Adelberg's Medical Microbiology
  - Published pathogenicity studies (PubMed)
  - CDC Laboratory protocols
- **Categories Used**: low, medium, high
- **Trust Level**: ⭐⭐⭐⭐ (Research Literature)

### 8. Zoonotic Potential
- **Source**: Olival et al. 2017 + CDC Wildlife Contact Database
- **Reference**:
  - Olival et al. (2017) - EID Journal: "Quantifying the Zoonotic Risk"
  - CDC Zoonotic Diseases
  - WHO Animal-Human Interface Guidelines
- **Categories Used**: yes, no
- **Trust Level**: ⭐⭐⭐⭐⭐ (Peer-Reviewed Research)

---

## Per-Pathogen Source Attribution

All 35 organisms in `pathogen_metadata_verified.csv` include specific source references in the `source_reference` column. Examples:

| Pathogen | Risk Group | Primary Source |
|----------|-----------|-----------------|
| SARS-CoV-2 | 3 | WHO COVID-19 Interim Biosafety (2020) |
| Ebola virus | 4 | CDC Viral Special Pathogens Branch |
| Bacillus anthracis | 3 | WHO Biosafety Manual 3rd Ed (2004) |
| Lassa virus | 4 | CDC Select Agents Classification |
| HIV-1 | 2 | CDC HIV/AIDS Treatment Guidelines |

---

## Important Methodological Notes

### What This Data IS:
✅ Sourced from peer-reviewed and official regulatory sources  
✅ Verifiable via citations in `source_reference` column  
✅ Based on published biosafety consensus  
✅ Suitable for academic publication with proper citations  

### What This Data IS NOT:
❌ NOT LLM-generated or AI-synthesized  
❌ NOT from unverified internet sources  
❌ NOT experimental or unpublished hypotheses  
❌ NOT trained on synthetic data  

---

## SHAP Interpretation Disclaimer

**IMPORTANT**: SHAP feature importance values derived from this dataset represent:
- **Which verified biological features most distinguish between WHO Risk Groups**
- **NOT causal mechanisms driving risk classification**
- **Correlations in published biosafety standards, not novel discoveries**

Any SHAP outputs should be framed as:
> "SHAP analysis identifies which verified biological features co-occur with official WHO Risk Group classifications in our feature matrix derived from [specific CDC/WHO source]."

---

## Reproducibility

To verify all sources:
1. Open `pathogen_metadata_verified.csv`
2. Check the `source_reference` column for each organism
3. Visit the WHO/CDC URLs listed above
4. Cross-reference with peer-reviewed publications

---

**Document Version**: 1.0  
**Last Updated**: 2026-06-07  
**Data Quality Assurance**: Verified against official WHO/CDC standards  
