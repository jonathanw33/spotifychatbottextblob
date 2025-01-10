from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path
from fastapi.responses import FileResponse

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

@router.get("/widget")
async def widget(request: Request):
    """Serve the widget HTML"""
    response = templates.TemplateResponse("widget.html", {"request": request})
    response.headers["X-Frame-Options"] = "ALLOW-FROM *"
    response.headers["Content-Security-Policy"] = "frame-ancestors *"
    return response

@router.get("/test")
async def test_page(request: Request):
    return templates.TemplateResponse("test.html", {"request": request})

@router.get("/static/js/widget-loader.js")
async def serve_widget_loader():
    file_path = Path("app/static/js/widget-loader.js")
    return FileResponse(
        file_path,
        media_type="application/javascript",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-cache"
        }
    )
    
@router.get("/admin")
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})    

@router.get("/aura")
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("musicalaura.html", {"request": request})    