from supabase import create_client, Client
from app.config import get_settings

settings = get_settings()

# Initialize Supabase client
supabase: Client = create_client(
    supabase_url=settings.SUPABASE_URL,
    supabase_key=settings.SUPABASE_KEY
)