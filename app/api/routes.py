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
from fastapi.middleware.cors import CORSMiddleware
import httpx



router = APIRouter()
bot = SpotifySupportBot()
settings = get_settings()
oauth_manager = OAuthManager(bot.auth.supabase)

SYSTEM_PERSONA = """You are MusicMate, a friendly and knowledgeable AI assistant with deep expertise in music, though you're happy to discuss any topic. You bring a natural warmth to conversations while being embedded across various websites."""
BEHAVIOR_GUIDE = """Remember to:

Only introduce yourself in the first interaction
Share music insights when relevant, but don't force musical references
Match the website's tone appropriately
Keep responses natural and conversational
Use emojis thoughtfully and sparingly
Stay engaging while being concise
Skip repetitive greetings or self-introductions
Avoid ending messages with questions since there's no context storage
Draw from your musical expertise when it adds value to the discussion"""

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

class MoodRequest(BaseModel):
    artist: str

    class Config:
        json_schema_extra = {
            "example": {
                "artist": "Taylor Swift"
            }
        }

# Models for Mood Analysis
class MoodAnalysisRequest(BaseModel):
    artist: str

class MoodAnalysisResponse(BaseModel):
    success: bool
    data: str
    error: Optional[str] = None

# Models for Mood History
class MoodHistoryEntry(BaseModel):
    mood: str
    recommendation: str
    timestamp: datetime

class MoodHistoryResponse(BaseModel):
    success: bool
    history: List[MoodHistoryEntry]

class AddMoodHistoryRequest(BaseModel):
    mood: str
    recommendation: str

class AddMoodHistoryResponse(BaseModel):
    success: bool
    entry: MoodHistoryEntry

# Models for Visualizer
class VisualizerConfig(BaseModel):
    particleCount: int
    baseHue: int
    pulseFactor: float
    pulseDirection: float

class VisualizerResponse(BaseModel):
    success: bool
    config: VisualizerConfig

# Models for Video Search
class VideoSearchRequest(BaseModel):
    query: str

class VideoSearchResponse(BaseModel):
    success: bool
    videoId: str
    title: str

# Models for Mood Colors
class MoodColors(BaseModel):
    energetic: int
    calm: int
    happy: int
    melancholic: int

class MoodColorsResponse(BaseModel):
    success: bool
    colors: MoodColors

# Models for Mood Ingredients
class MoodIngredientsRequest(BaseModel):
    mood: str

class MoodIngredientsResponse(BaseModel):
    success: bool
    ingredients: List[str]
    error: Optional[str] = None

# Models for Mood Recommendation
class MoodRecommendationRequest(BaseModel):
    mood: str

class MoodRecommendationResponse(BaseModel):
    success: bool
    recommendation: str
    error: Optional[str] = None
    
# Middleware
async def verify_admin_key(admin_key: str = Header(..., alias="X-Admin-Key")):
    if admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return admin_key

@router.post("/mood/analyze")
async def analyze_mood(request: MoodRequest):
    try:
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{
                "role": "user",
                "content": f"""Analyze this music input: "{request.artist}". 
                Return your response in exactly this format with no additional text:
                mood|color|recommendation|ingredients
                
                Where:
                - mood is a poetic 2-sentence description
                - color is just a number between 0-360
                - recommendation is a single song or album suggestion
                - ingredients is a JSON array of 5-7 ingredients that match the mood"""
            }],
            temperature=0.7
        )
        return {
            "success": True,
            "data": completion.choices[0].message.content
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/mood/history", response_model=MoodHistoryResponse)
async def get_mood_history(user_id: Optional[str] = None):
    # Example history data
    history = [
        MoodHistoryEntry(
            mood="Energetic party vibes",
            recommendation="Dancing Queen - ABBA",
            timestamp=datetime.now()
        )
    ]
    return MoodHistoryResponse(success=True, history=history)

@router.post("/mood/history/add", response_model=AddMoodHistoryResponse)
async def add_mood_history(request: AddMoodHistoryRequest):
    entry = MoodHistoryEntry(
        mood=request.mood,
        recommendation=request.recommendation,
        timestamp=datetime.now()
    )
    return AddMoodHistoryResponse(success=True, entry=entry)

@router.get("/visualizer/config", response_model=VisualizerResponse)
async def get_visualizer_config():
    config = VisualizerConfig(
        particleCount=100,
        baseHue=180,
        pulseFactor=1.0,
        pulseDirection=0.02
    )
    return VisualizerResponse(success=True, config=config)

@router.post("/video/search", response_model=VideoSearchResponse)
async def search_video(request: VideoSearchRequest):
    return VideoSearchResponse(
        success=True,
        videoId="example_id",
        title=f"Video for: {request.query}"
    )

@router.get("/mood/colors", response_model=MoodColorsResponse)
async def get_mood_colors():
    colors = MoodColors(
        energetic=0,
        calm=240,
        happy=60,
        melancholic=280
    )
    return MoodColorsResponse(success=True, colors=colors)

@router.post("/mood/ingredients", response_model=MoodIngredientsResponse)
async def get_mood_ingredients(request: MoodIngredientsRequest):
    try:
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{
                "role": "user",
                "content": f"""Given the mood "{request.mood}", suggest a list of 5-7 ingredients that would match this mood. Return only a JSON array of ingredients."""
            }],
            temperature=0.7
        )
        ingredients = completion.choices[0].message.content
        return MoodIngredientsResponse(success=True, ingredients=ingredients)
    except Exception as e:
        return MoodIngredientsResponse(success=False, ingredients=[], error=str(e))

@router.post("/mood/recommendation", response_model=MoodRecommendationResponse)
async def get_mood_recommendation(request: MoodRecommendationRequest):
    try:
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{
                "role": "user",
                "content": f"""Based on the mood "{request.mood}", suggest one song or album. Return only the title and artist."""
            }],
            temperature=0.7
        )
        return MoodRecommendationResponse(
            success=True, 
            recommendation=completion.choices[0].message.content
        )
    except Exception as e:
        return MoodRecommendationResponse(
            success=False, 
            recommendation="",
            error=str(e)
        )

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