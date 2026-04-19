import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Upload, FileText, Brain, Activity, User, ChevronRight, Loader2, Plus } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';

const API_BASE_URL = 'http://localhost:5000/api';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;

    const userMessage = { role: 'user', content: inputText };
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        query: inputText,
        session_id: sessionId
      });

      if (!sessionId) setSessionId(response.data.session_id);

      const assistantMessage = {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request.'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData);
      setUploadedFiles(prev => [...prev, file.name]);
      // Small automated message to notify processing
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Successfully indexed **${file.name}**. I can now answer questions based on its content.`
      }]);
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to upload file');
    } finally {
      setIsUploading(false);
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setSessionId(null);
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-icon">
            <Brain size={24} color="#0a0c10" />
          </div>
          <h1 className="sidebar-title">MedInsights AI</h1>
        </div>

        <button className="send-btn" onClick={startNewChat} style={{ width: '100%', marginBottom: '2rem', gap: '8px' }}>
          <Plus size={18} /> New Analysis
        </button>

        <div className="sidebar-section" style={{ flex: 1 }}>
          <h3 style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '1rem' }}>
            Active Knowledge Base
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {uploadedFiles.length === 0 ? (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>No documents uploaded yet.</p>
            ) : (
              uploadedFiles.map((file, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
                  <FileText size={16} color="var(--accent-primary)" />
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{file}</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="upload-card" onClick={() => fileInputRef.current.click()}>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            style={{ display: 'none' }}
            accept=".pdf,.txt"
          />
          {isUploading ? (
            <Loader2 className="upload-icon animate-spin" size={24} />
          ) : (
            <Upload className="upload-icon" size={24} />
          )}
          <h4 style={{ fontSize: '0.9rem', marginBottom: '4px' }}>Upload Document</h4>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>PDF or TXT pharmaceutical data</p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header style={{ padding: '1.25rem 2rem', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Activity size={20} color="var(--accent-primary)" />
            <span style={{ fontWeight: 600 }}>Pharma Insights Live</span>
          </div>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
             <div style={{ padding: '4px 12px', background: 'rgba(35, 134, 54, 0.1)', color: 'var(--success)', borderRadius: '20px', fontSize: '0.75rem', fontWeight: 600 }}>
               System Ready
             </div>
          </div>
        </header>

        <div className="chat-container">
          <AnimatePresence>
            {messages.length === 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                style={{ textAlign: 'center', marginTop: '10vh' }}
              >
                <div style={{ width: '80px', height: '80px', background: 'var(--glass-bg)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifySelf: 'center', justifyContent: 'center', marginBottom: '1.5rem', margin: '0 auto' }}>
                   <Brain size={40} color="var(--accent-primary)" />
                </div>
                <h2 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Welcome to MedInsights</h2>
                <p style={{ color: 'var(--text-secondary)', maxWidth: '500px', margin: '0 auto' }}>
                  Upload medical reports or pharmaceutical documents to get AI-powered Retrieval-Augmented insights. I can analyze trends, extract key data points, and answer complex queries.
                </p>
              </motion.div>
            )}

            {messages.map((msg, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`message ${msg.role}`}
              >
                 <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', fontSize: '0.75rem', opacity: 0.7 }}>
                    {msg.role === 'user' ? <User size={14} /> : <Brain size={14} />}
                    {msg.role === 'user' ? 'Scientist' : 'MedInsights AI'}
                 </div>
                 <div className="markdown-content">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                 </div>
                 {msg.sources && msg.sources.length > 0 && (
                   <div style={{ marginTop: '12px', paddingTop: '8px', borderTop: '1px solid var(--glass-border)', fontSize: '0.7rem' }}>
                      <span style={{ fontWeight: 600 }}>Sources:</span> {msg.sources.join(', ')}
                   </div>
                 )}
              </motion.div>
            ))}
          </AnimatePresence>
          {isLoading && (
            <div className="message assistant">
               <Loader2 className="animate-spin" size={20} color="var(--accent-primary)" />
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <form className="input-area" onSubmit={handleSendMessage}>
          <div className="input-wrapper">
             <input
               type="text"
               placeholder="Ask a medical insight query..."
               value={inputText}
               onChange={(e) => setInputText(e.target.value)}
             />
          </div>
          <button type="submit" className="send-btn" disabled={isLoading}>
            <Send size={20} />
          </button>
        </form>
      </main>
    </div>
  );
}

export default App;
