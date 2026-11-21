# PaperOrchestra SSCI Extension (Wiley / APA 7th / DOCX)

This directory extends [`google-research/paper-orchestra`](https://github.com/google-research/paper-orchestra) (Apache License 2.0) for **SSCI social sciences, disability studies, education, and policy journals** (such as Wiley's *Journal of Policy and Practice in Intellectual Disabilities*, *Adapted Physical Activity Quarterly*, *Disability & Society*, etc.).

## Why this extension exists

The upstream `PaperOrchestra` repository targets computer-science / ML conferences (CVPR, ICLR) using LaTeX. Applying it directly to SSCI manuscripts causes four critical problems:
1. **Limitation suppression**: Upstream `methods/prompts/content_refinement_agent.py` instructs *"Never explicitly state a limitation."* — which is fatal for SSCI empirical and policy-audit papers.
2. **Venue & reference bias**: Upstream literature search filters for `ArXiv/CVPR/NeurIPS/ICML/ICLR` and drops sources without Semantic Scholar abstracts (excluding government statistics, statutes, UN treaties, and books).
3. **LaTeX-only output**: Most SSCI social-science journals require **Microsoft Word (`.docx`)**, **APA 7th edition** references, **double-spaced** text, **continuous line numbers**, running heads, and **blinded metadata**.
4. **Submission compliance**: Missing checks for sole-vs-plural author voice (`I` vs `We`), leftover `[AUTHOR TO CONFIRM]` placeholders, duplicate table/figure captions, and PI real-name leaks in supplementary code.

## Contents

- `prompts/ssci_agent_review.py` — 3-reviewer SSCI ensemble (Policy/Scope, Domain/Theory, Methods/Ethics) + Associate Editor meta-review prompts.
- `prompts/ssci_lit_review_quality.py` — 6-axis anti-inflation literature review evaluation prompt calibrated for SSCI papers (supporting peer-reviewed articles, books, treaties, and official government data).
- `prompts/ssci_content_refinement.py` — Limitation-preserving, APA 7th-compliant SSCI Content Refinement prompt.
- `templates/wiley_ssci_apa7_guidelines.md` — Formatting, blinding, ethics, and APA 7th checklist for Wiley/SSCI submissions.
- `tools/ssci_docx_builder.py` — Converts Markdown manuscripts into Wiley/APA 7th `.docx` files (2.0x double-spaced, continuous line numbers, running head + page numbers, 0.5-inch hanging-indent references, 300 DPI figures, anonymized `core.xml` metadata) and runs an automated pre-submission validator.

## Quick Usage

### 1. Build a Wiley / APA 7th `.docx` submission package
```bash
python3 ssci_extension/tools/ssci_docx_builder.py \
  --input manuscript_blinded.md \
  --output Main_Manuscript_Blinded.docx \
  --doc-type manuscript \
  --running-head "SHORT RUNNING HEAD" \
  --figures-dir ./figures \
  --line-numbers
```

Supported `--doc-type` values: `manuscript`, `title_page`, `cover_letter`, `supplementary`.

### 2. Validate a Markdown/DOCX submission package before upload
```bash
python3 ssci_extension/tools/ssci_docx_builder.py \
  --validate-dir ./my_submission_folder \
  --sole-author
```

## License & Attribution

Derived from `google-research/paper-orchestra` (Copyright 2026 Google LLC), licensed under the Apache License, Version 2.0. See the root `LICENSE` file for full terms.
