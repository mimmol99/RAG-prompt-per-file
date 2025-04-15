# File Q&A Chatbot with Dynamic Query Modes

Ask questions about your documents! This application uses Gradio and the OpenAI API to create a chat interface for interacting with the content of uploaded PDF and text files.

## The Power of Two Modes

A unique feature of this tool is its ability to adapt how it queries your documents, switchable via a checkbox:

* **Combined Mode (Default - Checkbox Unchecked):**
    * **How it works:** Merges the text from all uploaded files into a single context before sending your question to the AI.
    * **Best for:** General overview questions, finding information that could be in any file, faster responses when dealing with multiple documents as one logical unit.

* **Per-File Mode (Checkbox Checked):**
    * **How it works:** Sends your exact question separately to the AI for *each* uploaded file, using only that specific file's content as context for each query.
    * **Best for:** Extracting the same specific data point (e.g., "What is the conclusion?") from every document, comparing how different files address the same topic, ensuring answers are strictly sourced from individual files. This mode is more thorough but takes longer as it makes multiple API calls.

You can switch between these modes at any point during your chat session.

## Key Features

* Supports multiple PDF and Text (.txt) file uploads.
* Intuitive chat interface (Gradio) with conversation history.
* **Dynamic Mode Switching:** Effortlessly change between Combined and Per-File querying.
* Utilizes OpenAI API for natural language understanding and generation.
* Secure API Key Handling: Prioritizes `OPENAI_API_KEY` environment variable, with a fallback to UI input if not set.
* Reports file processing errors (e.g., encrypted PDFs, unreadable files).

## Requirements

* Python 3.8 or newer
* An active OpenAI API Key with available credits/quota.
* Python packages listed in `requirements.txt`.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repo-url>
    cd <repository-folder>
    ```

2.  **Install dependencies:** Open your terminal in the project directory and run:
    ```bash
    pip install -r requirements.txt
    ```

## Running the App

1.  **Set your OpenAI API Key:**
    * **Method 1 (Recommended):** Set the `OPENAI_API_KEY` environment variable in your terminal.
        ```bash
        # Linux/macOS
        export OPENAI_API_KEY='sk-...'
        # Windows (Command Prompt)
        set OPENAI_API_KEY=sk-...
        # Windows (PowerShell)
        $env:OPENAI_API_KEY='sk-...'
        ```
    * **Method 2:** Don't set the environment variable. The application will prompt you to enter it in the UI on startup.
2.  **Launch the script:**
    ```bash
    python3 chat.py
    ```
3.  Open the local URL provided (e.g., `http://127.0.0.1:7860`) in your web browser.

## How to Use

1.  Use the file component to upload your documents.
2.  Decide if you want to query all files together (leave checkbox unchecked) or each one individually (check the "Ask about each file individually?" box).
3.  Enter your question in the input field at the bottom.
4.  Review the answer(s) provided by the chatbot.
5.  Feel free to change the query mode or upload different files for subsequent questions.

