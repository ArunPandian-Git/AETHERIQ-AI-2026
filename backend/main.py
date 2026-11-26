from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.health import router as health_router
from backend.api.routes.chat import router as chat_router
from backend.api.routes.conversations import router as conversations_router
from backend.api.routes.documents import router as documents_router

from backend.database.connection import initialize_database
from pathlib import Path
from fastapi.staticfiles import StaticFiles


app = FastAPI(
    title="AETHERIQ AI",
    description="Beyond Answers. Towards Intelligence.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# DATABASE INITIALIZATION
@app.on_event("startup")
async def startup_event():
    initialize_database()


# API ROUTES
app.include_router(health_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")



FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"

app.mount(
    "/",
    StaticFiles(directory=str(FRONTEND_DIR), html=True),
    name="frontend"
)