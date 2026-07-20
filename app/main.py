from fastapi import FastAPI

from app.database import Base, engine
from app.models import *

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Food Pre-Booking chatbot",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "message": "Welcome to Smart WhatsApp AI Chatbot API"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }