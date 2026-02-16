"""
DocuMind Backend API
FastAPI backend for RAG-based document Q&A using Groq LLM
"""
import os
import uuid
import tempfile
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Load environment variables
load_dotenv()

app = FastAPI(
    title="DocuMind RAG API",
    description="Backend API for document Q&A using RAG and Groq LLM",
    version="1.0.0"
)

# CORS middleware - allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (in production, use Redis or database)
SESSIONS: Dict[str, Dict[str, Any]] = {}


def load_llm():
    """Initialize Groq LLM"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment")
    return ChatGroq(
        model_name="llama-3.3-70b-versatile",  # Update with supported Groq model
        temperature=0.1,
        groq_api_key=api_key,
    )


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    session_id: str
    message: str


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "DocuMind API is running",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/sessions")
def list_sessions():
    """List all active sessions (for debugging)"""
    return {
        "session_count": len(SESSIONS),
        "sessions": {
            sid: {
                "file_name": session.get("file_name"),
                "chunk_count": session.get("chunk_count", 0)
            }
            for sid, session in SESSIONS.items()
        }
    }


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and index a PDF document
    
    Returns:
        session_id: Unique session identifier
        file_name: Name of uploaded file
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    try:
        logger.info(f"Starting PDF upload: {file.filename}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, file.filename or "document.pdf")
            
            # Save uploaded file
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            logger.info(f"PDF saved, size: {len(content)} bytes")

            # Load PDF
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            logger.info(f"PDF loaded, {len(docs)} pages")

            # Split into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            chunks = text_splitter.split_documents(docs)
            logger.info(f"Document split into {len(chunks)} chunks")

            # Setup embeddings
            embed_model = HuggingFaceEmbeddings(
                model_name="BAAI/bge-large-en-v1.5",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )

            # Create vector store
            logger.info("Creating FAISS vectorstore...")
            vectorstore = FAISS.from_documents(chunks, embed_model)
            retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
            logger.info("Vectorstore created successfully")
            
            # Initialize LLM
            logger.info("Loading LLM...")
            llm = load_llm()
            logger.info("LLM loaded successfully")

            # Create session - store vectorstore, retriever, and embedding model
            session_id = str(uuid.uuid4())
            SESSIONS[session_id] = {
                "vectorstore": vectorstore,
                "retriever": retriever,
                "embed_model": embed_model,
                "llm": llm,
                "file_name": file.filename,
                "chunk_count": len(chunks)
            }
            
            logger.info(f"Session created: {session_id} with {len(chunks)} chunks")

            return {
                "session_id": session_id,
                "file_name": file.filename,
                "message": "Document indexed successfully",
                "chunk_count": len(chunks)
            }
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )


@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Chat with the document using RAG
    
    Args:
        req: ChatRequest with session_id and message
        
    Returns:
        answer: Response from the LLM
    """
    session = SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please upload a document first."
        )

    retriever = session.get("retriever")
    llm = session.get("llm")
    
    if not retriever or not llm:
        raise HTTPException(
            status_code=500,
            detail="Session data corrupted. Please upload the document again."
        )

    try:
        logger.info(f"Processing chat request for session: {req.session_id}")
        
        # Retrieve relevant documents
        logger.info(f"Retrieving documents for query: {req.message[:50]}...")
        docs = retriever.invoke(req.message)
        logger.info(f"Retrieved {len(docs)} relevant documents")
        
        if not docs or len(docs) == 0:
            logger.warning("No documents retrieved for query")
            return {
                "answer": "I couldn't find relevant information in the document to answer your question. Please try rephrasing or asking about a different topic."
            }
        
        # Format context from documents
        context = "\n\n".join([doc.page_content for doc in docs])
        logger.info(f"Context length: {len(context)} characters")

        # Create prompt with context
        prompt_template = (
            "Context information is below.\n"
            "---------------------\n"
            f"{context}\n"
            "---------------------\n"
            "Given the context information above I want you to think step by step "
            "to answer the query in a crisp manner, in case you don't know the "
            "answer say 'I don't know!'.\n"
            f"Query: {req.message}\n"
            "Answer: "
        )

        # Get response from LLM
        logger.info("Invoking LLM...")
        response = llm.invoke(prompt_template)
        answer = response.content if hasattr(response, "content") else str(response)
        logger.info(f"LLM response received, length: {len(answer)} characters")

        return {"answer": answer}
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    """Delete a session"""
    if session_id in SESSIONS:
        del SESSIONS[session_id]
        return {"message": "Session deleted successfully"}
    raise HTTPException(status_code=404, detail="Session not found")

