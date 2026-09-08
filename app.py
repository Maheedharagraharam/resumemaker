import streamlit as st

st.set_page_config(
    page_title="Resume Maker",
    page_icon="📄",
    layout="wide",
)

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] == "maheedhar" and st.session_state["password"] == "maheedhar123":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.title("Login to Resume Maker")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        return False
    
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.title("Login to Resume Maker")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        st.error("😕 User not known or password incorrect")
        return False
    
    else:
        # Password correct.
        return True

if check_password():
    st.title("Welcome to Resume Maker 📄")
    st.markdown(
        """
        Welcome to your tailored Resume Generator.
        
        ### Navigation
        - **Profile**: Upload your base resume, parse it into JSON, and edit your details. You can download the JSON so you never lose your data.
        - **Generate**: Paste a Job Description (JD) and let the LLM generate a targeted LaTeX resume and compile it to PDF.
        """
    )
