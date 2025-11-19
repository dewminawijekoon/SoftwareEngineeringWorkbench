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
            raise ValueError(
                "Gemini API key not found. Set GEMINI_API_KEY in .env file")

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
        system_instruction = """You are Ada Chen, a Senior Solution Architect and Requirements Analyst with over 15 years of experience in enterprise software design. 
        
        Your role is to:
        1. Ask clarifying questions about user requirements
        2. Understand technical and business constraints
        3. Identify key stakeholders and use cases
        4. Explore non-functional requirements (scalability, security, performance)
        
        When introducing yourself, say: "Hello! I'm Ada Chen, Senior Solution Architect. I'll be working with you today to gather requirements and understand your vision for this project. My goal is to ask the right questions so we can design a solution that perfectly fits your needs."

        
        CRITICAL RULE: Ask ONLY ONE question at a time. 
        Wait for the user's answer before asking the next question.
        Keep questions simple and focused on one topic.

        Never ask multiple questions in a single response."""

        self.chat_session = self.model.start_chat(history=[system_instruction])
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

    def extract_requirements(
        self,
        chat_history: List[dict],
        supporting_docs: Optional[List[SupportingDocument]] = None
    ) -> List[UserRequirement]:
        """
        Extract structured requirements from chat history and documents.

        Args:
            chat_history: List of chat messages with 'role' and 'content'
            supporting_docs: Optional supporting documents

        Returns:
            List of extracted UserRequirement objects
        """
        # Build chat text
        chat_text = ""
        if chat_history and len(chat_history) > 0:
            chat_text = "\n".join([
                f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}"
                for m in chat_history
            ])

        # Build documents context
        docs_text = ""
        if supporting_docs and len(supporting_docs) > 0:
            docs_text = "\n\n## SUPPORTING DOCUMENTS (Scraped Information):\n"
            for doc in supporting_docs:
                # Use up to 5000 chars per doc for better context
                content_excerpt = doc.content[:5000]
                if len(doc.content) > 5000:
                    content_excerpt += "\n... (content truncated)"
                docs_text += f"\n### Document: {doc.filename} ({doc.document_type})\n{content_excerpt}\n"

        # Build extraction prompt
        extraction_prompt = f"""Analyze the chat conversation AND the scraped document information below to extract comprehensive structured requirements.

**Your Task:**
1. Extract requirements from the user's conversation (if provided)
2. Extract additional requirements from the scraped document content (if provided)
3. Combine and deduplicate requirements
4. For each requirement, infer priority based on emphasis/context
5. Extract at least 5-15 requirements covering functional, non-functional, and technical aspects

**Output Format:**
Return ONLY a valid JSON array with this exact format (no other text):
[{{"requirement": "clear statement", "priority": "High|Medium|Low", "category": "Functional|Non-functional|Technical|Business|Security"}}]

**Prioritization Guidelines:**
- High: Core features, security requirements, critical constraints
- Medium: Important features, performance needs, integration requirements  
- Low: Nice-to-have features, future considerations

**Category Guidelines:**
- Functional: User-facing features, business logic
- Non-functional: Performance, scalability, reliability
- Technical: Technology choices, architecture constraints
- Security: Authentication, authorization, data protection
- Business: Business rules, compliance, regulations

---

{f"## CHAT CONVERSATION:\n{chat_text}\n" if chat_text else ""}

{docs_text if docs_text else ""}

---

IMPORTANT: Return ONLY the JSON array, nothing else. Extract comprehensive requirements from ALL provided sources above."""

        # Get AI response
        response = self.model.generate_content(extraction_prompt)
        
        # Parse JSON response
        import json
        import re
        
        requirements = []
        try:
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                requirements_data = json.loads(json_match.group())
                
                for req_data in requirements_data:
                    requirements.append(
                        UserRequirement(
                            requirement=req_data.get('requirement', ''),
                            priority=req_data.get('priority', 'Medium'),
                            category=req_data.get('category', 'Functional')
                        )
                    )
        except Exception as e:
            console.print(f"[red]Error parsing requirements: {e}[/red]")
        
        return requirements

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
        prompt = self._build_architecture_prompt(
            requirements, supporting_docs, chat_history)

        # Generate architecture
        response = self.model.generate_content(prompt)

        return response.text

    def generate_architecture_multistage(
        self,
        requirements: List[UserRequirement],
        supporting_docs: Optional[List[SupportingDocument]] = None,
        chat_history: Optional[str] = None
    ) -> str:
        """
        Generate solution architecture using multi-stage approach to avoid token limits.
        
        Stage 1: Generate Executive Summary + Architecture Diagrams
        Stage 2: Generate Architecture Details (Sections 3-7)
        Stage 3: Generate Implementation Details (Sections 8-10)
        
        Args:
            requirements: List of user requirements
            supporting_docs: Optional supporting documents
            chat_history: Optional chat history from requirements gathering

        Returns:
            Complete architecture document as markdown text
        """
        console.print("[cyan]Using multi-stage generation to ensure complete output...[/cyan]")
        
        # Build context that will be reused across all stages
        context = self._build_context_section(requirements, supporting_docs, chat_history)
        
        # Stage 1: Executive Summary + Diagrams
        console.print("[cyan]Stage 1/3: Generating Executive Summary and Architecture Diagrams...[/cyan]")
        stage1 = self._generate_stage1_summary_diagrams(context)
        
        # Stage 2: Architecture Details (Patterns, Components, Tech Stack, Data, NFRs)
        console.print("[cyan]Stage 2/3: Generating Architecture Details (Sections 3-7)...[/cyan]")
        stage2 = self._generate_stage2_architecture_details(context, stage1)
        
        # Stage 3: Implementation Details (Deployment, Integration, Trade-offs)
        console.print("[cyan]Stage 3/3: Generating Implementation Details (Sections 8-10)...[/cyan]")
        stage3 = self._generate_stage3_implementation_details(context, stage1, stage2)
        
        # Combine all stages
        console.print("[green]✓ All stages complete. Combining document...[/green]")
        full_document = f"{stage1}\n\n{stage2}\n\n{stage3}"
        
        # Post-process to fix any Mermaid syntax errors
        console.print("[cyan]Post-processing: Fixing Mermaid syntax...[/cyan]")
        full_document = self._fix_mermaid_syntax(full_document)
        console.print("[green]✓ Mermaid syntax validated and fixed.[/green]")
        
        return full_document

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
        ]

        # Add requirements if available
        if requirements and len(requirements) > 0:
            prompt_parts.append("## Requirements:")
            prompt_parts.append("")
            for i, req in enumerate(requirements, 1):
                priority = f" [{req.priority}]" if req.priority else ""
                category = f" ({req.category})" if req.category else ""
                prompt_parts.append(
                    f"{i}. {req.requirement}{priority}{category}")
        else:
            prompt_parts.extend([
                "## Requirements:",
                "",
                "No explicit requirements provided. Please extract and infer requirements from the chat history and supporting documents below.",
                ""
            ])

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
                    doc.content[:2000] +
                    ("..." if len(doc.content) > 2000 else ""),
                    f"```",
                    ""
                ])

        # Add chat history ONLY if no explicit requirements (optimization to save tokens)
        # If requirements are already extracted, chat history is redundant
        if chat_history and (not requirements or len(requirements) == 0):
            prompt_parts.extend([
                "",
                "## Requirements Gathering Discussion:",
                f"```",
                chat_history,
                f"```",
                ""
            ])
        elif chat_history and requirements and len(requirements) > 0:
            # If we have requirements, just add a brief note that they were extracted from chat
            prompt_parts.extend([
                "",
                "## Note:",
                f"The above requirements were extracted from a detailed requirements gathering conversation with the user.",
                ""
            ])

        # Add architecture generation instructions
        prompt_parts.extend([
            "",
            "## ⚠️ CRITICAL MANDATORY INSTRUCTIONS - NON-NEGOTIABLE:",
            "",
            "You MUST generate a COMPLETE architecture document with ALL 10 sections listed below.",
            "This is MANDATORY and NON-NEGOTIABLE.",
            "",
            "**MINIMUM OUTPUT LENGTH REQUIREMENT:**",
            "- Your response must be AT LEAST 3,000 words (approximately 4,000-5,000 tokens)",
            "- Each section must have substantial, detailed content (100-200 words minimum per section)",
            "- DO NOT stop generating until ALL 10 sections are complete",
            "- DO NOT produce abbreviated or summary versions",
            "- If you skip ANY section, your response will be considered INCOMPLETE and REJECTED",
            "",
            "**Token Budget:** You have 8,192 output tokens available. USE THEM ALL if needed.",
            "Do NOT stop early. Generate comprehensive, detailed content for every section.",
            "",
            "## Required Architecture Document Structure (ALL 10 SECTIONS MANDATORY):",
            "",
            "### 1. Executive Summary (MANDATORY - DO NOT SKIP)",
            "Write a comprehensive executive summary that includes:",
            "   - Brief overview of the solution (what problem it solves)",
            "   - Key architectural decisions and their rationale",
            "   - High-level technology choices",
            "Minimum 100 words required.",
            "",
            "### 2. Architecture Diagrams (MANDATORY - MINIMUM 2 DIAGRAMS REQUIRED)",
            "   - Create at least 2 diagrams: System Architecture and Deployment Architecture",
            "",
            "   **CRITICAL MERMAID SYNTAX RULES - MUST FOLLOW EXACTLY:**",
            "",
            "   1. Diagram Type: ONLY use 'graph TD' or 'flowchart TD'",
            "   2. NO C4 syntax: Never use C4Context, C4Container, etc.",
            "   3. **Node Label Format - EXTREMELY IMPORTANT:**",
            "      - **EVERY node label MUST be wrapped in brackets: NodeID[Label]**",
            "      - **Node IDs must be single words (no spaces): VPC, PublicSubnet, DB1**",
            "      - **WRONG Examples - CAUSE PARSE ERRORS:**",
            "        * SProvider    Core Backend Microservice ❌",
            "        * VPC --> Public Subnet ❌",
            "        * Public Subnet --> Private Subnet ❌",
            "      - **CORRECT Examples:**",
            "        * SProvider[Core Backend Microservice] ✅",
            "        * VPC --> PublicSubnet[Public Subnet] ✅",
            "        * PublicSubnet[Public Subnet] --> PrivateSubnet[Private Subnet] ✅",
            "   4. **NEVER use parentheses () in node labels** - This causes parse errors!",
            "   5. **NEVER use spaces in node IDs** - Use camelCase or underscores",
            "",
            "   Valid node formats:",
            "     * NodeID[Simple Label] - rectangle (BRACKETS REQUIRED)",
            "     * NodeID[(Database Label)] - database shape (parentheses only for shape)",
            "     * NodeID{{Decision}} - diamond",
            "     * NodeID([Start/End]) - rounded (parentheses only for shape)",
            "",
            "   CORRECT examples:",
            "     * WebApp[Web Application]",
            "     * API[API Gateway - Node.js]  (use hyphen for tech)",
            "     * DB1[(User Database)]",
            "     * Cache[(Redis Cache)]",
            "     * LoadBalancer[Load Balancer] --> AppServer[Application Server]",
            "",
            "   INCORRECT examples (NEVER DO THIS):",
            "     * WebApp[Web Application (React)]  ❌ CAUSES PARSE ERROR",
            "     * API[API Gateway (Express)]       ❌ CAUSES PARSE ERROR",
            "     * DB[Database (PostgreSQL)]        ❌ CAUSES PARSE ERROR",
            "     * Load Balancer --> App Server     ❌ CAUSES PARSE ERROR (spaces in node IDs)",
            "",
            "   Connection syntax:",
            "     * NodeA --> NodeB  (simple arrow)",
            "     * NodeA -->|HTTPS| NodeB  (labeled arrow)",
            "     * NodeA -.-> NodeB  (dotted arrow)",
            "",
            "   Subgraph syntax:",
            "     * subgraph BackendSvc[\"Backend Services\"]",
            "     * ... nodes ...",
            "     * end",
            "",
            "### 3. Architecture Pattern & Reasoning (MANDATORY - DO NOT SKIP)",
            "You MUST include this section with:",
            "   - Chosen pattern (Microservices, Monolithic, Event-Driven, Layered, etc.)",
            "   - Detailed reasoning for this choice (at least 3 reasons)",
            "   - Alternative patterns considered and why they were rejected",
            "Minimum 150 words required.",
            "",
            "### 4. System Components (MANDATORY - DO NOT SKIP)",
            "You MUST detail all major components. For EACH component include:",
            "   - Component name and clear purpose",
            "   - Suggested technology/framework with version",
            "   - Detailed reasoning for technology choice",
            "   - Interactions with other components",
            "List at least 5 major components. Minimum 200 words required.",
            "",
            "### 5. Technology Stack (MANDATORY - DO NOT SKIP)",
            "You MUST provide complete technology stack:",
            "   - Frontend technologies with detailed reasoning",
            "   - Backend technologies with detailed reasoning",
            "   - Database choices with detailed reasoning",
            "   - Infrastructure and DevOps tools",
            "Minimum 150 words required.",
            "",
            "### 6. Data Architecture (MANDATORY - DO NOT SKIP)",
            "You MUST explain data architecture:",
            "   - Data storage strategy and database schema approach",
            "   - Data flow between components with examples",
            "   - Caching strategy and cache invalidation",
            "Minimum 150 words required.",
            "",
            "### 7. Non-Functional Requirements (MANDATORY - DO NOT SKIP)",
            "You MUST address all non-functional requirements:",
            "   - Scalability approach with specific strategies",
            "   - Security measures with detailed reasoning",
            "   - Performance optimization strategies",
            "   - Reliability and fault tolerance mechanisms",
            "Minimum 200 words required.",
            "",
            "### 8. Deployment Strategy (MANDATORY - DO NOT SKIP)",
            "You MUST provide deployment details:",
            "   - Deployment architecture (cloud/on-prem/hybrid)",
            "   - CI/CD pipeline approach with tools",
            "   - Environment strategy (dev/staging/prod)",
            "Minimum 150 words required.",
            "",
            "### 9. Integration Points (MANDATORY - DO NOT SKIP)",
            "You MUST describe all integration points:",
            "   - External system integrations",
            "   - API design approach (REST/GraphQL/gRPC)",
            "   - Authentication/Authorization strategy",
            "Minimum 150 words required.",
            "",
            "### 10. Trade-offs and Decisions (MANDATORY - DO NOT SKIP)",
            "You MUST document key decisions:",
            "    - Key trade-offs made with justification",
            "    - Risks identified and mitigation strategies",
            "    - Future scalability considerations",
            "Minimum 150 words required.",
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
            "- Be specific about technologies and explain WHY each choice was made",
            "",
            "## ⚠️ FINAL VALIDATION CHECKLIST - YOU MUST COMPLETE THIS:",
            "",
            "Before submitting, COUNT and VERIFY all sections are present with substantial content:",
            "",
            "□ 1. Executive Summary (with overview and key decisions) - MINIMUM 100 WORDS",
            "□ 2. Architecture Diagrams (MINIMUM 2 complete Mermaid diagrams)",
            "□ 3. Architecture Pattern & Reasoning (with alternatives) - MINIMUM 150 WORDS",
            "□ 4. System Components (at least 5 components detailed) - MINIMUM 200 WORDS",
            "□ 5. Technology Stack (frontend, backend, database, DevOps) - MINIMUM 150 WORDS",
            "□ 6. Data Architecture (storage, flow, caching) - MINIMUM 150 WORDS",
            "□ 7. Non-Functional Requirements (scalability, security, performance) - MINIMUM 200 WORDS",
            "□ 8. Deployment Strategy (architecture, CI/CD, environments) - MINIMUM 150 WORDS",
            "□ 9. Integration Points (external systems, APIs, auth) - MINIMUM 150 WORDS",
            "□ 10. Trade-offs and Decisions (trade-offs, risks, future) - MINIMUM 150 WORDS",
            "",
            "STOP AND COUNT: Did you include ALL 10 sections above? If NO, GO BACK and ADD missing sections NOW.",
            "Your response will be REJECTED if ANY section is missing or has insufficient content.",
            "This is MANDATORY and NON-NEGOTIABLE.",
            "",
            "## ⚠️ IMPORTANT GENERATION REMINDER:",
            "",
            "DO NOT STOP WRITING until you have completed ALL 10 sections with full detail.",
            "You have a generous token budget (8,192 tokens). Use it to create a COMPREHENSIVE document.",
            "Target: 3,000-4,000 words minimum for the complete architecture document.",
            "This means approximately:",
            "- Executive Summary: 100-150 words",
            "- Architecture Diagrams: 2-3 detailed Mermaid diagrams",
            "- Architecture Pattern: 150-200 words",
            "- System Components: 200-300 words (5+ components)",
            "- Technology Stack: 150-200 words",
            "- Data Architecture: 150-200 words",
            "- Non-Functional Requirements: 200-300 words",
            "- Deployment Strategy: 150-200 words",
            "- Integration Points: 150-200 words",
            "- Trade-offs and Decisions: 150-200 words",
            "",
            "CONTINUE WRITING until you have provided SUBSTANTIAL, DETAILED content for every section.",
            "Do NOT produce a shortened or summarized version."
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

        console.print(
            f"[green]✓[/green] Architecture exported to: {output_file}")
        console.print("\n[cyan]📊 Viewing Mermaid Diagrams:[/cyan]")
        console.print("  • GitHub/GitLab: Diagrams render automatically")
        console.print(
            "  • VS Code: Install 'Markdown Preview Mermaid Support' extension")
        console.print(
            "  • Online: https://mermaid.live (paste your Mermaid code)")
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

    def _build_context_section(
        self,
        requirements: List[UserRequirement],
        supporting_docs: Optional[List[SupportingDocument]],
        chat_history: Optional[str]
    ) -> str:
        """Build the context section that will be reused across all generation stages."""
        context_parts = []
        
        # Add requirements
        if requirements and len(requirements) > 0:
            context_parts.append("## Requirements:")
            context_parts.append("")
            for i, req in enumerate(requirements, 1):
                priority = f" [{req.priority}]" if req.priority else ""
                category = f" ({req.category})" if req.category else ""
                context_parts.append(f"{i}. {req.requirement}{priority}{category}")
            context_parts.append("")
        
        # Add supporting documents (concise version)
        if supporting_docs:
            context_parts.append("## Supporting Documents:")
            context_parts.append("")
            for doc in supporting_docs:
                context_parts.append(f"### {doc.filename}")
                # Limit document content to first 2000 chars per doc to save tokens
                content_preview = doc.content[:2000] + "..." if len(doc.content) > 2000 else doc.content
                context_parts.append(content_preview)
                context_parts.append("")
        
        return "\n".join(context_parts)

    def _generate_stage1_summary_diagrams(self, context: str) -> str:
        """Stage 1: Generate Executive Summary and Architecture Diagrams."""
        prompt = f"""You are an expert solution architect. Generate the first two sections of a comprehensive architecture document.

{context}

Generate ONLY these sections with FULL detail:

## 1. Executive Summary
Write a comprehensive executive summary (150-200 words) that includes:
- Brief overview of the solution (what problem it solves)
- Key architectural decisions and their rationale
- High-level technology choices
- Compliance and security considerations

## 2. Architecture Diagrams
Create AT LEAST 2 detailed Mermaid diagrams:

### System Architecture Diagram
Use `graph TD` or `flowchart TD`. Include:
- User interfaces (web/mobile)
- Frontend components
- API Gateway
- Backend services (at least 5-7 microservices)
- Databases and caching layers
- External integrations
- Use subgraphs for logical groupings

### Deployment Architecture Diagram
Use `graph TD` or `flowchart TD`. Include:
- CI/CD pipeline components
- Cloud infrastructure (VPC, subnets, load balancers)
- Kubernetes/container orchestration
- Database instances (multi-AZ)
- Monitoring and logging
- Security components (WAF, secrets management)

**CRITICAL Mermaid Syntax Rules - MUST FOLLOW EXACTLY:**

1. **Diagram Type**: ONLY use `graph TD` or `flowchart TD` at the start
2. **NO C4 Syntax**: Never use C4Context, C4Container, etc.
3. **Node Syntax Rules - EXTREMELY IMPORTANT:**
   - **EVERY node label MUST be wrapped in brackets: `NodeID[Label]`**
   - **Node IDs must be single alphanumeric words (no spaces): `VPC`, `PublicSubnet`, `DB1`**
   - **WRONG Examples - ALL CAUSE PARSE ERRORS:**
     * `SProvider    Core Backend Microservice` ❌
     * `VPC --> Public Subnet` ❌
     * `Public Subnet --> Private Subnet` ❌
   - **CORRECT Examples:**
     * `SProvider[Core Backend Microservice]` ✅
     * `VPC --> PublicSubnet[Public Subnet]` ✅
     * `PublicSubnet[Public Subnet] --> PrivateSubnet[Private Subnet]` ✅
   - **NEVER use parentheses () in node labels**
   - **NEVER use spaces in node IDs** (use camelCase or underscores: `PublicSubnet` or `Public_Subnet`)
   - Valid node formats:
     * `NodeID[Simple Label]` - rectangle (BRACKETS REQUIRED)
     * `NodeID[(Database Label)]` - database shape
     * `NodeID{{Decision}}` - diamond
     * `NodeID([Start/End])` - rounded
   
4. **Examples of CORRECT node syntax:**
   ```
   WebApp[Web Application]
   UserAPI[User Service API]
   DB1[(User Database)]
   Cache[(Redis Cache)]
   ```

5. **Examples of INCORRECT syntax (DO NOT USE):**
   ```
   WebApp[Web Application (React)]  ❌ NO PARENTHESES
   API[API (Node.js)]               ❌ NO PARENTHESES
   DB[Database (PostgreSQL)]        ❌ NO PARENTHESES
   ```

6. **How to include technology information:**
   - Use hyphens: `WebApp[Web Application - React]` ✅
   - Use separate nodes with connections
   - Add technology in a note comment: `%% WebApp uses React`

7. **Subgraph Syntax:**
   ```
   subgraph BackendServices["Backend Services"]
       API[API Gateway]
       UserSvc[User Service]
   end
   ```

8. **Connection Syntax:**
   - Simple: `NodeA --> NodeB`
   - Labeled: `NodeA -->|HTTPS| NodeB`
   - Dotted: `NodeA -.-> NodeB`

**EXAMPLE of CORRECT Diagram:**
```mermaid
graph TD
    User[User]
    WebApp[Web Application]
    API[API Gateway]
    
    subgraph Backend["Backend Services"]
        AuthSvc[Auth Service]
        UserSvc[User Service]
    end
    
    subgraph DataLayer["Data Layer"]
        DB[(Primary Database)]
        Cache[(Redis Cache)]
    end
    
    User --> WebApp
    WebApp -->|HTTPS| API
    API --> AuthSvc
    API --> UserSvc
    UserSvc --> DB
    API -.-> Cache
```

Format each diagram as:
### Diagram Title
```mermaid
graph TD
    [your diagram code]
```

**MANDATORY**: Test your Mermaid syntax mentally before generating. NO PARENTHESES in labels!

**IMPORTANT OUTPUT RULES:**
- Start DIRECTLY with "## 1. Executive Summary"
- Do NOT include phrases like "As an expert solution architect" or "Here are the sections"
- Do NOT include meta-commentary about what you're doing
- Generate the actual content sections ONLY

Generate COMPLETE, DETAILED content for both sections. Create valid, error-free Mermaid diagrams."""

        response = self.model.generate_content(prompt)
        return response.text

    def _generate_stage2_architecture_details(self, context: str, stage1_content: str) -> str:
        """Stage 2: Generate Architecture Pattern, Components, Tech Stack, Data, and NFRs."""
        prompt = f"""You are an expert solution architect. Continue the architecture document with sections 3-7.

{context}

The document already has:
- Executive Summary
- Architecture Diagrams

Now generate these sections with FULL detail:

## 3. Architecture Pattern & Reasoning
(200-250 words)
- Chosen pattern (Microservices, Monolithic, Event-Driven, etc.)
- Detailed reasoning for this choice (at least 3 reasons)
- Alternative patterns considered and why rejected
- How it addresses scalability, maintainability, and requirements

## 4. System Components
(300-400 words)
Detail all major components. For EACH component:
- Component name and purpose
- Suggested technology/framework with version
- Detailed reasoning for technology choice
- Interactions with other components
List at least 6-8 major components.

## 5. Technology Stack
(250-300 words)
- Frontend technologies with detailed reasoning
- Backend technologies with detailed reasoning
- Database choices with detailed reasoning
- Infrastructure and DevOps tools
- Why each technology was chosen over alternatives

## 6. Data Architecture
(250-300 words)
- Data storage strategy and database schema approach
- Data flow between components with examples
- Caching strategy and cache invalidation
- Data security and encryption
- Backup and recovery approach

## 7. Non-Functional Requirements
(300-400 words)
Address all NFRs:
- Scalability approach with specific strategies
- Security measures with detailed reasoning
- Performance optimization strategies
- Reliability and fault tolerance mechanisms
- Availability and disaster recovery

**IMPORTANT OUTPUT RULES:**
- Start DIRECTLY with "## 3. Architecture Pattern & Reasoning"
- Do NOT include phrases like "Here are the detailed sections" or "As requested"
- Do NOT include meta-commentary or introductory statements
- Generate the actual content sections ONLY

Generate COMPLETE, DETAILED content. Be specific about technologies, versions, and reasoning."""

        response = self.model.generate_content(prompt)
        return response.text

    def _generate_stage3_implementation_details(self, context: str, stage1_content: str, stage2_content: str) -> str:
        """Stage 3: Generate Deployment Strategy, Integration Points, and Trade-offs."""
        prompt = f"""You are an expert solution architect. Complete the architecture document with the final sections 8-10.

{context}

The document already covers:
- Executive Summary
- Architecture Diagrams
- Architecture Pattern
- System Components
- Technology Stack
- Data Architecture
- Non-Functional Requirements

Now generate these FINAL sections with FULL detail:

## 8. Deployment Strategy
(250-300 words)
- Deployment architecture (cloud/on-prem/hybrid) with specific platform
- CI/CD pipeline approach with specific tools and stages
- Environment strategy (dev/staging/prod) with details
- Container orchestration and infrastructure as code
- Rollback and blue-green deployment strategies
- Monitoring and observability tools

## 9. Integration Points
(250-300 words)
- External system integrations with specific APIs
- API design approach (REST/GraphQL/gRPC) with reasoning
- Authentication/Authorization strategy (OAuth, JWT, etc.)
- Third-party services and SDKs
- Integration patterns (synchronous vs asynchronous)
- Error handling and retry mechanisms

## 10. Trade-offs and Decisions
(250-300 words)
- Key trade-offs made with detailed justification
- Risks identified with specific mitigation strategies
- Future scalability considerations
- Cost implications and optimization opportunities
- Technical debt and when it's acceptable
- Alternative approaches considered

**IMPORTANT OUTPUT RULES:**
- Start DIRECTLY with "## 8. Deployment Strategy"
- Do NOT include phrases like "Here are the final sections" or "To complete the document"
- Do NOT include meta-commentary or transitional statements
- Generate the actual content sections ONLY

Generate COMPLETE, DETAILED content for all three sections. Be thorough and specific."""

        response = self.model.generate_content(prompt)
        return response.text

    def _fix_mermaid_syntax(self, content: str) -> str:
        """
        Post-process Mermaid diagrams to fix common syntax errors.
        
        Main fix: Remove parentheses from node labels (except for shape definitions).
        Example: NodeID[Label (Tech)] -> NodeID[Label - Tech]
        
        Args:
            content: Full markdown document content
            
        Returns:
            Fixed content with valid Mermaid syntax
        """
        import re
        
        # Find all mermaid code blocks
        mermaid_pattern = r'(```mermaid\n)(.*?)(```)'
        
        def fix_mermaid_block(match):
            """Fix syntax errors in a single Mermaid block."""
            opening = match.group(1)
            diagram_code = match.group(2)
            closing = match.group(3)
            
            lines = diagram_code.split('\n')
            fixed_lines = []
            
            for line in lines:
                # Skip diagram type declarations, empty lines, and subgraph declarations
                if line.strip().startswith(('graph ', 'flowchart ', 'sequenceDiagram', 'subgraph ', 'end', '%%')):
                    fixed_lines.append(line)
                    continue
                
                stripped = line.strip()

                # Skip style/class/link directives
                if stripped.startswith(('style ', 'class ', 'classDef ', 'linkStyle ', 'click ')):
                    fixed_lines.append(line)
                    continue

                # Fix connection lines with multi-word node names missing brackets
                # Example: "VPC --> Public Subnet" -> "VPC --> PublicSubnet[Public Subnet]"
                if ('-->' in line or '-.>' in line or '==>' in line) and '[' not in line and ']' not in line:
                    # Match connection patterns
                    connection_match = re.match(r'^(\s*)(\S+)\s+(-->|\.->|==>|\|[^|]+\|)\s+(.+)$', line)
                    if connection_match:
                        indent, source, arrow, target = connection_match.groups()
                        # If source or target have spaces, they need brackets
                        if ' ' in source.strip():
                            source_parts = source.strip().split()
                            source_id = ''.join(source_parts)
                            source = f"{source_id}[{source.strip()}]"
                        if ' ' in target.strip():
                            target_parts = target.strip().split()
                            target_id = ''.join(target_parts)
                            target = f"{target_id}[{target.strip()}]"
                        line = f"{indent}{source} {arrow} {target}"
                        fixed_lines.append(line)
                        continue
                
                # Auto-wrap bare node labels without brackets (e.g., Node    Description)
                # This fixes: "SProvider    Core Backend Microservice" -> "SProvider[Core Backend Microservice]"
                if '[' not in line and ']' not in line and '(' not in line and ')' not in line:
                    # Skip connection lines that are already fixed or simple
                    if ('-->' in line or '-.>' in line or '==>' in line):
                        fixed_lines.append(line)
                        continue
                    
                    # Match bare node definitions: NodeID followed by text
                    node_match = re.match(r'^(\s*)([A-Za-z0-9_]+)\s{2,}(.+)$', line)
                    if node_match:
                        indent, node_id, label = node_match.groups()
                        label = label.strip()
                        # Normalize whitespace
                        label = re.sub(r'\s+', ' ', label)
                        # Remove backticks/quotes that break Mermaid
                        label = label.replace('`', '').replace('"', '').replace("'", '')
                        # Wrap in brackets
                        line = f"{indent}{node_id}[{label}]"
                        fixed_lines.append(line)
                        continue

                # Fix node definitions with parentheses in labels
                # Pattern: NodeID[Label (something)] or NodeID[Label (something) more]
                # Exception: Database shapes NodeID[(Label)] should keep their parentheses
                
                # Check if this is a database shape definition (starts with ID[(
                if re.search(r'\w+\[\(', line):
                    # This is a database shape, keep it as is
                    fixed_lines.append(line)
                    continue
                
                # Check if this is a rounded shape definition (starts with ID([
                if re.search(r'\w+\(\[', line):
                    # This is a rounded shape, keep it as is
                    fixed_lines.append(line)
                    continue
                
                # Fix regular node labels with parentheses
                # Replace (text) with - text inside [...] brackets
                if '[' in line and ']' in line:
                    # Pattern to find [...] content with parentheses
                    def replace_parens_in_label(match):
                        label = match.group(1)
                        # Replace (text) with - text, preserving the content
                        fixed_label = re.sub(r'\s*\(([^)]+)\)', r' - \1', label)
                        return f"[{fixed_label}]"
                    
                    # Apply the fix to all [...] in the line
                    line = re.sub(r'\[([^\]]+)\]', replace_parens_in_label, line)
                
                fixed_lines.append(line)
            
            fixed_diagram = '\n'.join(fixed_lines)
            return f"{opening}{fixed_diagram}{closing}"
        
        # Apply fixes to all Mermaid blocks
        fixed_content = re.sub(mermaid_pattern, fix_mermaid_block, content, flags=re.DOTALL)
        
        return fixed_content
