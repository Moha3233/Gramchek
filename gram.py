import streamlit as st
import language_tool_python
from typing import List, Dict
import re

# Initialize the grammar checker
@st.cache_resource
def load_grammar_tool():
    """Load and cache the LanguageTool grammar checker"""
    return language_tool_python.LanguageTool('en-US')

def highlight_text(text: str, matches: List) -> str:
    """Highlight errors in the text using HTML"""
    if not matches:
        return text
    
    # Sort matches by offset in reverse to avoid index shifting
    sorted_matches = sorted(matches, key=lambda x: x.offset, reverse=True)
    
    highlighted = text
    for match in sorted_matches:
        start = match.offset
        end = match.offset + match.errorLength
        error_text = text[start:end]
        
        # Create tooltip with suggestion
        suggestion = match.replacements[0] if match.replacements else "No suggestion"
        tooltip = f'<span style="background-color: #ffcccc; border-bottom: 2px solid red; cursor: help;" title="{match.message} | Suggestion: {suggestion}">{error_text}</span>'
        
        highlighted = highlighted[:start] + tooltip + highlighted[end:]
    
    return highlighted

def get_error_details(matches: List) -> List[Dict]:
    """Extract detailed information about each error"""
    errors = []
    for i, match in enumerate(matches, 1):
        error_info = {
            'number': i,
            'error_text': match.context[match.offsetInContext:match.offsetInContext + match.errorLength],
            'message': match.message,
            'suggestions': match.replacements[:3] if match.replacements else ['No suggestions available'],
            'rule': match.ruleId,
            'category': match.category
        }
        errors.append(error_info)
    return errors

def apply_correction(text: str, match, suggestion: str) -> str:
    """Apply a single correction to the text"""
    start = match.offset
    end = match.offset + match.errorLength
    return text[:start] + suggestion + text[end:]

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
        placeholder="Type or paste your text here..."
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
        st.rerun()
    
    if check_button and user_input:
        with st.spinner("Checking grammar..."):
            tool = load_grammar_tool()
            matches = tool.check(user_input)
            st.session_state.matches = matches
            
            if matches:
                # Auto-correct all errors
                corrected = user_input
                for match in reversed(matches):
                    if match.replacements:
                        corrected = apply_correction(corrected, match, match.replacements[0])
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
        
        # Copy button
        st.code(st.session_state.corrected_text, language=None)

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
                
                if error['suggestions'][0] != 'No suggestions available':
                    st.markdown("**Suggestions:**")
                    for i, sugg in enumerate(error['suggestions'], 1):
                        st.markdown(f"{i}. {sugg}")
                else:
                    st.info("No suggestions available for this error.")
    else:
        st.success("🎉 Great job! No grammar errors found in your text.")

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>💡 <strong>Tips:</strong> This tool checks for grammar, spelling, punctuation, and style issues.</p>
        <p>Powered by LanguageTool | Built with Streamlit</p>
    </div>
""", unsafe_allow_html=True)
