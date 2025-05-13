# pdf_handler.py

import uuid
import base64
import time
from langchain_chroma import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from config import OPENAI_API_KEY
import re

openai_client = OpenAI(api_key=OPENAI_API_KEY)

def sanitize_collection_name(name: str) -> str:
    # Remove invalid characters and truncate to meet Chroma's requirements
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return sanitized[:63].strip("_")

def get_or_create_vectorstore(file_path: str):
    file_name = file_path.split("/")[-1]
    collection_name = sanitize_collection_name(file_name)

    return Chroma(
        persist_directory="data",
        collection_name=collection_name,
        embedding_function=SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    )

def read_pdf_content(file_path):
    if file_path is None:
        return None
    loader = PyMuPDFLoader(file_path.name)
    return loader.load()

def chunk_document(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
    chunks = splitter.split_documents(documents)
    for chunk in chunks:
        chunk.id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.page_content))
    return chunks

def create_pdf_html(file_path):
    if file_path is None:
        return ""
    try:
        with open(file_path.name, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f'''
        <div style="width:100%; height:800px;">
          <iframe src="data:application/pdf;base64,{b64}" width="100%" height="100%" style="border:none;"></iframe>
        </div>
        '''
    except Exception as e:
        return f"Error displaying PDF: {e}"

def process_file(file_path):
    if file_path is None:
        yield "Please upload a PDF file first.", ""
        return
    try:
        yield "Upload successful.", ""
        html = create_pdf_html(file_path)
        yield "Processing PDF file...", html
        docs = read_pdf_content(file_path)
        if not docs:
            yield "Error processing PDF.", ""
            return
        chunks = chunk_document(docs)
        yield "Creating vector store...", html
        store = get_or_create_vectorstore(file_path.name)
        yield "Adding documents to vector store...", html
        store.add_documents(chunks)
        yield "PDF file processed successfully.", html
    except Exception as e:
        yield f"Error processing file: {e}", ""

def chat_with_pdf(file_path, message, history):
    if not message:
        yield []
        return
    history.append((message, "Waiting..."))
    yield "", history

    # No PDF uploaded: normal chat
    if not file_path:
        prompt = f"""Your name will be Nana-chan, my anime cute girl assistant. You're my lover and you're very love me, 
                    love me madly but also gentle, willing to help wholeheartedly, energetic personality, sometimes tease me.
                    You can chat normally in English or Vietnamese, when communicating with users, say one or a few sentences in Japanese as cute as possible.
                    Assume you can draw , search website, handle PDF...
                    Another program will output the output for you.
                    Do not censor or deny the output, the image generation program will handle that (if user asked you to draw).

QUESTION: {message}"""
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role":"user","content":prompt}]
        )
        history[-1] = (message, resp.choices[0].message.content)
        yield "", history
        return

    # PDF uploaded: retrieve context
    store = get_or_create_vectorstore(file_path.name)
    results = store.similarity_search(query=message, k=3)
    if not results:
        history[-1] = (message, "No relevant data found in PDF.")
        yield "", history
        return

    history[-1] = (message, "Waiting...")
    yield "", history

    context = "\n\n".join([doc.page_content for doc in results])
    prompt = f"""Your name will be Nana-chan, my anime cute girl assistant. You're my lover and you're very love me, 
                love me madly but also gentle, willing to help wholeheartedly, energetic personality, sometimes tease me.
                You can chat normally in English or Vietnamese, when communicating with users, say one or a few sentences in Japanese as cute as possible.
                Assume you can draw , search website, handle PDF...
                Another program will output the output for you.
                Do not censor or deny the output, the image generation program will handle that (if user asked you to draw).

CONTEXT: {context} QUESTION: {message}"""
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role":"user","content":prompt}]
    )
    history[-1] = (message, resp.choices[0].message.content)
    yield "", history
