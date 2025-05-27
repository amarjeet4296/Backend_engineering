# AI Workflow for Government Social Security Department

An advanced, AI-powered application system for automating social security application processing, assessment, and enablement recommendations.

## Problem Statement

The current government social security application process takes 5-20 working days to assess and approve support applications, with several pain points:

- **Manual Data Gathering**: Manual entry from scanned documents, physical document collection, and extraction from handwritten forms
- **Semi-Automated Data Validations**: Basic form field validation with significant manual effort
- **Inconsistent Information**: Discrepancies in information across documents
- **Time-Consuming Reviews**: Multiple review rounds causing delays and bottlenecks
- **Subjective Decision-Making**: Assessment prone to human bias, leading to inconsistent decisions

## Solution Overview

This AI-powered system automates the entire application process, providing near-immediate decisions with consistent, fair assessments:

- **Multimodal Data Processing**: Handles text, images, and tabular data from various document types
- **ML-Based Eligibility Assessment**: Fair and objective assessment using machine learning models
- **Agentic AI Orchestration**: Coordinated workflow of specialized AI agents
- **Interactive Chat Assistance**: Real-time guidance and recommendations
- **Local LLM Integration**: Privacy-preserving, locally hosted language models

## Key Features

- **Automated Document Processing**: Extracts information from multiple document types (PDFs, images, Excel files)
- **Enhanced Data Validation**: Detects inconsistencies and ensures data quality
- **ML-Based Eligibility Assessment**: Fair, consistent application assessment
- **Economic Enablement Recommendations**: Personalized guidance based on applicant profiles
- **Interactive Chat Interface**: Real-time assistance for applicants
- **Multi-Agent Architecture**: Specialized agents for different processing stages
- **Reasoning Framework**: ReAct reasoning for improved decision-making
- **End-to-End Observability**: Comprehensive monitoring and tracking

## System Architecture

The system uses a multi-agent architecture with five core components:

1. **Orchestrator Agent**: Coordinates the overall workflow using LangGraph
2. **Data Extraction Agent**: Processes documents and extracts information using OCR and multimodal techniques
3. **Data Validation Agent**: Validates extracted data and checks for inconsistencies
4. **Eligibility Agent**: Assesses applications using ML models
5. **Counselor Agent**: Provides guidance and recommendations using local LLMs

### Technology Stack

- **Programming Language**: Python 3.9+
- **Data Pipeline**: Pandas, LlamaIndex, ChromaDB, PostgreSQL
- **AI Pipeline**:
  - ML Models: Scikit-learn (RandomForest, GradientBoosting)
  - LLM Integration: Ollama (local model hosting)
  - Agent Orchestration: LangGraph
  - Reasoning Framework: ReAct
  - Vector Store: ChromaDB
  - Model Serving: FastAPI
  - Frontend: Streamlit

## Prerequisites

- Python 3.9+
- PostgreSQL database
- Tesseract OCR
- Poppler (for PDF processing)
- Ollama (for local LLM hosting)

### Installing Dependencies

#### macOS
```bash
# Install Tesseract and Poppler
brew install tesseract
brew install tesseract-lang
brew install poppler

# Install Ollama for local LLMs
curl -fsSL https://ollama.com/install.sh | sh

# Install PostgreSQL
brew install postgresql@14
brew services start postgresql@14
```

#### Ubuntu/Debian
```bash
# Install Tesseract and Poppler
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-ara
sudo apt-get install poppler-utils

# Install Ollama for local LLMs
curl -fsSL https://ollama.com/install.sh | sh

# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd social_app_1
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the required Python packages:
```bash
pip install -r requirements.txt
```

4. Set up the PostgreSQL database:
```bash
# Create a database
createdb social

# Configure the .env file with your database credentials
echo 'DB_USER=your_username' > .env
echo 'DB_PASSWORD=your_password' >> .env
echo 'DB_HOST=localhost' >> .env
echo 'DB_PORT=5432' >> .env
echo 'DB_NAME=social' >> .env
```

5. Download required LLM models:
```bash
# Pull the Mistral model for local use
ollama pull mistral
```

## Usage

1. Run the enhanced application:
```bash
streamlit run enhanced_app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

3. Navigate through the application using the sidebar:
   - **Home**: Overview and quick actions
   - **New Application**: Submit a new application with documents
   - **Application Status**: Check status of existing applications
   - **Guidance Chat**: Get assistance through the AI chat interface
   - **Analytics**: View application statistics and insights
   - **System Info**: Information about the system architecture

## Project Structure

```
social_app_1/
├── agents/
│   ├── counselor.py          # Enhanced counselor agent
│   ├── data_extraction.py    # Document processing agent
│   ├── data_validation.py    # Data validation agent
│   ├── eligibility.py        # Eligibility assessment agent
│   └── orchestrator.py       # Main orchestration agent
├── data/
│   ├── db_connector.py       # PostgreSQL database integration
│   ├── synthetic/            # Synthetic data generation
│   └── vector_store.py       # ChromaDB vector store integration
├── models/
│   ├── llm_connector.py      # Local LLM integration
│   ├── ml_models.py          # ML models for assessment
│   └── multimodal.py         # Multimodal processing utilities
├── utils/
│   ├── chroma_utils.py       # ChromaDB utilities
│   ├── observability.py      # Monitoring and tracking
│   ├── ollama_utils.py       # Ollama integration
│   └── reasoning.py          # ReAct reasoning framework
├── app.py                    # Original application
├── enhanced_app.py           # Enhanced AI workflow application
├── requirements.txt          # Package dependencies
├── .env                      # Environment variables
└── README.md                 # Documentation
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.