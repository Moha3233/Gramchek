import streamlit as st
import re

st.set_page_config(page_title="ATS Resume Scorer", layout="wide")

st.title("📄 ATS Resume Scoring Engine (Strict HR Mode)")
st.caption("If it’s not written, it doesn’t exist.")
st.divider()

JOB_CRITERIA = {
    "mandatory_sections": {
        "summary": 10,
        "experience": 25,
        "skills": 20,
        "education": 10,
        "projects": 10
    }
}

def score_resume(text):
    score = 0
    feedback = []
    text = text.lower()

    if "summary" in text:
        score += 10
    else:
        feedback.append("Missing Summary")

    if "experience" in text:
        score += 25
    else:
        feedback.append("Missing Experience")

    if "skills" in text:
        score += 20
    else:
        feedback.append("Missing Skills")

    if "education" in text:
        score += 10
    else:
        feedback.append("Missing Education")

    if "projects" in text:
        score += 10
    else:
        feedback.append("Missing Projects")

    score = min(score, 100)

    verdict = (
        "Strong Hire" if score >= 85 else
        "Shortlist" if score >= 70 else
        "Borderline" if score >= 55 else
        "Reject"
    )

    return score, verdict, feedback

resume = st.text_area("Paste Resume Text", height=300)

if st.button("Analyze Resume"):
    if resume.strip() == "":
        st.warning("Please paste resume text.")
    else:
        score, verdict, feedback = score_resume(resume)
        st.metric("Final Score", score)
        st.subheader("Verdict")
        st.write(verdict)
        st.subheader("Feedback")
        for f in feedback:
            st.write("❌", f)
