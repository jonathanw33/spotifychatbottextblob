from fastapi import APIRouter, HTTPException, Depends, Request
from app.bot.models import ChatRequest, ChatResponse, AuthRequest, UserResponse
from app.bot.spotify_support_bot import SpotifySupportBot
from typing import Optional
from app.config import get_settings  # Add this import
from fastapi.responses import RedirectResponse, HTMLResponse
from app.bot.oauth_manager import OAuthManager

router = APIRouter()
bot = SpotifySupportBot()
settings = get_settings()  # Add this to use settings in health check
# Initialize OAuth manager with the same Supabase client used by the bot
oauth_manager = OAuthManager(bot.auth.supabase)



@router.get("/auth/spotify")
def spotify_login():
    """Initiate Spotify OAuth flow"""
    try:
        auth_url = oauth_manager.initiate_spotify_login()
        return RedirectResponse(url=auth_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auth/spotify/callback")
async def spotify_callback(code: str, state: str):
    success, result = oauth_manager.handle_spotify_callback(code, state)
    if not success:
        raise HTTPException(status_code=400, detail=result.get("error", "OAuth failed"))
    
    # Use the same popup handling as Google callback
    return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <body>
            <script>
                function sendMessageAndClose() {{
                    if (window.opener) {{
                        window.opener.postMessage({{
                            type: 'oauth-success',
                            userId: '{result["user"]["id"]}'
                        }}, '{settings.FRONTEND_URL}');
                        setTimeout(() => window.close(), 100);
                    }} else {{
                        window.location.href = '{settings.FRONTEND_URL}';
                    }}
                }}
                sendMessageAndClose();
            </script>
            <p>Authentication successful! You can close this window.</p>
        </body>
        </html>
    """)

@router.get("/auth/google")
def google_login():
    """Initiate Google OAuth flow"""
    try:
        auth_url = oauth_manager.initiate_google_login()
        return RedirectResponse(url=auth_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auth/google/callback")
async def google_callback(code: str, state: str):
    success, result = oauth_manager.handle_google_callback(code, state)
    if not success:
        raise HTTPException(status_code=400, detail=result.get("error", "OAuth failed"))
    
    return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <body>
            <script>
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'oauth-success',
                        userId: '{result["user"]["id"]}'
                    }}, '*');
                    setTimeout(() => window.close(), 500);
                }}
            </script>
            <p>Login successful! This window will close automatically.</p>
        </body>
        </html>
    """)

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
