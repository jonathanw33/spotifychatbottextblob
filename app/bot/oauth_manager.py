from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta, timezone
import requests
import os
import secrets
from typing import Optional, Tuple, Dict
import json
import uuid 

class OAuthManager:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        # Spotify credentials
        self.spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        # Google credentials
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("OAUTH_REDIRECT_URI")
        self.widget_url = os.getenv("WIDGET_URL", "http://localhost:8000/widget")     


    def initiate_spotify_login(self) -> str:
        """Start Spotify OAuth flow"""
        state = self._generate_state()
        self._save_oauth_state(state)
        
        auth_url = (
            "https://accounts.spotify.com/authorize"
            f"?client_id={self.spotify_client_id}"
            "&response_type=code"
            f"&redirect_uri={self.redirect_uri}/spotify"
            "&scope=user-read-private user-read-email"
            f"&state={state}"
        )
        return auth_url

    def initiate_google_login(self) -> str:
        """Start Google OAuth flow"""
        state = self._generate_state()
        self._save_oauth_state(state)
        
        auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={self.google_client_id}"
            "&response_type=code"
            f"&redirect_uri={self.redirect_uri}/google/callback"
            "&scope=email profile"
            "&access_type=offline"
            "&prompt=consent"
            f"&state={state}"
        )
        return auth_url


    def handle_spotify_callback(self, code: str, state: str) -> Tuple[bool, Dict]:
        """Handle Spotify OAuth callback"""
        stored_state = self._get_oauth_state()
        if not stored_state or stored_state != state:
            return False, {"error": "Invalid state parameter"}

        try:
            # Exchange code for tokens
            token_response = requests.post(
                "https://accounts.spotify.com/api/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": f"{self.redirect_uri}/spotify",
                    "client_id": self.spotify_client_id,
                    "client_secret": self.spotify_client_secret,
                }
            )
            
            if token_response.status_code != 200:
                return False, {"error": "Failed to get access token"}
            
            tokens = token_response.json()
            
            # Get user info from Spotify
            user_response = requests.get(
                "https://api.spotify.com/v1/me",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )
            
            if user_response.status_code != 200:
                return False, {"error": "Failed to get user info"}
            
            spotify_user = user_response.json()
            user_data = self._upsert_oauth_user("spotify", spotify_user, tokens)
            return True, user_data

        except Exception as e:
            return False, {"error": str(e)}

    def handle_google_callback(self, code: str, state: str) -> Tuple[bool, Dict]:
        """Handle Google OAuth callback"""
        try:
            # Get tokens from Google using the code
            token_response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": f"{self.redirect_uri}/google/callback",
                    "client_id": self.google_client_id,
                    "client_secret": self.google_client_secret,
                }
            )
            
            if token_response.status_code != 200:
                raise Exception("Failed to get access token")
            
            tokens = token_response.json()
            
            # Get user info from Google
            user_response = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )
            
            if user_response.status_code != 200:
                raise Exception("Failed to get user info")
            
            user_info = user_response.json()
            
            # First try to find existing user
            existing_user = self.supabase.table('profiles').select('*').eq('email', user_info['email']).execute()
            
            if existing_user.data:
                # Update existing user
                user_id = existing_user.data[0]['id']
                self.supabase.table('profiles').update({
                    'last_seen': datetime.now(timezone.utc).isoformat(),
                    'google_id': user_info['id'],
                    'google_access_token': tokens['access_token'],
                    'google_refresh_token': tokens.get('refresh_token'),
                }).eq('id', user_id).execute()
                
                return True, {"user": {"id": user_id, "email": user_info['email']}}
            else:
                # Create new user in auth.users first
                try:
                    auth_user = self.supabase.auth.sign_up({
                        "email": user_info['email'],
                        "password": f"oauth_{secrets.token_urlsafe(16)}"  # Random password
                    })
                    user_id = auth_user.user.id
                    
                    # Create profile
                    profile_data = {
                        'id': user_id,
                        'email': user_info['email'],
                        'google_id': user_info['id'],
                        'google_access_token': tokens['access_token'],
                        'google_refresh_token': tokens.get('refresh_token'),
                        'created_at': datetime.now(timezone.utc).isoformat(),
                        'last_seen': datetime.now(timezone.utc).isoformat()
                    }
                    
                    self.supabase.table('profiles').insert(profile_data).execute()
                    
                    return True, {"user": {"id": user_id, "email": user_info['email']}}
                except Exception as e:
                    print(f"Error creating user: {str(e)}")
                    raise

        except Exception as e:
            print(f"OAuth error: {str(e)}")
            return False, {"error": str(e)}

    def _upsert_oauth_user(self, provider: str, user_info: dict, tokens: dict) -> dict:
        """Create or update user in database"""
        email = user_info.get('email')
        provider_id = user_info.get('id')
        
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(seconds=tokens.get('expires_in', 3600))).isoformat()

        try:
            # Check if user exists in profiles
            existing_user = self.supabase.table('profiles').select('*').eq('email', email).execute()
            
            if existing_user.data:
                # For existing users, just return their info
                return {
                    'id': existing_user.data[0]['id'],
                    'email': email,
                    'provider': provider
                }
            else:
                # For new users, let Supabase handle the UUID generation
                user_data = {
                    'email': email,
                    'created_at': now.isoformat(),
                    'last_seen': now.isoformat(),
                    f'{provider}_id': provider_id,
                    f'{provider}_access_token': tokens['access_token'],
                    f'{provider}_refresh_token': tokens.get('refresh_token'),
                    f'{provider}_token_expires': expires_at
                }
                
                # Insert new profile
                result = self.supabase.table('profiles').insert(user_data).execute()
                
                if not result.data:
                    raise Exception("Failed to create profile")
                
                new_user = result.data[0]
                
                return {
                    'id': new_user['id'],
                    'email': email,
                    'provider': provider
                }
                
        except Exception as e:
            print(f"Error upserting user: {e}")
            print(f"Debug - user_info: {user_info}")
            print(f"Debug - tokens: {tokens}")
            raise

    def refresh_token(self, user_id: str, provider: str) -> Tuple[bool, Dict]:
        """Refresh OAuth token for specified provider"""
        try:
            user_data = self.supabase.table('profiles').select('*').eq('id', user_id).execute()
            if not user_data.data:
                return False, {"error": "User not found"}
            
            user = user_data.data[0]
            refresh_token = user.get(f'{provider}_refresh_token')
            
            if not refresh_token:
                return False, {"error": f"No {provider} refresh token found"}
            
            if provider == "spotify":
                response = requests.post(
                    "https://accounts.spotify.com/api/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": self.spotify_client_id,
                        "client_secret": self.spotify_client_secret,
                    }
                )
            elif provider == "google":
                response = requests.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": self.google_client_id,
                        "client_secret": self.google_client_secret,
                    }
                )
            else:
                return False, {"error": "Invalid provider"}
                
            if response.status_code != 200:
                return False, {"error": "Failed to refresh token"}
                
            new_tokens = response.json()
            
            # Update tokens in database
            self.supabase.table('profiles').update({
                f'{provider}_access_token': new_tokens['access_token'],
                f'{provider}_token_expires': datetime.utcnow().timestamp() + new_tokens.get('expires_in', 3600)
            }).eq('id', user_id).execute()
            
            return True, {"message": "Token refreshed successfully"}
            
        except Exception as e:
            return False, {"error": str(e)}

    def _generate_state(self) -> str:
        """Generate a random state string for CSRF protection"""
        return secrets.token_urlsafe(32)

    def _save_oauth_state(self, state: str) -> bool:
        """Save state to database"""
        try:
            now = datetime.now(timezone.utc)
            expires_at = (now + timedelta(minutes=10))
            
            self.supabase.table('oauth_states').insert({
                'state': state,
                'created_at': now.isoformat(),
                'expires_at': expires_at.isoformat()
            }).execute()
            return True
        except Exception as e:
            print(f"Error saving OAuth state: {e}")
            return False

    def _get_oauth_state(self) -> Optional[str]:
        """Retrieve and validate state from storage"""
        try:
            result = self.supabase.table('oauth_states')\
                .select('*')\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                state_data = result.data[0]
                expires_at = datetime.fromisoformat(state_data['expires_at'])
                now = datetime.now(timezone.utc)
                if expires_at > now:
                    return state_data['state']
            return None
        except Exception as e:
            print(f"Error getting OAuth state: {e}")
            return None