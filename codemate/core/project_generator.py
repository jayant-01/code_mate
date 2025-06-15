import os
from openai import OpenAI
from dotenv import load_dotenv
from github import Github
from github.GithubException import GithubException
import time # Import the time module

# Load environment variables from .env file
load_dotenv()

NOVITA_AI_API_KEY = os.getenv("NOVITA_AI_API_KEY")

client = OpenAI(
    base_url="https://api.novita.ai/v3/openai",
    api_key=NOVITA_AI_API_KEY,
)

def generate_project(project_description: str, github_user_login: str, github_token: str):
    """
    Generates a project structure, code, and basic GitHub workflows based on the project description.
    Creates a GitHub repository and pushes the generated files.
    """
    print(f"DEBUG: Generating project for '{github_user_login}' with description: {project_description}")

    if not NOVITA_AI_API_KEY:
        return {
            "status": "error",
            "message": "Novita AI API Key not found. Please set NOVITA_AI_API_KEY in your .env file.",
            "generated_files": []
        }

    # Generate a unique directory name for the project
    project_name_slug = "_".join(project_description.lower().split()[:5]).replace("\'", "")
    project_directory = f"generated_projects/{github_user_login}/{project_name_slug}"

    generated_files_map = {}
    generated_files_list = []

    try:
        # Create the main project directory locally
        os.makedirs(project_directory, exist_ok=True)

        # Prepare the prompt for the LLM
        system_prompt = """You are an expert software engineer assistant. Your task is to generate project files based on a user's description. You must provide the content for the following files, delimited by specific markers:

<README.md>
# [Project Title]
A brief, engaging description of the project.

## Table of Contents
- [Description](#description)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Description
[A more detailed explanation of what the project does, its features, and its purpose.]

## Installation
[Step-by-step instructions on how to set up the project locally. Include any prerequisites and commands.]
\`\`\`bash
# Example
git clone <repository_url>
cd <repository_name>
pip install -r requirements.txt
\`\`\`

## Usage
[Clear instructions and examples on how to use the project. Include code snippets if applicable.]
\`\`\`python
# Example
python src/app.py
\`\`\`

## Contributing
[Guidelines for how others can contribute to the project (e.g., bug reports, feature requests, pull requests).]

## License
[Information about the project's license.]
</README.md>

<requirements.txt>
[Content for requirements.txt]
</requirements.txt>

<src/app.py>
[Content for src/app.py]
</src/app.py>

<.github/workflows/main.yml>
[Content for .github/workflows/main.yml]
</.github/workflows/main.yml>

Ensure the content for each file is complete and valid. For Python projects, always include `streamlit` and `PyGithub` in `requirements.txt` if you are generating a Streamlit app or interacting with GitHub. Make sure the generated `app.py` is a runnable Python script and `main.yml` is a valid GitHub Actions workflow.
"""

        user_prompt = f"""Generate a project with the following description: {project_description}

Make sure to provide all the files specified in the system prompt.
"""

        chat_completion_res = client.chat.completions.create(
            model="meta-llama/llama-3.1-8b-instruct",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
            stream=False,
            max_tokens=2048,
        )

        llm_output = chat_completion_res.choices[0].message.content
        print(f"DEBUG: LLM Raw Output:\n{llm_output}")

        file_markers = {
            "README.md": {"start": "<README.md>", "end": "</README.md>"},
            "requirements.txt": {"start": "<requirements.txt>", "end": "</requirements.txt>"},
            "src/app.py": {"start": "<src/app.py>", "end": "</src/app.py>"},
            ".github/workflows/main.yml": {"start": "<.github/workflows/main.yml>", "end": "</.github/workflows/main.yml>"},
        }

        for file_path_key, markers in file_markers.items():
            start_marker = markers["start"]
            end_marker = markers["end"]

            start_index = llm_output.find(start_marker)
            end_index = llm_output.find(end_marker)

            if start_index != -1 and end_index != -1:
                content = llm_output[start_index + len(start_marker):end_index].strip()
                generated_files_map[file_path_key] = content
                
                full_file_path = os.path.join(project_directory, file_path_key)
                os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
                with open(full_file_path, "w") as f:
                    f.write(content)
                generated_files_list.append(full_file_path)
                print(f"DEBUG: Wrote local file: {full_file_path}")
            else:
                print(f"WARNING: Could not find markers for {file_path_key} in LLM output.")

        if not generated_files_map:
            raise ValueError("No files were generated from the LLM output. Check LLM response format.")

        # --- GitHub Operations (only if local file generation was successful) ---
        repo_url = None
        if github_token:
            try:
                g = Github(github_token)
                user = g.get_user()

                repo_name = f"codemate-{project_name_slug}"
                repo = None
                try:
                    repo = user.get_repo(repo_name)
                    print(f"DEBUG: Found existing GitHub repository: {repo.html_url}")
                except GithubException as e:
                    if e.status == 404: # Repository not found, so create it
                        print(f"DEBUG: Repository {repo_name} not found. Creating a new one.")
                        repo = user.create_repo(repo_name, private=False) # Create a public repository
                        print(f"DEBUG: Created new GitHub repository: {repo.html_url}")
                    else:
                        raise e # Re-raise if it's another GitHub API error

                # Now, repo is guaranteed to exist.
                # Update README content with repository URL before pushing
                if "README.md" in generated_files_map:
                    generated_files_map["README.md"] = generated_files_map["README.md"].replace("<repository_url>", repo.clone_url)

                commit_message = f"CodeMate: Project generation for '{project_description}'"

                # Check if the repository is truly empty (no commits)
                is_repo_truly_empty = (repo.get_commits().totalCount == 0)
            
                # Dictionary to hold files that will be pushed via standard Git tree/commit API after initial setup
                files_for_subsequent_push = generated_files_map.copy()

                if is_repo_truly_empty:
                    # For an empty repo, we MUST use create_file for the very first file to initialize the branch
                    print("DEBUG: Repository is truly empty. Performing initial commit via create_file.")
            
                    # Prioritize README.md for the initial commit
                    initial_file_path = "README.md"
                    initial_file_content = files_for_subsequent_push.get(initial_file_path)

                    if not initial_file_content and files_for_subsequent_push: # Fallback if README.md is not there or empty
                        # Get the first non-empty content file if README is not suitable
                        for path, content in files_for_subsequent_push.items():
                            if content.strip():
                                initial_file_path = path
                                initial_file_content = content
                                break
            
                    if initial_file_content:
                        try:
                            repo.create_file(
                                path=initial_file_path,
                                message=f"CodeMate: Initial project setup for {repo_name}",
                                content=initial_file_content,
                                branch="main" # This creates the main branch
                            )
                            print(f"DEBUG: Initial commit created via create_file for {initial_file_path}. Main branch initialized.")
                            # Remove the initially pushed file from the map for subsequent standard pushes
                            if initial_file_path in files_for_subsequent_push:
                                del files_for_subsequent_push[initial_file_path]
                        except Exception as create_file_e:
                            print(f"ERROR: Failed to create initial file using create_file ({initial_file_path}): {create_file_e}")
                            # If create_file fails, the repo will likely remain empty, and subsequent pushes will fail too.
                            # Re-raise to ensure the outer error handling catches it.
                            raise create_file_e
                    else:
                        print("WARNING: No suitable files generated for initial repository commit. Repository may remain empty on GitHub.")
                        # If no files are pushed initially, the repo remains empty, and subsequent operations might fail.

                # Now, process remaining files (if any) with the standard Git tree/commit API
                # This will execute for non-empty repos, or for new repos after create_file has initialized 'main'
                if files_for_subsequent_push:
                    print("DEBUG: Pushing remaining files via standard Git tree/commit.")
                    git_tree_elements = []
                    for file_path, content in files_for_subsequent_push.items():
                        git_tree_elements.append({
                            "path": file_path,
                            "mode": "100644",
                            "type": "blob",
                            "content": content
                        })

                    # This should now always succeed as main branch should exist (either pre-existing or created by create_file)
                    master_ref = None # Initialize master_ref here
                    max_retries = 5
                    for i in range(max_retries):
                        try:
                            master_ref = repo.get_git_ref("heads/main")
                            print(f"DEBUG: Successfully retrieved 'main' branch ref on attempt {i+1}.")
                            break
                        except GithubException as e:
                            if e.status == 409 or (e.status == 404 and "Branch not found" in str(e.data)):
                                print(f"DEBUG: Main branch not found/repo still inconsistent on attempt {i+1}. Retrying in 1 second...")
                                time.sleep(1)
                            else:
                                raise # Re-raise other GitHub exceptions immediately
                
                    if master_ref is None:
                        raise Exception("Failed to retrieve 'main' branch reference after multiple retries.")

                    master_sha = master_ref.object.sha
                    base_tree = repo.get_git_tree(master_sha)

                    new_tree = repo.create_git_tree(git_tree_elements, base_tree)
                    new_commit = repo.create_git_commit(
                        commit_message,
                        new_tree,
                        [repo.get_git_commit(master_sha)]
                    )
                    master_ref.set_to_commit(new_commit)
                    print(f"DEBUG: Successfully pushed updates to GitHub repo: {repo.html_url}")
                elif not is_repo_truly_empty: # No files to push, and repo was already not empty
                    print("DEBUG: No new files to push to an existing repository.")
                else: # is_repo_truly_empty is True, and no files_for_subsequent_push (meaning only initial commit by create_file, or no files at all)
                    print(f"DEBUG: Repository initialized (possibly with single file) but no further files to push: {repo.html_url}")

                repo_url = repo.html_url # Final repository URL
                print(f"DEBUG: GitHub operations completed for repo: {repo_url}")

                return {
                    "status": "success",
                    "message": f"Project '{project_name_slug}' generated successfully. Pushed to GitHub: {repo_url}",
                    "generated_files": generated_files_list,
                    "repo_url": repo_url
                }

            except GithubException as e:
                print(f"ERROR: GitHub operation failed: Status {e.status}, Message: {e.data.get('message', 'No message provided')}")
                return {
                    "status": "warning",
                    "message": f"Project files generated locally, but failed to push to GitHub: {e.data.get('message', str(e))}. Please check your GitHub PAT and network connection.",
                    "generated_files": generated_files_list,
                    "repo_url": None
                }
            except Exception as e:
                print(f"ERROR: An unexpected error occurred during project generation or GitHub operations: {e}")
                return {
                    "status": "error",
                    "message": f"Failed to generate project: {e}",
                    "generated_files": generated_files_list, # Include locally generated files
                    "repo_url": None
                }

        return {
            "status": "success",
            "message": f"Project '{project_name_slug}' generated successfully. Pushed to GitHub: {repo_url}",
            "generated_files": generated_files_list,
            "repo_url": repo_url
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate project files locally: {e}",
            "generated_files": []
        } 