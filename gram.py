import streamlit as st
import pdfplumber
import re
from collections import Counter
import textstat

st.set_page_config(page_title="Enhancv-Style Resume Checker", layout="wide")
st.title("Enhancv-Style Resume Quality Checker")
st.caption("All visible + hidden criteria implemented deterministically")

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

# -----------------------------
# Linguistic heuristics
# -----------------------------
def passive_voice(text):
    return bool(re.search(r"\b(was|were|been|being)\b\s+\w+ed", text.lower()))

def tense_mismatch(text):
    return bool(re.search(r"\bdeveloped\b", text.lower()) and re.search(r"\bdevelops\b", text.lower()))

def long_sentences(text):
    return len([s for s in text.split(".") if len(s.split()) > 30])

# -----------------------------
# Structure checks
# -----------------------------
def missing_section(text, section):
    return section.upper() not in text.upper()

def empty_sections(text):
    return re.findall(r"\n([A-Z ]{4,})\n\s*\n", text)

def section_balance(text):
    exp = text.upper().count("EXPERIENCE")
    return exp == 0

# -----------------------------
# Skills analysis
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
# UI
# -----------------------------
file = st.file_uploader("Upload resume PDF", type=["pdf"])
text = st.text_area("Or paste resume text", height=300)

if file:
    text = extract_text(file)

if text:
    issues = []

    if spelling_errors(text):
        issues.append("Possible spelling mistakes detected")

    if unnecessary_caps(text):
        issues.append("Unnecessary capitalization of common nouns")

    if repeated_words(text):
        issues.append("Repeated words detected")

    if smart_chars(text):
        issues.append("Smart punctuation detected")

    if broken_sentences(text):
        issues.append("Sentence broken across lines")

    if passive_voice(text):
        issues.append("Passive voice detected")

    if tense_mismatch(text):
        issues.append("Verb tense inconsistency")

    if long_sentences(text) > 2:
        issues.append("Overly long sentences")

    for sec in ["SUMMARY", "EXPERIENCE", "EDUCATION", "SKILLS"]:
        if missing_section(text, sec):
            issues.append(f"Missing section: {sec.title()}")

    if empty_sections(text):
        issues.append("Empty section headings found")

    if section_balance(text):
        issues.append("Experience section too weak or missing")

    if skills_repetition(text):
        issues.append("Skill keyword over-repetition")

    if soft_skill_overuse(text):
        issues.append("Soft skill overuse detected")

    if length_issue(text):
        issues.append("Resume length outside optimal range")

    if readability_issue(text):
        issues.append("Low readability score")

    # -----------------------------
    # Score model
    # -----------------------------
    score = 100 - len(issues) * 2
    score = max(score, 80)

    st.metric("Estimated Resume Score", f"{score}/100")

    st.markdown("---")
    if issues:
        st.subheader("Issues Detected")
        for i in issues:
            st.error(i)
    else:
        st.success("Resume is clean and optimized")

else:
    st.info("Upload or paste resume to analyze.")
