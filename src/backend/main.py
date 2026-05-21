from fastapi import FastAPI
from src.backend.app.api import music
from src.backend.app.models.track import init_db
from src.backend.app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# Initialize database
init_db()

# Include routers
app.include_router(music.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Music Downloader API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
