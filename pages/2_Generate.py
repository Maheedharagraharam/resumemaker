import streamlit as st
import json
import os
from utils.llm import tailor_resume_to_jd
from utils.latex import generate_pdf

st.set_page_config(page_title="Generate Resume", page_icon="📝", layout="wide")

if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
    st.warning("Please login from the Home page.")
    st.stop()

st.title("Generate Tailored Resume")

if "resume_data" not in st.session_state or not st.session_state["resume_data"]:
    st.warning("Please go to the Profile page and parse/upload your resume first.")
    st.stop()

st.write("Paste the Job Description below to tailor your resume.")

job_description = st.text_area("Job Description", height=300)

if st.button("Generate Resume"):
    if not job_description.strip():
        st.error("Please enter a job description.")
    else:
        with st.spinner("Tailoring resume with LLM..."):
            try:
                # 1. Tailor the resume using Groq
                tailored_json = tailor_resume_to_jd(st.session_state["resume_data"], job_description)
                
                # 2. Compile LaTeX
                st.info("Compiling LaTeX to PDF...")
                pdf_path = generate_pdf(tailored_json, output_dir="data")
                
                st.success("Resume generated successfully!")
                
                col1, col2 = st.columns(2)
                
                # Download PDF
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                
                with col1:
                    st.download_button(
                        label="📄 Download PDF Resume",
                        data=pdf_bytes,
                        file_name="Tailored_Resume.pdf",
                        mime="application/pdf"
                    )
                
                # Download JSON
                with col2:
                    st.download_button(
                        label="💾 Download Tailored JSON Data",
                        data=json.dumps(tailored_json, indent=4),
                        file_name="tailored_resume_data.json",
                        mime="application/json"
                    )
                    
                # Download TeX source
                tex_path = os.path.join("data", "generated_resume.tex")
                with open(tex_path, "r", encoding="utf-8") as f:
                    tex_bytes = f.read()
                    
                with col1:
                    st.download_button(
                        label="📄 Download LaTeX Source (.tex)",
                        data=tex_bytes,
                        file_name="resume_source.tex",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
