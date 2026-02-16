import os
import base64
import gc
import tempfile
import time
import uuid
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

import streamlit as st

# Load environment variables from .env file
load_dotenv()

if "id" not in st.session_state:
    st.session_state.id = uuid.uuid4()
    st.session_state.file_cache = {}

session_id = st.session_state.id


@st.cache_resource
def load_llm():
    # Initialize Groq LLM - you'll need to set GROQ_API_KEY environment variable
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",  # or "mixtral-8x7b-32768" or other Groq models
        temperature=0.1,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    return llm

def reset_chat():
    st.session_state.messages = []
    st.session_state.context = None
    gc.collect()


def display_pdf(file):
    # Opening file from file path
    st.markdown("### PDF Preview")
    base64_pdf = base64.b64encode(file.read()).decode("utf-8")

    # Embedding PDF in HTML
    pdf_display = f"""<iframe src="data:application/pdf;base64,{base64_pdf}" width="400" height="100%" type="application/pdf"
                        style="height:100vh; width:100%"
                    >
                    </iframe>"""

    # Displaying File
    st.markdown(pdf_display, unsafe_allow_html=True)


with st.sidebar:
    st.header(f"Add your documents!")
    
    # Check if API key is loaded from .env
    if not os.getenv("GROQ_API_KEY"):
        st.warning("⚠️ GROQ_API_KEY not found in .env file")
        # Optional: Allow manual entry as fallback
        groq_api_key = st.text_input("Enter your Groq API Key (optional)", type="password", help="Get your API key from https://console.groq.com/")
        if groq_api_key:
            os.environ["GROQ_API_KEY"] = groq_api_key
    else:
        st.success("✅ Groq API Key loaded from .env")
    
    uploaded_file = st.file_uploader("Choose your `.pdf` file", type="pdf")

    if uploaded_file:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                file_key = f"{session_id}-{uploaded_file.name}"
                st.write("Indexing your document...")

                if file_key not in st.session_state.get('file_cache', {}):
                    if not os.getenv("GROQ_API_KEY"):
                        st.error("Please enter your Groq API Key in the sidebar first!")
                        st.stop()

                    if os.path.exists(temp_dir):
                        # Load PDF using LangChain's PyPDFLoader
                        loader = PyPDFLoader(file_path)
                        docs = loader.load()
                    else:    
                        st.error('Could not find the file you uploaded, please check again...')
                        st.stop()
                    
                    # Split documents into chunks
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=1000,
                        chunk_overlap=200,
                        length_function=len,
                    )
                    chunks = text_splitter.split_documents(docs)

                    # Setup embedding model
                    embed_model = HuggingFaceEmbeddings(
                        model_name="BAAI/bge-large-en-v1.5",
                        model_kwargs={'device': 'cpu'},
                        encode_kwargs={'normalize_embeddings': True}
                    )
                    
                    # Create vector store
                    vectorstore = FAISS.from_documents(chunks, embed_model)
                    
                    # Setup LLM
                    llm = load_llm()
                    
                    # Create retriever
                    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
                    
                    # Store retriever and LLM for RAG function
                    qa_chain = {
                        "retriever": retriever,
                        "llm": llm
                    }
                    
                    st.session_state.file_cache[file_key] = qa_chain
                else:
                    qa_chain = st.session_state.file_cache[file_key]

                # Inform the user that the file is processed and Display the PDF uploaded
                st.success("Ready to Chat!")
                # Reset file pointer for PDF display
                uploaded_file.seek(0)
                display_pdf(uploaded_file)
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.stop()     

col1, col2 = st.columns([6, 1])

with col1:
    st.header(f"Chat with Docs using Groq LLM")

with col2:
    st.button("Clear ↺", on_click=reset_chat)

# Initialize chat history
if "messages" not in st.session_state:
    reset_chat()


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Accept user input
if prompt := st.chat_input("What's up?"):
    # Check if document is loaded
    if "file_cache" not in st.session_state or not st.session_state.file_cache:
        st.warning("Please upload a PDF document first!")
        st.stop()
    
    # Get the first available chain (for simplicity, using the first one)
    qa_chain = list(st.session_state.file_cache.values())[0]
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Get response using RAG
        try:
            # Retrieve relevant documents
            retriever = qa_chain["retriever"]
            llm = qa_chain["llm"]
            
            # Get relevant documents (LangChain retrievers are Runnables -> use .invoke)
            docs = retriever.invoke(prompt)
            
            # Format context from documents
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Create prompt with context
            prompt_template = (
                "Context information is below.\n"
                "---------------------\n"
                f"{context}\n"
                "---------------------\n"
                "Given the context information above I want you to think step by step to answer the query in a crisp manner, in case you don't know the answer say 'I don't know!'.\n"
                f"Query: {prompt}\n"
                "Answer: "
            )
            
            # Get response from LLM
            response = llm.invoke(prompt_template)
            full_response = response.content if hasattr(response, 'content') else str(response)
            
            # Simulate streaming for better UX
            for i in range(len(full_response)):
                partial_response = full_response[:i+1]
                message_placeholder.markdown(partial_response + "▌")
                time.sleep(0.01)  # Small delay for streaming effect
            
            message_placeholder.markdown(full_response)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            message_placeholder.markdown(error_msg)
            full_response = error_msg

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
