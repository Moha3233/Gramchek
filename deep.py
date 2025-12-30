import streamlit as st
import fitz  # PyMuPDF instead of pdfplumber
import docx
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import io
import base64
import zipfile
import tempfile
import os
from datetime import datetime

# Download NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except:
    nltk.download('punkt')
    nltk.download('stopwords')

# Set page configuration
st.set_page_config(
    page_title="ATS Resume Scanner",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (keep the same)
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    .criteria-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #4F46E5;
    }
    .match-high { color: #10B981; font-weight: bold; }
    .match-medium { color: #F59E0B; font-weight: bold; }
    .match-low { color: #EF4444; font-weight: bold; }
    .stProgress > div > div > div > div {
        background-color: #4F46E5;
    }
</style>
""", unsafe_allow_html=True)

class ATSResumeScanner:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.common_keywords = {
            'technical': ['python', 'java', 'javascript', 'sql', 'aws', 'docker', 'kubernetes', 
                         'react', 'node.js', 'machine learning', 'ai', 'data science', 'devops',
                         'git', 'ci/cd', 'rest api', 'microservices', 'agile', 'scrum'],
            'soft_skills': ['communication', 'leadership', 'teamwork', 'problem solving', 
                           'creativity', 'adaptability', 'time management', 'critical thinking'],
            'education': ['bachelor', 'master', 'phd', 'b.sc', 'm.sc', 'mba', 'bs', 'ms'],
            'experience': ['years experience', 'yr exp', 'experience in', 'worked on', 
                          'responsible for', 'managed', 'led', 'developed']
        }
    
    def extract_text_from_pdf(self, pdf_file):
        """Extract text from PDF file using PyMuPDF"""
        text = ""
        try:
            # Read the PDF file
            pdf_bytes = pdf_file.read()
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                page_text = page.get_text()
                if page_text:
                    text += page_text + "\n"
            
            pdf_document.close()
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            # Fallback: try reading as text
            try:
                pdf_file.seek(0)
                text = pdf_file.read().decode('utf-8', errors='ignore')
            except:
                pass
        return text
    
    def extract_text_from_docx(self, docx_file):
        """Extract text from DOCX file"""
        text = ""
        try:
            doc = docx.Document(docx_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            st.error(f"Error reading DOCX: {e}")
        return text
    
    # Keep all other methods exactly the same...
    # [Rest of the class remains unchanged - preprocess_text, extract_email, etc.]
    
    def preprocess_text(self, text):
        """Clean and preprocess text"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_email(self, text):
        """Extract email from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else "Not found"
    
    def extract_phone(self, text):
        """Extract phone number from text"""
        phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        phones = re.findall(phone_pattern, text)
        return phones[0] if phones else "Not found"
    
    def extract_skills(self, text, job_skills):
        """Extract skills from resume"""
        found_skills = []
        for skill in job_skills:
            if skill.lower() in text.lower():
                found_skills.append(skill)
        return found_skills
    
    def calculate_experience(self, text):
        """Calculate total years of experience"""
        experience_patterns = [
            r'(\d+)\s*(?:years?|yrs?)\s*(?:experience|exp)',
            r'experience\s*(?:of|:)\s*(\d+)\s*(?:years?|yrs?)'
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return max([int(match) for match in matches])
                except:
                    continue
        
        date_pattern = r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*\d{4}'
        dates = re.findall(date_pattern, text, re.IGNORECASE)
        if len(dates) >= 2:
            return len(dates) // 2
        
        return 0
    
    def check_keywords(self, resume_text, job_description):
        """Check keyword matches between resume and job description"""
        resume_words = set(word_tokenize(self.preprocess_text(resume_text)))
        job_words = set(word_tokenize(self.preprocess_text(job_description)))
        
        resume_words = resume_words - self.stop_words
        job_words = job_words - self.stop_words
        
        matches = resume_words.intersection(job_words)
        
        return {
            'total_job_keywords': len(job_words),
            'matched_keywords': len(matches),
            'match_percentage': (len(matches) / len(job_words) * 100) if job_words else 0,
            'matched_words': list(matches)
        }
    
    def score_resume(self, resume_text, job_description, criteria_weights=None):
        """Score resume based on multiple criteria"""
        if criteria_weights is None:
            criteria_weights = {
                'keyword_match': 30,
                'skills_match': 25,
                'experience': 20,
                'education': 15,
                'contact_info': 5,
                'formatting': 5
            }
        
        scores = {}
        feedback = []
        
        # 1. Keyword Match
        keyword_result = self.check_keywords(resume_text, job_description)
        keyword_score = min(keyword_result['match_percentage'], 100) * (criteria_weights['keyword_match'] / 100)
        scores['keyword_match'] = keyword_score
        
        if keyword_result['match_percentage'] >= 70:
            feedback.append(("✅ Excellent keyword match", "match-high"))
        elif keyword_result['match_percentage'] >= 40:
            feedback.append(("⚠️ Moderate keyword match - consider adding more relevant terms", "match-medium"))
        else:
            feedback.append(("❌ Low keyword match - needs improvement", "match-low"))
        
        # 2. Skills Match
        job_skills = []
        for skill_type in ['technical', 'soft_skills']:
            for skill in self.common_keywords[skill_type]:
                if skill in job_description.lower():
                    job_skills.append(skill)
        
        found_skills = self.extract_skills(resume_text, job_skills)
        skills_score = 0
        if job_skills:
            skills_match_percentage = (len(found_skills) / len(job_skills)) * 100
            skills_score = min(skills_match_percentage, 100) * (criteria_weights['skills_match'] / 100)
        
        scores['skills_match'] = skills_score
        
        if found_skills:
            feedback.append((f"✅ Found {len(found_skills)}/{len(job_skills)} required skills", "match-high"))
        else:
            feedback.append(("❌ No required skills found", "match-low"))
        
        # 3. Experience
        experience_years = self.calculate_experience(resume_text)
        exp_pattern = r'(\d+)\s*(?:years?|yrs?)\s*(?:experience|exp)'
        job_exp_matches = re.findall(exp_pattern, job_description.lower())
        required_exp = int(job_exp_matches[0]) if job_exp_matches else 0
        
        experience_score = 0
        if required_exp > 0:
            if experience_years >= required_exp:
                experience_score = criteria_weights['experience']
                feedback.append((f"✅ Meets experience requirement ({experience_years} years)", "match-high"))
            else:
                experience_score = (experience_years / required_exp) * criteria_weights['experience']
                feedback.append((f"⚠️ Below required experience ({experience_years}/{required_exp} years)", "match-medium"))
        else:
            experience_score = min(experience_years * 5, criteria_weights['experience'])
            if experience_years > 0:
                feedback.append((f"✅ Has {experience_years} years of experience", "match-high"))
        
        scores['experience'] = experience_score
        
        # 4. Education
        education_score = 0
        education_found = []
        for edu_term in self.common_keywords['education']:
            if edu_term in resume_text.lower():
                education_found.append(edu_term)
                education_score = criteria_weights['education']
        
        if education_found:
            feedback.append((f"✅ Education credentials found: {', '.join(education_found)}", "match-high"))
        else:
            feedback.append(("❌ No formal education credentials found", "match-low"))
        
        scores['education'] = education_score
        
        # 5. Contact Information
        contact_score = 0
        email = self.extract_email(resume_text)
        phone = self.extract_phone(resume_text)
        
        if email != "Not found":
            contact_score += criteria_weights['contact_info'] * 0.6
        if phone != "Not found":
            contact_score += criteria_weights['contact_info'] * 0.4
        
        scores['contact_info'] = contact_score
        
        if email != "Not found" and phone != "Not found":
            feedback.append(("✅ Complete contact information", "match-high"))
        elif email != "Not found" or phone != "Not found":
            feedback.append(("⚠️ Partial contact information", "match-medium"))
        else:
            feedback.append(("❌ No contact information found", "match-low"))
        
        # 6. Formatting
        formatting_score = criteria_weights['formatting']
        if any(char in resume_text for char in ['•', '○', '▪', '■', '- ', '* ']):
            formatting_score = criteria_weights['formatting']
            feedback.append(("✅ Good formatting with bullet points", "match-high"))
        else:
            formatting_score = criteria_weights['formatting'] * 0.5
            feedback.append(("⚠️ Consider using bullet points for better readability", "match-medium"))
        
        scores['formatting'] = formatting_score
        
        # Calculate total score
        total_score = sum(scores.values())
        
        # Determine ATS status
        if total_score >= 70:
            status = "✅ PASS"
            status_color = "green"
            recommendation = "Strong candidate - proceed to interview"
        elif total_score >= 50:
            status = "⚠️ REVIEW"
            status_color = "orange"
            recommendation = "Moderate match - review manually"
        else:
            status = "❌ REJECT"
            status_color = "red"
            recommendation = "Low match - consider other candidates"
        
        return {
            'total_score': total_score,
            'scores': scores,
            'feedback': feedback,
            'status': status,
            'status_color': status_color,
            'recommendation': recommendation,
            'details': {
                'email': email,
                'phone': phone,
                'experience_years': experience_years,
                'skills_found': found_skills,
                'keyword_matches': keyword_result['matched_words'][:10],
                'keyword_match_percentage': keyword_result['match_percentage']
            }
        }

def main():
    # App header
    st.markdown("<h1 class='main-header'>📄 ATS Resume Scanner & Analyzer</h1>", unsafe_allow_html=True)
    st.markdown("### Upload resumes and job description to get ATS compatibility scores")
    
    # Initialize scanner
    scanner = ATSResumeScanner()
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        st.markdown("#### Scoring Weights")
        keyword_weight = st.slider("Keyword Match Weight", 0, 40, 30)
        skills_weight = st.slider("Skills Match Weight", 0, 40, 25)
        experience_weight = st.slider("Experience Weight", 0, 30, 20)
        education_weight = st.slider("Education Weight", 0, 20, 15)
        
        criteria_weights = {
            'keyword_match': keyword_weight,
            'skills_match': skills_weight,
            'experience': experience_weight,
            'education': education_weight,
            'contact_info': 5,
            'formatting': 5
        }
        
        st.markdown("---")
        st.markdown("#### 📊 ATS Thresholds")
        pass_threshold = st.slider("Pass Threshold", 50, 90, 70)
        review_threshold = st.slider("Review Threshold", 30, 70, 50)
        
        st.markdown("---")
        st.markdown("#### ℹ️ About")
        st.info("""
        This ATS scanner evaluates resumes based on:
        - Keyword matching
        - Skills relevance
        - Experience level
        - Education credentials
        - Contact information
        - Formatting quality
        """)
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📝 Job Description")
        job_description = st.text_area(
            "Paste the job description here",
            height=300,
            placeholder="Enter the complete job description including requirements, skills, and qualifications..."
        )
    
    with col2:
        st.markdown("### 📎 Upload Resume(s)")
        uploaded_files = st.file_uploader(
            "Choose PDF or DOCX files",
            type=['pdf', 'docx'],
            accept_multiple_files=True,
            help="Upload one or multiple resumes"
        )
    
    # Process button
    if st.button("🚀 Analyze Resumes", type="primary", use_container_width=True):
        if not job_description:
            st.error("Please enter a job description")
            return
        
        if not uploaded_files:
            st.error("Please upload at least one resume")
            return
        
        # Process each resume
        results = []
        progress_bar = st.progress(0)
        
        for i, uploaded_file in enumerate(uploaded_files):
            progress = (i + 1) / len(uploaded_files)
            progress_bar.progress(progress)
            
            # Extract text based on file type
            if uploaded_file.name.lower().endswith('.pdf'):
                resume_text = scanner.extract_text_from_pdf(uploaded_file)
            else:
                resume_text = scanner.extract_text_from_docx(uploaded_file)
            
            if not resume_text.strip():
                st.warning(f"Could not extract text from {uploaded_file.name}")
                continue
            
            # Score resume
            result = scanner.score_resume(resume_text, job_description, criteria_weights)
            result['filename'] = uploaded_file.name
            results.append(result)
        
        progress_bar.empty()
        
        if not results:
            st.error("No valid resumes could be processed")
            return
        
        # Display results
        st.markdown("---")
        st.markdown(f"## 📊 Analysis Results ({len(results)} resumes analyzed)")
        
        # Create metrics
        col1, col2, col3 = st.columns(3)
        
        avg_score = sum([r['total_score'] for r in results]) / len(results)
        passed = sum([1 for r in results if r['total_score'] >= pass_threshold])
        
        with col1:
            st.metric("Average Score", f"{avg_score:.1f}/100")
        with col2:
            st.metric("Passed ATS", f"{passed}/{len(results)}")
        with col3:
            st.metric("Rejected", f"{len(results) - passed}/{len(results)}")
        
        # Sort results by score
        results.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Display each resume result
        for idx, result in enumerate(results, 1):
            with st.expander(f"{idx}. {result['filename']} - Score: {result['total_score']:.1f}/100 - Status: {result['status']}", expanded=idx==1):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # Score card
                    st.markdown(f"""
                    <div class="score-card">
                        <h3>ATS Score</h3>
                        <h1>{result['total_score']:.1f}/100</h1>
                        <h3 style="color: {result['status_color']}">{result['status']}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Score breakdown
                    st.markdown("#### 📈 Score Breakdown")
                    scores_df = pd.DataFrame({
                        'Criteria': list(result['scores'].keys()),
                        'Score': list(result['scores'].values())
                    })
                    st.dataframe(scores_df, use_container_width=True)
                    
                    # Quick details
                    st.markdown("#### 📋 Quick Details")
                    st.write(f"**Email:** {result['details']['email']}")
                    st.write(f"**Phone:** {result['details']['phone']}")
                    st.write(f"**Experience:** {result['details']['experience_years']} years")
                    st.write(f"**Keyword Match:** {result['details']['keyword_match_percentage']:.1f}%")
                
                with col2:
                    # Feedback
                    st.markdown("#### 💡 Feedback & Suggestions")
                    for feedback, color_class in result['feedback']:
                        st.markdown(f'<p class="{color_class}">{feedback}</p>', unsafe_allow_html=True)
                    
                    # Skills found
                    if result['details']['skills_found']:
                        st.markdown("#### ✅ Skills Found")
                        skills_cols = st.columns(3)
                        for i, skill in enumerate(result['details']['skills_found'][:9]):
                            with skills_cols[i % 3]:
                                st.success(skill)
                    
                    # Keyword matches
                    if result['details']['keyword_matches']:
                        st.markdown("#### 🔑 Top Keyword Matches")
                        st.write(", ".join(result['details']['keyword_matches']))
                    
                    # Recommendation
                    st.markdown("#### 🎯 Recommendation")
                    st.info(result['recommendation'])
        
        # Visualizations
        st.markdown("---")
        st.markdown("## 📊 Comparative Analysis")
        
        if len(results) > 1:
            col1, col2 = st.columns(2)
            
            with col1:
                # Bar chart of scores
                fig, ax = plt.subplots(figsize=(10, 6))
                filenames = [r['filename'][:20] + '...' if len(r['filename']) > 20 else r['filename'] 
                            for r in results]
                scores = [r['total_score'] for r in results]
                
                bars = ax.barh(filenames, scores, color=['#4F46E5' if s >= pass_threshold else 
                                                         '#F59E0B' if s >= review_threshold else 
                                                         '#EF4444' for s in scores])
                ax.set_xlabel('ATS Score')
                ax.set_title('Resume Scores Comparison')
                ax.set_xlim([0, 100])
                
                # Add score labels
                for bar in bars:
                    width = bar.get_width()
                    ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                           f'{width:.1f}', va='center')
                
                st.pyplot(fig)
            
            with col2:
                # Radar chart for top resume
                if results:
                    top_result = results[0]
                    categories = list(top_result['scores'].keys())
                    values = list(top_result['scores'].values())
                    
                    # Normalize values for radar chart
                    normalized_values = [v / criteria_weights.get(cat, 1) * 100 
                                        for v, cat in zip(values, categories)]
                    
                    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
                    
                    angles = [n / float(len(categories)) * 2 * 3.14159 for n in range(len(categories))]
                    angles += angles[:1]
                    normalized_values += normalized_values[:1]
                    
                    ax.plot(angles, normalized_values, 'o-', linewidth=2, color='#4F46E5')
                    ax.fill(angles, normalized_values, alpha=0.25, color='#4F46E5')
                    ax.set_xticks(angles[:-1])
                    ax.set_xticklabels(categories)
                    ax.set_ylim([0, 100])
                    ax.set_title(f"Score Breakdown - {top_result['filename'][:15]}...", size=14)
                    
                    st.pyplot(fig)
            
            # Download results
            st.markdown("---")
            st.markdown("## 📥 Download Results")
            
            # Create CSV
            csv_data = []
            for result in results:
                row = {
                    'Filename': result['filename'],
                    'ATS_Score': result['total_score'],
                    'Status': result['status'],
                    'Email': result['details']['email'],
                    'Phone': result['details']['phone'],
                    'Experience_Years': result['details']['experience_years'],
                    'Keyword_Match_Percentage': result['details']['keyword_match_percentage'],
                    'Skills_Found': ', '.join(result['details']['skills_found'])
                }
                csv_data.append(row)
            
            df = pd.DataFrame(csv_data)
            csv = df.to_csv(index=False)
            
            # Create download buttons
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📄 Download Results as CSV",
                    data=csv,
                    file_name=f"ats_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Create a summary report
                report = f"ATS Resume Analysis Report\n"
                report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                report += f"Total Resumes Analyzed: {len(results)}\n"
                report += f"Average Score: {avg_score:.1f}\n"
                report += f"Passed: {passed}, Failed: {len(results)-passed}\n\n"
                
                for result in results:
                    report += f"\n{'='*50}\n"
                    report += f"File: {result['filename']}\n"
                    report += f"Score: {result['total_score']:.1f}/100\n"
                    report += f"Status: {result['status']}\n"
                    report += f"Recommendation: {result['recommendation']}\n"
                
                st.download_button(
                    label="📋 Download Summary Report",
                    data=report,
                    file_name=f"ats_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        
        else:
            # Single resume analysis
            result = results[0]
            
            # Create gauge chart for single score
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.barh(['ATS Score'], [result['total_score']], color='#4F46E5')
            ax.set_xlim([0, 100])
            ax.set_xlabel('Score')
            ax.axvline(x=pass_threshold, color='green', linestyle='--', alpha=0.5, label='Pass Threshold')
            ax.axvline(x=review_threshold, color='orange', linestyle='--', alpha=0.5, label='Review Threshold')
            ax.legend()
            st.pyplot(fig)

if __name__ == "__main__":
    main()
