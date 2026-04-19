import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

class RAGEngine:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("WARNING: GOOGLE_API_KEY not found in .env file.")

        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=api_key
            )
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0,
                google_api_key=api_key
            )
            print("[OK] Google Gemini AI initialized successfully.")
        except Exception as e:
            print(f"Error initializing Google AI components: {e}")
            self.embeddings = None
            self.llm = None

        self.vector_store_path = "faiss_index"
        self.vector_store = None

        if self.embeddings and os.path.exists(os.path.join(self.vector_store_path, "index.faiss")):
            try:
                self.vector_store = FAISS.load_local(
                    self.vector_store_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print("[OK] FAISS index loaded.")
            except Exception as e:
                print(f"Could not load FAISS index: {e}")

    def process_document(self, file_path):
        if not self.embeddings:
            raise Exception("Google AI not initialized. Check your API key.")

        if file_path.lower().endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding='utf-8')

        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)

        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        else:
            self.vector_store.add_documents(chunks)

        self.vector_store.save_local(self.vector_store_path)
        return len(chunks)

    def get_response(self, query, chat_history=[]):
        if not self.llm or not self.embeddings:
            return "Google API key is missing or invalid. Please check your .env file.", []

        # Convert history to LangChain message format
        lc_history = []
        for role, content in chat_history:
            if role == "user":
                lc_history.append(HumanMessage(content=content))
            else:
                lc_history.append(AIMessage(content=content))

        # If no documents uploaded yet, answer as general medical expert
        if self.vector_store is None:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert AI assistant specializing in medical and pharmaceutical data analysis. Answer the user's question as thoroughly and accurately as possible."),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ])
            chain = prompt | self.llm | StrOutputParser()
            answer = chain.invoke({"input": query, "chat_history": lc_history})
            return answer, []

        # RAG-based retrieval
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 4})

        # Step 1: Contextualize the question using history
        contextualize_prompt = ChatPromptTemplate.from_messages([
            ("system", "Given the chat history and the latest question, reformulate it as a standalone question. Do NOT answer it—just reformulate."),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        contextualize_chain = contextualize_prompt | self.llm | StrOutputParser()

        if lc_history:
            standalone_question = contextualize_chain.invoke({"input": query, "chat_history": lc_history})
        else:
            standalone_question = query

        # Step 2: Retrieve relevant docs
        source_docs = retriever.invoke(standalone_question)
        context = "\n\n".join([doc.page_content for doc in source_docs])

        # Step 3: Answer with context
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert AI assistant specializing in medical and pharmaceutical data analysis.
Use the following context from the uploaded documents to answer accurately and in detail.
If the answer is not in the context, say: "This information is not found in the uploaded documents."

Context:
{context}"""),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        qa_chain = qa_prompt | self.llm | StrOutputParser()
        answer = qa_chain.invoke({
            "input": query,
            "chat_history": lc_history,
            "context": context
        })

        return answer, source_docs


rag_engine = RAGEngine()
