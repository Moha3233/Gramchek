import streamlit as st
import requests
from typing import List, Dict
import json

# Use LanguageTool API (free public instance)
LANGUAGETOOL_API = "https://api.languagetool.org/v2/check"

def check_grammar(text: str, language: str = "en-US") -> Dict:
    """Check grammar using LanguageTool public API"""
    try:
        data = {
            'text': text,
            'language': language
        }
        response = requests.post(LANGUAGETOOL_API, data=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to grammar check service: {e}")
        return None

def apply_corrections(text: str, matches: List[Dict]) -> str:
    """Apply all corrections to the text"""
    if not matches:
        return text
    
    # Sort matches by offset in reverse to avoid index shifting
    sorted_matches = sorted(matches, key=lambda x: x['offset'], reverse=True)
    
    corrected = text
    for match in sorted_matches:
        if match['replacements']:
            start = match['offset']
            end = match['offset'] + match['length']
            replacement = match['replacements'][0]['value']
            corrected = corrected[:start] + replacement + corrected[end:]
    
    return corrected

def get_error_details(matches: List[Dict]) -> List[Dict]:
    """Extract detailed information about each error"""
    errors = []
    for i, match in enumerate(matches, 1):
        context = match.get('context', {})
        error_text = context.get('text', '')[context.get('offset', 0):context.get('offset', 0) + context.get('length', 0)]
        
        error_info = {
            'number': i,
            'error_text': error_text,
            'message': match.get('message', 'No description'),
            'suggestions': [r['value'] for r in match.get('replacements', [])[:3]] or ['No suggestions available'],
            'rule': match.get('rule', {}).get('id', 'Unknown'),
            'category': match.get('rule', {}).get('category', {}).get('name', 'Unknown')
        }
        errors.append(error_info)
    return errors

# Streamlit App Configuration
st.set_page_config(
    page_title="English Grammar Checker",
    page_icon="✍️",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stats-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-card {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.3rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">✍️ English Grammar Checker</div>', unsafe_allow_html=True)
st.markdown("Check your text for grammar, spelling, and style issues with instant suggestions.")

# Initialize session state
if 'corrected_text' not in st.session_state:
    st.session_state.corrected_text = ""
if 'matches' not in st.session_state:
    st.session_state.matches = []
if 'original_text' not in st.session_state:
    st.session_state.original_text = ""

# Main layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Input Text")
    
    # Sample texts
    sample_option = st.selectbox(
        "Try a sample text:",
        ["Custom text", "Sample 1: Common errors", "Sample 2: Business email", "Sample 3: Academic writing"]
    )
    
    samples = {
        "Sample 1: Common errors": "Their are many reason why grammer is important. Its helps us communicate more better and makes our writing more clear.",
        "Sample 2: Business email": "Dear Sir, I am writing to enquire about the postion advertised on you're website. I have alot of experience in this feild and would be gratefull for the opportunity.",
        "Sample 3: Academic writing": "The study demonstrates that the results was significantly different. This phenomena have been observed in multiple experiment, which suggests that further research are needed."
    }
    
    default_text = samples.get(sample_option, "")
    
    user_input = st.text_area(
        "Enter your text here:",
        value=default_text,
        height=300,
        placeholder="Type or paste your text here...",
        key="input_text"
    )
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        check_button = st.button("🔍 Check Grammar", type="primary", use_container_width=True)
    with col_btn2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)

with col2:
    st.subheader("✅ Corrected Text")
    
    if clear_button:
        st.session_state.corrected_text = ""
        st.session_state.matches = []
        st.session_state.original_text = ""
        st.rerun()
    
    if check_button and user_input:
        with st.spinner("Checking grammar..."):
            result = check_grammar(user_input)
            
            if result:
                matches = result.get('matches', [])
                st.session_state.matches = matches
                st.session_state.original_text = user_input
                
                if matches:
                    # Auto-correct all errors
                    corrected = apply_corrections(user_input, matches)
                    st.session_state.corrected_text = corrected
                else:
                    st.session_state.corrected_text = user_input
    
    if st.session_state.corrected_text:
        st.text_area(
            "Corrected version:",
            value=st.session_state.corrected_text,
            height=300,
            key="corrected_output"
        )
        
        # Copy button hint
        if st.session_state.corrected_text != st.session_state.original_text:
            st.success("✨ Text has been corrected! You can copy it from above.")
        else:
            st.info("👍 No corrections needed!")

# Statistics and Errors Section
if check_button and user_input:
    st.divider()
    
    # Statistics
    word_count = len(user_input.split())
    char_count = len(user_input)
    error_count = len(st.session_state.matches)
    
    st.markdown("### 📊 Statistics")
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.metric("Words", word_count)
    with stat_col2:
        st.metric("Characters", char_count)
    with stat_col3:
        st.metric("Errors Found", error_count)
    with stat_col4:
        accuracy = max(0, 100 - (error_count / max(word_count, 1) * 100))
        st.metric("Accuracy", f"{accuracy:.1f}%")
    
    # Error Details
    if st.session_state.matches:
        st.markdown("### 🔍 Error Details")
        
        errors = get_error_details(st.session_state.matches)
        
        for error in errors:
            with st.expander(f"❌ Error {error['number']}: {error['error_text']}", expanded=False):
                st.markdown(f"**Issue:** {error['message']}")
                st.markdown(f"**Category:** {error['category']}")
                st.markdown(f"**Rule ID:** {error['rule']}")
                
                if error['suggestions'][0] != 'No suggestions available':
                    st.markdown("**Suggestions:**")
                    for i, sugg in enumerate(error['suggestions'], 1):
                        st.markdown(f"{i}. **{sugg}**")
                else:
                    st.info("No suggestions available for this error.")
    else:
        st.success("🎉 Great job! No grammar errors found in your text.")

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>💡 <strong>Tips:</strong> This tool checks for grammar, spelling, punctuation, and style issues.</p>
        <p>Powered by LanguageTool API | Built with Streamlit</p>
        <p style='font-size: 0.8rem; color: #999;'>Using free public API - for heavy usage, consider self-hosting</p>
    </div>
""", unsafe_allow_html=True)
