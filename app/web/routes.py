from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

@router.get("/widget")
async def widget(request: Request):
    """Serve the widget HTML"""
    return templates.TemplateResponse("widget.html", {"request": request})

