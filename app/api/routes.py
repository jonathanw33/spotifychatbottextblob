from fastapi import APIRouter, HTTPException, Depends
from app.bot.models import ChatRequest, ChatResponse, AuthRequest, UserResponse
from app.bot.spotify_support_bot import SpotifySupportBot
from typing import Optional
from app.config import get_settings  # Add this import

router = APIRouter()
bot = SpotifySupportBot()
settings = get_settings()  # Add this to use settings in health check


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response, debug_info = bot.get_response(request.user_id, request.message)
        return ChatResponse(
            message=response,
            debug_info=debug_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auth/signup", response_model=UserResponse)
async def signup(request: AuthRequest):
    print(f"Signup attempt for email: {request.email}")  # Debug log
    try:
        success, result = bot.auth.sign_up(request.email, request.password)
        if success:
            # Convert User object to dict
            user_dict = {
                'id': result.id,
                'email': result.email,
                'created_at': result.created_at
            }
            return UserResponse(success=True, user=user_dict)
        raise HTTPException(status_code=400, detail=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auth/signin", response_model=UserResponse)
async def signin(request: AuthRequest):
    print(f"Signin attempt for email: {request.email}")  # Debug log

    try:
        success, result = bot.auth.sign_in(request.email, request.password)
        if success:
            # Convert User object to dict
            user_dict = {
                'id': result.id,
                'email': result.email,
                'last_sign_in_at': result.last_sign_in_at
            }
            return UserResponse(success=True, user=user_dict)
        raise HTTPException(status_code=401, detail=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "api_version": "1.0",
        "project": settings.PROJECT_NAME
    }