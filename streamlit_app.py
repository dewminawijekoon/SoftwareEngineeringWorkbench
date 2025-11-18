"""
Streamlit Frontend for Solution Architecture Generator
A web-based interface for generating solution architectures using Gemini AI
"""
import streamlit as st
import tempfile
import os
import re
from pathlib import Path
from typing import List

from architecture_generator import ArchitectureGenerator
from document_processor import DocumentProcessor
from models import UserRequirement, SupportingDocument

# Page configuration
st.set_page_config(
    page_title="Architecture Generator",
    page_icon="🏗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'generator' not in st.session_state:
    st.session_state.generator = ArchitectureGenerator()
    st.session_state.generator.start_chat_session()
if 'requirements' not in st.session_state:
    st.session_state.requirements = []
if 'supporting_docs' not in st.session_state:
    st.session_state.supporting_docs = []
if 'architecture' not in st.session_state:
    st.session_state.architecture = None
if 'chat_started' not in st.session_state:
    st.session_state.chat_started = False
if 'chat_completed' not in st.session_state:
    st.session_state.chat_completed = False
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0  # 0=Chat, 1=Documents, 2=Summary, 3=Architecture
if 'docs_completed' not in st.session_state:
    st.session_state.docs_completed = False

# Custom CSS
st.markdown("""
<style>
    /* Chat container styling */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        border: 1px solid #e0e0e0;
    }
    
    .summary-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .requirement-item-high {
        background-color: #fff5f5;
        padding: 1rem;
        border-radius: 0.3rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #dc3545;
    }
    .requirement-item-medium {
        background-color: #fffbf0;
        padding: 1rem;
        border-radius: 0.3rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #ffc107;
    }
    .requirement-item-low {
        background-color: #f0f9ff;
        padding: 1rem;
        border-radius: 0.3rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #0d6efd;
    }
    .requirement-item {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.3rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #6c757d;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("Solution Architecture Generator")
st.markdown("""
<div style="background-color: #e3f2fd; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
    <strong>📋 Workflow:</strong> 
    <span style="color: #1976d2;">1. Chat → 2. Documents → 3. Summary (Optional Requirements) → 4. Generate Architecture</span>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    st.header("Navigation")

    # Navigation buttons
    tabs = ["Chat", "Documents", "Summary", "Architecture"]
    for idx, tab_name in enumerate(tabs):
        button_type = "primary" if idx == st.session_state.active_tab else "secondary"
        if st.button(
            tab_name,
            key=f"nav_{tab_name}",
            use_container_width=True,
            type=button_type
        ):
            st.session_state.active_tab = idx
            st.rerun()

    st.markdown("---")

    # Progress indicators
    st.subheader("Progress")
    chat_status = "✅" if st.session_state.chat_completed else "⏳"
    docs_status = "✅" if st.session_state.docs_completed or len(
        st.session_state.supporting_docs) > 0 else "⏳"
    summary_status = "✅" if (
        st.session_state.chat_completed and st.session_state.docs_completed) else "⏳"
    arch_status = "✅" if st.session_state.architecture else "⏳"

    st.markdown(f"{chat_status} 1. Chat")
    st.markdown(f"{docs_status} 2. Documents")
    st.markdown(f"{summary_status} 3. Summary")
    st.markdown(f"{arch_status} 4. Architecture")

    st.markdown("---")

    # Copyright
    st.caption("© 2025 84H. All rights reserved.")

# Display content based on active tab
active_tab = st.session_state.active_tab

# Tab 0: Chat Interface
if active_tab == 0:
    st.header("Requirements Gathering Chat")
    st.markdown("Chat with AI to define your project requirements")

    # Auto-start chat on first load
    if not st.session_state.chat_started:
        st.session_state.chat_started = True
        # Initial AI greeting with loading effect
        with st.spinner("AI is preparing to chat..."):
            initial_message = st.session_state.generator.chat(
                "Please introduce yourself and ask your first question to gather software requirements."
            )
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": initial_message
            })

    # Chat interface - Display chat history in a scrollable container
    chat_container = st.container(height=500, border=True)
    with chat_container:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input
    if not st.session_state.chat_completed:
        user_input = st.chat_input(
            "Type your response (or 'done' to finish)...")

        if user_input:
            # Check if user manually wants to finish
            if user_input.lower() == 'done':
                st.session_state.chat_completed = True
                st.session_state.active_tab = 1
                st.balloons()
                st.success("Chat completed! Moving to Documents...")
                st.rerun()

            # Add user message
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input
            })

            # Get AI response with completion detection
            with st.spinner("AI is thinking..."):
                # Ask AI to respond and indicate if done
                enhanced_prompt = f"""{user_input}

After your response, if you have gathered enough information to create a comprehensive architecture (project type, key requirements, technical constraints, and main features are clear), end your message with the exact phrase: [REQUIREMENTS_COMPLETE]
Otherwise, continue asking clarifying questions."""

                ai_response = st.session_state.generator.chat(enhanced_prompt)

                # Check if AI indicates completion
                if "[REQUIREMENTS_COMPLETE]" in ai_response:
                    # Remove the completion marker from display
                    ai_response = ai_response.replace(
                        "[REQUIREMENTS_COMPLETE]", "").strip()
                    st.session_state.chat_completed = True

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": ai_response
                    })

                    st.balloons()
                    st.success(
                        "Requirements gathering complete! Moving to Documents...")
                    st.session_state.active_tab = 1
                    st.rerun()
                else:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": ai_response
                    })

                    st.rerun()
    else:
        st.info("Chat completed! Next step: Upload Documents")
        st.markdown("### Quick Navigation")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📄 Go to Documents", use_container_width=True, type="primary"):
                st.session_state.active_tab = 1
                st.rerun()
        with col2:
            if st.button("📋 View Summary", use_container_width=True):
                st.session_state.active_tab = 2
                st.rerun()
        with col3:
            if st.button("🏗 Generate Architecture", use_container_width=True):
                st.session_state.active_tab = 3
                st.rerun()

# Tab 1: Documents Upload
elif active_tab == 1:
    st.header("Supporting Documents")
    st.markdown(
        "Upload any supporting documents (PDF, DOCX, TXT, MD) to provide additional context for architecture generation")

    if not st.session_state.chat_completed:
        st.info("💡 Tip: Complete the chat first to gather initial requirements, then upload documents for additional context.")

    # Show summary of what will be sent to AI
    if st.session_state.supporting_docs:
        st.success(
            f"✅ {len(st.session_state.supporting_docs)} document(s) uploaded and ready to be sent to the AI agent")

        # Summary card showing what will be passed to AI
        with st.container():
            st.markdown("#### 📊 Data Summary - What the AI Agent Will Receive")
            col1, col2, col3 = st.columns(3)

            with col1:
                total_chars = sum(len(doc.content)
                                  for doc in st.session_state.supporting_docs)
                st.metric("Total Content", f"{total_chars:,} chars")

            with col2:
                total_words = sum(len(doc.content.split())
                                  for doc in st.session_state.supporting_docs)
                st.metric("Approx. Words", f"{total_words:,}")

            with col3:
                doc_types = set(
                    doc.document_type for doc in st.session_state.supporting_docs)
                st.metric("Document Types", len(doc_types))

            # Show list of files
            st.markdown("**Files included:**")
            for doc in st.session_state.supporting_docs:
                st.markdown(f"- 📄 `{doc.filename}` ({doc.document_type})")
    else:
        st.info(
            "ℹ️ No documents uploaded yet. Documents are optional but can improve architecture quality.")

    uploaded_files = st.file_uploader(
        "Choose files",
        type=['pdf', 'docx', 'txt', 'md'],
        accept_multiple_files=True,
        key="doc_uploader_main"
    )

    if uploaded_files:
        if st.button("Process Uploaded Documents", type="primary"):
            doc_processor = DocumentProcessor()

            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {uploaded_file.name}...")

                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                try:
                    doc = doc_processor.process_document(tmp_path)

                    # Check if already added
                    if not any(d.filename == doc.filename for d in st.session_state.supporting_docs):
                        st.session_state.supporting_docs.append(doc)
                        st.success(
                            f"✓ {uploaded_file.name} processed successfully")
                    else:
                        st.info(f"ℹ {uploaded_file.name} already added")

                except Exception as e:
                    st.error(f"✗ Error processing {uploaded_file.name}: {e}")
                finally:
                    # Clean up temp file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

                progress_bar.progress((i + 1) / len(uploaded_files))

            status_text.text("All documents processed!")
            st.success(
                "Documents ready! You can now generate the architecture.")
            st.rerun()

    # Display processed documents with enhanced viewing
    if st.session_state.supporting_docs:
        st.markdown("---")
        st.markdown("### 📑 Uploaded Documents - Content Sent to AI Agent")
        st.markdown(
            "Below are the documents and their complete content that will be analyzed by the AI:")

        for idx, doc in enumerate(st.session_state.supporting_docs, 1):
            with st.expander(f"📄 {idx}. {doc.filename} ({doc.document_type})", expanded=False):
                # Document metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("File", doc.filename)
                with col2:
                    st.metric("Type", doc.document_type.replace(
                        '_', ' ').title())
                with col3:
                    st.metric("Size", f"{len(doc.content):,} chars")

                st.markdown("---")

                # Show full content in tabs
                tab1, tab2 = st.tabs(["📝 Full Content", "🔍 Preview"])

                with tab1:
                    st.markdown(
                        "**Complete content that will be sent to the AI agent:**")
                    # Show full content in a scrollable text area
                    st.text_area(
                        "Full Document Content",
                        value=doc.content,
                        height=400,
                        disabled=True,
                        label_visibility="collapsed"
                    )
                    st.caption(
                        f"Total: {len(doc.content):,} characters | {len(doc.content.split())} words approximately")

                with tab2:
                    st.markdown("**First 1000 characters preview:**")
                    preview_text = doc.content[:1000]
                    if len(doc.content) > 1000:
                        preview_text += "\n\n... (content truncated for preview)"
                    st.markdown(f"```\n{preview_text}\n```")

                # Option to remove document
                if st.button(f"🗑️ Remove {doc.filename}", key=f"remove_doc_{idx}"):
                    st.session_state.supporting_docs = [
                        d for d in st.session_state.supporting_docs if d.filename != doc.filename
                    ]
                    st.success(f"Removed {doc.filename}")
                    st.rerun()

    # Navigation buttons
    st.markdown("---")
    st.markdown("### Next Steps")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Chat", use_container_width=True, type="secondary"):
            st.session_state.active_tab = 0
            st.rerun()
    with col2:
        if st.button("➡️ Continue to Summary", use_container_width=True, type="primary"):
            st.session_state.docs_completed = True
            st.session_state.active_tab = 2
            st.rerun()

# Tab 2: Summary (Auto-generated from Chat + Documents)
elif active_tab == 2:
    st.header("Summary & Requirements Review")
    st.markdown(
        "Review the information gathered from chat and documents. Add or modify requirements as needed.")

    if not st.session_state.chat_completed:
        st.warning(
            "⚠️ Please complete the chat first before viewing the summary.")
        if st.button("Go to Chat", type="primary"):
            st.session_state.active_tab = 0
            st.rerun()
    else:
        # Display conversation summary
        st.subheader("📝 Chat Conversation Summary")

        with st.expander("View Full Conversation", expanded=False):
            for msg in st.session_state.chat_history:
                role = "**You:**" if msg["role"] == "user" else "**AI:**"
                st.markdown(f"{role} {msg['content']}")
                st.markdown("---")

        # Display documents summary
        if st.session_state.supporting_docs:
            st.subheader("📄 Supporting Documents")
            st.info(
                f"{len(st.session_state.supporting_docs)} document(s) uploaded")

            with st.expander("View Documents", expanded=False):
                for doc in st.session_state.supporting_docs:
                    st.markdown(f"**{doc.filename}** ({doc.document_type})")
                    st.caption(f"Size: {len(doc.content):,} characters")
                    st.markdown("---")

        st.markdown("---")

        # Auto-extract requirements button
        if len(st.session_state.requirements) == 0:
            st.markdown("### 🤖 Auto-Extract Requirements")
            st.info(
                "Let AI analyze the chat and documents to extract structured requirements")

            if st.button("Auto-Extract Requirements from Chat & Documents", type="primary", use_container_width=True):
                with st.spinner("Analyzing conversation and documents to extract requirements..."):
                    # Build chat history text
                    chat_text = "\n".join([
                        f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}"
                        for m in st.session_state.chat_history
                    ])

                    # Build documents context
                    docs_text = ""
                    if st.session_state.supporting_docs:
                        docs_text = "\n\nSupporting Documents:\n"
                        for doc in st.session_state.supporting_docs:
                            docs_text += f"\n--- {doc.filename} ---\n{doc.content[:2000]}\n"

                    # Ask AI to extract requirements
                    extraction_prompt = f"""Based on this conversation and supporting documents, extract structured requirements.
                    For each requirement, provide:
                    - requirement: clear statement
                    - priority: High/Medium/Low (infer from context)
                    - category: Functional/Non-functional/Technical/Business
                    
                    Return ONLY a valid JSON array with this exact format:
                    [{{"requirement": "...", "priority": "High", "category": "Functional"}}]
                    
                    Conversation:
                    {chat_text}
                    
                    {docs_text}
                    """

                    response = st.session_state.generator.chat(
                        extraction_prompt)

                    # Try to parse JSON
                    import json

                    try:
                        # Extract JSON array from response
                        json_match = re.search(r'\[.*\]', response, re.DOTALL)
                        if json_match:
                            requirements_data = json.loads(json_match.group())

                            for req_data in requirements_data:
                                st.session_state.requirements.append(
                                    UserRequirement(
                                        requirement=req_data.get(
                                            'requirement', ''),
                                        priority=req_data.get(
                                            'priority', 'Medium'),
                                        category=req_data.get(
                                            'category', 'Functional')
                                    )
                                )

                            st.success(
                                f"Extracted {len(requirements_data)} requirements!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(
                                "Could not extract requirements. Please add them manually below.")
                    except Exception as e:
                        st.error(f"Error parsing requirements: {e}")

        # Display extracted requirements
        if st.session_state.requirements:
            st.markdown("### ✅ Extracted Requirements")

            for i, req in enumerate(st.session_state.requirements, 1):
                priority_badge = {
                    "High": "HIGH",
                    "Medium": "MEDIUM",
                    "Low": "LOW"
                }.get(req.priority, "N/A")

                css_class = f"requirement-item-{req.priority.lower()}" if req.priority and req.priority in [
                    "High", "Medium", "Low"] else "requirement-item"

                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"""
                    <div class="{css_class}">
                        <strong>{i}. {req.requirement}</strong><br>
                        <small>Priority: {priority_badge} | Category: {req.category or 'N/A'}</small>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("🗑️", key=f"del_req_{i}", help="Delete requirement"):
                        st.session_state.requirements.pop(i-1)
                        st.rerun()

        st.markdown("---")

        # Manual requirement addition
        st.markdown("### ➕ Add Additional Requirements (Optional)")
        st.info(
            "You can add more requirements manually if needed, or proceed to generate architecture")

        with st.form("add_requirement_form"):
            col1, col2 = st.columns(2)

            with col1:
                req_text = st.text_area("Requirement Description", height=100)
                priority = st.selectbox("Priority", ["High", "Medium", "Low"])

            with col2:
                category = st.selectbox("Category",
                                        ["Functional", "Non-functional", "Technical", "Business", "Security"])

                submitted = st.form_submit_button(
                    "Add Requirement", type="primary")

                if submitted and req_text:
                    st.session_state.requirements.append(
                        UserRequirement(
                            requirement=req_text,
                            priority=priority,
                            category=category
                        )
                    )
                    st.success("Requirement added!")
                    st.rerun()

        # Navigation buttons
        st.markdown("---")
        st.markdown("### Ready to Generate Architecture?")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back to Documents", use_container_width=True, type="secondary"):
                st.session_state.active_tab = 1
                st.rerun()
        with col2:
            if st.button("🏗 Generate Architecture", use_container_width=True, type="primary"):
                st.session_state.active_tab = 3
                st.rerun()

# Tab 3: Architecture Generation
elif active_tab == 3:
    st.header("Generate Solution Architecture")

    # Check prerequisites - chat or documents must exist
    has_chat = st.session_state.chat_completed and len(
        st.session_state.chat_history) > 0
    has_docs = len(st.session_state.supporting_docs) > 0
    has_requirements = len(st.session_state.requirements) > 0

    can_generate = has_chat or has_docs

    if not can_generate:
        st.warning(
            "⚠️ Please complete the chat or upload documents before generating architecture")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Go to Chat", use_container_width=True):
                st.session_state.active_tab = 0
                st.rerun()
        with col2:
            if st.button("Go to Documents", use_container_width=True):
                st.session_state.active_tab = 1
                st.rerun()
    else:
        # Show what we have
        status_parts = []
        if has_chat:
            status_parts.append(
                f"✅ Chat completed ({len(st.session_state.chat_history)} messages)")
        if has_docs:
            status_parts.append(
                f"✅ {len(st.session_state.supporting_docs)} document(s) uploaded")
        if has_requirements:
            status_parts.append(
                f"✅ {len(st.session_state.requirements)} requirement(s) defined")

        st.success(" | ".join(status_parts))

        # Show comprehensive summary of what will be sent to AI
        with st.expander("🔍 View Complete Data Being Sent to AI Agent", expanded=False):
            st.markdown("### 📋 Input Data Summary")

            # Requirements section
            if st.session_state.requirements:
                st.markdown(
                    f"#### Requirements ({len(st.session_state.requirements)})")
                for i, req in enumerate(st.session_state.requirements, 1):
                    priority_emoji = {"High": "🔴", "Medium": "🟡",
                                      "Low": "🔵"}.get(req.priority, "⚪")
                    st.markdown(f"{i}. {priority_emoji} **{req.requirement}**")
                    st.markdown(
                        f"   *Priority: {req.priority or 'N/A'} | Category: {req.category or 'N/A'}*")
            else:
                st.markdown("#### Requirements")
                st.info(
                    "No explicit requirements defined. AI will extract requirements from chat and documents.")

            # Documents section
            if st.session_state.supporting_docs:
                st.markdown(
                    f"#### Supporting Documents ({len(st.session_state.supporting_docs)})")
                for doc in st.session_state.supporting_docs:
                    st.markdown(
                        f"- 📄 **{doc.filename}** ({doc.document_type})")
                    st.markdown(f"  *Size: {len(doc.content):,} characters*")
                    with st.expander(f"View content of {doc.filename}"):
                        st.text_area("Content", value=doc.content, height=300,
                                     disabled=True, label_visibility="collapsed")
            else:
                st.markdown("#### Supporting Documents")
                st.info("No supporting documents included")

            # Chat history section
            if st.session_state.chat_history:
                st.markdown(
                    f"#### Chat History ({len(st.session_state.chat_history)} messages)")
                total_chat_chars = sum(len(msg['content'])
                                       for msg in st.session_state.chat_history)
                st.info(f"Total chat content: {total_chat_chars:,} characters")
                with st.expander("View full chat history"):
                    for msg in st.session_state.chat_history:
                        role_label = "👤 You" if msg['role'] == 'user' else "🤖 AI"
                        st.markdown(f"**{role_label}:** {msg['content']}")
                        st.markdown("---")
            else:
                st.markdown("#### Chat History")
                st.info("No chat history available")

    # Generation button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "Generate Architecture",
            disabled=not can_generate,
            use_container_width=True,
            type="primary"
        ):
            with st.spinner("AI is generating your solution architecture... This may take 30-60 seconds"):
                # Build chat history text
                chat_history_text = None
                if st.session_state.chat_history:
                    chat_history_text = "\n".join([
                        f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}"
                        for m in st.session_state.chat_history
                    ])

                # Generate architecture
                try:
                    # Pass requirements or empty list
                    reqs_to_pass = st.session_state.requirements if st.session_state.requirements else []

                    architecture = st.session_state.generator.generate_architecture(
                        requirements=reqs_to_pass,
                        supporting_docs=st.session_state.supporting_docs if st.session_state.supporting_docs else None,
                        chat_history=chat_history_text
                    )

                    st.session_state.architecture = architecture
                    st.success("Architecture generated successfully!")
                    st.balloons()
                    st.rerun()

                except Exception as e:
                    st.error(f"Error generating architecture: {e}")

    # Display generated architecture
    if st.session_state.architecture:
        st.markdown("---")
        st.markdown("### Generated Architecture")

        # Download button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.download_button(
                label="Download as Markdown",
                data=st.session_state.architecture,
                file_name="solution_architecture.md",
                mime="text/markdown",
                use_container_width=True
            )

        # Display architecture with mermaid support
        st.markdown("---")

        # Split content to find and render mermaid diagrams
        content = st.session_state.architecture
        parts = re.split(r'```mermaid\n(.*?)\n```', content, flags=re.DOTALL)

        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Regular markdown
                if part.strip():
                    st.markdown(part)
            else:
                # Mermaid diagram
                st.code(part, language='mermaid')
                try:
                    import streamlit.components.v1 as components
                    mermaid_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                        <script>
                            mermaid.initialize({{
                                startOnLoad: true,
                                theme: 'default',
                                flowchart: {{ useMaxWidth: true, htmlLabels: true }}
                            }});
                        </script>
                    </head>
                    <body style="margin: 0; padding: 20px; background-color: white;">
                        <div class="mermaid" style="text-align: center;">
                        {part}
                        </div>
                    </body>
                    </html>
                    """
                    components.html(mermaid_html, height=800, scrolling=True)
                except:
                    st.info(
                        "Mermaid diagram code shown above. Copy to visualize in a Mermaid renderer.")
