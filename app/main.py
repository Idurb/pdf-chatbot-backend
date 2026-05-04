from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "PDF Chatbot Backend Running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}



class QueryRequest(BaseModel):
    question: str

@app.post("/query")
def query(req: QueryRequest):
    return {
        "question": req.question,
        "answer": "This is a placeholder response"
    }