import streamlit as st
import json
import os
from utils.llm import parse_resume_text, extract_text_from_pdf

st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")

if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
    st.warning("Please login from the Home page.")
    st.stop()

st.title("User Profile")

# Initialize session state for resume data
if "resume_data" not in st.session_state:
    st.session_state["resume_data"] = None

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Upload Base Resume (PDF)")
    uploaded_file = st.file_uploader("Upload your existing resume to parse into JSON", type=["pdf"])
    if st.button("Parse Resume"):
        if uploaded_file is not None:
            with st.spinner("Extracting text and parsing with LLM..."):
                try:
                    # Save temporarily
                    temp_path = os.path.join("data", "temp_resume.pdf")
                    os.makedirs("data", exist_ok=True)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    text = extract_text_from_pdf(temp_path)
                    parsed_json = parse_resume_text(text)
                    st.session_state["resume_data"] = parsed_json
                    st.success("Successfully parsed resume!")
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
            st.success("Loaded JSON data successfully!")
        else:
            st.error("Please upload a JSON file first.")

st.divider()

if st.session_state["resume_data"]:
    st.subheader("Current Resume Data")
    
    # We can edit JSON directly using st.data_editor or just a text area for simplicity
    json_str = json.dumps(st.session_state["resume_data"], indent=4)
    edited_json = st.text_area("Edit JSON", value=json_str, height=400)
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("Save Changes"):
            try:
                new_data = json.loads(edited_json)
                st.session_state["resume_data"] = new_data
                st.success("Changes saved to session!")
            except json.JSONDecodeError:
                st.error("Invalid JSON format. Please check your syntax.")
                
    with col4:
        st.download_button(
            label="Download JSON Data",
            data=json_str,
            file_name="resume_data.json",
            mime="application/json"
        )
