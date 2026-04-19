from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from database import init_db, SessionLocal, ChatSession, Message, Document
from rag_engine import rag_engine
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

init_db()

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Process with RAG Engine
        num_chunks = rag_engine.process_document(file_path)
        
        # Save to DB
        db = SessionLocal()
        new_doc = Document(filename=filename, file_path=file_path)
        db.add(new_doc)
        db.commit()
        db.close()
        
        return jsonify({
            "message": f"File {filename} uploaded and processed successfully",
            "chunks": num_chunks
        }), 200

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    session_id = data.get('session_id')
    query = data.get('query')
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    if not session_id:
        session_id = str(uuid.uuid4())
    
    db = SessionLocal()
    
    # Check if session exists
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        session = ChatSession(session_id=session_id)
        db.add(session)
        db.commit()
    
    # Get history
    history = []
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp).all()
    for msg in messages:
        history.append((msg.role, msg.content))
    
    # Get AI response
    answer, sources = rag_engine.get_response(query, history)
    
    # Save messages
    user_msg = Message(session_id=session_id, role="user", content=query)
    assistant_msg = Message(session_id=session_id, role="assistant", content=answer)
    db.add(user_msg)
    db.add(assistant_msg)
    db.commit()
    db.close()
    
    return jsonify({
        "session_id": session_id,
        "answer": answer,
        "sources": [doc.metadata.get('source', 'unknown') for doc in sources] if isinstance(sources, list) else []
    })

@app.route('/api/history/<session_id>', methods=['GET'])
def get_history(session_id):
    db = SessionLocal()
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp).all()
    history = [{"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()} for m in messages]
    db.close()
    return jsonify(history)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
