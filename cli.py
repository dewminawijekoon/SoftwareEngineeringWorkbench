"""Command-line interface for the Solution Architecture Generator."""
import sys
from pathlib import Path
from typing import List
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from models import UserRequirement, SupportingDocument
from architecture_generator import ArchitectureGenerator
from document_processor import DocumentProcessor

console = Console()


class ArchitectureCLI:
    """Interactive CLI for architecture generation."""
    
    def __init__(self):
        self.generator = ArchitectureGenerator()
        self.doc_processor = DocumentProcessor()
        self.requirements: List[UserRequirement] = []
        self.supporting_docs: List[SupportingDocument] = []
        self.chat_history = []
    
    def run(self):
        """Run the interactive CLI."""
        console.print(Panel.fit(
            "[bold cyan]Solution Architecture Generator[/bold cyan]\n"
            "Powered by Gemini 2.0 Flash",
            border_style="cyan"
        ))
        
        # Main menu
        while True:
            console.print("\n[bold]Main Menu:[/bold]")
            console.print("1. Chat with AI to gather requirements")
            console.print("2. Add requirements manually")
            console.print("3. Upload supporting documents")
            console.print("4. Review current requirements")
            console.print("5. Generate architecture")
            console.print("6. Exit")
            
            choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4", "5", "6"])
            
            if choice == "1":
                self._chat_mode()
            elif choice == "2":
                self._add_manual_requirements()
            elif choice == "3":
                self._upload_documents()
            elif choice == "4":
                self._review_requirements()
            elif choice == "5":
                self._generate_architecture()
            elif choice == "6":
                console.print("[yellow]Goodbye![/yellow]")
                break
    def _chat_mode(self):
        """Enhanced interactive chat mode for gathering user requirements intelligently."""
        console.print("\n[bold cyan]🤖 Chat Mode - Intelligent Requirements Gathering[/bold cyan]")
        console.print("[dim]Type 'done' to finish or 'back' to return to the main menu.[/dim]\n")

        self.generator.start_chat_session()
        self.chat_history.clear()

        # Opening instruction prompt to AI
        initial_prompt = (
            "You are an expert software architect assistant. "
            "Start a conversation to gather complete software requirements from the user. "
            "Ask one question at a time to explore system purpose, key features, users, constraints, "
            "and technologies. Be concise and professional."
        )

        ai_response = self.generator.chat(initial_prompt)
        console.print(f"[bold blue]AI:[/bold blue] {ai_response}\n")
        self.chat_history.append(f"AI: {ai_response}")

        conversation_round = 0
        summarized_points = []

        while True:
            user_input = Prompt.ask("[bold green]You[/bold green]").strip()

            if user_input.lower() == "done":
                # Summarize conversation before extraction
                if self.chat_history:
                    console.print("\n[bold yellow]Summarizing conversation before extraction...[/bold yellow]")
                    summary_prompt = (
                        "Summarize the key software requirements or ideas mentioned in this conversation:\n"
                        + "\n".join(self.chat_history)
                    )
                    summary = self.generator.chat(summary_prompt)
                    console.print(f"\n[bold blue]AI Summary:[/bold blue]\n{summary}\n")
                    summarized_points.append(summary)

                self._extract_requirements_from_chat()
                break

            elif user_input.lower() == "back":
                console.print("[yellow]Returning to main menu...[/yellow]")
                break

            # Avoid empty input
            if not user_input:
                console.print("[dim]Please enter a response or type 'done' to finish.[/dim]")
                continue

            # Append and send to AI
            self.chat_history.append(f"User: {user_input}")
            ai_response = self.generator.chat(user_input)
            self.chat_history.append(f"AI: {ai_response}")

            console.print(f"\n[bold blue]AI:[/bold blue] {ai_response}\n")

            conversation_round += 1

            # Optional: auto-summarize after every 5 exchanges to keep context manageable
            if conversation_round % 5 == 0:
                console.print("[dim]Auto-summarizing recent discussion...[/dim]")
                partial_summary_prompt = (
                    "Summarize the following part of the chat in concise bullet points:\n"
                    + "\n".join(self.chat_history[-10:])
                )
                partial_summary = self.generator.chat(partial_summary_prompt)
                summarized_points.append(partial_summary)
                console.print(f"[italic cyan]{partial_summary}[/italic cyan]\n")

        # Merge summaries for better requirement extraction
        if summarized_points:
            self.chat_history.append("AI Summary Blocks: " + " ".join(summarized_points))
    
    
    def _extract_requirements_from_chat(self):
        """Extract structured requirements from chat history."""
        chat_text = "\n".join(self.chat_history)
        
        extraction_prompt = f"""Based on this conversation, extract a list of clear, 
        structured software requirements. For each requirement, identify:
        - The requirement statement
        - Priority (High/Medium/Low) if mentioned
        - Category (Functional/Non-functional/Technical/Business)
        
        Conversation:
        {chat_text}
        
        Provide the requirements in this format:
        REQ1: [requirement text] | Priority: [level] | Category: [type]
        REQ2: ...
        """
        
        response = self.generator.chat(extraction_prompt)
        
        # Parse the response and add requirements
        console.print("\n[bold]Extracted Requirements:[/bold]")
        console.print(response)
        
        if Confirm.ask("\nAdd these requirements?"):
            # Simple parsing - in production, use more robust parsing
            lines = response.split('\n')
            for line in lines:
                if line.strip().startswith('REQ'):
                    parts = line.split('|')
                    if len(parts) >= 1:
                        req_text = parts[0].split(':', 1)[1].strip() if ':' in parts[0] else parts[0]
                        priority = parts[1].split(':')[1].strip() if len(parts) > 1 else None
                        category = parts[2].split(':')[1].strip() if len(parts) > 2 else None
                        
                        self.requirements.append(UserRequirement(
                            requirement=req_text,
                            priority=priority,
                            category=category
                        ))
            
            console.print(f"[green]✓[/green] Added {len(self.requirements)} requirements")
    
    def _add_manual_requirements(self):
        """Manually add requirements."""
        console.print("\n[bold cyan]Add Requirements Manually[/bold cyan]")
        console.print("[dim]Enter 'done' when finished[/dim]\n")
        
        while True:
            req_text = Prompt.ask("Requirement")
            
            if req_text.lower() == 'done':
                break
            
            priority = Prompt.ask(
                "Priority",
                choices=["High", "Medium", "Low", "Skip"],
                default="Skip"
            )
            priority = None if priority == "Skip" else priority
            
            category = Prompt.ask(
                "Category",
                choices=["Functional", "Non-functional", "Technical", "Business", "Skip"],
                default="Skip"
            )
            category = None if category == "Skip" else category
            
            self.requirements.append(UserRequirement(
                requirement=req_text,
                priority=priority,
                category=category
            ))
            
            console.print(f"[green]✓[/green] Requirement added\n")
    
    def _upload_documents(self):
        """Upload supporting documents."""
        console.print("\n[bold cyan]Upload Supporting Documents[/bold cyan]")
        console.print("[dim]Supported formats: .txt, .md, .pdf, .docx[/dim]\n")
        
        while True:
            file_path = Prompt.ask("Document path (or 'done' to finish)")
            
            if file_path.lower() == 'done':
                break
            
            try:
                doc = self.doc_processor.process_document(file_path)
                self.supporting_docs.append(doc)
                console.print(f"[green]✓[/green] Processed: {doc.filename} ({len(doc.content)} characters)\n")
            except Exception as e:
                console.print(f"[red]✗[/red] Error: {e}\n")
    
    def _review_requirements(self):
        """Review current requirements and documents."""
        console.print("\n[bold cyan]Current Requirements and Documents[/bold cyan]\n")
        
        if self.requirements:
            table = Table(title="Requirements")
            table.add_column("№", style="cyan")
            table.add_column("Requirement", style="white")
            table.add_column("Priority", style="yellow")
            table.add_column("Category", style="green")
            
            for i, req in enumerate(self.requirements, 1):
                table.add_row(
                    str(i),
                    req.requirement,
                    req.priority or "-",
                    req.category or "-"
                )
            
            console.print(table)
        else:
            console.print("[yellow]No requirements added yet[/yellow]")
        
        if self.supporting_docs:
            console.print("\n[bold]Supporting Documents:[/bold]")
            for doc in self.supporting_docs:
                console.print(f"  • {doc.filename} ({doc.document_type})")
        else:
            console.print("\n[yellow]No supporting documents added yet[/yellow]")
    
    def _generate_architecture(self):
        """Generate the solution architecture."""
        if not self.requirements:
            console.print("[red]✗[/red] No requirements found. Add requirements first.")
            return
        
        console.print("\n[bold cyan]Generating Solution Architecture...[/bold cyan]")
        
        with console.status("[bold green]Thinking..."):
            chat_history_text = "\n".join(self.chat_history) if self.chat_history else None
            
            architecture = self.generator.generate_architecture(
                requirements=self.requirements,
                supporting_docs=self.supporting_docs if self.supporting_docs else None,
                chat_history=chat_history_text
            )
        
        console.print("\n[bold green]✓ Architecture Generated![/bold green]\n")
        
        # Display the architecture
        md = Markdown(architecture)
        console.print(md)
        
        # Offer to save
        if Confirm.ask("\nSave architecture to file?"):
            output_file = Prompt.ask("Output filename", default="solution_architecture.md")
            self.generator.export_architecture(architecture, output_file)


def main():
    """Main entry point."""
    try:
        cli = ArchitectureCLI()
        cli.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
