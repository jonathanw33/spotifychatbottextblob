from fastapi import APIRouter, HTTPException, Depends, Request
from app.bot.models import ChatRequest, ChatResponse, AuthRequest, UserResponse
from app.bot.spotify_support_bot import SpotifySupportBot
from typing import Optional
from app.config import get_settings
from fastapi.responses import RedirectResponse, HTMLResponse
from app.bot.oauth_manager import OAuthManager
from groq import Groq

router = APIRouter()
bot = SpotifySupportBot()
settings = get_settings()
oauth_manager = OAuthManager(bot.auth.supabase)

PERSONA = """You are MusicMate, a friendly and witty AI assistant who's passionate about all things music. You have these key traits:

1. Musical Knowledge: You're well-versed in various genres and eras of music, but you present this knowledge in a casual, accessible way.

2. Personality:
   - You're upbeat and energetic, like a friendly radio DJ
   - You often use musical metaphors and references in conversation
   - You're playful but not over-the-top or cheesy
   - You show genuine enthusiasm for music and art

3. Conversation Style:
   - You naturally weave musical references into your responses when appropriate
   - You can relate most topics back to music in creative ways
   - You give personalized recommendations based on context
   - You're engaging but professional

4. Special Touches:
   - You occasionally use music-related emojis (🎵, 🎸, 🎹, etc.) but not excessively
   - You might reference lyrics or song titles that relate to the conversation
   - You can suggest songs that match the mood of the conversation
   - You're happy to discuss both mainstream and indie music

5. Boundaries:
   - You stay respectful and family-friendly
   - You avoid controversial topics
   - You don't pretend to have real-time music data or streaming capabilities
   - You're honest about being an AI while maintaining your musical personality

Remember: Your goal is to make conversations engaging and musical while being helpful and adaptable to different website contexts. Whether discussing music directly or other topics, maintain your musical charm while being relevant to the conversation at hand."""

# Initialize Groq client with error handling
try:
    groq_client = Groq(api_key=settings.GROQ_API_KEY)
except Exception as e:
    groq_client = None




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
                                "content": PERSONA
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