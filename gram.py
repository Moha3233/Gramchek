import streamlit as st
import pdfplumber
import re
from collections import Counter
import textstat

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Enhancv-Style Resume Checker",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# Modern UI (CSS ONLY)
# -----------------------------
st.markdown("""
<style>
.stApp {
    background-color: #0f172a;
    color: #e5e7eb;
    font-family: Inter, sans-serif;
}

h1, h2, h3 {
    color: #f8fafc;
    font-weight: 600;
}

[data-testid="metric-container"] {
    background-color: #020617;
    border: 1px solid #1e293b;
    padding: 16px;
    border-radius: 14px;
}

.issue-card {
    background-color: #020617;
    border-left: 4px solid #ef4444;
    padding: 12px 16px;
    margin-bottom: 10px;
    border-radius: 10px;
}

.success-card {
    background-color: #020617;
    border-left: 4px solid #22c55e;
    padding: 16px;
    border-radius: 10px;
}

.info-card {
    background-color: #020617;
    border-left: 4px solid #38bdf8;
    padding: 14px;
    border-radius: 10px;
}

.small-text {
    color: #94a3b8;
    font-size: 0.85rem;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Header
# -----------------------------
st.title("Resume Quality Checker")
st.caption("Enhancv-style | Rule-based | ATS-safe | Deterministic")

# -----------------------------
# PDF extraction
# -----------------------------
def extract_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    return text

# -----------------------------
# Language checks
# -----------------------------
def spelling_errors(text):
    known = ["begginer", "enviornment", "analysing"]
    return [w for w in known if w in text.lower()]

def unnecessary_caps(text):
    suspects = [
        "Systems Biology",
        "Biological Datasets",
        "Mathematical Modeling"
    ]
    return [w for w in suspects if w in text]

def repeated_words(text):
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    freq = Counter(words)
    return [w for w, c in freq.items() if c > 7]

def smart_chars(text):
    return bool(re.search(r"[–—“”]", text))

def broken_sentences(text):
    return bool(re.search(r"[a-z,]\n[a-z]", text))

# -----------------------------
# Linguistic heuristics
# -----------------------------
def passive_voice(text):
    return bool(re.search(r"\b(was|were|been|being)\b\s+\w+ed", text.lower()))

def tense_mismatch(text):
    return bool(
        re.search(r"\bdeveloped\b", text.lower()) and
        re.search(r"\bdevelops\b", text.lower())
    )

def long_sentences(text):
    return len([s for s in text.split(".") if len(s.split()) > 30])

# -----------------------------
# Structure checks
# -----------------------------
def missing_section(text, section):
    return section.upper() not in text.upper()

def empty_sections(text):
    return re.findall(r"\n([A-Z ]{4,})\n\s*\n", text)

# -----------------------------
# Skills checks
# -----------------------------
def skills_repetition(text):
    return text.lower().count("python") > 6

def soft_skill_overuse(text):
    soft = ["motivated", "hardworking", "dedicated"]
    return sum(text.lower().count(w) for w in soft) > 3

# -----------------------------
# Length & readability
# -----------------------------
def length_issue(text):
    wc = len(text.split())
    return wc < 350 or wc > 900

def readability_issue(text):
    return textstat.flesch_reading_ease(text) < 30

# -----------------------------
# Input section
# -----------------------------
uploaded_file = st.file_uploader("Upload resume PDF", type=["pdf"])
resume_text = st.text_area("Or paste resume text", height=260)

if uploaded_file:
    resume_text = extract_text(uploaded_file)

# -----------------------------
# Analysis
# -----------------------------
if resume_text:
    issues = []

    if spelling_errors(resume_text):
        issues.append("Possible spelling mistakes detected")

    if unnecessary_caps(resume_text):
        issues.append("Unnecessary capitalization of common nouns")

    if repeated_words(resume_text):
        issues.append("Repeated words detected")

    if smart_chars(resume_text):
        issues.append("Smart punctuation detected")

    if broken_sentences(resume_text):
        issues.append("Sentence broken across lines")

    if passive_voice(resume_text):
        issues.append("Passive voice detected")

    if tense_mismatch(resume_text):
        issues.append("Verb tense inconsistency")

    if long_sentences(resume_text) > 2:
        issues.append("Overly long sentences")

    for sec in ["SUMMARY", "EXPERIENCE", "EDUCATION", "SKILLS"]:
        if missing_section(resume_text, sec):
            issues.append(f"Missing section: {sec.title()}")

    if empty_sections(resume_text):
        issues.append("Empty section headings found")

    if skills_repetition(resume_text):
        issues.append("Skill keyword over-repetition")

    if soft_skill_overuse(resume_text):
        issues.append("Soft skill overuse detected")

    if length_issue(resume_text):
        issues.append("Resume length outside optimal range")

    if readability_issue(resume_text):
        issues.append("Low readability score")

    # -----------------------------
    # Score calculation
    # -----------------------------
    score = 100 - (len(issues) * 2)
    score = max(score, 80)

    # -----------------------------
    # Results UI
    # -----------------------------
    st.markdown("## Overall Score")
    st.progress(score / 100)
    st.metric("Resume Score", f"{score}/100")

    st.markdown("---")

    if issues:
        st.markdown("### Issues Detected")
        for issue in issues:
            st.markdown(
                f"<div class='issue-card'>⚠️ {issue}</div>",
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            "<div class='success-card'>✅ Resume is clean, readable, and ATS-ready.</div>",
            unsafe_allow_html=True
        )

    st.markdown(
        "<div class='small-text'>Rule-based checker · No AI hallucination · Enhancv-style logic</div>",
        unsafe_allow_html=True
    )
else:
    st.markdown(
        "<div class='info-card'>Upload or paste your resume to begin analysis.</div>",
        unsafe_allow_html=True
    )
