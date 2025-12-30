import streamlit as st
import re

st.set_page_config(page_title="ATS Resume Scorer", layout="wide")

st.title("📄 ATS Resume Scoring Engine (Strict HR Mode)")
st.caption("Evidence-based resume evaluation • Offline • Rule-driven")
st.divider()

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
        "simple_format": 5
    }
}

def normalize(text):
    return re.sub(r"\s+", " ", text.lower())

def extract_section(text, keywords):
    for k in keywords:
        match = re.search(rf"{k}[:\n](.*?)(summary|experience|skills|education|projects|$)",
                          text, re.DOTALL)
        if match:
            return match.group(1)
    return ""

def extract_years(text):
    yrs = re.findall(r"(\d+)\+?\s*(years|yrs)", text)
    return max([int(y[0]) for y in yrs], default=0)

def quantified_impact(text):
    patterns = [r"\d+%", r"\d+\+", "increase", "reduce", "improve", "optimize"]
    return sum(len(re.findall(p, text)) for p in patterns)

def has_standard_headings(text):
    for h in ["summary", "experience", "skills", "education", "projects"]:
        if h not in text:
            return False
    return True

def score_resume(resume_text):
    feedback = []
    score = 0

    text = normalize(resume_text)

    sections = {
        "summary": extract_section(text, ["summary", "profile"]),
        "experience": extract_section(text, ["experience", "employment"]),
        "skills": extract_section(text, ["skills", "technical skills"]),
        "education": extract_section(text, ["education"]),
        "projects": extract_section(text, ["projects"])
    }

    for sec, weight in JOB_CRITERIA["mandatory_sections"].items():
        if sections[sec]:
            score += weight
        else:
            feedback.append(f"Missing mandatory section: {sec.title()}")

    for skill, w in JOB_CRITERIA["skills"]["core"].items():
        if skill in text:
            score += w
        else:
            feedback.append(f"Missing core skill: {skill}")

    for skill, w in JOB_CRITERIA["skills"]["secondary"].items():
        if skill in text:
            score += w

    years = extract_years(sections["experience"])
    if years >= JOB_CRITERIA["experience_rules"]["minimum_years"]:
        score += 10
    else:
        feedback.append("Insufficient years of experience")

    if quantified_impact(sections["experience"]) == 0:
        score += JOB_CRITERIA["experience_rules"]["penalty_no_numbers"]
        feedback.append("No quantified impact in experience")

    if has_standard_headings(text):
        score += JOB_CRITERIA["ats_rules"]["standard_headings"]
    else:
        feedback.append("Non-standard or missing section headings")

    score += JOB_CRITERIA["ats_rules"]["simple_format"]
    score = max(0, min(score, 100))

    verdict = (
        "Strong Hire" if score >= 85 else
        "Shortlist" if score >= 70 else
        "Borderline" if score >= 55 else
        "Reject"
    )

    return score, verdict, list(set(feedback))

resume_input = st.text_area("Paste Resume Text Here", height=350)

if st.button("Analyze Resume"):
    if resume_input.strip() == "":
        st.warning("Please paste resume text.")
    else:
        score, verdict, feedback = score_resume(resume_input)

        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Final Score", score)
            st.subheader("HR Verdict")
            st.write(verdict)

        with col2:
            st.subheader("Feedback")
            for f in feedback:
                st.write("❌", f)

st.caption("If it’s not written, it doesn’t exist.")
