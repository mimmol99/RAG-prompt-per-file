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

    with gr.Blocks(theme=gr.themes.Soft()) as interface:
        gr.Markdown("# Simple File Q&A")
        gr.Markdown("Upload text or PDF files, ask a question, and get answers based on their content.")

        # --- API Key Input Area (Visible only if needed) ---
        # Use gr.Group instead of gr.Box
        with gr.Group(visible=api_key_needed) as api_key_group: # <--- CHANGE HERE
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
                     height=500,
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
