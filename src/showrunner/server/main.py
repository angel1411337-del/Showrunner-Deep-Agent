from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from showrunner.server.api import router

app = FastAPI(title="Showrunner Command Center")

# Allow CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Showrunner Command and Ops Center API"}
