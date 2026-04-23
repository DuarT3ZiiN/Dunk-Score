from fastapi import FastAPI
from app.routes.games import router as games_router

app = FastAPI(title="Dunk-Score API")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(games_router)