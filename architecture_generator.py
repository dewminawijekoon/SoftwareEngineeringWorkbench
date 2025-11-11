"""Solution Architecture Generator using Gemini AI."""
import google.generativeai as genai
from typing import List, Optional
import json
from rich.console import Console
from rich.markdown import Markdown
import re

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
                    doc.content[:2000] + ("..." if len(doc.content) > 2000 else ""),
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
            "2. **Architecture Diagrams (Mermaid)**",
            "   - Create at least 2 diagrams: System Architecture and Deployment Architecture",
            "   - ONLY use these valid Mermaid diagram types:",
            "     * 'graph TD' (top-down flowchart)",
            "     * 'graph LR' (left-right flowchart)",
            "     * 'flowchart TD' or 'flowchart LR'",
            "     * 'sequenceDiagram' (for interaction flows)",
            "   - DO NOT use: C4Context, C4Container, C4_Context, C4_Container, or any C4 syntax",
            "   - Use standard Mermaid node shapes:",
            "     * [Rectangle] for components",
            "     * [(Database)] for databases",
            "     * {{Diamond}} for decision points",
            "     * ([Rounded]) for start/end",
            "   - Use arrows for relationships:",
            "     * --> (solid arrow)",
            "     * -.-> (dotted arrow for monitoring/logging)",
            "     * -->|label| (labeled arrow)",
            "   - For subgraphs with spaces in names, use this syntax:",
            "     * subgraph identifier[\"Display Name With Spaces\"]",
            "     * Example: subgraph BackendServices[\"Backend Services\"]",
            "   - **CRITICAL NODE NAMING RULES:**",
            "     * Node IDs must be simple (e.g., CDN, API, DB1)",
            "     * Node labels should avoid parentheses () inside subgraphs",
            "     * Use hyphens or 'via' instead: 'CDN - CloudFront' not 'CDN (CloudFront)'",
            "     * Keep labels simple and descriptive",
            "",
            "3. **Architecture Pattern & Reasoning**",
            "   - Chosen pattern (Microservices, Monolithic, Event-Driven, etc.)",
            "   - Detailed reasoning for this choice",
            "   - Alternative patterns considered and why they were rejected",
            "",
            "4. **System Components**",
            "   For each major component:",
            "   - Component name and purpose",
            "   - Suggested technology/framework",
            "   - Detailed reasoning for technology choice",
            "   - Interactions with other components",
            "",
            "5. **Technology Stack**",
            "   - Frontend technologies with reasoning",
            "   - Backend technologies with reasoning",
            "   - Database choices with reasoning",
            "   - Infrastructure and DevOps tools",
            "",
            "6. **Data Architecture**",
            "   - Data storage strategy",
            "   - Data flow between components",
            "   - Caching strategy",
            "",
            "7. **Non-Functional Requirements**",
            "   - Scalability approach and reasoning",
            "   - Security measures and reasoning",
            "   - Performance optimization strategies",
            "   - Reliability and fault tolerance",
            "",
            "8. **Deployment Strategy**",
            "   - Deployment architecture",
            "   - CI/CD pipeline approach",
            "   - Environment strategy",
            "",
            "9. **Integration Points**",
            "   - External system integrations",
            "   - API design approach",
            "   - Authentication/Authorization strategy",
            "",
            "10. **Trade-offs and Decisions**",
            "    - Key trade-offs made",
            "    - Risks and mitigation strategies",
            "    - Future scalability considerations",
            "",
            "## CRITICAL Output Format Requirements:",
            "",
            "**For Mermaid Diagrams - VERY IMPORTANT:**",
            "1. Start each diagram with a markdown heading: ### System Architecture Diagram",
            "2. On the next line, start the code block with: ```mermaid",
            "3. On the next line, specify ONLY one of these diagram types:",
            "   - graph TD",
            "   - graph LR", 
            "   - flowchart TD",
            "   - flowchart LR",
            "   - sequenceDiagram",
            "4. Then add your diagram code",
            "5. End with three backticks: ```",
            "6. NEVER use C4Context, C4Container, C4_Context, C4_Container, or any C4 syntax",
            "7. For subgraphs, use: subgraph identifier[\"Display Name\"]",
            "8. **AVOID parentheses in node labels, especially inside subgraphs**",
            "",
            "**Valid Diagram Example Structure:**",
            "### System Architecture Diagram",
            "```mermaid",
            "graph TD",
            "    User[User]",
            "    Browser[Web Browser]",
            "    CDN[CDN - CloudFront]",
            "    LB[Load Balancer]",
            "    ",
            "    subgraph BackendServices[\"Backend Services\"]",
            "        API[API Gateway]",
            "        Auth[Auth Service]",
            "        UserSvc[User Service]",
            "    end",
            "    ",
            "    subgraph DataLayer[\"Data Layer\"]",
            "        DB[(PostgreSQL Database)]",
            "        Cache[(Redis Cache)]",
            "    end",
            "    ",
            "    User --> Browser",
            "    Browser -->|HTTPS| CDN",
            "    Browser -->|API Calls| LB",
            "    LB --> API",
            "    API --> Auth",
            "    API --> UserSvc",
            "    Auth --> DB",
            "    UserSvc --> DB",
            "    API --> Cache",
            "```",
            "",
            "**General Format:**",
            "- Use clear markdown headings (##, ###)",
            "- Use bullet points and numbered lists appropriately",
            "- Provide detailed reasoning for EVERY major decision",
            "- Be specific about technologies and explain WHY each choice was made"
        ])
        
        return "\n".join(prompt_parts)
    
    def export_architecture(self, architecture_text: str, output_file: str):
        """
        Export the generated architecture to a file with Mermaid diagrams.
        
        Args:
            architecture_text: Generated architecture text
            output_file: Output file path
        """
        # Enhance the markdown with Mermaid instructions
        enhanced_text = self._add_mermaid_instructions(architecture_text)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(enhanced_text)
        
        console.print(f"[green]✓[/green] Architecture exported to: {output_file}")
        console.print("\n[cyan]📊 Viewing Mermaid Diagrams:[/cyan]")
        console.print("  • GitHub/GitLab: Diagrams render automatically")
        console.print("  • VS Code: Install 'Markdown Preview Mermaid Support' extension")
        console.print("  • Online: https://mermaid.live (paste your Mermaid code)")
        console.print("  • Export images: Use Mermaid CLI or online tools")
    
    def _add_mermaid_instructions(self, architecture_text: str) -> str:
        """
        Add instructions for viewing Mermaid diagrams at the beginning of the file.
        
        Args:
            architecture_text: Original architecture text
            
        Returns:
            Enhanced text with viewing instructions
        """
        instructions = """# Solution Architecture Document

> **📊 Viewing Diagrams**: This document contains Mermaid diagrams that render in:
> - GitHub, GitLab, Bitbucket (automatic)
> - VS Code (install "Markdown Preview Mermaid Support" extension)
> - Online viewers: [mermaid.live](https://mermaid.live)
> - Export to PNG/SVG: Use [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli)

---

"""
        return instructions + architecture_text
