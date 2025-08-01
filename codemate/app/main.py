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
from codemate.core.github_agent import GitHubAgent

# --- Initialize session state keys ---
if "github_token" not in st.session_state:
    st.session_state["github_token"] = None
if "github_user_login" not in st.session_state:
    st.session_state["github_user_login"] = None
if "shared_github_token" not in st.session_state:
    st.session_state["shared_github_token"] = None

st.set_page_config(page_title="CodeMate AI Assistant", page_icon="🤖")

st.title("🤖 CodeMate AI Assistant")

# GitHub Authentication Section
st.header("GitHub Integration")

# Check if GitHub token is already in session state
if "github_token" not in st.session_state:
    st.session_state["github_token"] = None

# --- Shared GitHub Token Section ---
st.sidebar.header("🔑 Shared GitHub Token (for all users)")
if "shared_github_token" not in st.session_state:
    st.session_state["shared_github_token"] = None

shared_token_input = st.sidebar.text_input(
    "Enter a shared GitHub Personal Access Token (PAT):",
    type="password",
    value=st.session_state["shared_github_token"] or ""
)
if st.sidebar.button("Set Shared Token"):
    if shared_token_input:
        st.session_state["shared_github_token"] = shared_token_input
        st.sidebar.success("Shared GitHub token set!")
    else:
        st.sidebar.warning("Please enter a token to set.")

# --- Use shared token as fallback ---
if "github_token" not in st.session_state or st.session_state["github_token"] is None:
    if st.session_state.get("shared_github_token"):
        st.session_state["github_token"] = st.session_state["shared_github_token"]
        st.session_state["github_user_login"] = "Shared User"

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

# --- Feature Selection ---
feature = st.selectbox(
    "What would you like to do?",
    [
        "Create Project",
        "Create GitHub Issue",
        "List Pull Requests"
    ],
    key="selected_feature"
)

if st.session_state["github_token"]:
    st.write("Welcome to CodeMate! Your GitHub account is connected.")
    st.write("Now you can start using CodeMate's features:")

    if feature == "Create Project":
        st.subheader("🤖 Project Builder for Beginners")
        project_description = st.text_area(
        "Describe the project you want to build (e.g., 'A simple Python web server using Flask that displays 'Hello World' on the homepage.'):",
        height=150
    )

    if st.button("Generate Project Structure and Code"):
        if project_description:
                with st.status("Generating your project...", expanded=True) as status:
                    status.update(label="Generating project files with AI...", state="running")
            # Call the project generation function
                generation_result = generate_project(
                project_description=project_description,
                github_user_login=st.session_state["github_user_login"],
                github_token=st.session_state["github_token"]
            )
                if generation_result["status"] == "success":
                        status.update(label="Pushing files to GitHub...", state="running")
                        status.update(label="Project successfully pushed to GitHub!", state="complete")
                        st.success(f"Project generation successful! {generation_result['message']}")
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
                            st.markdown(f"**GitHub Repository:** [ {generation_result['repo_url']} ]({generation_result['repo_url']})")
                else:
                        status.update(label="Project generation failed.", state="error")
                        st.error(f"Project generation failed: {generation_result['message']}")
        else:
            st.warning("Please describe the project you want to build.")

    elif feature == "Create GitHub Issue":
        st.subheader("Create a GitHub Issue")
        agent = GitHubAgent(st.session_state["github_token"])
        repos = agent.list_repos()
        repo_dict = {repo.full_name: repo for repo in repos}
        repo_names = list(repo_dict.keys())
        selected_repo_full_name = st.selectbox("Select a repository", repo_names)
        issue_title = st.text_input("Issue Title")
        issue_body = st.text_area("Issue Description")
        if st.button("Create Issue"):
            try:
                issue = agent.create_issue(selected_repo_full_name, issue_title, issue_body)
                st.success(f"Issue created: {issue.html_url}")
            except Exception as e:
                st.error(f"Failed to create issue: {e}")

    elif feature == "List Pull Requests":
        st.subheader("List Pull Requests")
        agent = GitHubAgent(st.session_state["github_token"])
        repos = agent.list_repos()
        repo_dict = {repo.full_name: repo for repo in repos}
        repo_names = list(repo_dict.keys())
        selected_repo_full_name = st.selectbox("Select a repository", repo_names)
        try:
            prs = agent.list_pull_requests(selected_repo_full_name)
            for pr in prs:
                st.markdown(f"- [{pr.title}]({pr.html_url}) by {pr.user.login}")
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---") # Separator

    st.markdown("- **Automatic Debugging (Python)**: *Coming Soon*")
    st.markdown("- **Generate Tests (Unit/Integration)**: *Coming Soon*")
    st.markdown("- **Review GitHub Pull Requests**: *Coming Soon*")
    st.markdown("- **Natural Language Codebase Navigation**: *Coming Soon*")
    st.markdown("- **Team Collaboration**: *Coming Soon*")
else:
    st.info("Please connect your GitHub account to unlock CodeMate's features.") 