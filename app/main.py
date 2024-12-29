from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.routes import router as api_router
from app.web.routes import router as web_router
from pathlib import Path
from starlette.responses import PlainTextResponse
import logging
import sys

# Completely reset and reconfigure logging
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Force everything to stdout
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='!!!! %(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)

# Create our app logger
logger = logging.getLogger("spotify_bot")
logger.setLevel(logging.DEBUG)

# Create a stdout handler
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('!!!! %(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = FastAPI(title="Spotify Support Bot API")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"!!!! INCOMING REQUEST: {request.method} {request.url.path}", flush=True)
    try:
        response = await call_next(request)
        print(f"!!!! OUTGOING RESPONSE: {request.method} {request.url.path} - {response.status_code}", flush=True)
        return response
    except Exception as e:
        print(f"!!!! ERROR IN REQUEST: {str(e)}", flush=True)
        raise

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

@app.get("/")
async def root(request: Request):
    print("!!!! ROOT ENDPOINT ACCESSED", flush=True)
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    print("!!!! HEALTH CHECK ACCESSED", flush=True)
    return {"status": "healthy"}

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", "https://spotify-bot.azurewebsites.net/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(web_router)