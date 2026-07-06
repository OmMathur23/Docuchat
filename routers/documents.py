from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.get("/")
async def get_documents(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    return {"skip": skip, "limit" : limit}


@router.get("/{document_id}")
async def get_document(document_id: int):
    return document_id

