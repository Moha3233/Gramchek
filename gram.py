"""
STRICT HR RESUME SCORING ENGINE
Author: HR Evaluation System
Mode: Rule-based | ATS-style | Offline

INPUT  : Resume text (already extracted from PDF/DOCX)
OUTPUT : Score (0–100), HR verdict, improvement suggestions
"""

import re
from typing import Dict, List

# -----------------------------
# JOB CRITERIA (PDF → JSON LOGIC)
# -----------------------------

JOB_CRITERIA = {
    "mandatory_sections": {
        "summary": 10,
        "experience": 25,
        "skills": 20,
        "education": 10,
        "projects": 10
    },

    "skills": {
        "core": {
            "python": 5,
            "bioinformatics": 5,
            "molecular docking": 5,
            "data analysis": 5
        },
        "secondary": {
            "machine learning": 3,
            "r": 2,
            "linux": 2
        }
    },

    "experience_rules": {
        "minimum_years": 2,
        "penalty_no_numbers": -5
    },

    "ats_rules": {
        "standard_headings": 5,
        "no_tables": 3,
        "simple_format": 2
    }
}

# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())

def extract_section(text: str, keywords: List[str]) -> str:
    for k in keywords:
        pattern = rf"{k}[:\n](.*?)(summary|experience|skills|education|projects|$)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1)
    return ""

def count_quantified_bullets(text: str) -> int:
    patterns = [
        r"\d+%",
        r"\d+\+",
        r"increased",
        r"reduced",
        r"improved",
        r"optimized",
        r"decreased"
    ]
    return sum(len(re.findall(p, text)) for p in patterns)

def extract_years_of_experience(text: str) -> int:
    matches = re.findall(r"(\d+)\+?\s*(years|yrs)", text)
    if matches:
        return max(int(m[0]) for m in matches)
    return 0

def uses_standard_headings(text: str) -> bool:
    headings = ["summary", "experience", "skills", "education", "projects"]
    return all(h in text for h in headings)

# -----------------------------
# CORE SCORING ENGINE
# -----------------------------

class ResumeScorer:

    def __init__(self, resume_text: str):
        self.resume_text = normalize_text(resume_text)
        self.sections = {
            "summary": extract_section(self.resume_text, ["summary", "profile"]),
            "experience": extract_section(self.resume_text, ["experience", "employment"]),
            "skills": extract_section(self.resume_text, ["skills", "technical skills"]),
            "education": extract_section(self.resume_text, ["education"]),
            "projects": extract_section(self.resume_text, ["projects"])
        }
        self.feedback = []

    def score_sections(self) -> int:
        score = 0
        for sec, weight in JOB_CRITERIA["mandatory_sections"].items():
            if self.sections[sec]:
                score += weight
            else:
                self.feedback.append(f"Missing mandatory section: {sec.title()}")
        return score

    def score_skills(self) -> int:
        score = 0

        for skill, weight in JOB_CRITERIA["skills"]["core"].items():
            if skill in self.resume_text:
                score += weight
            else:
                self.feedback.append(f"Missing core skill: {skill}")

        for skill, weight in JOB_CRITERIA["skills"]["secondary"].items():
            if skill in self.resume_text:
                score += weight

        return score

    def score_experience(self) -> int:
        score = 0
        exp_text = self.sections["experience"]

        years = extract_years_of_experience(exp_text)
        if years >= JOB_CRITERIA["experience_rules"]["minimum_years"]:
            score += 15
        else:
            self.feedback.append("Insufficient years of experience")

        quantified = count_quantified_bullets(exp_text)
        if quantified == 0:
            score += JOB_CRITERIA["experience_rules"]["penalty_no_numbers"]
            self.feedback.append("No quantified impact in experience bullets")

        return score

    def score_ats(self) -> int:
        score = 0

        if uses_standard_headings(self.resume_text):
            score += JOB_CRITERIA["ats_rules"]["standard_headings"]
        else:
            self.feedback.append("Non-standard section headings")

        # Tables & formatting checks are placeholders (PDF-level analysis)
        score += JOB_CRITERIA["ats_rules"]["no_tables"]
        score += JOB_CRITERIA["ats_rules"]["simple_format"]

        return score

    def final_score(self) -> Dict:
        total = (
            self.score_sections()
            + self.score_skills()
            + self.score_experience()
            + self.score_ats()
        )

        total = max(0, min(total, 100))

        verdict = (
            "Strong Hire" if total >= 85 else
            "Shortlist" if total >= 70 else
            "Borderline" if total >= 55 else
            "Reject"
        )

        return {
            "final_score": total,
            "verdict": verdict,
            "feedback": list(set(self.feedback))
        }

# -----------------------------
# EXAMPLE USAGE
# -----------------------------

if __name__ == "__main__":
    sample_resume_text = """
    Summary:
    Computational Biologist with 3+ years experience.

    Experience:
    Improved docking accuracy by 25% using AutoDock Vina.
    Analyzed 100+ ligands for protein-ligand interactions.

    Skills:
    Python, Bioinformatics, Molecular Docking, Data Analysis, Linux

    Education:
    MSc Biochemistry

    Projects:
    AI-driven Drug Discovery Platform
    """

    scorer = ResumeScorer(sample_resume_text)
    result = scorer.final_score()

    print("FINAL SCORE:", result["final_score"])
    print("HR VERDICT:", result["verdict"])
    print("IMPROVEMENT FEEDBACK:")
    for f in result["feedback"]:
        print("-", f)
