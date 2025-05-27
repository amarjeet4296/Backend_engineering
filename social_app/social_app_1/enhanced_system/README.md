# Enhanced Social Security Application System

An AI-powered workflow system for automating social security application processing, reducing application time from 5-20 working days to just minutes.

## System Overview

This system uses a multi-agent architecture orchestrated through LangGraph to process social security applications efficiently and accurately. The solution addresses key pain points in the traditional process:

- **Manual Data Gathering**: Automated extraction from multiple document types
- **Semi-Automated Validations**: Comprehensive validation with consistency checks
- **Inconsistent Information**: Cross-document verification and correlation
- **Time-Consuming Reviews**: Parallel processing with AI agents
- **Subjective Decision-Making**: Data-driven assessment with ML models

## Features

- **Multimodal Document Processing**: Extract data from text, images, and tabular documents
- **Interactive Web Form**: User-friendly application submission
- **Advanced Validation**: Rule-based and ML-based data validation
- **Risk Assessment**: Automated eligibility determination and risk scoring
- **Personalized Recommendations**: Tailored support options based on individual needs
- **Interactive Chat**: Real-time assistance through AI chatbot
- **Audit System**: Complete transparency with decision explanations

## Architecture

The system uses a layered architecture:

1. **Data Ingestion Layer**: Processes documents and form submissions
2. **Data Storage Layer**: PostgreSQL for structured data, ChromaDB for vector storage
3. **Agent Layer**: Specialized AI agents for different tasks
4. **Machine Learning Layer**: Risk classification and eligibility models
5. **User Interface Layer**: Streamlit frontend with interactive dashboard
6. **Observability Layer**: Monitoring and audit capabilities

## Technology Stack

- **Backend**: Python, FastAPI
- **Frontend**: Streamlit
- **Database**: PostgreSQL, ChromaDB
- **ML/AI**: Scikit-learn, LangChain, LlamaIndex
- **Reasoning**: ReAct framework for agent reasoning
- **Orchestration**: LangGraph for agent workflow
- **LLM**: Locally hosted models via Ollama
- **Document Processing**: PyTesseract, PDF2Image, PyMuPDF

## Setup and Installation

### Prerequisites

- Python 3.10+
- PostgreSQL
- Ollama (for local LLM hosting)
- Tesseract OCR

### Environment Setup

1. Clone the repository:

```bash
git clone <repository_url>
cd social_app_1/enhanced_system
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install Tesseract OCR:

```bash
# On macOS
brew install tesseract

# On Ubuntu
sudo apt-get install tesseract-ocr
```

5. Install and run Ollama:

Download from [Ollama website](https://ollama.ai/download) or follow their installation instructions.

6. Pull the required model:

```bash
ollama pull mistral
```

### Database Setup

1. Create a PostgreSQL database:

```sql
CREATE DATABASE social;
CREATE USER amarjeet WITH PASSWORD '9582924264';
GRANT ALL PRIVILEGES ON DATABASE social TO amarjeet;
```

2. Configure environment variables by creating a `.env` file:

```
DB_USER=amarjeet
DB_PASSWORD=9582924264
DB_HOST=localhost
DB_PORT=5432
DB_NAME=social
OLLAMA_HOST=http://localhost:11434
```

### Running the System

1. Initialize the database:

```bash
python database/db_setup.py
```

2. Start the FastAPI backend:

```bash
cd enhanced_system
uvicorn app:app --reload
```

3. Start the Streamlit frontend:

```bash
cd enhanced_system/ui
streamlit run streamlit_app.py
```

4. Access the application at `http://localhost:8501`

## Agent Architecture

The system uses five specialized agents:

1. **Orchestrator Agent**: Coordinates workflow between all agents
2. **Data Collector Agent**: Extracts information from documents
3. **Validator Agent**: Verifies data completeness and consistency
4. **Assessor Agent**: Evaluates eligibility and risk
5. **Counselor Agent**: Provides personalized recommendations

## Usage Flow

1. **Application Submission**:
   - Submit application through web form
   - Upload supporting documents

2. **Document Processing**:
   - OCR for image-based documents
   - Text extraction for PDFs
   - Data parsing for spreadsheets

3. **Validation**:
   - Field-level validation
   - Cross-document consistency checks
   - Anomaly detection

4. **Assessment**:
   - Eligibility determination
   - Risk scoring
   - Financial support calculation

5. **Recommendation**:
   - Support program matching
   - Economic enablement suggestions
   - Required documentation guidance

6. **Interactive Support**:
   - Chat with AI assistant
   - Application status tracking
   - Decision explanation

## ML Models

The system uses two main machine learning models:

1. **Risk Classification Model**: Random Forest classifier to determine risk level
2. **Eligibility Model**: Random Forest classifier to predict application approval

## Directory Structure

```
enhanced_system/
│
├── agents/                  # Specialized AI agents
│   ├── orchestrator.py      # Main workflow orchestrator
│   ├── data_collector.py    # Document processing agent
│   ├── validator.py         # Data validation agent
│   ├── assessor.py          # Eligibility assessment agent
│   └── counselor.py         # Recommendation agent
│
├── database/                # Database modules
│   ├── db_setup.py          # PostgreSQL database setup
│   └── chroma_manager.py    # ChromaDB vector database manager
│
├── models/                  # Machine learning models
│   ├── risk_model.pkl       # Risk classification model
│   └── eligibility_model.pkl # Eligibility prediction model
│
├── utils/                   # Utility modules
│   └── llm_factory.py       # LLM configuration utility
│
├── ui/                      # User interface
│   └── streamlit_app.py     # Streamlit frontend application
│
├── uploads/                 # Document upload directory
├── chroma_db/               # ChromaDB data directory
├── app.py                   # FastAPI main application
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

## API Endpoints

- `POST /api/applications`: Submit a new application
- `POST /api/documents`: Upload documents for an application
- `POST /api/chat`: Send chat messages to the AI assistant
- `GET /api/applications/{application_id}`: Get application status
- `GET /api/applications`: Get all applications (admin only)
- `GET /api/applications/{application_id}/explanation`: Get decision explanation

## Future Enhancements

- **Fraud Detection**: Advanced anomaly detection for fraudulent applications
- **Multi-language Support**: Process documents in multiple languages
- **Mobile App**: Native mobile application for easier document uploads
- **Integration**: Connect with other government services
- **Federated Learning**: Privacy-preserving model training across departments

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built upon the existing social security application system
- Utilizes open-source AI and ML libraries
- Developed to improve accessibility to social services
