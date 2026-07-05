from fastapi import FastAPI
from pydantic import BaseModel

class DocumentCreate(BaseModel):
    title : str
    content : str


app = FastAPI()

@app.get("/")
def home():
    return {"message" : "The forest is red."}

@app.get("/documents/{document_id}")
def doc(document_id: int):
    return {"document_id": document_id, "title": "placeholder"}

@app.get('/documents')
def skip(skip : int = 0, limit : int = 10):
    return {"skip": skip, "limit" : limit}

@app.post("/items")
def create_doc(doc: DocumentCreate):
    return doc
