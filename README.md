# MedInsights AI - Advanced RAG Chatbot

An advanced, production-ready Retrieval-Augmented Generation (RAG) system designed for medical and pharmaceutical data insights.

## 🚀 Features
- **Advanced RAG Pipeline**: Built with LangChain, OpenAI, and FAISS for precise document retrieval.
- **Premium UI**: Modern React dashboard with glassmorphism, dark mode, and fluid animations.
- **Persistent Memory**: SQLite database integration for session history and document tracking.
- **Context-Aware Analytics**: Ability to process complex medical PDFs and TXT files.
- **Source Attribution**: See exactly which documents the AI used to generate its insights.

## 🛠️ Tech Stack
- **Frontend**: React (Vite), Vanilla CSS, Lucide Icons, Framer Motion.
- **Backend**: Flask (Python), SQLAlchemy.
- **AI/ML**: LangChain, OpenAI GPT-4o, FAISS Vector Store.
- **Database**: SQLite.

## 📦 Installation

### Backend Setup
1. Navigate to the `server` directory.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or .\venv\Scripts\activate on Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your `.env` file with your `OPENAI_API_KEY`.
5. Run the server:
   ```bash
   python app.py
   ```

### Frontend Setup
1. Navigate to the `client` directory.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the dev server:
   ```bash
   npm run dev
   ```

## 📄 License
MIT License
