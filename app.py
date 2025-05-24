import streamlit as st
import google.generativeai as genai
import docx2txt
import PyPDF2

# Configure Gemini API
api_key = st.secrets.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = []
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []
if "docs_text" not in st.session_state:
    st.session_state.docs_text = []

# App title
st.title("🎨 Gemini Flash Chatbot")

# One row with two columns for file uploaders
col1, col2 = st.columns(2)

with col1:
    st.session_state.uploaded_images = st.file_uploader(
        label="Upload Images",
        type=["jpg", "jpeg", "png"],
        key="images_hidden",
        accept_multiple_files=True
    )

with col2:
    st.session_state.uploaded_docs = st.file_uploader(
        label="Upload Documents",
        type=["pdf", "docx", "txt"],
        key="docs_hidden",
        accept_multiple_files=True
    )

# Extract text from uploaded documents
st.session_state.docs_text = []
for doc in st.session_state.uploaded_docs:
    ext = doc.name.split(".")[-1].lower()
    if ext == "pdf":
        reader = PyPDF2.PdfReader(doc)
        text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        st.session_state.docs_text.append((doc.name, text))
    elif ext == "docx":
        st.session_state.docs_text.append((doc.name, docx2txt.process(doc)))
    elif ext == "txt":
        st.session_state.docs_text.append((doc.name, doc.read().decode("utf-8")))

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input and response generation
if prompt := st.chat_input("💬 Ask your question..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        parts = []

        prompt_lower = prompt.lower()

        # PDF-only context
        if "pdf" in prompt_lower:
            for name, text in st.session_state.docs_text:
                if name.lower().endswith(".pdf"):
                    parts.append(f"Document: {name}\n\n{text}")

        # Image-only context
        elif "image" in prompt_lower or "photo" in prompt_lower or "picture" in prompt_lower:
            for image_file in st.session_state.uploaded_images:
                parts.append({"mime_type": "image/jpeg", "data": image_file.read()})

        # Default: send all content
        else:
            for image_file in st.session_state.uploaded_images:
                parts.append({"mime_type": "image/jpeg", "data": image_file.read()})
            for name, text in st.session_state.docs_text:
                parts.append(f"Document: {name}\n\n{text}")

        parts.append(prompt)

        # Generate response from Gemini
        response = model.generate_content(parts)
        reply = response.text
        placeholder.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
