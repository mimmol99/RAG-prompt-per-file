import gradio as gr
import os
import tempfile
from typing import List, Tuple, Union, Any
import PyPDF2 # For PDF processing
import openai # Import OpenAI library

# --- Global Variables ---
client: Union[openai.OpenAI, None] = None
api_key_needed: bool = False
initial_env_key_warning: str = ""

# --- OpenAI Client Initialization ---
# Attempt to initialize from environment variable first
try:
    openai_api_key_env = os.getenv("OPENAI_API_KEY")
    if not openai_api_key_env:
        api_key_needed = True
        initial_env_key_warning = "Info: OPENAI_API_KEY environment variable not found. Please enter it below."
        print(initial_env_key_warning) # Also print to console
    else:
        client = openai.OpenAI(api_key=openai_api_key_env)
        print("OpenAI client initialized successfully using environment variable.")
except Exception as e:
    print(f"Error initializing OpenAI client from environment variable: {e}")
    client = None # Ensure client is None if init fails
    api_key_needed = True # Still need the key via UI
    initial_env_key_warning = f"Warning: Error during initial OpenAI client setup: {e}. Please enter API key manually."
# --- End OpenAI Client Initialization ---


def extract_text_from_files(files_input: List[Any]) -> Tuple[List[Tuple[str, str]], List[str]]:
    """
    Extracts text content from a list of uploaded files (PDF or text).
    (No changes needed in this function)
    """
    processed_content = []
    errors_warnings = []
    files_to_process_paths = []

    if not files_input:
        return [], ["Error: No files provided."]

    for file_obj in files_input:
       if hasattr(file_obj, 'name') and isinstance(file_obj.name, str):
            files_to_process_paths.append(file_obj.name)
       elif isinstance(file_obj, str) and os.path.isfile(file_obj):
            files_to_process_paths.append(file_obj)
       else:
            errors_warnings.append(f"Warning: Skipping invalid file input object: {type(file_obj)}")

    if not files_to_process_paths:
        if files_input and not errors_warnings:
            errors_warnings.append("Error: No valid file paths found in input.")
        elif not files_input:
            errors_warnings.append("Error: No files were uploaded.")
        return [], errors_warnings

    for file_path in files_to_process_paths:
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            errors_warnings.append(f"Warning: File path not found or not a file: {file_path}. Skipping.")
            continue

        file_name = os.path.basename(file_path)
        file_content = None

        try:
            if file_name.lower().endswith('.pdf'):
                try:
                    extracted_text = ""
                    with open(file_path, 'rb') as pdf_file:
                        reader = PyPDF2.PdfReader(pdf_file)
                        if reader.is_encrypted:
                            errors_warnings.append(f"File: {file_name} - Warning: PDF is encrypted. Skipping.")
                            continue
                        if not reader.pages:
                            errors_warnings.append(f"File: {file_name} - Warning: PDF has no pages. Skipping.")
                            continue

                        for i, page in enumerate(reader.pages):
                            try:
                                page_text = page.extract_text()
                                if page_text:
                                    extracted_text += page_text + "\n"
                            except Exception as page_error:
                                errors_warnings.append(f"File: {file_name} - Warning: Error extracting text from page {i+1}. {page_error}. Skipping page.")
                                continue

                    if not extracted_text and len(reader.pages) > 0:
                         errors_warnings.append(f"File: {file_name} - Warning: PDF processed, but no text extracted (image-based or extraction failed?). Skipping.")
                         continue
                    elif not extracted_text:
                         errors_warnings.append(f"File: {file_name} - Warning: PDF seems empty or unreadable. Skipping.")
                         continue
                    else:
                         file_content = extracted_text
                except Exception as pdf_error:
                    errors_warnings.append(f"File: {file_name} - Error processing PDF: {pdf_error}. Skipping.")
                    continue
            else: # Process as text
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        if not file_content:
                            errors_warnings.append(f"File: {file_name} - Warning: Text file is empty. Skipping.")
                            continue
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='latin-1') as f:
                            file_content = f.read()
                            if not file_content:
                                errors_warnings.append(f"File: {file_name} - Warning: Text file is empty. Skipping.")
                                continue
                            errors_warnings.append(f"File: {file_name} - Info: Read using latin-1 encoding.")
                    except Exception:
                        errors_warnings.append(f"File: {file_name} - Error: Cannot decode file content (not UTF-8 or Latin-1). Skipping.")
                        continue
                except Exception as text_error:
                    errors_warnings.append(f"File: {file_name} - Error reading text file: {text_error}. Skipping.")
                    continue

            if file_content:
                processed_content.append((file_name, file_content))

        except Exception as e:
            errors_warnings.append(f"File: {file_name} - Unexpected error during processing: {e}. Skipping.")

    return processed_content, errors_warnings


def get_answer_from_content(openai_client: openai.OpenAI, content: str, question: str) -> str:
    """
    Uses the OpenAI API to answer a question based on the
    provided content.
    (No changes needed in this function, relies on the passed client)
    """
    # Note: The check 'if not openai_client' is now crucial inside respond() before calling this
    if not question:
        return "Error: No question provided."
    if not content:
        return "Error: Content is empty, cannot answer question."

    system_prompt = "You are an AI assistant. Answer the user's question based *only* on the provided text content from one or more files. Be concise and stick strictly to the information given in the text. If the answer cannot be found in the text, say so."
    user_prompt = f"File Content:\n```\n{content}\n```\n\nQuestion:\n{question}"

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            n=1,
            stop=None
        )
        if response.choices and len(response.choices) > 0:
            answer = response.choices[0].message.content.strip()
            return answer if answer else "LLM returned an empty answer."
        else:
            return "Error: LLM response structure was unexpected."

    except openai.AuthenticationError:
         # This specific error is useful if the key provided via UI is wrong
         print("Authentication Error: Potentially invalid API key.")
         return "Error: OpenAI Authentication Error. Please check if your API key is correct and valid."
    except openai.APIError as e:
        return f"Error: OpenAI API Error: {e}"
    except Exception as e:
        return f"Error during OpenAI call: {e}"

# --- New Function to Set API Key ---
def set_api_key(api_key_input: str):
    """
    Attempts to initialize the OpenAI client using the key from the input field.
    Updates UI elements based on success or failure.
    """
    global client, api_key_needed # We need to modify the global client

    if not api_key_input:
        return {
            status_display: gr.update(value="Error: API Key cannot be empty.", visible=True)
            # Keep input visible
        }

    try:
        # Attempt to initialize the client with the provided key
        client = openai.OpenAI(api_key=api_key_input)
        # Try a simple test call (optional, but confirms connectivity & key validity)
        client.models.list() # Example: list models
        print("OpenAI client initialized successfully using key from UI.")
        api_key_needed = False # Key is now set

        # Return updates for UI elements
        return {
            api_key_textbox: gr.update(visible=False),
            set_key_button: gr.update(visible=False),
            status_display: gr.update(value="API Key set successfully!", visible=True),
            # Enable the main chat interface elements
            chatbot: gr.update(visible=True),
            msg_textbox: gr.update(visible=True, interactive=True, placeholder="Type your question about the file content here..."),
            file_input: gr.update(visible=True),
            ask_individually_checkbox: gr.update(visible=True)
        }

    except openai.AuthenticationError:
        print("Authentication Error: Invalid API Key provided via UI.")
        client = None # Reset client if auth failed
        api_key_needed = True
        return {
             status_display: gr.update(value="Error: Invalid API Key. Please check and try again.", visible=True),
             api_key_textbox: gr.update(value=""), # Clear the invalid key
             # Keep input visible
        }
    except Exception as e:
        print(f"Error initializing OpenAI client from UI input: {e}")
        client = None # Reset client if any other error occurred
        api_key_needed = True
        return {
             status_display: gr.update(value=f"Error: Could not initialize client: {e}", visible=True),
             # Keep input visible
        }


def respond(
    message: str,
    chat_history: List[Tuple[str, str]],
    files_input: List[Any],
    ask_individually: bool
    ) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Core function called by Gradio on submission. Processes files, calls LLM,
    and updates chat history. Now checks if client is ready.
    """
    # Use the global client variable
    global client, api_key_needed

    if client is None:
        # Determine why client is None
        if api_key_needed:
             bot_message = "Error: OpenAI API Key not set. Please enter your key above and click 'Set API Key'."
        else:
             # This case might happen if initialization failed unexpectedly even with env var
             bot_message = "Error: Cannot process request. OpenAI client is not configured or failed to initialize."
        chat_history.append((message, bot_message))
        return "", chat_history

    if not message:
        bot_message = "Please type a question."
        chat_history.append((None, bot_message)) # Don't add user message if empty
        return "", chat_history

    # Append user message FIRST
    chat_history.append((message, None)) # Placeholder for bot response

    # 1. Extract content from uploaded files
    processed_content, errors_warnings = extract_text_from_files(files_input)

    # Report extraction errors/warnings
    if errors_warnings:
        error_summary = "\n".join(errors_warnings)
        if not processed_content:
            chat_history[-1] = (message, f"Could not process files:\n{error_summary}")
            return "", chat_history
        # else: Append warnings later

    if not processed_content:
        if not errors_warnings:
            bot_message = "No text could be extracted from the provided files. Please upload valid PDF or text files."
        else:
            bot_message = "No files remaining after processing errors."
        chat_history[-1] = (message, bot_message)
        return "", chat_history

    # 2. Generate Answer(s) using OpenAI (client is guaranteed to be not None here)
    bot_response_parts = []

    if ask_individually:
        bot_response_parts.append(f"Answering for {len(processed_content)} file(s):\n---")
        for file_name, content in processed_content:
            answer = get_answer_from_content(client, content, message) # Pass the initialized client
            bot_response_parts.append(f"**File: {file_name}**\n{answer}\n---")
        final_bot_message = "\n".join(bot_response_parts)

    else:
        combined_content = "\n\n--- End of File --- \n\n".join(
            [f"Content from: {fname}\n\n{fcontent}" for fname, fcontent in processed_content]
        )
        if len(processed_content) > 1:
            bot_response_parts.append(f"Answering based on combined content of {len(processed_content)} files:")
        else:
             bot_response_parts.append(f"Answering based on content of {processed_content[0][0]}:") # Use filename

        answer = get_answer_from_content(client, combined_content, message) # Pass the initialized client
        bot_response_parts.append(answer)
        final_bot_message = "\n".join(bot_response_parts)

    # Append any file processing warnings/errors to the final answer
    if errors_warnings:
        final_bot_message += "\n\n**File Processing Issues:**\n" + "\n".join(errors_warnings)

    # Update the last entry in chat history
    chat_history[-1] = (message, final_bot_message)

    # Return empty string to clear textbox, and the updated history
    return "", chat_history


# --- Gradio Interface Setup ---
# Define components globally within this scope so set_api_key can return updates for them
api_key_textbox = None
set_key_button = None
status_display = None
chatbot = None
msg_textbox = None
file_input = None
ask_individually_checkbox = None

def build_gradio_interface():
    """Sets up the Gradio interface using Blocks for layout."""
    # Make components accessible to the outer scope/other functions
    global api_key_textbox, set_key_button, status_display
    global chatbot, msg_textbox, file_input, ask_individually_checkbox

    with gr.Blocks(theme=gr.themes.Soft(),fill_height=True) as interface:
        gr.Markdown("# Simple File Q&A")
        gr.Markdown("Upload text or PDF files, ask a question, and get answers based on their content.")

        # --- API Key Input Area (Visible only if needed) ---
        with gr.Group(visible=api_key_needed) as api_key_box: # Use a Box for grouping
             status_display = gr.Markdown(value=initial_env_key_warning, visible=True)
             with gr.Row():
                 api_key_textbox = gr.Textbox(
                     label="Enter OpenAI API Key",
                     type="password",
                     placeholder="sk-...",
                     scale=3 # Make textbox wider
                 )
                 set_key_button = gr.Button("Set API Key", scale=1) # Button next to it

        # --- Main Chat Area (Initially hidden/disabled if API key needed) ---
        is_chat_visible = not api_key_needed
        with gr.Row():
             with gr.Column(scale=1):
                 file_input = gr.File(
                     label="Upload Files or Directory",
                     file_count="multiple",
                     visible=is_chat_visible # Initially hidden if key needed
                 )
                 ask_individually_checkbox = gr.Checkbox(
                     label="Ask about each file individually?",
                     value=False,
                     visible=is_chat_visible # Initially hidden if key needed
                 )

             with gr.Column(scale=2):
                 chatbot = gr.Chatbot(
                     label="Chat",
                     bubble_full_width=False,
                     height=900,
                     visible=is_chat_visible # Initially hidden if key needed
                 )
                 msg_textbox = gr.Textbox(
                     label="Your Question:",
                     placeholder="Set API Key above first..." if api_key_needed else "Type your question...",
                     show_label=False,
                     container=False,
                     interactive=is_chat_visible, # Disable input if key needed
                     visible=is_chat_visible # Initially hidden if key needed
                 )

        # --- Component Actions ---
        # Action for the 'Set API Key' button
        if set_key_button: # Check if the button was created
             set_key_button.click(
                 fn=set_api_key,
                 inputs=[api_key_textbox],
                 # Outputs need to update visibility/status of multiple components
                 outputs=[
                     api_key_textbox,
                     set_key_button,
                     status_display,
                     chatbot,
                     msg_textbox,
                     file_input,
                     ask_individually_checkbox
                     # Note: We are updating the components themselves,
                     # Gradio handles applying the gr.update() dictionaries returned by set_api_key
                 ]
             )

        # Action for submitting a question (Enter key in textbox)
        if msg_textbox: # Check if the textbox was created
            msg_textbox.submit(
                fn=respond,
                inputs=[msg_textbox, chatbot, file_input, ask_individually_checkbox],
                outputs=[msg_textbox, chatbot] # Clear textbox, update chatbot
            )

    return interface

# --- Main Execution ---
if __name__ == "__main__":
    print("\n--- Starting Gradio Application ---")
    # Build the interface (which sets up component visibility based on api_key_needed)
    iface = build_gradio_interface()
    # Launch the interface
    iface.queue().launch()

    # Note: The error handling for client initialization failure before launch
    # is now integrated into the UI itself. If the key is needed, the UI prompts for it.
