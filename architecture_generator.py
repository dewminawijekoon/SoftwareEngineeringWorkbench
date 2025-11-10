"""Solution Architecture Generator using Gemini AI."""
import google.generativeai as genai
from typing import List, Optional
import json
from rich.console import Console
from rich.markdown import Markdown

from config import GEMINI_API_KEY, GEMINI_MODEL, GENERATION_CONFIG, SAFETY_SETTINGS
from models import UserRequirement, SupportingDocument, SolutionArchitecture

console = Console()


class ArchitectureGenerator:
    """Generate solution architecture using Gemini 2.5 Flash API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Architecture Generator.
        
        Args:
            api_key: Gemini API key (optional, defaults to config)
        """
        self.api_key = api_key or GEMINI_API_KEY
        
        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY in .env file")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config=GENERATION_CONFIG,
            safety_settings=SAFETY_SETTINGS
        )
        
        # Initialize chat session
        self.chat_session = None
    
    def start_chat_session(self):
        """Start a new chat session for interactive requirements gathering."""
        system_instruction = """You are an expert software architect and requirements analyst. 
        Your role is to:
        1. Ask clarifying questions about user requirements
        2. Understand technical and business constraints
        3. Identify key stakeholders and use cases
        4. Explore non-functional requirements (scalability, security, performance)
        
        Be thorough but concise. Ask one question at a time to gather complete information."""
        
        self.chat_session = self.model.start_chat(history=[])
        return self.chat_session
    
    def chat(self, message: str) -> str:
        """
        Send a message in the chat session.
        
        Args:
            message: User message
            
        Returns:
            AI response
        """
        if not self.chat_session:
            self.start_chat_session()
        
        response = self.chat_session.send_message(message)
        return response.text
    
    def generate_architecture(
        self,
        requirements: List[UserRequirement],
        supporting_docs: Optional[List[SupportingDocument]] = None,
        chat_history: Optional[str] = None
    ) -> str:
        """
        Generate solution architecture based on requirements and documents.
        
        Args:
            requirements: List of user requirements
            supporting_docs: Optional supporting documents
            chat_history: Optional chat history from requirements gathering
            
        Returns:
            Generated architecture as markdown text
        """
        # Build the prompt
        prompt = self._build_architecture_prompt(requirements, supporting_docs, chat_history)
        
        # Generate architecture
        response = self.model.generate_content(prompt)
        
        return response.text
    
    def _build_architecture_prompt(
        self,
        requirements: List[UserRequirement],
        supporting_docs: Optional[List[SupportingDocument]],
        chat_history: Optional[str]
    ) -> str:
        """Build a comprehensive prompt for architecture generation."""
        
        prompt_parts = [
            "# Task: Generate a Comprehensive Solution Architecture",
            "",
            "You are an expert solution architect. Based on the provided requirements and supporting documents, "
            "design a complete solution architecture with detailed reasoning for each decision.",
            "",
            "## Requirements:",
        ]
        
        # Add requirements
        for i, req in enumerate(requirements, 1):
            priority = f" [{req.priority}]" if req.priority else ""
            category = f" ({req.category})" if req.category else ""
            prompt_parts.append(f"{i}. {req.requirement}{priority}{category}")
        
        # Add supporting documents
        if supporting_docs:
            prompt_parts.extend([
                "",
                "## Supporting Documents:",
                ""
            ])
            for doc in supporting_docs:
                prompt_parts.extend([
                    f"### {doc.filename} ({doc.document_type})",
                    f"```",
                    doc.content[:2000] + ("..." if len(doc.content) > 2000 else ""),  # Limit content
                    f"```",
                    ""
                ])
        
        # Add chat history
        if chat_history:
            prompt_parts.extend([
                "",
                "## Requirements Gathering Discussion:",
                f"```",
                chat_history,
                f"```",
                ""
            ])
        
        # Add architecture generation instructions
        prompt_parts.extend([
            "",
            "## Instructions:",
            "",
            "Generate a comprehensive solution architecture that includes:",
            "",
            "1. **Executive Summary**",
            "   - Brief overview of the solution",
            "   - Key architectural decisions",
            "",
            "2. **Architecture Pattern & Reasoning**",
            "   - Chosen pattern (Microservices, Monolithic, Event-Driven, etc.)",
            "   - Detailed reasoning for this choice",
            "   - Alternative patterns considered and why they were rejected",
            "",
            "3. **System Components**",
            "   For each major component:",
            "   - Component name and purpose",
            "   - Suggested technology/framework",
            "   - Detailed reasoning for technology choice",
            "   - Interactions with other components",
            "",
            "4. **Technology Stack**",
            "   - Frontend technologies with reasoning",
            "   - Backend technologies with reasoning",
            "   - Database choices with reasoning",
            "   - Infrastructure and DevOps tools",
            "",
            "5. **Data Architecture**",
            "   - Data storage strategy",
            "   - Data flow between components",
            "   - Caching strategy",
            "",
            "6. **Non-Functional Requirements**",
            "   - Scalability approach and reasoning",
            "   - Security measures and reasoning",
            "   - Performance optimization strategies",
            "   - Reliability and fault tolerance",
            "",
            "7. **Deployment Strategy**",
            "   - Deployment architecture",
            "   - CI/CD pipeline approach",
            "   - Environment strategy",
            "",
            "8. **Integration Points**",
            "   - External system integrations",
            "   - API design approach",
            "   - Authentication/Authorization strategy",
            "",
            "9. **Trade-offs and Decisions**",
            "   - Key trade-offs made",
            "   - Risks and mitigation strategies",
            "   - Future scalability considerations",
            "",
            "10. **Architecture Diagram Description**",
            "    - Textual description of how components connect",
            "    - Data flow description",
            "",
            "## Output Format:",
            "Provide the architecture in well-structured Markdown format with clear headings, "
            "bullet points, and detailed reasoning for EVERY major decision. Be specific about "
            "technologies and explain WHY each choice was made based on the requirements."
        ])
        
        return "\n".join(prompt_parts)
    
    def export_architecture(self, architecture_text: str, output_file: str):
        """
        Export the generated architecture to a file.
        
        Args:
            architecture_text: Generated architecture text
            output_file: Output file path
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(architecture_text)
        
        console.print(f"[green]✓[/green] Architecture exported to: {output_file}")
