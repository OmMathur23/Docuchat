from fastapi import FastAPI, Depends
from pydantic import BaseModel
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

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
async def skip(skip : int = 0, limit : int = 10, db: AsyncSession = Depends(get_db)):
    return {"skip": skip, "limit" : limit}

@app.post("/items")
def create_doc(doc: DocumentCreate):
    return doc
