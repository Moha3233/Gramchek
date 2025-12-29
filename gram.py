import streamlit as st
import pdfplumber
import re
from collections import Counter

st.set_page_config(page_title="ATS Resume Analyzer", layout="wide")

st.title("📄 ATS Resume Analyzer & Optimizer")
st.caption("Precise ATS-style analysis with actionable resume fixes")

# -----------------------------
# Helper functions
# -----------------------------

def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text


def count_quantified_bullets(text):
    return len(re.findall(r"\d+%|\d+\+|\~\d+|\d+", text))


def find_empty_sections(text):
    sections = re.findall(r"\n([A-Z\s]{3,})\n", text)
    empty = []
    for sec in sections:
        pattern = sec + r"\n\s*\n"
        if re.search(pattern, text):
            empty.append(sec.strip())
    return empty


def detect_repetition(text):
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    common = Counter(words).most_common(10)
    return [(w, c) for w, c in common if c > 6]


def detect_formatting_issues(text):
    issues = []
    if "mailto:" in text.lower():
        issues.append("Remove 'mailto:' from email address")

    if re.search(r"[a-zA-Z],\s*\n[a-zA-Z]", text):
        issues.append("Line break inside sentence detected")

    if re.search(r"\b(Wet Lab|Academic Projects|Enzymatic)\b", text):
        issues.append("Unnecessary capitalization of common nouns")

    return issues


# -----------------------------
# UI
# -----------------------------

uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
resume_text = st.text_area("Or paste resume text here", height=300)

if uploaded_file:
    resume_text = extract_text_from_pdf(uploaded_file)

if resume_text:
    st.subheader("🔍 ATS Analysis Results")

    col1, col2 = st.columns(2)

    # Quantification
    quantified = count_quantified_bullets(resume_text)
    col1.metric("Quantified Impact", quantified)

    # Empty sections
    empty_sections = find_empty_sections(resume_text)
    col1.metric("Empty Sections", len(empty_sections))

    # Repetition
    repetition = detect_repetition(resume_text)
    col2.metric("Repetitive Keywords", len(repetition))

    # Formatting
    formatting_issues = detect_formatting_issues(resume_text)
    col2.metric("Formatting / Grammar Issues", len(formatting_issues))

    # -----------------------------
    # ATS Score Estimation
    # -----------------------------
    score = 100
    if quantified < 3:
        score -= 10
    if empty_sections:
        score -= 10
    if repetition:
        score -= 5
    if formatting_issues:
        score -= 10

    st.markdown("---")
    st.subheader(f"📊 Estimated ATS Score: **{max(score, 60)}/100**")

    # -----------------------------
    # Suggestions
    # -----------------------------
    st.markdown("---")
    st.subheader("🛠️ Precise Improvement Suggestions")

    if quantified < 3:
        st.warning("Add measurable impact (%, numbers, scale) to more bullets.")

    if empty_sections:
        st.error(f"Remove or fill empty sections: {', '.join(empty_sections)}")

    if repetition:
        st.warning("Reduce overuse of keywords:")
        for w, c in repetition:
            st.write(f"• '{w}' appears {c} times")

    if formatting_issues:
        st.error("Formatting / Grammar issues detected:")
        for issue in formatting_issues:
            st.write(f"• {issue}")

    if not (quantified < 3 or empty_sections or repetition or formatting_issues):
        st.success("Resume is ATS-clean and recruiter-ready 🎯")

else:
    st.info("Upload a resume or paste text to start analysis.")
