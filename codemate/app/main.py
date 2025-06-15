import streamlit as st
import sys
import os

# Add the project root to the Python path dynamically
# This helps resolve imports like 'from codemate.core.project_generator import generate_project'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = os.path.join(current_dir, '..', '..') # Go up two levels from app/main.py to codemate/
sys.path.insert(0, project_root_dir)

from github import Github
from codemate.core.project_generator import generate_project

st.set_page_config(page_title="CodeMate AI Assistant", page_icon="🤖")

st.title("🤖 CodeMate AI Assistant")

# GitHub Authentication Section
st.header("GitHub Integration")

# Check if GitHub token is already in session state
if "github_token" not in st.session_state:
    st.session_state["github_token"] = None

if st.session_state["github_token"] is None:
    with st.expander("Connect your GitHub Account"):
        github_pat = st.text_input("Enter your GitHub Personal Access Token (PAT):", type="password")
        st.info("You can generate a PAT from your GitHub settings: Developer settings -> Personal access tokens -> Tokens (classic)")

        if st.button("Connect to GitHub"):
            if github_pat:
                try:
                    g = Github(github_pat)
                    user = g.get_user()
                    st.session_state["github_token"] = github_pat
                    st.session_state["github_user_login"] = user.login
                    st.success(f"Successfully connected to GitHub as {user.login}!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error connecting to GitHub: {e}. Please check your PAT.")
            else:
                st.warning("Please enter your GitHub Personal Access Token.")
else:
    st.success(f"Already connected to GitHub as {st.session_state['github_user_login']}!")
    if st.button("Disconnect GitHub"):
        st.session_state["github_token"] = None
        st.session_state["github_user_login"] = None
        st.experimental_rerun()

# Main application features (placeholders for now)
st.header("CodeMate Features")

if st.session_state["github_token"]:
    st.write("Welcome to CodeMate! Your GitHub account is connected.")
    st.write("Now you can start using CodeMate's features:")

    st.subheader("🤖 Project Builder for Beginners")
    project_description = st.text_area(
        "Describe the project you want to build (e.g., 'A simple Python web server using Flask that displays 'Hello World' on the homepage.'):",
        height=150
    )

    if st.button("Generate Project Structure and Code"):
        if project_description:
            st.info("Generating project... This might take a moment.")
            
            # Call the project generation function
            generation_result = generate_project(
                project_description=project_description,
                github_user_login=st.session_state["github_user_login"],
                github_token=st.session_state["github_token"]
            )

            if generation_result["status"] == "success":
                st.success(f"Project generation successful! {generation_result["message"]}")
                st.write("Generated Files:")
                for file_path in generation_result["generated_files"]:
                    try:
                        with open(file_path, "r") as f:
                            file_content = f.read()
                        
                        file_name = os.path.basename(file_path)
                        relative_path = os.path.relpath(file_path, os.path.join(os.path.dirname(os.path.dirname(file_path)), os.path.basename(os.path.dirname(os.path.dirname(file_path)))))
                        
                        with st.expander(f"`{relative_path}`"):
                            st.code(file_content, language="python" if file_name.endswith(".py") else "markdown" if file_name.endswith(".md") else "yaml" if file_name.endswith(".yml") else "text")
                    except Exception as e:
                        st.warning(f"Could not read file {file_path}: {e}")
                
                if "repo_url" in generation_result:
                    st.markdown(f"**GitHub Repository:** [ {generation_result["repo_url"]} ]({generation_result["repo_url"]})")
            else:
                st.error(f"Project generation failed: {generation_result["message"]}")

        else:
            st.warning("Please describe the project you want to build.")

    st.markdown("---") # Separator

    st.markdown("- **Automatic Debugging (Python)**: *Coming Soon*")
    st.markdown("- **Generate Tests (Unit/Integration)**: *Coming Soon*")
    st.markdown("- **Review GitHub Pull Requests**: *Coming Soon*")
    st.markdown("- **Natural Language Codebase Navigation**: *Coming Soon*")
    st.markdown("- **Team Collaboration**: *Coming Soon*")
else:
    st.info("Please connect your GitHub account to unlock CodeMate's features.") 