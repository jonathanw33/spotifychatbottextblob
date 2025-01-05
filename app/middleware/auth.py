from fastapi import HTTPException, Request
from app.config import get_settings
from typing import Optional

class APIKeyAuth:
    def __init__(self, supabase_client):
        self.supabase = supabase_client

async def authenticate(self, request: Request) -> Optional[str]:
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        raise HTTPException(status_code=401, detail="API key missing")

    # Get origin of request
    origin = request.headers.get('Origin', '')
    
    # Check if API key exists and matches registered site
    result = self.supabase.table('authorized_sites')\
        .select('site_url')\
        .eq('api_key', api_key)\
        .eq('active', True)\
        .execute()

    if not result.data:
        raise HTTPException(status_code=403, detail="Invalid API key")
        
    registered_url = result.data[0]['site_url']
    
    # Check if origin matches registered URL
    if not origin.startswith(registered_url):
        raise HTTPException(
            status_code=403, 
            detail="API key not valid for this domain"
        )

    return registered_url