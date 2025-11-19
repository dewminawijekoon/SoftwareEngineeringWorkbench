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
                st.balloons()
                st.success("Chat completed! You can now proceed to Documents or generate architecture.")
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

After your response, evaluate if you have gathered enough information to create a comprehensive architecture. You should have clear understanding of:
- Project type and purpose
- Key functional requirements
- Technical constraints and preferences
- Main features and capabilities
- Non-functional requirements (scalability, security, performance)

If you have gathered sufficient information:
1. Provide a brief summary of what you've learned (3-5 bullet points covering: project type, key features, technical stack preferences, and any constraints)
2. Thank the user for the information
3. Inform them that the requirements gathering is complete and they'll now move to the document upload section
4. End your message with the exact phrase: [REQUIREMENTS_COMPLETE]

If you need more information, continue asking clarifying questions (ONE question at a time)."""

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
                        "Requirements gathering complete! You can now proceed to Documents or generate architecture.")
                    st.rerun()
                else:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": ai_response
                    })
                    st.rerun()
    else:
        st.success("✅ Chat completed! Next step: Upload Documents")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Go to Documents", use_container_width=True, type="primary"):
                st.session_state.active_tab = 1
                st.rerun()
        with col2:
            if st.button("View Summary", use_container_width=True):
                st.session_state.active_tab = 2
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
            f"✅ {len(st.session_state.supporting_docs)} document(s) uploaded and ready")

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

                # Save to temp file with original filename
                temp_dir = tempfile.gettempdir()
                tmp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(tmp_path, 'wb') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())

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

    # Display processed documents - clean summary view
    if st.session_state.supporting_docs:
        st.markdown("---")
        st.markdown("### 📑 Uploaded Documents")

        # Summary table
        for idx, doc in enumerate(st.session_state.supporting_docs, 1):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.markdown(f"**{idx}. {doc.filename}**")
            with col2:
                st.markdown(f"*{doc.document_type.replace('_', ' ').title()}*")
            with col3:
                word_count = len(doc.content.split())
                st.markdown(f"~{word_count:,} words")
            with col4:
                if st.button("🗑️", key=f"remove_doc_{idx}", help=f"Remove {doc.filename}"):
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

    # Check if we have either chat OR documents (at least one is required)
    has_chat = st.session_state.chat_completed and len(st.session_state.chat_history) > 0
    has_docs = len(st.session_state.supporting_docs) > 0
    
    if not has_chat and not has_docs:
        st.warning(
            "⚠️ Please complete the chat OR upload documents before viewing the summary.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Go to Chat", type="primary", use_container_width=True):
                st.session_state.active_tab = 0
                st.rerun()
        with col2:
            if st.button("Go to Documents", type="primary", use_container_width=True):
                st.session_state.active_tab = 1
                st.rerun()
    else:
        # Display conversation summary (if available)
        if has_chat:
            st.subheader("📝 Chat Conversation Summary")
            with st.expander("View Full Conversation", expanded=False):
                for msg in st.session_state.chat_history:
                    role = "**You:**" if msg["role"] == "user" else "**AI:**"
                    st.markdown(f"{role} {msg['content']}")
                    st.markdown("---")
        else:
            st.info("ℹ️ No chat conversation - Requirements will be extracted from documents only")

        # Display documents summary (if available)
        if has_docs:
            st.subheader("📄 Supporting Documents")
            st.info(
                f"{len(st.session_state.supporting_docs)} document(s) uploaded")

            with st.expander("View Documents", expanded=False):
                for doc in st.session_state.supporting_docs:
                    st.markdown(f"**{doc.filename}** ({doc.document_type})")
                    st.caption(f"Size: {len(doc.content):,} characters")
                    st.markdown("---")
        else:
            st.info("ℹ️ No documents uploaded - Requirements will be extracted from chat only")

        
        # Show what data sources are available for extraction
        st.success(f"✅ Ready to extract requirements from: {'Chat' if has_chat else ''}{' + ' if has_chat and has_docs else ''}{'Documents' if has_docs else ''}")

        # Auto-extract requirements button
        if len(st.session_state.requirements) == 0:
            st.markdown("### 🤖 Auto-Extract Requirements")
            st.info(
                "Let AI analyze the chat and documents to extract structured requirements")

            if st.button("Auto-Extract Requirements from Chat & Documents", type="primary", use_container_width=True):
                with st.spinner("Analyzing conversation and documents to extract requirements..."):
                    # Verify we have data to extract from
                    has_chat = len(st.session_state.chat_history) > 0
                    has_docs = len(st.session_state.supporting_docs) > 0
                    
                    if not has_chat and not has_docs:
                        st.error("❌ No data available. Please complete the chat or upload documents first.")
                        st.stop()
                    
                    # Show what we're analyzing
                    st.info(f"📊 Analyzing: {len(st.session_state.chat_history)} chat messages + {len(st.session_state.supporting_docs)} document(s)")
                    
                    try:
                        # Use the generator's extract_requirements method
                        extracted_requirements = st.session_state.generator.extract_requirements(
                            chat_history=st.session_state.chat_history,
                            supporting_docs=st.session_state.supporting_docs if has_docs else None
                        )
                        
                        if extracted_requirements and len(extracted_requirements) > 0:
                            # Add to session state
                            st.session_state.requirements.extend(extracted_requirements)
                            
                            st.success(f"✅ Extracted {len(extracted_requirements)} requirements!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.warning("⚠️ No requirements could be extracted. Please add them manually below.")
                            
                    except Exception as e:
                        st.error(f"❌ Error extracting requirements: {str(e)}")
                        st.info("💡 Please try adding requirements manually below.")

        # Display extracted requirements
        if st.session_state.requirements:
            st.markdown("### ✅ Extracted Requirements")
            
            # Requirements quality metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Requirements", len(st.session_state.requirements))
            with col2:
                high_count = sum(1 for r in st.session_state.requirements if r.priority == "High")
                st.metric("High Priority", high_count)
            with col3:
                functional_count = sum(1 for r in st.session_state.requirements if r.category in ["Functional", "Business"])
                st.metric("Functional", functional_count)
            with col4:
                nonfunctional_count = sum(1 for r in st.session_state.requirements if r.category in ["Non-functional", "Technical", "Security"])
                st.metric("Non-Functional", nonfunctional_count)
            
            st.markdown("---")

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
        with st.expander("🔍 View Data Being Sent to AI Agent", expanded=False):
            st.markdown("### 📋 Input Data Summary")

            # Requirements section
            if st.session_state.requirements and len(st.session_state.requirements) > 0:
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
                st.info("No requirements defined")

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

                # Generate architecture using multi-stage approach
                # Pass requirements or empty list
                reqs_to_pass = st.session_state.requirements if st.session_state.requirements else []

                architecture = st.session_state.generator.generate_architecture_multistage(
                    requirements=reqs_to_pass,
                    supporting_docs=st.session_state.supporting_docs if st.session_state.supporting_docs else None,
                    chat_history=chat_history_text
                )

                st.session_state.architecture = architecture
                st.success("✅ Complete architecture generated successfully using multi-stage approach!")
                st.info("ℹ️ This architecture was generated in 3 stages to ensure all 10 sections are complete.")
                st.balloons()
                st.rerun()

    # Display generated architecture
    if st.session_state.architecture:
        st.markdown("---")
        st.markdown("### 🎉 Generated Architecture")
        
        # Architecture quality metrics
        st.markdown("#### 📊 Architecture Quality Analysis")
        
        arch_content = st.session_state.architecture
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            # Count major sections
            sections = len(re.findall(r'^#{1,3}\s+', arch_content, re.MULTILINE))
            st.metric("Sections", sections)
        with col2:
            # Count mermaid diagrams
            diagrams = len(re.findall(r'```mermaid', arch_content))
            st.metric("Diagrams", diagrams)
        with col3:
            # Count total words
            total_words = len(arch_content.split())
            st.metric("Total Words", f"{total_words:,}")
        with col4:
            # Validate all 10 REQUIRED sections are present
            required_sections = [
                'Executive Summary', 
                'Architecture Diagram', 
                'Architecture Pattern', 
                'System Component', 
                'Technology Stack',
                'Data Architecture',
                'Non-Functional',
                'Deployment',
                'Integration',
                'Trade-off'
            ]
            found_sections = sum(1 for section in required_sections if section.lower() in arch_content.lower())
            completeness = int((found_sections / len(required_sections)) * 100)
            st.metric("Completeness", f"{found_sections}/10 sections")
            
            # Show missing sections warning if any
            if found_sections < 10:
                st.warning(f"⚠️ Missing {10 - found_sections} required section(s). All 10 sections should be present.")

        st.markdown("---")

        # Download button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.download_button(
                label="📥 Download as Markdown",
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
                # Mermaid diagram - render directly without showing code
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
