import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import router
from .config import DEMO_MODE, IMPORT_DIR, WEB_DIR
from .db import connect, initialize, now_iso
from .worker import background_worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
stop_event = None
worker_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker_task, stop_event
    stop_event = asyncio.Event()
    initialize()
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    if DEMO_MODE:
        with connect() as db:
            count = db.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        if count == 0:
            from .api import load_demo
            load_demo()
    worker_task = asyncio.create_task(background_worker(stop_event))
    yield
    stop_event.set()
    if worker_task:
        await worker_task
        worker_task = None


app = FastAPI(title="Threadline Personal AI", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.get("/api/status")
def status():
    return {"ok": True, "version": "0.1.0", "local_data": True, "checked_at": now_iso()}


if WEB_DIR.exists():
    assets = WEB_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{path:path}")
    def web(path: str):
        candidate = (WEB_DIR / path).resolve()
        try:
            candidate.relative_to(WEB_DIR.resolve())
        except ValueError:
            return JSONResponse({"detail": "Not found"}, status_code=404)
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(WEB_DIR / "index.html")
