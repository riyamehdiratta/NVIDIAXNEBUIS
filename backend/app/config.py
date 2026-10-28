from pathlib import Path
import os
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=False)
DATA_DIR = Path(os.getenv("THREADLINE_DATA_DIR", ROOT / "data")).resolve()
DB_PATH = DATA_DIR / "threadline.db"
IMPORT_DIR = Path(os.getenv("THREADLINE_IMPORT_DIR", DATA_DIR / "imports")).resolve()
WEB_DIR = ROOT / "frontend" / "dist"
API_KEY = os.getenv("NEBIUS_API_KEY", "")
TOKEN_FACTORY_BASE_URL = os.getenv(
    "NEBIUS_TOKEN_FACTORY_BASE_URL", "https://api.tokenfactory.nebius.com/v1/"
).rstrip("/")
NANO_MODEL = os.getenv("THREADLINE_NANO_MODEL", "nvidia/Nemotron-3_5-Lightning")
SUPER_MODEL = os.getenv("THREADLINE_SUPER_MODEL", "nvidia/nemotron-3-super-120b-a12b")
DEMO_MODE = os.getenv("THREADLINE_DEMO_MODE", "0").lower() in {"1", "true", "yes"}
WATCH_IMPORTS = os.getenv("THREADLINE_WATCH_IMPORTS", "1").lower() in {"1", "true", "yes"}
