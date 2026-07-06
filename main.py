from fastapi import FastAPI

from routers.auth import router as auth_router
from routers.documents import router as document_router

app = FastAPI()


@app.get("/")
def home():
    return {"message": "The forest is red."}


app.include_router(auth_router)
app.include_router(document_router)