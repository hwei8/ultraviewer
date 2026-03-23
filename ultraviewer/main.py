import argparse
import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from ultraviewer.db import init_db
from ultraviewer.api.tabs import router as tabs_router
from ultraviewer.api.suites import router as suites_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

def create_app() -> FastAPI:
    app = FastAPI(title="UltraViewer", lifespan=lifespan)
    app.include_router(tabs_router)
    app.include_router(suites_router)
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    return app

app = create_app()

def cli():
    parser = argparse.ArgumentParser(description="UltraViewer Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--db-path", type=str, default=None, help="SQLite database path")
    args = parser.parse_args()
    if args.db_path:
        os.environ["ULTRAVIEWER_DB_PATH"] = args.db_path
    uvicorn.run("ultraviewer.main:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    cli()
