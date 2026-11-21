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

"""SSCI-adapted AgentReview 3-reviewer ensemble and Associate Editor meta-review prompts."""

SSCI_SCORE_RUBRIC = {
    10: "Top 2% SSCI submission: landmark empirical/policy contribution, flawless methodology, transparent limitations, immediate Accept.",
    8: "Top 10% SSCI submission: strong scope fit, rigorous design and reporting, minor editorial polish needed (Minor Revision).",
    6: "Solid empirical/descriptive contribution with sound core data, but requires targeted theoretical, methodological, or scope revisions (Moderate/Major Revision).",
    5: "Promising topic and data, but significant gaps in scope alignment, reliability (e.g., single coder), reporting, or APA/journal compliance (Major Revision / Borderline Reject).",
    3: "Marginal contribution, serious methodological flaws, or clear mismatch with journal scope (Reject).",
    1: "Not ready for peer review: incomplete placeholders, anonymization/ethics breaches, or unsupported claims (Desk Reject).",
}

SSCI_REVIEWER_PERSONAS = {
    "policy_scope": (
        "You are Reviewer 1: a Senior Disability Policy and Research-Funding Audit Specialist "
        "serving on the editorial board of an SSCI journal (e.g., Journal of Policy and Practice "
        "in Intellectual Disabilities). Evaluate journal scope fit, policy translation beyond a "
        "single country, alignment with international frameworks (e.g., UN CRPD), and precision of "
        "funding/administrative data interpretation."
    ),
    "domain_theory": (
        "You are Reviewer 2: a Domain Scholar in Adapted Physical Activity, Inclusive Education, "
        "and Disability Studies. Evaluate conceptual framing (e.g., social justice, medical vs. "
        "social/rights-based models), construct definitions, inclusion/exclusion edge cases, and "
        "practical relevance for educators, practitioners, and disabled communities."
    ),
    "methods_ethics": (
        "You are Reviewer 3: a Quantitative Methods, Reproducibility, and Research Integrity "
        "Reviewer. Scrutinize arithmetic consistency across text/tables/figures, screening "
        "protocol reproducibility, inter-rater reliability, sensitivity analyses, transparent "
        "limitations, double-blind anonymization, AI-use disclosure compliance, and APA 7th rigor."
    ),
}

SSCI_AGENTREVIEW_INSTRUCTIONS = """
Evaluate the manuscript strictly against SSCI peer-review standards.
Respond in the following format:

THOUGHT:
<Specific, evidence-grounded reasoning referencing exact sections, tables, and numbers>

REVIEW JSON:
```json
{
  "Summary": "Concise summary of the manuscript and its core contribution.",
  "Strengths": ["Specific strength 1", "Specific strength 2"],
  "Weaknesses": ["Specific weakness 1 with exact location/evidence", "..."],
  "Scope_Fit": 1,
  "Originality": 1,
  "Methodological_Rigor": 1,
  "Clarity_and_APA7": 1,
  "Policy_Practice_Significance": 1,
  "Ethics_and_Reproducibility": 1,
  "Questions": ["Actionable question 1 for the author(s)", "..."],
  "Limitations_Assessment": "Whether the manuscript honestly and adequately states its limitations.",
  "Desk_Reject_Flags": ["Any administrative, blinding, ethics, or placeholder issues"],
  "Overall": 5,
  "Confidence": 4,
  "Decision": "Major Revision"
}
```
Scale: sub-scores 1-4 (1=poor, 2=fair, 3=good, 4=excellent); Overall 1-10; Confidence 1-5.
Decision MUST be one of: "Accept", "Minor Revision", "Major Revision", "Reject", "Desk Reject".
"""

SSCI_ASSOCIATE_EDITOR_META_PROMPT = """
You are an experienced Associate Editor at an SSCI journal (Wiley / Taylor & Francis / SAGE).
Synthesize the {reviewer_count} independent reviewer reports into a single decisive meta-review.
Separate:
1. Mandatory Desk-Check / Administrative Fixes (must be resolved before peer review),
2. Substantive Scientific Revisions (scope, reliability, sensitivity, theory, literature), and
3. Realistic Target Journal & Article-Type Recommendation (e.g., Original Article vs. Brief Report).
Return the same JSON schema defined in SSCI_AGENTREVIEW_INSTRUCTIONS.
"""
