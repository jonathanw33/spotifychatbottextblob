from textblob import TextBlob
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from email.mime.text import MIMEText
import smtplib
from datetime import datetime
from app.bot.spotify_bot_auth import SpotifyBotAuth
import json 
import random

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
                    "account_access": {
                        "text": "Having trouble accessing your account?",
                        "children": {
                            "cant_login": {
                                "text": "Unable to log in to your account?",
                                "responses": {
                                    "regular": "Let's get you back into your account. Try these steps:\n1. Double-check your username/email and password\n2. Clear your browser cookies and cache\n3. Try the 'Forgot Password' option\n4. If using Facebook/Google login, try logging in directly through that service\n\nStill no luck? I can help you contact our support team.",
                                    "frustrated": "I understand how frustrating it is to be locked out of your account. Don't worry - we'll get this sorted out together. Let's try these proven solutions:\n1. First, let's verify your login credentials\n2. We'll clear your browser data for a fresh start\n3. If needed, we can easily reset your password\n\nI'm here to help every step of the way."
                                },
                                "keywords": ["login", "cant login", "password", "forgot password", "authentication", "sign in", "signup", "register", "locked out", "access denied", "reset password", "wrong password", "account blocked", "verification", "email verification", "2fa", "two factor"]
                            },
                            "account_hacked": {
                                "text": "Think your account might be hacked?",
                                "responses": {
                                    "regular": "Let's secure your account immediately:\n1. Change your password right away\n2. Sign out of all devices\n3. Check for any unauthorized changes\n4. Enable two-factor authentication\n\nContact support if you notice any unauthorized charges.",
                                    "frustrated": "I understand how concerning it is to think your account might be compromised. Let's act quickly to protect your account and get everything back to normal. We'll start by changing your password and securing your account together."
                                },
                                "keywords": ["hacked", "compromised", "stolen", "unauthorized", "strange activity", "someone else", "security", "suspicious", "unknown device", "unfamiliar login", "different country", "weird songs", "unknown playlists"]
                            },
                            "account_linking": {
                                "text": "Issues with linking accounts or services?",
                                "responses": {
                                    "regular": "Let's help you with account linking:\n1. Check which service you're trying to connect\n2. Ensure both accounts are active\n3. Remove and re-link the connection\n4. Update both apps to latest versions\n\nI can guide you through specific platform connections.",
                                    "frustrated": "Connecting accounts should be simple - I understand your frustration. Let's get your services working together smoothly with some proven solutions."
                                },
                                "keywords": ["link", "connect", "facebook", "instagram", "discord", "last.fm", "social", "integration", "unlink", "disconnect", "third party", "connection failed"]
                            }
                        }
                    },
                    "payment_billing": {
                        "text": "Having payment or billing issues?",
                        "children": {
                            "payment_failed": {
                                "text": "Is your payment not going through?",
                                "responses": {
                                    "regular": "Let's check your payment details:\n1. Verify your card information is current\n2. Ensure sufficient funds are available\n3. Check if your bank is blocking the transaction\n4. Try an alternative payment method\n\nNeed to update your payment info? I can guide you through that.",
                                    "frustrated": "I understand payment issues can be very stressing. Let's work together to get your premium service running smoothly again. We'll check your payment details step by step and find the best solution."
                                },
                                "keywords": ["payment", "declined", "card", "billing", "charge", "transaction", "failed payment", "cant pay", "payment method", "update card", "expired", "insufficient funds", "bank declined", "payment error"]
                            },
                            "subscription_issues": {
                                "text": "Having trouble with your subscription?",
                                "responses": {
                                    "regular": "Let's review your subscription:\n1. Check your current plan status\n2. Verify recent payments\n3. Review any pending changes\n4. Confirm billing cycle dates\n\nI can help you understand your options and make any needed adjustments.",
                                    "frustrated": "I know subscription issues can be confusing and frustrating. Let's look at your account together and make sure you're getting exactly what you're paying for. We'll review your plan and sort out any issues."
                                },
                                "keywords": ["subscription", "premium", "plan", "cancel", "renew", "upgrade", "downgrade", "family plan", "student plan", "duo plan", "billing cycle", "autorenew", "subscription type", "group plan", "premium benefits"]
                            },
                            "promotional_offers": {
                                "text": "Questions about promotions or special offers?",
                                "responses": {
                                    "regular": "Let me help you with promotional offers:\n1. Check offer eligibility\n2. Verify promotion code validity\n3. Review terms and conditions\n4. Confirm application to your account\n\nI can explain available promotions and help you apply them.",
                                    "frustrated": "I understand you want to make sure you're getting the best deal possible. Let's review your promotions and make sure everything is properly applied to your account."
                                },
                                "keywords": ["promotion", "offer", "discount", "trial", "free trial", "promo code", "coupon", "special offer", "student discount", "military discount", "family discount", "deals"]
                            }
                        }
                    },
                    "playback": {
                        "text": "Having trouble playing music?",
                        "children": {
                            "audio_quality": {
                                "text": "Issues with sound quality or playback?",
                                "responses": {
                                    "regular": "Let's improve your listening experience:\n1. Check your internet connection speed\n2. Adjust the streaming quality in settings\n3. Try downloading for offline listening\n4. Update your audio drivers\n5. Check your device volume and equalizer settings",
                                    "frustrated": "Poor audio quality can really ruin the experience - I get it. Let's work together to get your music sounding crystal clear again. We'll check your settings and connection to find the best solution."
                                },
                                "keywords": ["quality", "sound", "audio", "static", "cutting out", "buffering", "lag", "skip", "stutter", "offline", "download", "bitrate", "high quality", "equalizer", "crossfade", "volume normalize", "audio settings"]
                            },
                            "device_sync": {
                                "text": "Problems with device synchronization?",
                                "responses": {
                                    "regular": "Let's get your devices in sync:\n1. Check your internet connection\n2. Force close and restart Spotify\n3. Log out and back in\n4. Remove unused devices\n5. Update the app on all devices",
                                    "frustrated": "It's really annoying when your devices aren't working together smoothly. Let's fix this sync issue step by step so you can enjoy your music anywhere."
                                },
                                "keywords": ["sync", "devices", "connect", "switch", "transfer", "multiple devices", "phone", "computer", "tablet", "speaker", "car", "smart tv", "gaming console", "alexa", "google home", "spotify connect"]
                            },
                            "connectivity": {
                                "text": "Having connection or streaming issues?",
                                "responses": {
                                    "regular": "Let's resolve your connection issues:\n1. Check your internet connection\n2. Test other apps to isolate the problem\n3. Clear app cache\n4. Try switching between WiFi and mobile data\n5. Check for network restrictions",
                                    "frustrated": "Connection problems can be really frustrating when you just want to listen to your music. Let's work together to get you streaming smoothly again."
                                },
                                "keywords": ["connection", "internet", "wifi", "network", "offline", "streaming", "buffer", "loading", "timeout", "disconnected", "no internet", "poor connection", "mobile data", "cellular"]
                            }
                        }
                    },
                    "playlist_library": {
                        "text": "Having issues with playlists or your library?",
                        "children": {
                            "missing_content": {
                                "text": "Can't find your music or playlists?",
                                "responses": {
                                    "regular": "Let's locate your content:\n1. Check if you're logged into the correct account\n2. Look in your 'Liked Songs'\n3. Search for specific playlists\n4. Check Recently Played\n5. Verify if songs are still available in your region",
                                    "frustrated": "I understand how upsetting it is when your carefully curated music collection seems to disappear. Let's work together to find your content and get everything back in order."
                                },
                                "keywords": ["missing", "disappeared", "cant find", "lost", "deleted", "gone", "playlist", "songs", "library", "collection", "unavailable", "grayed out", "region locked", "not available", "removed"]
                            },
                            "playlist_management": {
                                "text": "Need help managing your playlists?",
                                "responses": {
                                    "regular": "Here's how to manage your playlists:\n1. Create new playlists\n2. Add or remove songs\n3. Change playlist privacy settings\n4. Collaborate with friends\n5. Sort and organize your music",
                                    "frustrated": "I know organizing your music collection is important to you. Let's walk through the playlist management tools together and get everything arranged just the way you want it."
                                },
                                "keywords": ["create playlist", "edit playlist", "organize", "sort", "collaborate", "share", "private", "public", "add songs", "remove songs", "duplicate", "backup", "import", "export", "merge playlists"]
                            },
                            "recommendations": {
                                "text": "Issues with music recommendations or radio?",
                                "responses": {
                                    "regular": "Let's improve your recommendations:\n1. Review your listening history\n2. Update your taste preferences\n3. Like/dislike more songs\n4. Check private session settings\n5. Try the Discover Weekly refresh",
                                    "frustrated": "Getting the right music recommendations is crucial for enjoying Spotify. Let's work on tuning your preferences to get better suggestions."
                                },
                                "keywords": ["recommendations", "discover", "radio", "similar", "suggestion", "discover weekly", "release radar", "daily mix", "taste", "preferences", "new music", "algorithm"]
                            }
                        }
                    },
                    "app_technical": {
                        "text": "Having technical issues with the app?",
                        "children": {
                            "app_crashes": {
                                "text": "Is the app crashing or not responding?",
                                "responses": {
                                    "regular": "Let's fix the app issues:\n1. Force close the app\n2. Clear app cache and data\n3. Check for app updates\n4. Restart your device\n5. Reinstall if necessary",
                                    "frustrated": "App crashes are incredibly frustrating when you just want to listen to your music. Let's get Spotify working smoothly again with some proven troubleshooting steps."
                                },
                                "keywords": ["crash", "freeze", "stuck", "not responding", "black screen", "force close", "slow", "buggy", "glitch", "error", "app not opening", "white screen", "loading forever", "performance", "memory usage"]
                            },
                            "offline_mode": {
                                "text": "Problems with offline mode or downloads?",
                                "responses": {
                                    "regular": "Let's check your offline settings:\n1. Verify Premium subscription status\n2. Check available storage space\n3. Confirm download settings\n4. Try re-downloading content\n5. Check download quality settings",
                                    "frustrated": "I understand how important it is to have your music available offline. Let's make sure your downloads are working properly so you can enjoy your music anywhere, anytime."
                                },
                                "keywords": ["offline", "download", "storage", "space", "local files", "save", "mobile data", "wifi", "no internet", "available offline", "storage full", "download failed", "pending download", "sync offline"]
                            },
                            "compatibility": {
                                "text": "Having device or OS compatibility issues?",
                                "responses": {
                                    "regular": "Let's check compatibility:\n1. Verify device meets minimum requirements\n2. Check OS version compatibility\n3. Update app to latest version\n4. Clear app data and reinstall\n5. Check for known device-specific issues",
                                    "frustrated": "It's frustrating when apps don't work properly with your device. Let's figure out what's causing the compatibility issue and find a solution."
                                },
                                "keywords": ["compatibility", "version", "update", "old version", "legacy", "operating system", "android", "ios", "windows", "mac", "linux", "chromebook", "unsupported", "device compatibility"]
                            }
                        }
                    }
                }
            }
        }
        
        # Create embeddings for each issue and their keywords
        self.issue_embeddings = {}

        # Traverse the decision tree to get all subcategories and their keywords
        for main_issue, main_data in self.decision_tree["root"]["children"].items():
            if "children" in main_data:
                for sub_issue, sub_data in main_data["children"].items():
                    # Create a unique key for this subcategory
                    issue_key = f"{main_issue}.{sub_issue}"
                    
                    # Combine all relevant text for matching
                    all_texts = [
                        main_issue,  # main category name
                        sub_issue,   # subcategory name
                        sub_data.get("text", "")  # question text
                    ]
                    
                    # Add keywords if they exist
                    if "keywords" in sub_data:
                        all_texts.extend(sub_data["keywords"])
                    
                    # Calculate embedding
                    embeddings = [self.model.encode(text.lower()) for text in all_texts]
                    self.issue_embeddings[issue_key] = np.mean(embeddings, axis=0)
            
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
        input_embedding = self.model.encode(user_input.lower())
        
        similarities = {}
        for issue_key, embedding in self.issue_embeddings.items():
            similarity = float(cosine_similarity(
                [input_embedding],
                [embedding]
            )[0][0])
            similarities[issue_key] = similarity
        
        # Get the highest similarity
        max_issue = max(similarities.items(), key=lambda x: x[1])
        if max_issue[1] > 0.5:
            # Split the composite key back into main category and subcategory
            main_category, subcategory = max_issue[0].split('.')
            return (main_category, subcategory), max_issue[1]
        return (None, None), 0.0

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
        match_result = self.find_closest_issue(user_input)
        print(f"Match result: {match_result}")  # Debug log


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
            "matched_issue": match_result[0] if match_result else None,
            "similarity_score": match_result[1] if match_result else 0,
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
            if match_result and match_result[0] and match_result[0][0]:  # Check if we have a valid match
                main_category, subcategory = match_result[0]
                try:
                    # Navigate to the correct subcategory
                    node = self.decision_tree['root']['children'][main_category]['children'][subcategory]
                    response = node['responses'][response_type]
                    print(f"Found response for {main_category}.{subcategory}")  # Debug log
                except (KeyError, TypeError) as e:
                    print(f"Error accessing decision tree: {e}")  # Debug log
                    response = "I'm not sure I understand. Could you please rephrase your question?"
            else:
                print("No valid match found")  # Debug log
                response = "I'm not sure I understand. Could you please rephrase your question?"
            
        # Save updated state
        self.auth.save_user_state(user_id, self.user_states[user_id])
            
        return response, debug_info
            
    def get_frustration_or_default_response(self, sentiment, user_input):
        """Helper method to return either frustration or default response"""
        if sentiment < -0.5 and not any(keyword in user_input.lower() for keyword in [
            'login', 'password', 'play', 'song', 'account', 'premium', 'payment', 'spotify'
        ]):
            frustration_responses = [
                "I understand this is frustrating. Could you tell me more about what specific issue you're experiencing?",
                "I hear your frustration, and I want to help. Can you describe the specific problem you're facing?",
                "I'm sorry you're having trouble. Let's work through this together. What exactly isn't working as expected?",
                "That sounds really frustrating. I'm here to help - could you provide more details about what's happening?"
            ]
            return random.choice(frustration_responses)
        
        return "I'm not sure I understand. Could you please rephrase your question?"    

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
            password = "jxaa iqak dyvv lnwv"  # Replace with your generated App Password
            
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