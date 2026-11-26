# AETHERIQ AI

### Beyond Answers. Towards Intelligence.

AETHERIQ AI is an enterprise-style AI assistant designed to provide intelligent conversations, document understanding, semantic search, and Retrieval-Augmented Generation (RAG).

The platform combines AI language models with document intelligence to deliver context-aware responses based on uploaded documents.

---

## Features

- Intelligent AI conversations
- Multiple AI provider support
- Document upload and processing
- Retrieval-Augmented Generation (RAG)
- Semantic document search
- Context-aware AI responses
- Conversation history management
- Document source references
- SQLite database persistence
- Premium interactive web frontend
- FastAPI backend
- Interactive API documentation
- Configurable AI provider selection

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| FastAPI | REST API framework |
| Uvicorn | ASGI application server |
| Google Gemini | AI generation and embeddings |
| Groq | AI language model provider |
| OpenRouter | AI model access |
| OpenAI SDK | AI provider integration |
| SQLite | Database storage |
| Pydantic | Data validation |
| HTML, CSS, JavaScript | Frontend interface |

---

## Supported Document Formats

AETHERIQ AI supports the following document formats:

- PDF
- DOCX
- PPTX
- XLSX
- CSV
- TXT

Uploaded documents are processed, divided into smaller text chunks, and prepared for semantic retrieval.

---

## Project Structure

```text
AETHERIQ-AI-2026/
│
├── backend/
│   ├── api/
│   │   └── routes/
│   ├── ai_engine/
│   │   ├── providers/
│   │   └── prompts/
│   ├── core/
│   ├── database/
│   ├── documents/
│   ├── rag/
│   │   └── retrieval/
│   └── schemas/
│
├── frontend/
│   └── index.html
│
├── data/
├── docs/
├── infrastructure/
├── scripts/
├── tests/
│
├── .env.example
├── .gitignore
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## Installation

### 1. Clone the Repository

After creating the GitHub repository, clone it:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Navigate into the project directory:

```bash
cd AETHERIQ-AI-2026
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Configuration

Create a `.env` file in the project root.

Configure your AI provider settings:

```env
DEFAULT_PROVIDER=groq

GROQ_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=
```

Add your own API keys to the `.env` file.

Never publish your API keys or upload your `.env` file to GitHub.

---

## Running the Application

From the project root, activate the virtual environment and run:

```powershell
python -m uvicorn backend.main:app --reload
```

Wait until the server starts successfully.

---

## Application URLs

| Service | URL |
|---|---|
| AETHERIQ AI Frontend | http://127.0.0.1:8000/ |
| API Documentation | http://127.0.0.1:8000/docs |
| ReDoc Documentation | http://127.0.0.1:8000/redoc |
| Health Endpoint | http://127.0.0.1:8000/api/v1/health |

---

## Retrieval-Augmented Generation (RAG)

AETHERIQ AI uses Retrieval-Augmented Generation to answer questions using relevant information from uploaded documents.

### RAG Workflow

1. Upload a document.
2. Extract text from the document.
3. Divide the text into smaller chunks.
4. Generate semantic embeddings.
5. Store document information and embeddings in SQLite.
6. Search for relevant document chunks when a user asks a question.
7. Provide retrieved context to the AI model.
8. Generate a context-aware response.
9. Display the answer with document source information.

This process helps the assistant provide answers grounded in the user's uploaded documents.

---

## API Overview

The backend provides REST API endpoints for:

- Health monitoring
- AI chat
- Conversation creation
- Conversation history
- Conversation search
- Conversation management
- Document upload
- Document retrieval
- Document listing
- Document deletion

Visit the interactive API documentation to explore the available endpoints:

http://127.0.0.1:8000/docs

---

## Database

AETHERIQ AI uses SQLite for persistent storage.

The database stores information related to:

- Documents
- Document chunks
- Chunk embeddings
- Conversations
- Messages

The database is stored locally in the project's `data/` directory.

---

## Security

The project follows basic security practices:

- API keys are stored in environment variables.
- The `.env` file is excluded from Git.
- The virtual environment is excluded from Git.
- Python cache files are excluded from Git.
- Sensitive credentials should never be committed to a public repository.

---

## Project Status

AETHERIQ AI is an active AI application development project.

The backend, document processing, RAG functionality, conversation management, and frontend integration have been implemented.

Further improvements and deployment preparation are ongoing.

---

## Future Enhancements

Potential future improvements include:

- Advanced analytics dashboard
- User authentication
- Role-based access control
- Cloud database integration
- Production deployment
- Advanced document visualization
- Additional AI model providers

---

## License

Choose and add an appropriate open-source license before distributing this project publicly.

---

**AETHERIQ AI**

*Beyond Answers. Towards Intelligence.*