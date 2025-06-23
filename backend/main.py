from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# ensure DI bootstrap
import core.bootstrap  # noqa: F401

# Import routers
from backend.realtime import router as realtime_router
from backend.routers.asr import router as asr_router
from backend.routers.streaming_ws import router as stream_router

# Setup logging using the standard Python logging module
logger = logging.getLogger("ambient_scribe")

app = FastAPI(title="Ambient Scribe API")

# Define allowed origins
origins = [
    "http://localhost:4200",  # Angular frontend
    "http://127.0.0.1:4200", # Alternative for localhost
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, # Important for WebSockets and some auth flows
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount WebSocket router
app.include_router(realtime_router)
app.include_router(asr_router)
app.include_router(stream_router)
