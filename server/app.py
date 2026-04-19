from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import traceback
from database import init_db, SessionLocal, ChatSession, Message, Document
from rag_engine import rag_engine
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part in request"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Only PDF and TXT files are supported"}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        num_chunks = rag_engine.process_document(file_path)

        db = SessionLocal()
        new_doc = Document(filename=filename, file_path=file_path)
        db.add(new_doc)
        db.commit()
        db.close()

        return jsonify({
            "message": f"File '{filename}' uploaded and indexed successfully.",
            "chunks": num_chunks
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        session_id = data.get('session_id')
        query = data.get('query', '').strip()

        if not query:
            return jsonify({"error": "Query is required"}), 400

        if not session_id:
            session_id = str(uuid.uuid4())

        db = SessionLocal()

        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            session = ChatSession(session_id=session_id)
            db.add(session)
            db.commit()

        messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.timestamp).all()
        history = [(m.role, m.content) for m in messages]

        answer, sources = rag_engine.get_response(query, history)

        user_msg = Message(session_id=session_id, role="user", content=query)
        assistant_msg = Message(session_id=session_id, role="assistant", content=answer)
        db.add(user_msg)
        db.add(assistant_msg)
        db.commit()
        db.close()

        source_names = []
        if isinstance(sources, list):
            seen = set()
            for doc in sources:
                src = doc.metadata.get('source', '')
                if src and src not in seen:
                    source_names.append(os.path.basename(src))
                    seen.add(src)

        return jsonify({
            "session_id": session_id,
            "answer": answer,
            "sources": source_names
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/history/<session_id>', methods=['GET'])
def get_history(session_id):
    try:
        db = SessionLocal()
        messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.timestamp).all()
        history = [{"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()} for m in messages]
        db.close()
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/documents', methods=['GET'])
def list_documents():
    try:
        db = SessionLocal()
        docs = db.query(Document).order_by(Document.upload_date.desc()).all()
        db.close()
        return jsonify([{"id": d.id, "filename": d.filename, "upload_date": d.upload_date.isoformat()} for d in docs])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "gemini_ready": rag_engine.llm is not None,
        "docs_indexed": rag_engine.vector_store is not None
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
