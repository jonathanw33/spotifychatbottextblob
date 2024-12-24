from supabase import create_client
from datetime import datetime, timedelta
import os
import json

class SpotifyBotAuth:
    def __init__(self):
        # Initialize Supabase client
        self.supabase_url = "https://miisnwyfwzsxrwjpcgdb.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1paXNud3lmd3pzeHJ3anBjZ2RiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQxODE5NDEsImV4cCI6MjA0OTc1Nzk0MX0.-vOVdYpY08Rrauio21sBjYhLJ59QcFRt4G5NrnOVoC0"
        self.supabase = create_client(self.supabase_url, self.supabase_key)
                # Initialize OAuth manager
        from app.bot.oauth_manager import OAuthManager
        self.oauth = OAuthManager(self.supabase)
        
    def sign_up(self, email: str, password: str):
        try:
            data = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if data.user:
                # Create user profile in profiles table
                self.supabase.table('profiles').insert({
                    'id': data.user.id,
                    'email': email,
                    'created_at': datetime.utcnow().isoformat(),
                    'last_seen': datetime.utcnow().isoformat()
                }).execute()
                return True, data.user
            return False, "Sign up failed"
        except Exception as e:
            print(f"Signup error: {str(e)}")  # Add this for debugging
            return False, str(e)

    def sign_in(self, email: str, password: str):
        try:
            data = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            if data.user:
                # Update last seen
                self.supabase.table('profiles').update({
                    'last_seen': datetime.utcnow().isoformat()
                }).eq('id', data.user.id).execute()
                return True, data.user
            return False, "Sign in failed"
        except Exception as e:
            return False, str(e)

    def get_user_state(self, user_id: str):
        try:
            data = self.supabase.table('user_states').select('*').eq('user_id', user_id).execute()
            if data.data:
                return json.loads(data.data[0]['state'])
            return None
        except Exception as e:
            print(f"Error getting user state: {e}")
            return None

    def save_user_state(self, user_id: str, state: dict):
        try:
            state_json = json.dumps(state)
            # Upsert the state (insert if not exists, update if exists)
            data = self.supabase.table('user_states').upsert({
                'user_id': user_id,
                'state': state_json,
                'updated_at': datetime.utcnow().isoformat()
            }).execute()
            return True
        except Exception as e:
            print(f"Error saving user state: {e}")
            return False

    def save_conversation_history(self, user_id: str, history: list):
        try:
            data = self.supabase.table('conversation_history').insert({
                'user_id': user_id,
                'history': json.dumps(history),
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            return True
        except Exception as e:
            print(f"Error saving conversation history: {e}")
            return False