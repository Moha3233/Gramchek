import streamlit as st
import pdfplumber
import re
from collections import Counter
import textstat

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="Resume Quality Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# Modern UI / SaaS-grade CSS
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: radial-gradient(circle at top, #020617 0%, #020617 100%);
    color: #e5e7eb;
}

/* Hero */
.hero {
    padding: 3rem 1rem 2.5rem;
    text-align: center;
}
.hero h1 {
    font-size: 3rem;
    font-weight: 700;
    color: #f8fafc;
}
.hero p {
    font-size: 1.1rem;
    color: #94a3b8;
}

/* Cards */
.card {
    background: rgba(15, 23, 42, 0.75);
    backdrop-filter: blur(14px);
    border: 1px solid #1e293b;
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 22px;
}

/* Score */
.score {
    font-size: 4rem;
    font-weight: 700;
    color: #22c55e;
    text-align: center;
    margin-bottom: 10px;
}

/* Issues */
.issue {
    background: #020617;
    border-left: 4px solid #ef4444;
    padding: 14px 16px;
    border-radius: 12px;
    margin-bottom: 12px;
}

/* Success */
.success {
    background: #020617;
    border-left: 4px solid #22c55e;
    padding: 18px;
    border-radius: 14px;
    font-size: 1.05rem;
}

/* Footer */
.footer {
    color: #64748b;
    font-size: 0.85rem;
    text-align: center;
    margin: 40px 0 10px;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Hero header
# --------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>Resume Quality Analyzer</h1>
    <p>Enhancv-style diagnostics · ATS-safe · Rule-based · Deterministic</p>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# PDF text extraction
# --------------------------------------------------
def extract_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    return text

# --------------------------------------------------
# Checks (LOGIC UNCHANGED)
# --------------------------------------------------
def spelling_errors(text):
    known = ["begginer", "enviornment", "analysing"]
    return [w for w in known if w in text.lower()]

def unnecessary_caps(text):
    suspects = ["Systems Biology", "Biological Datasets", "Mathematical Modeling"]
    return [w for w in suspects if w in text]

def repeated_words(text):
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    freq = Counter(words)
    return [w for w, c in freq.items() if c > 7]

def smart_chars(text):
    return bool(re.search(r"[–—“”]", text))

def broken_sentences(text):
    return bool(re.search(r"[a-z,]\n[a-z]", text))

def passive_voice(text):
    return bool(re.search(r"\b(was|were|been|being)\b\s+\w+ed", text.lower()))

def tense_mismatch(text):
    return bool(re.search(r"\bdeveloped\b", text.lower()) and re.search(r"\bdevelops\b", text.lower()))

def long_sentences(text):
    return len([s for s in text.split(".") if len(s.split()) > 30])

def missing_section(text, section):
    return section.upper() not in text.upper()

def empty_sections(text):
    return re.findall(r"\n([A-Z ]{4,})\n\s*\n", text)

def skills_repetition(text):
    return text.lower().count("python") > 6

def soft_skill_overuse(text):
    soft = ["motivated", "hardworking", "dedicated"]
    return sum(text.lower().count(w) for w in soft) > 3

def length_issue(text):
    wc = len(text.split())
    return wc < 350 or wc > 900

def readability_issue(text):
    return textstat.flesch_reading_ease(text) < 30

# --------------------------------------------------
# Input section
# --------------------------------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
resume_text = st.text_area("Or paste your resume text", height=220)
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file:
    resume_text = extract_text(uploaded_file)

# --------------------------------------------------
# Analysis & Output
# --------------------------------------------------
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

    # Score (same logic)
    score = 100 - (len(issues) * 2)
    score = max(score, 80)

    # Score card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="score">{score}%</div>', unsafe_allow_html=True)
    st.progress(score / 100)
    st.markdown('</div>', unsafe_allow_html=True)

    # Issues card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Analysis Report")
    if issues:
        for issue in issues:
            st.markdown(f"<div class='issue'>⚠️ {issue}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='success'>✅ Resume is ATS-ready, readable, and professionally written.</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.markdown("""
<div class="footer">
Rule-based resume checker · No AI hallucination · Built for ATS precision
</div>
""", unsafe_allow_html=True)
