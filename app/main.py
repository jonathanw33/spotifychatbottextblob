from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from app.api.routes import router as api_router
from app.web.routes import router as web_router
from pathlib import Path
from starlette.responses import PlainTextResponse
from app.middleware.auth import APIKeyAuth
from app.config import get_settings
from app.db import supabase  # Import from db.py instead

app = FastAPI(title="Spotify Support Bot API")
settings = get_settings()


# Initialize API auth with Supabase client
api_auth = APIKeyAuth(supabase)


app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Skip auth for these paths
    skip_auth_paths = [
        '/docs', 
        '/openapi.json', 
        '/health', 
        '/admin',
        '/',  # Main site
        '/widget',  # Direct widget access
        '/static',  # Static files
        '/auth'  # Auth endpoints
    ]
    
    # Skip auth if path starts with any of skip_auth_paths
    if any(request.url.path.startswith(path) for path in skip_auth_paths):
        return await call_next(request)

    # Only check API key for widget-loader.js usage
    if 'X-API-Key' not in request.headers:
        raise HTTPException(status_code=401, detail="API key required for widget usage")

    try:
        site_url = await api_auth.authenticate(request)
        request.state.site_url = site_url
        return await call_next(request)
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Now we can use * because we have API key auth
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-API-Key"],  # Add API key header
    expose_headers=["*"]
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(web_router)