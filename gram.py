import streamlit as st
import pdfplumber
import re
from collections import Counter
import textstat

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="ATS Resume Analyzer",
    layout="wide"
)

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
body {
    background-color: #0e1628;
    color: #ffffff;
}
.card {
    background: linear-gradient(145deg, #111c33, #0b1224);
    padding: 20px;
    border-radius: 14px;
    margin-bottom: 18px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.35);
}
.score {
    font-size: 42px;
    font-weight: 700;
}
.issue {
    padding: 12px;
    margin-bottom: 8px;
    border-left: 4px solid #ff5c5c;
    background-color: rgba(255,92,92,0.08);
    border-radius: 6px;
}
.good {
    border-left: 4px solid #4ade80;
    background-color: rgba(74,222,128,0.08);
}
.resume-panel {
    background: #0b1224;
    padding: 18px;
    border-radius: 14px;
    height: 88vh;
    overflow-y: auto;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.05);
}
.highlight {
    background-color: rgba(255, 0, 0, 0.35);
    padding: 2px 4px;
    border-radius: 4px;
}
.section-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 12px;
}
small {
    color: #9ca3af;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def extract_text(pdf):
    text = ""
    with pdfplumber.open(pdf) as p:
        for page in p.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def smart_punctuation(text):
    return bool(re.search(r"[“”‘’]", text))

def broken_sentences(text):
    return bool(re.search(r"[a-z]\n[a-z]", text))

def long_sentences(text):
    sentences = re.split(r"[.!?]", text)
    return any(len(s.split()) > 30 for s in sentences)

def repetition(text):
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    freq = Counter(words)
    return any(v > 10 for v in freq.values())

def readability_issue(text):
    return textstat.flesch_reading_ease(text) < 40

def highlight_text(text):
    text = re.sub(r"[“”‘’]", r"<span class='highlight'>\g<0></span>", text)
    text = re.sub(r"([a-z])\n([a-z])", r"\1<span class='highlight'>↵</span>\2", text)

    sentences = re.split(r"([.!?])", text)
    rebuilt = ""
    for i in range(0, len(sentences)-1, 2):
        sentence = sentences[i]
        punct = sentences[i+1]
        if len(sentence.split()) > 30:
            sentence = f"<span class='highlight'>{sentence}</span>"
        rebuilt += sentence + punct
    return rebuilt

# ---------------- UI ----------------
st.title("📄 ATS Resume Quality Analyzer")

uploaded = st.file_uploader("Upload Resume (PDF only)", type=["pdf"])

if uploaded:
    resume_text = extract_text(uploaded)

    issues = []
    score = 100

    if smart_punctuation(resume_text):
        issues.append("Smart punctuation detected (ATS incompatible).")
        score -= 2

    if broken_sentences(resume_text):
        issues.append("Sentence broken across lines.")
        score -= 3

    if long_sentences(resume_text):
        issues.append("Overly long sentences detected.")
        score -= 3

    if repetition(resume_text):
        issues.append("Repetitive words reduce ATS clarity.")
        score -= 2

    if readability_issue(resume_text):
        issues.append("Low readability score.")
        score -= 3

    score = max(score, 0)

    # ---------------- LAYOUT ----------------
    left, right = st.columns([1.9, 1.1], gap="large")

    # -------- LEFT: ANALYSIS --------
    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("## Overall Score")
        st.markdown(f"<div class='score'>{score}/100</div>", unsafe_allow_html=True)
        st.progress(score / 100)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("## Issues Detected")
        if issues:
            for issue in issues:
                st.markdown(f"<div class='issue'>⚠️ {issue}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='issue good'>✅ No issues detected</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # -------- RIGHT: PERMANENT RESUME VIEW --------
    with right:
        st.markdown("<div class='resume-panel'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Resume Preview</div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="white-space:pre-wrap; font-size:0.85rem; line-height:1.6;">
            {highlight_text(resume_text)}
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("Upload a PDF resume to begin analysis.")
