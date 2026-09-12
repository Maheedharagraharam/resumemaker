import streamlit as st
import json
import os
import base64
from utils.llm import tailor_resume_to_jd
from utils.latex import generate_pdf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(page_title="Generate Resume", page_icon="📄", layout="wide")

if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
    st.warning("Please login from the Home page.")
    st.stop()

st.title("🎯 Generate Tailored Resume")

if "resume_data" not in st.session_state or not st.session_state["resume_data"]:
    st.warning("⚠️ Please go to the **Profile** page and upload/parse your base resume first.")
    st.stop()

base_data = st.session_state["resume_data"]

st.markdown(
    """
    Paste the target **Job Description (JD)** below. The AI will actively rewrite your **target job title**, 
    **professional summary**, prioritize and align **technical skills**, and reframe all **experience & project bullet points** 
    to match the role requirements.
    """
)

# Current base profile summary banner
with st.expander("👁️ View Current Base Profile Summary & Skills", expanded=False):
    st.markdown(f"**Target Title:** `{base_data.get('job_title', 'Software Engineer')}`")
    st.markdown(f"**Summary:** {base_data.get('summary', '')}")
    skills_obj = base_data.get('skills', {})
    if skills_obj:
        st.markdown("**Skills:**")
        for cat, items in skills_obj.items():
            if items:
                st.markdown(f"- **{cat.capitalize()}:** {', '.join(items)}")

job_description = st.text_area(
    "Job Description",
    value=st.session_state.get("last_tailored_jd", ""),
    height=240,
    placeholder="Paste the full job description or requirements here..."
)

col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    generate_clicked = st.button("🚀 Generate Tailored Resume", type="primary", use_container_width=True)

if generate_clicked:
    if not job_description.strip():
        st.error("Please paste a Job Description first.")
    else:
        with st.spinner("Analyzing JD and actively tailoring title, summary, skills & bullets with LLM..."):
            try:
                tailored_json = tailor_resume_to_jd(base_data, job_description)
                pdf_path = generate_pdf(tailored_json, output_dir=DATA_DIR)
                
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                    
                tex_path = os.path.join(DATA_DIR, "generated_resume.tex")
                tex_str = ""
                if os.path.exists(tex_path):
                    with open(tex_path, "r", encoding="utf-8") as f:
                        tex_str = f.read()
                        
                st.session_state["tailored_resume_data"] = tailored_json
                st.session_state["tailored_pdf_bytes"] = pdf_bytes
                st.session_state["tailored_tex_str"] = tex_str
                st.session_state["last_tailored_jd"] = job_description
                
                st.success("Resume tailored successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"An error occurred during tailoring or PDF generation: {str(e)}")

# Display tailored results if available in session state
if "tailored_resume_data" in st.session_state and st.session_state["tailored_resume_data"]:
    tailored_data = st.session_state["tailored_resume_data"]
    pdf_bytes = st.session_state.get("tailored_pdf_bytes")
    tex_str = st.session_state.get("tailored_tex_str", "")
    
    st.divider()
    st.subheader("🎉 Tailored Resume Output")
    
    # Download action bar
    dcol1, dcol2, dcol3, dcol4 = st.columns([1.2, 1.2, 1.2, 1.4])
    
    if pdf_bytes:
        with dcol1:
            st.download_button(
                label="📄 Download PDF",
                data=pdf_bytes,
                file_name="Tailored_Resume.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
    with dcol2:
        st.download_button(
            label="💾 Download JSON",
            data=json.dumps(tailored_data, indent=4),
            file_name="tailored_resume.json",
            mime="application/json",
            use_container_width=True
        )
        
    if tex_str:
        with dcol3:
            st.download_button(
                label="📝 Download LaTeX (.tex)",
                data=tex_str,
                file_name="resume_source.tex",
                mime="text/plain",
                use_container_width=True
            )
            
    with dcol4:
        if st.button("⭐ Set as Active Profile", help="Promote this tailored resume to your main profile", use_container_width=True):
            st.session_state["resume_data"] = tailored_data
            st.success("Updated active profile with tailored data!")
            st.rerun()

    # Comparison and preview tabs
    tab_diff, tab_exp, tab_pdf, tab_json = st.tabs([
        "⚖️ Side-by-Side Comparison",
        "💼 Experience & Projects Bullets",
        "📄 PDF Preview",
        "🔍 Raw JSON"
    ])
    
    with tab_diff:
        st.markdown("### Target Role Alignment")
        rcol1, rcol2 = st.columns(2)
        with rcol1:
            st.markdown(f"**Original Role:** `{base_data.get('job_title', 'Software Engineer')}`")
        with rcol2:
            st.markdown(f"**Tailored Role:** `{tailored_data.get('job_title', 'Software Engineer')}`")
            
        st.markdown("### Professional Summary Comparison")
        scol1, scol2 = st.columns(2)
        with scol1:
            st.caption("ORIGINAL BASE SUMMARY")
            st.info(base_data.get("summary", "No summary provided."))
        with scol2:
            st.caption("TAILORED ATS SUMMARY")
            st.success(tailored_data.get("summary", "No summary generated."))

        st.markdown("### Technical Skills Comparison")
        sk_base = base_data.get("skills", {})
        sk_tail = tailored_data.get("skills", {})
        all_categories = sorted(list(set(list(sk_base.keys()) + list(sk_tail.keys()))))
        
        for cat in all_categories:
            b_list = sk_base.get(cat, [])
            t_list = sk_tail.get(cat, [])
            if b_list or t_list:
                with st.expander(f"Skills: {cat.capitalize()}", expanded=True):
                    kcol1, kcol2 = st.columns(2)
                    with kcol1:
                        st.caption("Original")
                        st.write(", ".join(b_list) if b_list else "None")
                    with kcol2:
                        st.caption("Tailored (JD Prioritized)")
                        st.write(", ".join(t_list) if t_list else "None")

    with tab_exp:
        st.markdown("### Work Experience Bullets Comparison")
        base_exps = base_data.get("experience", [])
        tail_exps = tailored_data.get("experience", [])
        
        for idx in range(max(len(base_exps), len(tail_exps))):
            b_exp = base_exps[idx] if idx < len(base_exps) else {}
            t_exp = tail_exps[idx] if idx < len(tail_exps) else {}
            
            company = t_exp.get("company") or b_exp.get("company") or f"Role {idx+1}"
            title = t_exp.get("title") or b_exp.get("title") or ""
            st.markdown(f"#### {company} — {title}")
            
            ecol1, ecol2 = st.columns(2)
            with ecol1:
                st.caption("Original Bullets")
                for b in b_exp.get("bullets", []):
                    st.markdown(f"- {b}")
            with ecol2:
                st.caption("Tailored Bullets (ATS Action Verbs & Metrics)")
                for b in t_exp.get("bullets", []):
                    st.markdown(f"- {b}")
            st.divider()

        st.markdown("### Projects Bullets Comparison")
        base_projs = base_data.get("projects", [])
        tail_projs = tailored_data.get("projects", [])
        for idx in range(max(len(base_projs), len(tail_projs))):
            b_proj = base_projs[idx] if idx < len(base_projs) else {}
            t_proj = tail_projs[idx] if idx < len(tail_projs) else {}
            
            pname = t_proj.get("name") or b_proj.get("name") or f"Project {idx+1}"
            st.markdown(f"#### {pname}")
            
            pcol1, pcol2 = st.columns(2)
            with pcol1:
                st.caption("Original Bullets")
                for b in b_proj.get("bullets", []):
                    st.markdown(f"- {b}")
            with pcol2:
                st.caption("Tailored Bullets")
                for b in t_proj.get("bullets", []):
                    st.markdown(f"- {b}")
            st.divider()

    with tab_pdf:
        if pdf_bytes:
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="900px" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            st.info("No PDF data available.")

    with tab_json:
        st.json(tailored_data)
