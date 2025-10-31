from fastapi import FastAPI
from src.app.core.config import settings
from src.app.core.startup import validate_environment

app = FastAPI(title=settings.PROJECT_NAME)

@app.on_event("startup")  # type: ignore[misc]
async def startup_event() -> None:
    validate_environment()
