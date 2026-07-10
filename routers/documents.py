from fastapi import APIRouter, Depends, HTTPException, UploadFile , File, Response
from sqlalchemy.ext.asyncio import AsyncSession
from security import get_current_user
from schemas import DocumentCreate, AskRequest
from database import get_db
from models import Document
from sqlalchemy import select
import pdfplumber
from rag.chunker import chunk_text
from rag.embedder import embed_chunks, get_client, embed_query
from fastapi.concurrency import run_in_threadpool
from rag.vector_store import ChromaVectorStore
from rag.generator import generate_answer

gemini_client = get_client()
vector_store = ChromaVectorStore()

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.get("/")# return the logged in user's document
async def get_documents(
    db: AsyncSession = Depends(get_db),
    user =  Depends(get_current_user), #Before running this function, first run get_current_user(). If authentication fails, stop here. Otherwise, give me the logged-in user.
    limit: int  = 10,
    skip: int = 0
):
    #query the doc table, get docs for current_user
    query = select(Document).where(Document.user_id == user.id).offset(skip).limit(limit) #only 10 at a time, in url write skip = 10 and you can get the next 10 docs 
    res = await db.execute(query)
    doc = res.scalars().all() #not scalar one or none as we need all 
    '''
    scalars() → extract the Document objects from the SQL result.
    all() → return them as a list.
    '''
    return doc #no need for if doc is none as in that case doc = [] which is fine

        
    

@router.post("/")
async def create_documents(
    document: DocumentCreate, #Recieve the JSON
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    new_document = Document(  #Document from models.py
        title = document.title,
        content = document.content,
        user_id = user.id
    )
    db.add(new_document)
    await db.commit()
    await db.refresh(new_document) #the row has been saved in the database, but the Python object (new_document) may not yet have the latest values that the database generated, such as:id(check model Document)
    return new_document

#/{document_id} is a path parameter, whatever value in URL appears after /document is taken as document_id then we convert it by type hint in function definition
@router.get("/{document_id}") #GET /documents/{id}-> user fetching a particular doc by its id, fetching allowed only if he owns it
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)    
):
    query = select(Document).where(
        Document.id == document_id,
        Document.user_id == user.id
    )

    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return document


@router.delete("/{document_id}", status_code=204)  # DELETE /documents/{id} -> remove a document you own, and its indexed chunks
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    query = select(Document).where(
        Document.id == document_id,
        Document.user_id == user.id
    )
    result = await db.execute(query)
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    await run_in_threadpool(vector_store.delete_document, user.id, document_id)
    await db.delete(doc)
    await db.commit()
    return Response(status_code=204)

'''
file: UploadFile = File(...) , UploadFile tells FastAPI this parameter is a file being uploaded 
File(...)-> Expect this value from multipart/form-data, not JSON.
multipart/form-data → This format is used when forms send files or mixed data (text + files). 
For example, uploading a profile picture along with your name.
'''
@router.post("/upload")
async def upload_document(
    file : UploadFile, 
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):   
    u_id = user.id #need it in threadpool, before it db.commit shuts down every ORM object attached to the session
    if file.filename.endswith(".txt"):
        content = await file.read() #reading a file is an asynchronous operation, so we wait until it's finished.
    #await file.read() loads the whole uploaded file into memory as bytes, so notes.txt with "Hello\nFastAPI" becomes b"Hello\nFastAPI" because files are transferred as bytes, not strings
        text = content.decode("utf-8")
    elif file.filename.endswith(".pdf"):
        with pdfplumber.open(file.file) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages]
        text = "\n".join(pages_text)
    else:
        raise HTTPException(
                status_code=400,
                detail = "Unsupported File Type"
            )
    new_doc = Document(
        title = file.filename,
        content = text,
        user_id = user.id
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    chunks = chunk_text(text)
    '''
    run_in_threadpool() is a FastAPI utility (from Starlette) that lets you safely 
    run blocking or synchronous functions (BASICALLY, ALL RAG FUNCTIONS HERE)(ALL DB CALLS ARE ASYNCHRONOUS OTOH)
    inside a thread pool without freezing the main async event loop.
    You use it when you need to call regular Python functions (like file I/O, database drivers, or CPU-heavy tasks) inside an async route handler.
    '''
    embeddings = await run_in_threadpool(embed_chunks, gemini_client, chunks)
    await run_in_threadpool(
            vector_store.add_chunks, chunks, embeddings, u_id, new_doc.id
        )
    return new_doc

@router.post("/{document_id}/ask")
async def ask_question(
    document_id :int ,
    body : AskRequest,
    db:AsyncSession= Depends(get_db),
    user = Depends(get_current_user),
):
    u_id = user.id #capture before any potential commit; same lesson as before
    query = select(Document).where(
        Document.user_id == u_id,
        Document.id == document_id
    )
    result = await db.execute(query)
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail= "Document not found"
        )
    
    qv = await run_in_threadpool(embed_query,gemini_client,body.question)
    sources = await run_in_threadpool(vector_store.search, qv,u_id, document_id, top_k=3)
    answer = await run_in_threadpool(generate_answer, gemini_client, body.question,sources)
    return {
        "answer": answer,
        "sources": sources,  # each has text + similarity
    }