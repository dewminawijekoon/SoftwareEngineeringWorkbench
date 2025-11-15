# Solution Architecture Generator

An AI-powered tool that helps generate comprehensive solution architectures with detailed reasoning using Google's Gemini 2.0 Flash API.

## Features

✨ **Interactive Requirements Gathering**
- Chat with AI to explore and refine requirements
- Ask clarifying questions automatically
- Extract structured requirements from conversations

📄 **Document Processing**
- Support for multiple formats: PDF, DOCX, TXT, Markdown
- Automatic content extraction
- Context integration into architecture generation

🏗️ **Comprehensive Architecture Generation**
- Detailed architecture patterns with reasoning
- Technology stack recommendations
- Component design with justifications
- Scalability and security considerations
- Deployment strategies
- Trade-off analysis

## Installation

1. Clone the repository:
```bash
git clone https://github.com/dewminawijekoon/SoftwareEngineeringWorkbench.git
cd SoftwareEngineeringWorkbench
```

2. Install dependencies using `uv`:
```bash
uv sync
```

Or using pip:
```bash
pip install -e .
```

3. Set up your Gemini API key:
   - Get an API key from [Google AI Studio](https://aistudio.google.com/apikey)
   - Copy `.env.example` to `.env`
   - Add your API key to the `.env` file:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

### Option 1: Streamlit Web Interface (Recommended)

Launch the interactive web application:
```bash
uv run streamlit run streamlit_app.py
```

Or if you've activated the virtual environment:
```bash
streamlit run streamlit_app.py
```

The web app will open at `http://localhost:8501` with the following features:
- **Chat Tab** - Interactive requirements gathering with Ada (AI assistant)
- **Summary Tab** - Review chat history and extract requirements
- **Documents Tab** - Upload supporting documents (PDF, DOCX, TXT, MD)
- **Architecture Tab** - Generate and download solution architecture

### Option 2: Interactive CLI Mode

Run the command-line interface:
```bash
uv run python main.py
```

Or if you've activated the virtual environment:
```bash
python main.py
```

The CLI offers the following options:
1. **Chat with AI** - Interactive requirements gathering
2. **Add Requirements Manually** - Direct requirement input
3. **Upload Supporting Documents** - Process PDFs, DOCX, etc.
4. **Review Requirements** - View all collected information
5. **Generate Architecture** - Create the solution architecture
6. **Exit** - Close the application


### Programmatic Usage

```python
from architecture_generator import ArchitectureGenerator
from document_processor import DocumentProcessor
from models import UserRequirement, SupportingDocument

# Initialize
generator = ArchitectureGenerator()
doc_processor = DocumentProcessor()

# Define requirements
requirements = [
    UserRequirement(
        requirement="Build a scalable e-commerce platform",
        priority="High",
        category="Functional"
    ),
    UserRequirement(
        requirement="Support 10,000 concurrent users",
        priority="High",
        category="Non-functional"
    )
]

# Process documents (optional)
docs = doc_processor.process_multiple_documents([
    "requirements.pdf",
    "api_spec.docx"
])

# Generate architecture
architecture = generator.generate_architecture(
    requirements=requirements,
    supporting_docs=docs
)

print(architecture)

# Save to file
generator.export_architecture(architecture, "solution_architecture.md")
```

### Chat Mode for Requirements Gathering

```python
from architecture_generator import ArchitectureGenerator

generator = ArchitectureGenerator()
generator.start_chat_session()

# Interactive conversation
response = generator.chat("I want to build a social media platform")
print(response)

response = generator.chat("It should support real-time messaging")
print(response)
```

## Project Structure

```
SoftwareEngineeringWorkbench/
├── streamlit_app.py           # Web interface (Streamlit)
├── main.py                    # CLI entry point
├── cli.py                     # Interactive CLI interface
├── automated_architecture.py  # Batch/automated processing
├── architecture_generator.py  # Core architecture generation logic
├── document_processor.py      # Document processing utilities
├── models.py                  # Pydantic data models
├── config.py                  # Configuration settings
├── .env.example              # Environment variables template
├── .streamlit/config.toml    # Streamlit theme configuration
├── pyproject.toml            # Project dependencies
└── README.md                 # This file
```

## Configuration

Edit `config.py` to customize:
- **Model Selection**: Change `GEMINI_MODEL` (default: gemini-2.0-flash-exp)
- **Generation Settings**: Adjust temperature, top_p, max_tokens
- **Safety Settings**: Configure content filtering
- **File Support**: Modify supported document formats

## Example Output

The generated architecture includes:

1. **Executive Summary** - High-level overview
2. **Architecture Pattern** - Chosen pattern with detailed reasoning
3. **System Components** - Each component with technology choices and rationale
4. **Technology Stack** - Frontend, backend, database, infrastructure
5. **Data Architecture** - Storage strategy and data flow
6. **Non-Functional Requirements** - Scalability, security, performance
7. **Deployment Strategy** - CI/CD, environments, deployment approach
8. **Integration Points** - APIs, external systems, auth
9. **Trade-offs** - Decisions made, risks, mitigation strategies
10. **Architecture Diagram Description** - Textual component relationships

## Requirements

- Python 3.13+
- Gemini API key
- Dependencies (auto-installed):
  - google-generativeai
  - streamlit
  - python-dotenv
  - rich
  - pydantic
  - pypdf
  - python-docx

## Tips for Best Results

1. **Be Specific**: Provide detailed requirements with context
2. **Use Chat Mode**: Interactive conversations help clarify ambiguities
3. **Add Documents**: Supporting docs provide valuable context
4. **Specify Constraints**: Mention budget, timeline, team size, existing systems
5. **Review Generated Architecture**: AI suggestions should be validated by experts

## Troubleshooting

**API Key Issues**:
- Verify your API key in `.env` file
- Check key permissions at [Google AI Studio](https://aistudio.google.com)

**Document Processing Errors**:
- Ensure files are not password-protected
- Check file size limits (default: 10MB)
- Verify file format is supported

**Import Errors**:
- Run `uv sync` or `pip install -e .` to install dependencies
- Ensure Python 3.13+ is installed

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details

## Acknowledgments

Powered by [Google Gemini 2.5 Flash](https://ai.google.dev/)
