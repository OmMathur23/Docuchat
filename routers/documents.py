from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from security import get_current_user
from schemas import DocumentCreate
from database import get_db
from models import Document
from sqlalchemy import select

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
    



