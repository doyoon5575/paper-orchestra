# Copyright 2026 Google LLC (upstream PaperOrchestra)
# Modifications Copyright 2026 Contributors (SSCI Extension)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Wiley / SSCI APA 7th DOCX Builder & Pre-Submission Validator.

Converts structured Markdown manuscripts into publication-ready Wiley/APA 7th
Microsoft Word (.docx) files and validates submission packages for blinding,
formatting, APA 7th citations, placeholders, and code anonymization.
"""

import argparse
import glob
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Optional, Tuple

import docx
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor


INLINE_TOKEN_RE = re.compile(r"(\*\*.*?\*\*|\*[^*]+?\*|`[^`]+?`)")


def set_run_font(run, font_name="Times New Roman", east_asia="Malgun Gothic", size_pt=12):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), font_name)
    rFonts.set(qn("w:hAnsi"), font_name)
    rFonts.set(qn("w:eastAsia"), east_asia)
    rFonts.set(qn("w:cs"), font_name)


def add_formatted_runs(paragraph, text: str, size_pt: int = 12, base_bold: bool = False, base_italic: bool = False):
    """Parse inline Markdown (**bold**, *italic*, `code`) into Word runs."""
    pos = 0
    for match in INLINE_TOKEN_RE.finditer(text):
        if match.start() > pos:
            r = paragraph.add_run(text[pos : match.start()])
            r.bold = base_bold
            r.italic = base_italic
            set_run_font(r, size_pt=size_pt)
        token = match.group(0)
        if token.startswith("**") and token.endswith("**"):
            inner = token[2:-2]
            add_formatted_runs(paragraph, inner, size_pt=size_pt, base_bold=True, base_italic=base_italic)
        elif token.startswith("*") and token.endswith("*"):
            inner = token[1:-1]
            add_formatted_runs(paragraph, inner, size_pt=size_pt, base_bold=base_bold, base_italic=True)
        elif token.startswith("`") and token.endswith("`"):
            inner = token[1:-1]
            r = paragraph.add_run(inner)
            r.bold = base_bold
            r.italic = base_italic
            set_run_font(r, font_name="Consolas", size_pt=max(size_pt - 1, 9))
        pos = match.end()
    if pos < len(text):
        r = paragraph.add_run(text[pos:])
        r.bold = base_bold
        r.italic = base_italic
        set_run_font(r, size_pt=size_pt)


def add_page_number_field(paragraph):
    """Insert a dynamic Word PAGE field into a header/footer paragraph."""
    run_begin = paragraph.add_run()
    set_run_font(run_begin, size_pt=11)
    fld_begin = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls("w"))
    run_begin._r.append(fld_begin)

    run_instr = paragraph.add_run()
    set_run_font(run_instr, size_pt=11)
    instr = parse_xml(r'<w:instrText %s xml:space="preserve"> PAGE </w:instrText>' % nsdecls("w"))
    run_instr._r.append(instr)

    run_sep = paragraph.add_run()
    set_run_font(run_sep, size_pt=11)
    fld_sep = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls("w"))
    run_sep._r.append(fld_sep)

    run_end = paragraph.add_run()
    set_run_font(run_end, size_pt=11)
    fld_end = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls("w"))
    run_end._r.append(fld_end)


def enable_continuous_line_numbers(section):
    """Add continuous line numbering to a Word section."""
    sectPr = section._sectPr
    for existing in sectPr.findall(qn("w:lnNumType")):
        sectPr.remove(existing)
    ln = OxmlElement("w:lnNumType")
    ln.set(qn("w:countBy"), "1")
    ln.set(qn("w:start"), "1")
    ln.set(qn("w:restart"), "continuous")
    sectPr.append(ln)


def configure_apa_table(table, headers: List[str], rows: List[List[str]], font_pt: int = 10):
    """Style a Word table using APA 7th three-line borders (no vertical borders)."""
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True

    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f"""
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="12" w:space="0" w:color="000000"/>
            <w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>
            <w:insideH w:val="none"/>
            <w:left w:val="none"/>
            <w:right w:val="none"/>
            <w:insideV w:val="none"/>
        </w:tblBorders>
        """
    )
    for old in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(old)
    tblPr.append(borders)

    # Header row
    hdr_row = table.rows[0]
    trPr = hdr_row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    for j, htext in enumerate(headers):
        cell = hdr_row.cells[j]
        tcPr = cell._tc.get_or_add_tcPr()
        tcPr.append(
            parse_xml(
                f"""
                <w:tcBorders {nsdecls("w")}>
                    <w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>
                </w:tcBorders>
                """
            )
        )
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
        add_formatted_runs(p, htext.strip(), size_pt=font_pt, base_bold=True)

    # Body rows
    for row_vals in rows:
        row = table.add_row()
        for j, val in enumerate(row_vals):
            cell = row.cells[j]
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
            add_formatted_runs(p, val.strip(), size_pt=font_pt)


def parse_markdown_table(lines: List[str], start_idx: int) -> Tuple[List[str], List[List[str]], int]:
    """Parse a GitHub-flavored Markdown table starting at start_idx."""
    header_line = lines[start_idx].strip().strip("|")
    headers = [c.strip() for c in header_line.split("|")]
    idx = start_idx + 2  # skip separator row
    rows = []
    while idx < len(lines) and lines[idx].strip().startswith("|"):
        row_cells = [c.strip() for c in lines[idx].strip().strip("|").split("|")]
        while len(row_cells) < len(headers):
            row_cells.append("")
        rows.append(row_cells[: len(headers)])
        idx += 1
    return headers, rows, idx


def anonymize_docx_metadata(doc: Document):
    """Clear identifying metadata from docProps/core.xml."""
    cp = doc.core_properties
    cp.author = ""
    cp.last_modified_by = ""
    cp.comments = ""
    cp.title = ""
    cp.subject = ""
    cp.keywords = ""


def build_docx_from_markdown(
    input_md: str,
    output_docx: str,
    doc_type: str = "manuscript",
    running_head: str = "",
    figures_dir: Optional[str] = None,
    line_numbers: bool = False,
):
    with open(input_md, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    doc = Document()

    # Configure page margins (1 inch) & header/footer
    section = doc.sections[0]
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    section.header_distance = Inches(0.5)
    section.footer_distance = Inches(0.5)

    if line_numbers:
        enable_continuous_line_numbers(section)

    if doc_type in ("manuscript", "supplementary"):
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if running_head:
            r_rh = hp.add_run(f"{running_head.upper()}    |    ")
            set_run_font(r_rh, size_pt=10)
            r_rh.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
        add_page_number_field(hp)

    # Set base Normal style
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    rPr = normal.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), "Times New Roman")
    rFonts.set(qn("w:hAnsi"), "Times New Roman")
    rFonts.set(qn("w:eastAsia"), "Malgun Gothic")

    default_spacing = 2.0 if doc_type == "manuscript" else 1.5
    if doc_type == "cover_letter":
        default_spacing = 1.15

    in_references = False
    in_figure_captions = False
    in_tables_section = False
    in_code_block = False
    code_lines: List[str] = []
    figure_captions: List[Tuple[str, str]] = []  # (fig_num, full_caption_text)

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Fenced code blocks (e.g., regex/code in Supplementary Materials)
        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                in_code_block = False
                p = doc.add_paragraph()
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.left_indent = Inches(0.25)
                r = p.add_run("\n".join(code_lines))
                set_run_font(r, font_name="Consolas", size_pt=9)
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        if not stripped or stripped == "---":
            i += 1
            continue

        # Markdown Table
        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1].strip()):
            headers, rows, next_i = parse_markdown_table(lines, i)
            tbl = doc.add_table(rows=1, cols=len(headers))
            font_pt = 9 if len(headers) >= 6 else 10
            configure_apa_table(tbl, headers, rows, font_pt=font_pt)
            i = next_i
            continue

        # H1 Title
        if stripped.startswith("# "):
            title_text = stripped[2:].strip()
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if doc_type == "manuscript" else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = default_spacing
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(12)
            add_formatted_runs(p, title_text, size_pt=14, base_bold=True)
            i += 1
            continue

        # H2 Section heading
        if stripped.startswith("## "):
            h2 = stripped[3:].strip()
            h2_low = h2.lower()
            in_references = h2_low == "references"
            in_figure_captions = h2_low in ("figure captions", "figures")
            in_tables_section = h2_low == "tables"

            # Page break before References and Tables in manuscripts
            if doc_type == "manuscript" and (in_references or in_tables_section):
                doc.add_page_break()

            # Do not emit a separate "Figure Captions" header when embedding figures with captions at the end
            if doc_type == "manuscript" and in_figure_captions and figures_dir:
                i += 1
                continue

            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = default_spacing
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, h2, size_pt=13, base_bold=True)
            i += 1
            continue

        # H3 Subsection heading
        if stripped.startswith("### "):
            h3 = stripped[4:].strip()
            # Avoid duplicate "Table 1" heading when next line is "**Table 1. ...**"
            if in_tables_section and re.match(r"^Table\s+\d+$", h3, re.I):
                if i + 1 < len(lines) and re.match(r"^\*\*Table\s+\d+\.", lines[i + 1].strip(), re.I):
                    i += 1
                    continue
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = default_spacing
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, h3, size_pt=12, base_bold=True)
            i += 1
            continue

        # Collect figure captions to attach directly below embedded figures (prevents duplicate captions)
        if in_figure_captions and doc_type == "manuscript" and figures_dir:
            cap_text = re.sub(r"^[-*]\s+", "", stripped)
            m_fig = re.search(r"Figure\s+(\d+)", cap_text)
            fig_num = m_fig.group(1) if m_fig else str(len(figure_captions) + 1)
            figure_captions.append((fig_num, cap_text))
            i += 1
            continue

        # References (APA 7th hanging indent)
        if in_references:
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = default_spacing
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.first_line_indent = Inches(-0.5)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(4)
            add_formatted_runs(p, stripped, size_pt=12)
            i += 1
            continue

        # Bullet / numbered list items
        if re.match(r"^[-*]\s+", stripped):
            item_text = re.sub(r"^[-*]\s+", "", stripped)
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = default_spacing
            p.paragraph_format.left_indent = Inches(0.35)
            p.paragraph_format.first_line_indent = Inches(-0.18)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(4)
            r_bul = p.add_run("• ")
            set_run_font(r_bul, size_pt=12)
            add_formatted_runs(p, item_text, size_pt=12)
            i += 1
            continue

        # Table note lines (*Note.*)
        if stripped.startswith("*Note.*"):
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(12)
            add_formatted_runs(p, stripped, size_pt=10)
            i += 1
            continue

        # Table title lines (**Table X. ...**)
        if re.match(r"^\*\*Table\s+S?\d+\.", stripped):
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, stripped, size_pt=11)
            i += 1
            continue

        # Regular paragraph
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = default_spacing
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        add_formatted_runs(p, stripped, size_pt=12)
        i += 1

    # Embed Figures at the end of manuscript (one figure per page with single caption)
    if doc_type == "manuscript" and figures_dir and os.path.isdir(figures_dir) and figure_captions:
        fig_files = sorted(
            f for f in os.listdir(figures_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))
        )
        for idx, (fig_num, cap_text) in enumerate(figure_captions):
            doc.add_page_break()
            # Match Figure{num}*.png or fallback by index
            matched = next(
                (f for f in fig_files if re.search(rf"figure\s*{fig_num}\b|figure{fig_num}_", f, re.I)),
                fig_files[idx] if idx < len(fig_files) else None,
            )
            if matched:
                img_path = os.path.join(figures_dir, matched)
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(12)
                p_img.paragraph_format.space_after = Pt(8)
                run_img = p_img.add_run()
                run_img.add_picture(img_path, width=Inches(6.2))
            p_cap = doc.add_paragraph()
            p_cap.paragraph_format.line_spacing = 1.5
            p_cap.paragraph_format.space_before = Pt(4)
            p_cap.paragraph_format.space_after = Pt(12)
            add_formatted_runs(p_cap, cap_text, size_pt=11)

    if doc_type in ("manuscript", "supplementary"):
        anonymize_docx_metadata(doc)

    os.makedirs(os.path.dirname(os.path.abspath(output_docx)), exist_ok=True)
    doc.save(output_docx)
    print(f"[OK] Built {output_docx} ({doc_type})")


def count_manuscript_stats(md_path: str) -> dict:
    """Compute exact Abstract, Main Text, and Reference counts from Markdown."""
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    stats = {"abstract_words": 0, "main_text_words": 0, "references_count": 0}
    if "## Abstract" in text and "**Keywords**" in text:
        abs_block = text.split("## Abstract", 1)[1].split("**Keywords**", 1)[0]
        abs_clean = re.sub(r"[*`#]", "", abs_block).strip()
        stats["abstract_words"] = len(abs_clean.split())

    if "## 1. Introduction" in text and "## Declarations" in text:
        main_block = text.split("## 1. Introduction", 1)[1].split("## Declarations", 1)[0]
        # Strip markdown headings & formatting markers, keep section words
        main_clean = re.sub(r"[*`#]", "", main_block).strip()
        stats["main_text_words"] = len(main_clean.split())

    if "## References" in text:
        ref_sec = text.split("## References", 1)[1]
        for stop in ("## Figure Captions", "## Figures", "## Tables"):
            if stop in ref_sec:
                ref_sec = ref_sec.split(stop, 1)[0]
        refs = [r.strip() for r in ref_sec.strip().split("\n\n") if r.strip() and not r.strip().startswith("---")]
        stats["references_count"] = len(refs)

    return stats


def validate_submission_dir(directory: str, sole_author: bool = False) -> int:
    """Run automated SSCI pre-submission checks on a folder of MD/DOCX/PY files."""
    print(f"=== SSCI Pre-Submission Validator: {directory} ===")
    errors = []
    warnings = []

    # 1. Inspect Markdown files
    for md_path in sorted(glob.glob(os.path.join(directory, "*.md"))):
        fname = os.path.basename(md_path)
        with open(md_path, "r", encoding="utf-8") as f:
            txt = f.read()

        placeholders = re.findall(r"\[AUTHOR TO[^\]]*\]|\[TODO[^\]]*\]", txt)
        if placeholders:
            warnings.append(f"{fname}: {len(placeholders)} author placeholder(s) remaining -> {placeholders[:3]}")

        is_main = "manuscript" in fname.lower()
        is_cover = "cover_letter" in fname.lower()

        if sole_author and (is_main or is_cover):
            # Check body before References for first-person plural pronouns
            body = txt.split("## References")[0]
            # Strip quoted phrases or citations like "With or without us?"
            body_no_quotes = re.sub(r"[\"“].*?[\"”]", "", body)
            plural_hits = re.findall(r"\b(we|our|ours|ourselves)\b", body_no_quotes, re.I)
            if plural_hits:
                errors.append(f"{fname}: sole-author voice violation (found {len(plural_hits)} plural pronouns: {plural_hits[:5]})")

        if is_main:
            stats = count_manuscript_stats(md_path)
            print(
                f"  [STATS] {fname}: Abstract={stats['abstract_words']} words, "
                f"Main Text={stats['main_text_words']} words, References={stats['references_count']}"
            )
            if stats["abstract_words"] > 250:
                warnings.append(f"{fname}: Abstract exceeds 250 words ({stats['abstract_words']})")

            # Check APA 7th references
            if "## References" in txt:
                body = txt.split("## References", 1)[0]
                ref_sec = txt.split("## References", 1)[1]
                for stop in ("## Figure Captions", "## Figures", "## Tables"):
                    if stop in ref_sec:
                        ref_sec = ref_sec.split(stop, 1)[0]
                refs = [r.strip() for r in ref_sec.strip().split("\n\n") if r.strip() and not r.strip().startswith("---")]
                for idx, ref in enumerate(refs, 1):
                    m = re.match(r"^([^(]+)\((\d{4}|n\.d\.)", ref)
                    if m:
                        surname = m.group(1).split(",")[0].strip().rstrip(".")
                        yr = m.group(2)
                        if surname not in body or yr not in body:
                            errors.append(f"{fname}: Reference #{idx} ({surname}, {yr}) not cited in text")
                    # Title case check on journal article titles
                    mt = re.search(r"\)\.\s+([^*]+?)\.\s+\*", ref)
                    if mt:
                        title = mt.group(1)
                        # Check lowercase immediately after colon
                        mc = re.search(r":\s+([a-z])", title)
                        if mc:
                            errors.append(f"{fname}: Ref #{idx} has lowercase after colon: '{title}'")
                        words = [w for w in re.findall(r"[A-Za-z]+", title) if len(w) > 3]
                        # Exclude known proper nouns/acronyms from title-case heuristic
                        proper = {
                            "Korean", "Australia", "Australian", "African", "English", "World", "Health",
                            "Organization", "Universal", "Design", "Learning", "Physical", "Education",
                            "Python", "Scikit", "Dirichlet", "Bayesian", "United", "Nations", "Rights",
                            "Persons", "Disabilities", "Convention", "Republic", "Korea", "Kiwi",
                            "Intelligent", "Word", "Identifier", "South", "Southern",
                        }
                        # Strip words immediately following colon/question mark
                        subtitles_stripped = re.sub(r"[:?]\s+[A-Z][a-z]+", "", title)
                        w_check = [w for w in re.findall(r"[A-Za-z]+", subtitles_stripped)[1:] if len(w) > 3 and w not in proper]
                        cap_words = [w for w in w_check if w[0].isupper()]
                        if len(cap_words) >= 2:
                            errors.append(f"{fname}: Ref #{idx} appears Title Case (APA 7th needs sentence case): '{title}'")

    # 2. Inspect DOCX files
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    for docx_path in sorted(glob.glob(os.path.join(directory, "*.docx"))):
        fname = os.path.basename(docx_path)
        with zipfile.ZipFile(docx_path) as z:
            doc = ET.fromstring(z.read("word/document.xml"))
            paras = ["".join(t.text for t in p.findall(".//w:t", ns) if t.text).strip() for p in doc.findall(".//w:body/w:p", ns)]
            paras = [p for p in paras if p]

            # Markdown leftovers
            for p in paras:
                if "**" in p or "###" in p or "`" in p:
                    errors.append(f"{fname}: Unparsed markdown syntax found -> '{p[:70]}'")
                    break

            # Duplicate consecutive Table headings or Figure captions
            fig_caps = [p for p in paras if re.match(r"^Figure\s+\d+\.", p)]
            if len(fig_caps) != len(set(fig_caps)):
                errors.append(f"{fname}: Duplicate Figure captions detected")
            for idx in range(len(paras) - 1):
                if re.match(r"^Table\s+\d+$", paras[idx]) and re.match(r"^Table\s+\d+\.", paras[idx + 1]):
                    errors.append(f"{fname}: Duplicate Table heading ('{paras[idx]}' before '{paras[idx+1][:40]}')")

            if "blinded" in fname.lower():
                # Check anonymized metadata
                if "docProps/core.xml" in z.namelist():
                    core = z.read("docProps/core.xml").decode("utf-8", errors="ignore")
                    if re.search(r"<dc:creator>[^<]+</dc:creator>", core):
                        errors.append(f"{fname}: Non-empty dc:creator in core.xml (blinding risk)")
                # Check double-spacing (480 twips)
                sp_vals = {
                    sp.get(qn("w:line"))
                    for p in doc.findall(".//w:body/w:p", ns)
                    for sp in p.findall(".//w:spacing", ns)
                    if sp.get(qn("w:line"))
                }
                if "480" not in sp_vals:
                    errors.append(f"{fname}: Double spacing (480 twips / 2.0x) not detected (found: {sp_vals})")
                # Check continuous line numbering
                if doc.find(".//w:lnNumType", ns) is None:
                    errors.append(f"{fname}: Continuous line numbering missing")
                # Check page numbering header
                hdr_files = [n for n in z.namelist() if "header" in n or "footer" in n]
                if not hdr_files:
                    errors.append(f"{fname}: Missing header/footer page numbers")

    # 3. Inspect supplementary Python scripts for path / PI leaks
    for py_path in sorted(glob.glob(os.path.join(directory, "**", "*.py"), recursive=True)):
        fname = os.path.relpath(py_path, directory)
        with open(py_path, "r", encoding="utf-8") as f:
            code = f.read()
        if re.search(r"[A-Za-z]:\\|/Users/|내 드라이브", code):
            errors.append(f"{fname}: Hardcoded local machine path found")
        if re.search(r'["\']연구책임자["\']', code):
            errors.append(f"{fname}: References PI real-name column ('연구책임자') — anonymization risk")

    print(f"\nValidation complete: {len(errors)} error(s), {len(warnings)} warning(s).")
    for e in errors:
        print(f"  [ERROR]   {e}")
    for w in warnings:
        print(f"  [WARNING] {w}")
    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description="Wiley / SSCI APA 7th DOCX Builder & Validator")
    parser.add_argument("--input", help="Input Markdown file")
    parser.add_argument("--output", help="Output DOCX file")
    parser.add_argument(
        "--doc-type",
        choices=["manuscript", "title_page", "cover_letter", "supplementary"],
        default="manuscript",
    )
    parser.add_argument("--running-head", default="", help="Running head text for header")
    parser.add_argument("--figures-dir", default=None, help="Directory with high-DPI figure PNG/JPG files")
    parser.add_argument("--line-numbers", action="store_true", help="Enable continuous line numbering")
    parser.add_argument("--validate-dir", default=None, help="Validate all submission files in directory")
    parser.add_argument("--sole-author", action="store_true", help="Check for sole-author pronoun consistency")
    args = parser.parse_args()

    if args.validate_dir:
        sys.exit(validate_submission_dir(args.validate_dir, sole_author=args.sole_author))

    if not args.input or not args.output:
        parser.error("Provide --input and --output (or --validate-dir).")

    build_docx_from_markdown(
        input_md=args.input,
        output_docx=args.output,
        doc_type=args.doc_type,
        running_head=args.running_head,
        figures_dir=args.figures_dir,
        line_numbers=args.line_numbers,
    )


if __name__ == "__main__":
    main()
