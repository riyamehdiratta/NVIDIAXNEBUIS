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
from .workflows import router as workflows_router
from .apprenticeship import router as apprenticeship_router
from .preference_model import router as preference_router
from .conformal import router as conformal_router
from .synthesizer import router as synthesizer_router
from .world_model import router as world_model_router
from .live_chat import router as live_chat_router
from .mcp_connectors import router as mcp_connectors_router
from .device_agent import router as device_agent_router
from .backtest import router as backtest_router
from .dreaming import router as dreaming_router
from .privacy_proof import router as privacy_proof_router, CHAOS_ROUTER as chaos_router

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


app = FastAPI(title="Threadline Sovereign Delegate OS", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
app.include_router(workflows_router)
app.include_router(apprenticeship_router)
app.include_router(preference_router)
app.include_router(conformal_router)
app.include_router(synthesizer_router)
app.include_router(world_model_router)
app.include_router(live_chat_router)
app.include_router(mcp_connectors_router)
app.include_router(device_agent_router)
app.include_router(backtest_router)
app.include_router(dreaming_router)
app.include_router(privacy_proof_router)
app.include_router(chaos_router)


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
