# import os
# import shutil
# from fastapi import FastAPI,UploadFile, File
# from pydantic import BaseModel
# from app.core.database import Base, engine
# from app.models import document
# from app.core.database import SessionLocal
# from app.models.document import Document
# from app.models import chunk
# from rag.pdf_parser import extract_text
# from rag.chunker import chunk_text
# from rag.embedding import get_embedding
# from rag.vector_store import add_embeddings, chunk_store
# from rag.router import classify_query
# from rag.context_builder import build_context
# Base.metadata.create_all(bind=engine)


# app = FastAPI()

# @app.get("/")
# def read_root():
#     return {"message": "PDF Chatbot Backend Running"}

# @app.get("/health")
# def health_check():
#     return {"status": "ok"}



# class QueryRequest(BaseModel):
#     question: str




# @app.post("/upload")
# def upload_pdf(file: UploadFile = File(...)):
#     db = SessionLocal()
#     UPLOAD_DIR = "uploads"
#     os.makedirs(UPLOAD_DIR, exist_ok=True)
#     file_path = os.path.join(UPLOAD_DIR, file.filename)

#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     doc = Document(filename=file.filename, filepath=file_path)
#     db.add(doc)
#     db.commit()
#     db.refresh(doc)
#     # Extract text
#     text = extract_text(file_path)

#     # Chunk text
#     chunks = chunk_text(text)

#     # Save chunks
#     for text in chunks:
#         db_chunk = chunk.Chunk(document_id=doc.id, chunk_content=text)
#         db.add(db_chunk)

#     # Get embeddings
#     embeddings = [get_embedding(text) for text in chunks]

#     # Add embeddings to vector store
#     add_embeddings(embeddings, chunks)

#     db.commit()

#     return {
#         "document_id": doc.id,
#         "chunks_created": len(chunks)
#     }
# from rag.vector_store import search

# # @app.post("/query")
# # def query(req: QueryRequest):
# #     query_embedding = get_embedding(req.question)

# #     results = search(query_embedding)

# #     return {
# #         "question": req.question,
# #         "retrieved_chunks": results
# #     }
# from rag.generator import generate_answer

# # @app.post("/query")
# # def query(req: QueryRequest):
# #     query_embedding = get_embedding(req.question)

# #     chunks = search(query_embedding)

# #     answer = generate_answer(req.question, chunks)

# #     return {
# #         "question": req.question,
# #         "answer": answer,
# #         "sources": chunks
# #     }
# @app.post("/query")
# def query(req: QueryRequest):
#     query_type = classify_query(req.question)

#     db = SessionLocal()

#     if query_type == "metadata":
#         doc = db.query(Document).first()

#         if not doc:
#             return {"answer": "No document found"}

#         return {
#             "question": req.question,
#             "type": "metadata",
#             "answer": f"Case: {doc.case_name or 'Not available'}, Date: {doc.judgment_date or 'Not available'}",
#             "confidence": "high"
#         }

#     # 🔍 semantic search
#     query_embedding = get_embedding(req.question)
#     chunks = search(query_embedding, top_k=5)

#     # include first chunk (important!)
#     if chunk_store:
#         chunks.insert(0, chunk_store[0])

#     context = build_context(chunks)

#     answer = generate_answer(req.question, context)

#     return {
#         "question": req.question,
#         "type": "semantic",
#         "answer": answer,
#         "sources": chunks[:3],
#         "confidence": "high" if len(chunks) > 2 else "low"
#     }
# from rag.vector_store import reset_index

# @app.on_event("startup")
# def load_embeddings():
#     reset_index()

#     db = SessionLocal()
#     chunks = db.query(chunk.Chunk).all()

#     texts = [c.chunk_content for c in chunks]

#     if texts:
#         embeddings = [get_embedding(t) for t in texts]
#         add_embeddings(embeddings, texts)

#     print(f"Loaded {len(texts)} chunks into FAISS")
import os
import shutil
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

from app.core.database import Base, engine, SessionLocal
from app.models.document import Document
from app.models import chunk

from rag.pdf_parser import extract_text
from rag.chunker import chunk_text
from rag.embedding import get_embedding
from rag.vector_store import add_embeddings, search, reset_index, chunk_store
from rag.router import classify_query
from rag.context_builder import build_context
from rag.generator import generate_answer

Base.metadata.create_all(bind=engine)

app = FastAPI()


# -----------------------------
# Health APIs
# -----------------------------
@app.get("/")
def read_root():
    return {"message": "PDF Chatbot Backend Running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}


# -----------------------------
# Request Model
# -----------------------------
class QueryRequest(BaseModel):
    question: str


# -----------------------------
# Upload API
# -----------------------------
@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):
    db = SessionLocal()

    UPLOAD_DIR = "uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create document
    doc = Document(filename=file.filename, filepath=file_path)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Extract text
    text = extract_text(file_path)

    # Chunk text
    chunks = chunk_text(text)

    # Save chunks
    for ch in chunks:
        db_chunk = chunk.Chunk(document_id=doc.id, chunk_content=ch)
        db.add(db_chunk)

    # Create embeddings
    embeddings = [get_embedding(ch) for ch in chunks]
    add_embeddings(embeddings, chunks)

    # -----------------------------
    # Metadata extraction
    # -----------------------------
    first_text = text[:1500]

    meta_prompt = f"""
Extract:
- Case Name
- Judgment Date
- Judge Name

Return exactly like:
Case Name: ...
Judgment Date: ...
Judge Name: ...

Text:
{first_text}
"""

    meta_response = generate_answer("Extract metadata", meta_prompt)

    case_name, date, judge = None, None, None

    for line in meta_response.split("\n"):
        if "Case Name:" in line:
            case_name = line.split("Case Name:")[-1].strip()
        elif "Judgment Date:" in line:
            date = line.split("Judgment Date:")[-1].strip()
        elif "Judge Name:" in line:
            judge = line.split("Judge Name:")[-1].strip()

    doc.case_name = case_name
    doc.judgment_date = date
    doc.judge = judge

    db.commit()

    return {
        "document_id": doc.id,
        "chunks_created": len(chunks),
        "metadata": {
            "case_name": case_name,
            "date": date,
            "judge": judge
        }
    }


# -----------------------------
# Query API (SMART RAG)
# -----------------------------
@app.post("/query")
def query(req: QueryRequest):
    db = SessionLocal()
    query_type = classify_query(req.question)

    # Metadata query
    if query_type == "metadata":
        doc = db.query(Document).first()

        if not doc:
            return {"answer": "No document found"}

        return {
            "question": req.question,
            "type": "metadata",
            "answer": f"Case: {doc.case_name or 'Not available'}, Date: {doc.judgment_date or 'Not available'}",
            "confidence": "high"
        }

    # Semantic query
    query_embedding = get_embedding(req.question)
    chunks = search(query_embedding, top_k=5)

    if chunk_store:
        chunks.insert(0, chunk_store[0])

    context = build_context(chunks)
    answer = generate_answer(req.question, context)

    return {
        "question": req.question,
        "type": "semantic",
        "answer": answer,
        "sources": chunks[:3],
        "confidence": "high" if len(chunks) > 2 else "low"
    }


# -----------------------------
# Startup loader
# -----------------------------
@app.on_event("startup")
def load_embeddings():
    reset_index()

    db = SessionLocal()
    chunks = db.query(chunk.Chunk).all()

    texts = [c.chunk_content for c in chunks]

    if texts:
        embeddings = [get_embedding(t) for t in texts]
        add_embeddings(embeddings, texts)

    print(f"Loaded {len(texts)} chunks into FAISS")