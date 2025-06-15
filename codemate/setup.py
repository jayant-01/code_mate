from setuptools import setup, find_packages

setup(
    name="codemate",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "PyGithub",
        "openai",
        "python-dotenv",
    ],
    # You can add other metadata here if needed
    author="Your Name",
    author_email="your.email@example.com",
    description="CodeMate: An AI-powered developer assistant",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/codemate", # Replace with your project's GitHub URL
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
) 