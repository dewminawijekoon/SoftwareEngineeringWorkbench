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
    st.session_state.active_tab = 0  # 0=Chat, 1=Summary, 2=Documents, 3=Architecture

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
    tabs = ["Chat", "Summary", "Documents", "Architecture"]
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
    reqs_status = "✅" if len(st.session_state.requirements) > 0 else "⏳"
    docs_status = "✅" if len(st.session_state.supporting_docs) > 0 else "⏳"
    arch_status = "✅" if st.session_state.architecture else "⏳"
    
    st.markdown(f"{chat_status} Chat Completed")
    st.markdown(f"{reqs_status} Requirements")
    st.markdown(f"{docs_status} Documents")
    st.markdown(f"{arch_status} Architecture Generated")
    
    st.markdown("---")
    
    # Copyright
    st.caption("© 2025 84H. All rights reserved.")

# Main content - Display selected tab content
if st.session_state.chat_completed and st.session_state.active_tab == 0:
    st.session_state.active_tab = 1  # Auto-move to Summary after chat
    
if len(st.session_state.requirements) > 0 and st.session_state.active_tab == 1:
    # Allow staying on summary or moving forward
    pass

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
            user_input = st.chat_input("Type your response (or 'done' to finish)...")
            
            if user_input:
                # Check if user manually wants to finish
                if user_input.lower() == 'done':
                    st.session_state.chat_completed = True
                    st.session_state.active_tab = 1
                    st.balloons()
                    st.success("Chat completed! Moving to Summary...")
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
                        ai_response = ai_response.replace("[REQUIREMENTS_COMPLETE]", "").strip()
                        st.session_state.chat_completed = True
                        
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": ai_response
                        })
                        
                        st.balloons()
                        st.success("Requirements gathering complete! Moving to Summary...")
                        st.session_state.active_tab = 1
                        st.rerun()
                    else:
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": ai_response
                        })
                        
                        st.rerun()
    else:
        st.info("Chat completed. Moving to Summary tab...")
        st.markdown("### Quick Navigation")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Go to Summary", use_container_width=True):
                st.session_state.active_tab = 1
                st.rerun()
        with col2:
            if st.button("Upload Documents", use_container_width=True):
                st.session_state.active_tab = 2
                st.rerun()
        with col3:
            if st.button("Generate Architecture", use_container_width=True):
                st.session_state.active_tab = 3
                st.rerun()

# Tab 1: Summary
elif active_tab == 1:
    st.header("Chat Summary & Requirements")
    
    if not st.session_state.chat_history:
        st.info("Start the chat first to see a summary here")
    else:
        # Display conversation summary
        st.subheader("Conversation Summary")
        
        with st.expander("View Full Conversation", expanded=False):
            for msg in st.session_state.chat_history:
                role = "**You:**" if msg["role"] == "user" else "**AI:**"
                st.markdown(f"{role} {msg['content']}")
                st.markdown("---")
        
        # Extract requirements button
        if st.session_state.chat_completed and len(st.session_state.requirements) == 0:
            st.markdown("### Extract Requirements")
            
            if st.button("Auto-Extract Requirements from Chat", type="primary"):
                with st.spinner("Analyzing conversation and extracting requirements..."):
                    # Build chat history text
                    chat_text = "\n".join([
                        f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}"
                        for m in st.session_state.chat_history
                    ])
                    
                    # Ask AI to extract requirements
                    extraction_prompt = f"""Based on this conversation, extract structured requirements.
                    For each requirement, provide:
                    - requirement: clear statement
                    - priority: High/Medium/Low (infer from context)
                    - category: Functional/Non-functional/Technical/Business
                    
                    Return ONLY a valid JSON array with this exact format:
                    [{{"requirement": "...", "priority": "High", "category": "Functional"}}]
                    
                    Conversation:
                    {chat_text}
                    """
                    
                    response = st.session_state.generator.chat(extraction_prompt)
                    
                    # Try to parse JSON
                    import json
                    import re
                    
                    try:
                        # Extract JSON array from response
                        json_match = re.search(r'\[.*\]', response, re.DOTALL)
                        if json_match:
                            requirements_data = json.loads(json_match.group())
                            
                            for req_data in requirements_data:
                                st.session_state.requirements.append(
                                    UserRequirement(
                                        requirement=req_data.get('requirement', ''),
                                        priority=req_data.get('priority', 'Medium'),
                                        category=req_data.get('category', 'Functional')
                                    )
                                )
                            
                            st.success(f"Extracted {len(requirements_data)} requirements!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Could not extract requirements. Please add them manually below.")
                    except Exception as e:
                        st.error(f"Error parsing requirements: {e}")
        
        # Display extracted requirements
        if st.session_state.requirements:
            st.markdown("### Extracted Requirements")
            
            for i, req in enumerate(st.session_state.requirements, 1):
                priority_badge = {
                    "High": "HIGH",
                    "Medium": "MEDIUM",
                    "Low": "LOW"
                }.get(req.priority, "N/A")
                
                css_class = f"requirement-item-{req.priority.lower()}" if req.priority and req.priority in ["High", "Medium", "Low"] else "requirement-item"
                
                st.markdown(f"""
                <div class="{css_class}">
                    <strong>{i}. {req.requirement}</strong><br>
                    <small>Priority: {priority_badge} | Category: {req.category or 'N/A'}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Navigation buttons
        if st.session_state.requirements:
            st.markdown("### Next Steps")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Upload Supporting Documents", use_container_width=True, type="secondary"):
                    st.session_state.active_tab = 2
                    st.rerun()
            with col2:
                if st.button("Generate Architecture Now", use_container_width=True, type="primary"):
                    st.session_state.active_tab = 3
                    st.rerun()
        
        st.markdown("---")
        
        # Manual requirement addition
        st.markdown("### Add Additional Requirements")
        
        with st.form("add_requirement_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                req_text = st.text_area("Requirement Description", height=100)
                priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            
            with col2:
                category = st.selectbox("Category", 
                    ["Functional", "Non-functional", "Technical", "Business", "Security"])
                
                submitted = st.form_submit_button("Add Requirement", type="primary")
                
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

# Tab 2: Documents Upload
elif active_tab == 2:
    st.header("Supporting Documents")
    st.markdown("Upload any supporting documents (PDF, DOCX, TXT, MD)")
    
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
                        st.success(f"{uploaded_file.name} processed successfully")
                    else:
                        st.info(f"{uploaded_file.name} already added")
                    
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {e}")
                finally:
                    # Clean up temp file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            status_text.text("All documents processed!")
            st.success("Documents ready! You can now generate the architecture.")
            st.rerun()
    
    # Display processed documents
    if st.session_state.supporting_docs:
        st.markdown("### Processed Documents")
        
        for doc in st.session_state.supporting_docs:
            with st.expander(f"{doc.filename} ({doc.document_type})"):
                st.text_area(
                    "Content Preview",
                    value=doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                    height=200,
                    disabled=True
                )
                st.caption(f"Total characters: {len(doc.content)}")
    
    # Navigation to architecture
    if st.session_state.supporting_docs or st.session_state.requirements:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Proceed to Generate Architecture", use_container_width=True, type="primary"):
                st.session_state.active_tab = 3
                st.rerun()

# Tab 3: Architecture Generation
elif active_tab == 3:
    st.header("Generate Solution Architecture")
    
    # Check prerequisites
    can_generate = len(st.session_state.requirements) > 0
    
    if not can_generate:
        st.warning("Please add at least one requirement before generating architecture")
    else:
        st.success(f"Ready to generate! Found {len(st.session_state.requirements)} requirements")
    
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
                    architecture = st.session_state.generator.generate_architecture(
                        requirements=st.session_state.requirements,
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
                    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                    <script>mermaid.initialize({{startOnLoad:true}});</script>
                    <div class="mermaid">
                    {part}
                    </div>
                    """
                    components.html(mermaid_html, height=400)
                except:
                    st.info("Mermaid diagram code shown above. Copy to visualize in a Mermaid renderer.")
