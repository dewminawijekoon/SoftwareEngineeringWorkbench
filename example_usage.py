"""
Example usage of the Solution Architecture Generator.
This demonstrates how to use the tool programmatically.
"""
from architecture_generator import ArchitectureGenerator
from document_processor import DocumentProcessor
from models import UserRequirement
from rich.console import Console
from rich.markdown import Markdown

console = Console()


def example_1_basic_usage():
    """Example 1: Basic architecture generation with requirements."""
    console.print("\n[bold cyan]Example 1: Basic Usage[/bold cyan]\n")
    
    # Initialize generator
    generator = ArchitectureGenerator()
    
    # Define requirements
    requirements = [
        UserRequirement(
            requirement="Build a RESTful API for managing customer orders",
            priority="High",
            category="Functional"
        ),
        UserRequirement(
            requirement="System must handle 1000 requests per second",
            priority="High",
            category="Non-functional"
        ),
        UserRequirement(
            requirement="Support PostgreSQL database",
            priority="Medium",
            category="Technical"
        ),
        UserRequirement(
            requirement="Deploy on AWS cloud infrastructure",
            priority="Medium",
            category="Technical"
        ),
        UserRequirement(
            requirement="Implement JWT-based authentication",
            priority="High",
            category="Security"
        ),
    ]
    
    # Generate architecture
    console.print("[yellow]Generating architecture...[/yellow]")
    architecture = generator.generate_architecture(requirements=requirements)
    
    # Display result
    md = Markdown(architecture)
    console.print(md)
    
    # Save to file
    generator.export_architecture(architecture, "example_architecture_1.md")


def example_2_with_chat():
    """Example 2: Using chat mode for requirements gathering."""
    console.print("\n[bold cyan]Example 2: Chat Mode[/bold cyan]\n")
    
    generator = ArchitectureGenerator()
    generator.start_chat_session()
    
    # Simulate a conversation
    messages = [
        "I want to build a mobile app for food delivery",
        "The app should support real-time order tracking and support iOS and Android",
        "We expect around 50,000 daily active users in the first year",
        "Budget is moderate, and we have a team of 5 developers"
    ]
    
    chat_log = []
    for msg in messages:
        console.print(f"[bold green]User:[/bold green] {msg}")
        response = generator.chat(msg)
        console.print(f"[bold blue]AI:[/bold blue] {response}\n")
        chat_log.append(f"User: {msg}\nAI: {response}")
    
    # Extract requirements from the conversation
    requirements = [
        UserRequirement(
            requirement="Mobile app for food delivery (iOS and Android)",
            priority="High",
            category="Functional"
        ),
        UserRequirement(
            requirement="Real-time order tracking",
            priority="High",
            category="Functional"
        ),
        UserRequirement(
            requirement="Support 50,000 daily active users",
            priority="High",
            category="Non-functional"
        ),
    ]
    
    # Generate architecture with chat history
    console.print("\n[yellow]Generating architecture with chat context...[/yellow]")
    architecture = generator.generate_architecture(
        requirements=requirements,
        chat_history="\n".join(chat_log)
    )
    
    generator.export_architecture(architecture, "example_architecture_2.md")
    console.print("[green]Architecture saved to example_architecture_2.md[/green]")


def example_3_with_documents():
    """Example 3: Architecture generation with supporting documents."""
    console.print("\n[bold cyan]Example 3: With Supporting Documents[/bold cyan]\n")
    
    # Create sample documents
    sample_doc_content = """
    # Requirements Document
    
    ## Functional Requirements
    - User registration and authentication
    - Product catalog management
    - Shopping cart functionality
    - Order processing and payment
    - Order history and tracking
    
    ## Non-Functional Requirements
    - 99.9% uptime SLA
    - Page load time < 2 seconds
    - Support for 10,000 concurrent users
    - PCI DSS compliance for payment processing
    """
    
    # Save sample document
    with open("sample_requirements.txt", "w", encoding="utf-8") as f:
        f.write(sample_doc_content)
    
    # Process document
    doc_processor = DocumentProcessor()
    docs = doc_processor.process_multiple_documents(["sample_requirements.txt"])
    
    # Define additional requirements
    requirements = [
        UserRequirement(
            requirement="E-commerce platform for selling physical products",
            priority="High",
            category="Business"
        ),
        UserRequirement(
            requirement="Integration with Stripe payment gateway",
            priority="High",
            category="Technical"
        ),
    ]
    
    # Generate architecture
    generator = ArchitectureGenerator()
    console.print("[yellow]Generating architecture with documents...[/yellow]")
    architecture = generator.generate_architecture(
        requirements=requirements,
        supporting_docs=docs
    )
    
    generator.export_architecture(architecture, "example_architecture_3.md")
    console.print("[green]Architecture saved to example_architecture_3.md[/green]")


if __name__ == "__main__":
    console.print(Panel.fit(
        "[bold cyan]Solution Architecture Generator - Examples[/bold cyan]\n"
        "Demonstrating different usage patterns",
        border_style="cyan"
    ))
    
    # Run examples
    try:
        console.print("\n[bold]Choose an example to run:[/bold]")
        console.print("1. Basic usage with requirements")
        console.print("2. Chat mode for requirements gathering")
        console.print("3. Architecture with supporting documents")
        console.print("4. Run all examples")
        
        from rich.prompt import Prompt
        choice = Prompt.ask("Select", choices=["1", "2", "3", "4"])
        
        if choice == "1":
            example_1_basic_usage()
        elif choice == "2":
            example_2_with_chat()
        elif choice == "3":
            example_3_with_documents()
        elif choice == "4":
            example_1_basic_usage()
            example_2_with_chat()
            example_3_with_documents()
        
        console.print("\n[bold green]✓ Examples completed![/bold green]")
        
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        console.print("\n[yellow]Note:[/yellow] Make sure to set your GEMINI_API_KEY in the .env file")
