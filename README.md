# CodeMate: AI-Powered Project Generator

CodeMate is an intelligent assistant designed to streamline your development workflow by automatically generating project structures, essential code files, and basic GitHub workflows based on a simple project description. It integrates seamlessly with GitHub, creating new repositories and pushing generated content, making project setup a breeze.

## Features

*   **AI-Powered Code Generation:** Leverage advanced AI models (via Novita AI) to translate natural language project descriptions into functional code and project files.
*   **Automated GitHub Integration:** Automatically creates new GitHub repositories and pushes generated project files, including `README.md`, `requirements.txt`, and application code.
*   **Local Project Structure Creation:** Organizes generated files into a well-defined local directory structure.
*   **Streamlined Setup:** Simplifies the initial project setup phase, allowing developers to focus on core development tasks sooner.

## Technologies Used

*   Python
*   Novita AI (for code generation)
*   PyGithub (for GitHub API interaction)
*   Python-dotenv (for environment variable management)

## Setup and Installation

To set up and run CodeMate, follow these steps:

1.  **Clone the Repository (if you haven't already):**
    ```bash
    git clone <repository_url_of_CodeMate>
    cd codemate
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install openai python-dotenv PyGithub
    ```

4.  **Environment Variables:**
    Create a `.env` file in the root of your `codemate` directory with the following:

    ```
    NOVITA_AI_API_KEY="YOUR_NOVITA_AI_API_KEY"
    GITHUB_PAT="YOUR_GITHUB_PERSONAL_ACCESS_TOKEN"
    ```

    *   **NOVITA_AI_API_KEY:** Obtain your API key from the [Novita AI Dashboard](https://novita.ai).
    *   **GITHUB_PAT:** Generate a GitHub Personal Access Token (PAT) with `repo` scope from your [GitHub Developer Settings](https://github.com/settings/tokens).

## Usage

CodeMate provides a `generate_project` function that you can integrate into your Python scripts or applications.

Here's an example of how to use it:

```python
from codemate.core.project_generator import generate_project
import os

# Replace with your actual GitHub username and token (or load from .env)
# For demonstration, assuming they are available from environment variables
github_user = os.getenv("GITHUB_USER_LOGIN", "your_github_username") # You might need to set GITHUB_USER_LOGIN in .env
github_personal_access_token = os.getenv("GITHUB_PAT")

if not github_personal_access_token:
    print("Error: GITHUB_PAT not set in .env file or environment variables.")
else:
    project_description = "A simple Streamlit web application to display current weather."

    print(f"Generating project: {project_description}")
    result = generate_project(
        project_description=project_description,
        github_user_login=github_user,
        github_token=github_personal_access_token
    )

    if result["status"] == "success":
        print(f"Project generated and pushed to: {result.get('repo_url', 'N/A')}")
        print(f"Generated files locally at: {result.get('generated_files', ['N/A'])}")
    else:
        print(f"Error generating project: {result['message']}")
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details. 