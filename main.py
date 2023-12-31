import uvicorn
from fastapi import FastAPI

from app import auth, routes

app = FastAPI()

app.include_router(auth.router)
app.include_router(routes.router)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True
    )
