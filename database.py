from dotenv import load_dotenv
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL)

session_factory = async_sessionmaker(engine)

async def get_db():
    async with session_factory() as session:
        yield session

class Base(DeclarativeBase):
    pass







