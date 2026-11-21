# Wiley / SSCI APA 7th Manuscript Submission Guidelines (Checklist)

Use this guideline file with `ssci_extension/tools/ssci_docx_builder.py` when preparing SSCI submissions (e.g., *Journal of Policy and Practice in Intellectual Disabilities*, *Adapted Physical Activity Quarterly*, *Disability & Society*).

## 1. Separate Files for Double-Blind Review
- `Title_Page.docx`: Full title, running head (<= 50 characters), author name(s), affiliation(s), corresponding author email, ORCID iD, manuscript statistics (exact word/table/figure counts), and full declarations (Ethics, Data/Code Availability, Funding, COI, AI Disclosure, CRediT).
- `Main_Manuscript_Blinded.docx`: Title, Structured Abstract (<= 250 words), Keywords (4–6), Main Text, Blinded Declarations, References, Tables, and Figures. **Zero author-identifying text or file metadata (`docProps/core.xml`).**
- `Cover_Letter.docx`: Addressed to Editor-in-Chief, concise fit & key findings (<= 1 page), originality/non-duplication confirmation, AI disclosure, corresponding author contact.
- `Supplementary_Materials.docx` + anonymized code/data files: **Must NOT contain personal names of investigators/participants or local machine paths.**

## 2. Typography & Page Layout (`.docx`)
- Margins: 1 inch (2.54 cm) on all sides.
- Font: Times New Roman, 12 pt throughout body and references.
- Line spacing: **Double-spaced (2.0x)** across abstract, main text, and references.
- Line numbers: **Continuous line numbering** enabled on the blinded main manuscript.
- Header/Footer: Running head (short title) and page numbers in header/footer.

## 3. Tables & Figures
- APA 7th three-line table style (top rule, header rule, bottom rule; no vertical borders).
- No duplicate table titles (e.g., avoid `Table 1` followed immediately by `Table 1. Title...`).
- Figures: >= 300 DPI PNG/TIFF, colorblind-safe palette, single non-duplicated caption.

## 4. APA 7th Reference Rules
- 1:1 correspondence between in-text citations and reference list.
- Alphabetical order by first author's surname; 0.5-inch hanging indent.
- Article titles in **sentence case** (capitalize first word, proper nouns, and first word after colon `:`).
- Journal titles in *Title Case* and italics; volume italicized; issue in parentheses non-italic.
- En-dash (`–`) for page ranges and year ranges (`1995–2005`).
- Full `https://doi.org/...` links without trailing periods.

## 5. Pre-Submission Zero-Tolerance Checks
- Zero `[AUTHOR TO CONFIRM]` or `[TODO]` placeholders left in any uploaded file.
- Author pronoun consistency: sole author uses `I` or impersonal voice (not `We`/`our`).
- Exact match between Title Page word counts and actual `.docx` word counts.
- Anonymized supplementary scripts (IDs only, no real names or local drive paths).
