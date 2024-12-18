from textblob import TextBlob
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from email.mime.text import MIMEText
import smtplib
from datetime import datetime
from app.bot.spotify_bot_auth import SpotifyBotAuth
import json 

class SpotifySupportBot:
    def __init__(self):
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.auth = SpotifyBotAuth()

        # Initialize user state
        self.user_states = {}
        self.tickets_created = set()  # Track users with created tickets
        self.failed_ticket_attempts = set()



        # Enhanced decision tree with more common Spotify issues
        self.decision_tree = {
            "root": {
                "text": "What kind of issue are you experiencing?",
                "children": {
                    "cant_login": {
                        "text": "Having trouble logging in?",
                        "responses": {
                            "regular": "Let's verify your login credentials. First, check if your username and password are correct. If you're using Facebook/Google login, try logging in directly through that service.",
                            "frustrated": "I understand login issues can be very frustrating. Let's solve this together step by step. First, let's verify your login method and credentials."
                        },
                        "keywords": ["login", "cant login", "password", "forgot password", "authentication", "sign in", "signup", "register"]
                    },
                    "playback": {
                        "text": "Having playback issues?",
                        "responses": {
                            "regular": "Let's troubleshoot your playback issues. First, check if your internet connection is stable and try playing a different song.",
                            "frustrated": "I know it's frustrating when your music won't play properly. Let's get this fixed together."
                        },
                        "keywords": ["wont play", "no sound", "playback", "buffer", "streaming", "stuck", "freezing"]
                    }
                }
            }
        }
        
        # Create embeddings for each issue and their keywords
        self.issue_embeddings = {}
        for issue, data in self.decision_tree["root"]["children"].items():
            # Combine issue name with all its keywords for better matching
            all_texts = [issue] + data.get("keywords", [])
            # Calculate average embedding
            embeddings = [self.model.encode(text) for text in all_texts]
            self.issue_embeddings[issue] = np.mean(embeddings, axis=0)
            
    async def initialize_user_state(self, user_id: str):
        """Initialize or load existing user state"""
        state = await self.auth.get_user_state(user_id)
        if not state:
            state = {
                'frustration_count': 0,
                'current_node': 'root',
                'awaiting_choice': False,
                'last_interaction': datetime.utcnow().isoformat()
            }
            await self.auth.save_user_state(user_id, state)
        return state    
    
    def analyze_sentiment(self, text):
        """Analyze text sentiment using TextBlob"""
        analysis = TextBlob(text)
        return analysis.sentiment.polarity

    def find_closest_issue(self, user_input):
        """Find the closest matching issue using semantic similarity"""
        input_embedding = self.model.encode(user_input)
        
        similarities = {}
        for issue, embedding in self.issue_embeddings.items():
            similarity = float(cosine_similarity(
                [input_embedding],
                [embedding]
            )[0][0])
            similarities[issue] = similarity
        
        # Get the highest similarity
        max_issue = max(similarities.items(), key=lambda x: x[1])
        return max_issue if max_issue[1] > 0.3 else (None, 0.0)

    def get_response(self, user_id, user_input):
        """Main function to process user input and return appropriate response"""
        if user_input.lower() == '/reopen':
            if user_id in self.tickets_created:
                self.user_states[user_id]['chat_ended'] = False
                return "Chat reopened. How can I help you?", {"chat_reopened": True}
            return "No previous chat found to reopen.", {"error": "no_chat_to_reopen"}
        
        # Get user state from memory first, then from database if not in memory
        if user_id not in self.user_states:
            user_state = self.auth.get_user_state(user_id)
            if user_state:
                self.user_states[user_id] = user_state
            else:
                self.user_states[user_id] = {
                    'frustration_count': 0,
                    'current_node': 'root',
                    'awaiting_choice': False
                }
                
                # If awaiting choice for ticket
        if self.user_states[user_id].get('awaiting_choice'):
            if user_input.strip() == '1':
                self.user_states[user_id]['awaiting_choice'] = False
                return "Thank you. Our support team will contact you soon. Chat ended.", {"choice": "end_chat"}
            elif user_input.strip() == '2':
                self.user_states[user_id]['awaiting_choice'] = False
                return "Okay, let's continue chatting. How else can I help you?", {"choice": "continue_chat"}
            else:
                return "Please type '1' to end chat or '2' to continue chatting.", {"awaiting_choice": True}
        
        
        # Analyze sentiment
        sentiment = self.analyze_sentiment(user_input)
        
        # Update frustration count based on sentiment
        if sentiment < -0.3:
            self.user_states[user_id]['frustration_count'] += 1
        
        # Find closest matching issue and get similarity score
        closest_issue, similarity_score = self.find_closest_issue(user_input)
        
        # Get appropriate response type
        response_type = "frustrated" if self.user_states[user_id]['frustration_count'] >= 2 else "regular"
        
        # Prepare debug info
        debug_info = {
            "sentiment": sentiment,
            "matched_issue": closest_issue,
            "similarity_score": similarity_score,
            "response_type": response_type,
            "frustration_count": self.user_states[user_id]['frustration_count']
        }
        
        # Check if we need to create a support ticket
        if (self.user_states[user_id]['frustration_count'] >= 3 and 
            user_id not in self.tickets_created and 
            user_id not in self.failed_ticket_attempts):  # Add this check
            
            ticket_created = self.create_support_ticket(user_id)
            if ticket_created:
                self.tickets_created.add(user_id)
                self.user_states[user_id]['awaiting_choice'] = True
                debug_info["ticket_created"] = True
                response = """I notice you're having difficulties. I've escalated this to our support team - they'll contact you soon to help resolve your issue.

Would you like to:
1. End this chat and wait for support team
2. Continue chatting with me

Please type '1' or '2' to choose."""
            else:
                self.failed_ticket_attempts.add(user_id)  # Mark as failed
                response = "I'm here to help you directly. What seems to be the problem?"
        else:
            # Get response for normal flow
            if closest_issue and closest_issue in self.decision_tree['root']['children']:
                node = self.decision_tree['root']['children'][closest_issue]
                response = node['responses'][response_type]
            else:
                response = "I'm not sure I understand. Could you please rephrase your question?"
        
        # Save updated state
        self.auth.save_user_state(user_id, self.user_states[user_id])
        
        return response, debug_info

    def create_support_ticket(self, user_id: str, conversation_history=None):
        """Create and send support ticket via email with user information from Supabase"""
        try:
            # Get user profile from Supabase
            user_profile = self.auth.supabase.table('profiles').select('*').eq('id', user_id).execute()
            
            if not user_profile.data:
                print(f"User profile not found for ID: {user_id}")
                return False
                
            user_email = user_profile.data[0]['email']
            
            # Email configuration for Gmail
            sender = "jonathanwigunapromotion@gmail.com"  # Replace with your Gmail
            recipient = "jonathanwiguna2004@gmail.com"  # Replace with your destination email
            # password = "jxaa iqak dyvv lnwv"  # Replace with your generated App Password
            
            # Create detailed message body with user information
            body = f"""
    Support Ticket for User {user_id}
    User Email: {user_email}
    Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Status: User has shown repeated frustration

    User State Information:
    - Frustration Count: {self.user_states[user_id]['frustration_count']}
    - Current Node: {self.user_states[user_id]['current_node']}

    Recent Conversation History:
    """
            if conversation_history:
                for entry in conversation_history[-6:]:  # Last 3 exchanges
                    body += f"\n{entry['type']}: {entry['message']}"
                    if 'sentiment' in entry:
                        body += f"\nSentiment: {entry['sentiment']:.2f}"
                    body += "\n"

            # Create email message
            msg = MIMEText(body)
            msg['Subject'] = f"Support Ticket - {user_email}"
            msg['From'] = sender
            msg['To'] = recipient

            # Send email
            try:
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(sender, password)
                    server.send_message(msg)
                print(f"Support ticket successfully sent to {recipient}")
                
                # Store ticket in Supabase
                self.auth.supabase.table('support_tickets').insert({
                    'user_id': user_id,
                    'email': user_email,
                    'ticket_content': body,
                    'status': 'open',
                    'created_at': datetime.utcnow().isoformat(),
                    'conversation_history': json.dumps(conversation_history[-6:] if conversation_history else [])
                }).execute()
                
                # Update user state in Supabase
                self.auth.save_user_state(user_id, self.user_states[user_id])
                
                return True
                
            except Exception as e:
                print(f"Failed to send support ticket: {str(e)}")
                return False
                
        except Exception as e:
            print(f"Error creating support ticket: {str(e)}")
            return False