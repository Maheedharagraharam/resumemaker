import streamlit as st
import json
import os
from utils.llm import parse_resume_text, extract_text_from_pdf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")

if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
    st.warning("Please login from the Home page.")
    st.stop()

st.title("User Profile")

# Initialize session state for resume data and editor versioning
if "resume_data" not in st.session_state:
    st.session_state["resume_data"] = None
if "json_version" not in st.session_state:
    st.session_state["json_version"] = 0

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Upload Base Resume (PDF)")
    uploaded_file = st.file_uploader("Upload your existing resume to parse into JSON", type=["pdf"])
    if st.button("Parse Resume", type="primary"):
        if uploaded_file is not None:
            with st.spinner("Extracting text and parsing with LLM..."):
                try:
                    # Save temporarily
                    temp_path = os.path.join(DATA_DIR, "temp_resume.pdf")
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    text = extract_text_from_pdf(temp_path)
                    parsed_json = parse_resume_text(text)
                    st.session_state["resume_data"] = parsed_json
                    st.session_state["json_version"] += 1
                    st.toast("Successfully parsed resume!", icon="✅")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error parsing resume: {str(e)}")
        else:
            st.error("Please upload a PDF file first.")

with col2:
    st.subheader("2. Upload Existing JSON")
    st.markdown("If you already have your parsed JSON, upload it here to restore state (e.g., after a server restart).")
    uploaded_json = st.file_uploader("Upload resume_data.json", type=["json"])
    if st.button("Load JSON"):
        if uploaded_json is not None:
            data = json.load(uploaded_json)
            st.session_state["resume_data"] = data
            st.session_state["json_version"] += 1
            st.toast("Loaded JSON data successfully!", icon="✅")
            st.rerun()
        else:
            st.error("Please upload a JSON file first.")

st.divider()

if st.session_state["resume_data"]:
    data = st.session_state["resume_data"]
    
    st.subheader("📋 Candidate Summary & Contact Details")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**Name:** {data.get('name') or '*(Not specified)*'}")
        st.markdown(f"**Role:** {data.get('job_title') or '*(Not specified)*'}")
    with c2:
        st.markdown(f"**Email:** {data.get('email') or '*(Not specified)*'}")
        st.markdown(f"**Phone:** {data.get('phone') or '*(Not specified)*'}")
    with c3:
        linkedin_url = data.get('linkedin', '')
        if linkedin_url:
            st.markdown(f"**LinkedIn:** [🔗 {linkedin_url}]({linkedin_url})")
        else:
            st.markdown("**LinkedIn:** ⚠️ *Not found in PDF*")
            
        github_url = data.get('github', '')
        if github_url:
            st.markdown(f"**GitHub:** [🐙 {github_url}]({github_url})")
        else:
            st.markdown("**GitHub:** *(None)*")

    st.markdown("---")
    st.subheader("Current Resume JSON")
    
    json_str = json.dumps(data, indent=4)
    # Dynamic key ensures text area re-renders whenever a new file is parsed or loaded
    editor_key = f"json_editor_{st.session_state['json_version']}"
    edited_json = st.text_area("Edit JSON", value=json_str, height=400, key=editor_key)
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("Save Changes"):
            try:
                new_data = json.loads(edited_json)
                st.session_state["resume_data"] = new_data
                st.session_state["json_version"] += 1
                st.success("Changes saved to session!")
                st.rerun()
            except json.JSONDecodeError:
                st.error("Invalid JSON format. Please check your syntax.")
                
    with col4:
        st.download_button(
            label="Download JSON Data",
            data=json_str,
            file_name="resume_data.json",
            mime="application/json"
        )
