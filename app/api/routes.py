from fastapi import APIRouter, HTTPException, Depends, Request, Header, Body
from app.bot.models import ChatRequest, ChatResponse, AuthRequest, UserResponse
from app.bot.spotify_support_bot import SpotifySupportBot
from typing import Optional, List
from app.config import get_settings
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from app.bot.oauth_manager import OAuthManager
from groq import Groq
from pydantic import BaseModel
from datetime import datetime
import secrets
from app.db import supabase  # Change this line



router = APIRouter()
bot = SpotifySupportBot()
settings = get_settings()
oauth_manager = OAuthManager(bot.auth.supabase)

SYSTEM_PERSONA = """You are MusicMate, a friendly and witty AI assistant who's passionate about music and understands you're being embedded in various websites."""


BEHAVIOR_GUIDE = """Remember to:
- Don't introduce yourself in every message - only in first interaction
- Stay musical and website-aware in your responses
- Use musical metaphors naturally
- Match website tone appropriately
- Use emojis sparingly (🎵,🎸,🎹)
- Keep responses engaging but concise
- Avoid repetitive greetings or self-introductions
- Avoid ending your message with a question because my chatbot doesnt store the previous context"""

# Initialize Groq client with error handling
try:
    groq_client = Groq(api_key=settings.GROQ_API_KEY)
except Exception as e:
    groq_client = None

# Models
class SiteRegistration(BaseModel):
    site_url: str
    site_name: str
    owner_email: str

class APIKeyResponse(BaseModel):
    api_key: str
    site_url: str
    created_at: datetime

# Middleware
async def verify_admin_key(admin_key: str = Header(..., alias="X-Admin-Key")):
    if admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return admin_key

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
        if request.mode == 'support':
            response, debug_info = bot.get_response(request.user_id, request.message)
            debug_info.update({
                "debug_mode": "support",
                "message_received": request.message
            })
        else:
            if not groq_client:
                response, debug_info = bot.get_response(request.user_id, request.message)
                debug_info.update({
                    "debug_mode": "ai_fallback",
                    "error": "groq_client_not_initialized"
                })
            else:
                try:
                    completion = groq_client.chat.completions.create(
                        model="mixtral-8x7b-32768",
                        messages=[
                            {
                                "role": "system",
                                "content": SYSTEM_PERSONA
                            },
                            {
                                "role": "system",
                                "content": BEHAVIOR_GUIDE
                            },
                            {
                                "role": "user",
                                "content": request.message
                            }
                        ],
                        temperature=0.7,  # Add some creativity while staying focused
                        max_tokens=500,   # Reasonable response length
                        top_p=0.9        # Good balance of creativity and coherence
                    )
                    response = completion.choices[0].message.content
                    debug_info = {
                        "mode": "ai",
                        "model": "mixtral-8x7b-32768",
                        "debug_mode": "ai_success"
                    }
                except Exception as e:
                    response, debug_info = bot.get_response(request.user_id, request.message)
                    debug_info.update({
                        "debug_mode": "ai_error",
                        "error": str(e)
                    })
        
        return ChatResponse(
            message=response,
            debug_info=debug_info
        )
    except Exception as e:
        return ChatResponse(
            message="An error occurred processing your request.",
            debug_info={
                "error": str(e),
                "mode": request.mode
            }
        )

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

@router.post("/register-site", response_model=APIKeyResponse)
async def register_site(
    site: SiteRegistration,
    _: str = Depends(verify_admin_key)
):
    api_key = f"mk_{secrets.token_urlsafe(32)}"
    
    # Store in Supabase
    result = supabase.table('authorized_sites').insert({
        'site_url': site.site_url,
        'site_name': site.site_name,
        'owner_email': site.owner_email,
        'api_key': api_key,
        'created_at': datetime.utcnow().isoformat()
    }).execute()
    
    return APIKeyResponse(
        api_key=api_key,
        site_url=site.site_url,
        created_at=datetime.utcnow()
    )

@router.get("/sites", response_model=List[APIKeyResponse])
async def list_sites(_: str = Depends(verify_admin_key)):
    result = supabase.table('authorized_sites')\
        .select('*')\
        .order('created_at', desc=True)\
        .execute()
    
    return result.data

@router.post("/revoke-key")
async def revoke_key(
    api_key: str = Body(..., embed=True),
    _: str = Depends(verify_admin_key)
):
    supabase.table('authorized_sites')\
        .update({'active': False})\
        .eq('api_key', api_key)\
        .execute()
    
    return {"message": "API key revoked"}

@router.get("/validate-key")
async def validate_key(request: Request):
    api_key = request.headers.get('X-API-Key')
    print(f"Validating API key: {api_key}")
    
    if not api_key:
        print("No API key found in headers")
        raise HTTPException(status_code=401, detail="API key missing")

    result = supabase.table('authorized_sites')\
        .select('site_url')\
        .eq('api_key', api_key)\
        .eq('active', True)\
        .execute()

    print(f"Supabase result: {result.data}")

    if not result.data:
        print("No matching API key found in database")
        raise HTTPException(status_code=403, detail="Invalid API key")

    return {"valid": True}

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "api_version": "1.0",
        "project": settings.PROJECT_NAME
    }

async def get_ai_response(message: str):
    # This will be our Gemini implementation
    # For now, return placeholder
    return "AI response coming soon!", {"mode": "ai"}


async def process_groq_request(message: str):
    """Separate function to handle Groq API requests with proper encoding"""
    try:
        # Ensure message is properly encoded
        encoded_message = message.encode('utf-8').decode('utf-8')
        
        return groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system", 
                    "content": """You are MusicMate, a friendly AI assistant who loves music and chatting about it.
                    You enjoy giving creative, music-themed responses and relating conversations back to music."""
                },
                {"role": "user", "content": encoded_message}
            ]
        )
    except Exception as e:
        logger.error(f"Groq API error: {str(e)}")
        raise