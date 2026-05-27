# 📧 AI Email Generator

Production-grade AI system that generates professional emails
from bullet points using Groq (Llama 3.1) + FastAPI + LangChain.

## 🚀 Quick Start

### 1. Clone & Setup

git clone <your-repo>
cd email-generator

### 2. Create Virtual Environment

python -m venv venv

# Mac/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

### 3. Install Dependencies

pip install -r requirements.txt

### 4. Configure Environment

cp .env.example .env
# Edit .env and add your GROQ_API_KEY

### 5. Run the Server

uvicorn app.main:app --reload --port 8000

### 6. Test It

Open: http://localhost:8000
Docs: http://localhost:8000/docs
Health: http://localhost:8000/health
Ready: http://localhost:8000/health/ready

## 📦 Project Phases

| Phase | Feature                    | Status  |
|-------|----------------------------|---------|
| 1     | Project Setup              | ✅ Done |
| 2     | Basic Email Generation     | 🔜 Next |
| 3     | Validation + Pydantic      | 🔜      |
| 4     | Tone & Templates           | 🔜      |
| 5     | Advanced Prompt Engineering| 🔜      |
| 6     | PostgreSQL History         | 🔜      |
| 7     | Redis Caching              | 🔜      |
| 8     | Multi-Language             | 🔜      |
| 9     | Brand Voice                | 🔜      |
| 10    | Enterprise Features        | 🔜      |