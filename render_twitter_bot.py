import tweepy
import time
import os
import threading
from flask import flask
import random
import os
import requests
import json
from datetime import datetime

# Twitter API credentials
API_KEY = os.getenv('26jZNt9hGMwnjot9xuSQ3B4W9')
API_SECRET = os.getenv('1W19qTEWHXZ5lPsGDC950ypAN8id2z34XqpVjooYtnBFL6xAiJ')
ACCESS_TOKEN = os.getenv('1951146671431131136-PAGq10iFiv7PxwnCiVWztvM3xAvyRD')
ACCESS_TOKEN_SECRET = os.getenv('qffbFKZgKljssg8dDOcdHIaPugbHL5wuQTdOo3Xp3bYUG')
BEARER_TOKEN = os.getenv('AAAAAAAAAAAAAAAAAAAAANht3QEAAAAAAfpF7El3B47tArS1qM%2FUCdxIALw%3DX3GjMr6UmPzQQJL1qYZrMRwZxV7Y1ULp2N1sysmmTcN6fJ4SYo')

# Create Flask app (add this after your existing imports)
app = Flask(__name__)

# Health check endpoints
@app.route('/')
def home():
    return "Twitter Bot is running! ✅"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "active"}

# AI API credentials - you'll need one of these:
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # For GPT
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')  # For free AI models

class AITwitterBot:
    """Twitter Bot with AI capabilities"""
    
    def __init__(self):
        # Initialize Twitter client
        self.client = tweepy.Client(
            bearer_token=BEARER_TOKEN,
            consumer_key=API_KEY,
            consumer_secret=API_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True
        )
        
        # Bot settings
        self.retweet_count = 0
        self.max_retweets_per_hour = 8
        self.retweeted_ids = set()
        self.ai_responses_count = 0
        self.max_ai_responses_per_hour = 5
        
        print("🤖 AI-Enhanced Twitter Bot initialized!")
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
    
    def analyze_tweet_with_ai(self, tweet_text):
        """Use AI to analyze if a tweet is worth retweeting"""
        
        try:
            # Option 1: Use Hugging Face (FREE!)
            if HUGGINGFACE_API_KEY:
                return self.analyze_with_huggingface(tweet_text)
            
            # Option 2: Use OpenAI GPT (PAID but better)
            elif OPENAI_API_KEY:
                return self.analyze_with_openai(tweet_text)
            
            # Option 3: Fallback to simple analysis
            else:
                return self.analyze_simple(tweet_text)
                
        except Exception as e:
            self.log(f"❌ AI analysis failed: {e}")
            return self.analyze_simple(tweet_text)
    
    def analyze_with_huggingface(self, tweet_text):
        """Free AI analysis using Hugging Face"""
        
        try:
            # Sentiment analysis
            sentiment_url = "https://api-inference.huggingface.co/models/cardiffnlp/twitter-roberta-base-sentiment-latest"
            
            headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
            payload = {"inputs": tweet_text}
            
            response = requests.post(sentiment_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                # Get sentiment score
                if isinstance(result, list) and len(result) > 0:
                    sentiment_scores = result[0]
                    
                    # Find the highest scoring sentiment
                    best_sentiment = max(sentiment_scores, key=lambda x: x['score'])
                    
                    # Scoring logic
                    score = 0
                    sentiment_label = best_sentiment['label'].upper()
                    confidence = best_sentiment['score']
                    
                    if sentiment_label == 'LABEL_2':  # POSITIVE
                        score += confidence * 40
                    elif sentiment_label == 'LABEL_1':  # NEUTRAL  
                        score += confidence * 20
                    else:  # NEGATIVE
                        score -= confidence * 30
                    
                    # Content quality bonus
                    if len(tweet_text) > 50:
                        score += 10
                    if any(word in tweet_text.lower() for word in ['tip', 'learn', 'how to', 'tutorial']):
                        score += 15
                    if any(word in tweet_text.lower() for word in ['spam', 'buy now', 'click here']):
                        score -= 50
                    
                    self.log(f"🧠 AI Analysis - Sentiment: {sentiment_label}, Score: {score:.1f}")
                    
                    return {
                        'should_retweet': score > 25,
                        'confidence': confidence,
                        'sentiment': sentiment_label,
                        'score': score,
                        'reason': f"AI scored this {score:.1f}/100"
                    }
            
            # Fallback if API fails
            return self.analyze_simple(tweet_text)
            
        except Exception as e:
            self.log(f"❌ Hugging Face analysis failed: {e}")
            return self.analyze_simple(tweet_text)
    
    def analyze_with_openai(self, tweet_text):
        """Premium AI analysis using OpenAI GPT"""
        
        try:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""
            Analyze this tweet and determine if it's worth retweeting for a tech/programming focused account.
            
            Tweet: "{tweet_text}"
            
            Consider:
            - Stating the truth on political matters no matter the potential outcome 
            - Harsh facts based on popular evidence
            - Is it educational or informative?
            - Does it avoid spampromotional content?
            - Is it atleast somewhat relevant to tech/cybersecurity/AI?
            
            Respond with JSON only:
            {{
                "should_retweet": true/false,
                "score": 0-100,
                "reason": "brief explanation, sometimes based with fact backed resources",
                "sentiment": "positive/neutral/negative"
            }}
            """
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150,
                "temperature": 0.3
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Parse JSON response
                ai_analysis = json.loads(content.strip())
                self.log(f"🧠 GPT Analysis: {ai_analysis['reason']}")
                
                return ai_analysis
            
            return self.analyze_simple(tweet_text)
            
        except Exception as e:
            self.log(f"❌ OpenAI analysis failed: {e}")
            return self.analyze_simple(tweet_text)
    
    def analyze_simple(self, tweet_text):
        """Simple fallback analysis (no AI API needed)"""
        
        score = 0
        
        # Positive keywords
        positive_words = ['OMG YESSS', 'TEA', 'tip', 'guide', 'how to', 'clockit', 'unite', 'queen']
        negative_words = ['spam', 'buy now', 'click here', 'urgent', 'limited time']
        
        text_lower = tweet_text.lower()
        
        # Scoring
        for word in positive_words:
            if word in text_lower:
                score += 10
                
        for word in negative_words:
            if word in text_lower:
                score -= 20
        
        # Length bonus
        if 30 < len(tweet_text) < 200:
            score += 10
        
        return {
            'should_retweet': score > 15,
            'score': score,
            'reason': 'Simple keyword analysis',
            'sentiment': 'neutral'
        }
    
    def generate_ai_response(self, original_tweet):
        """Generate AI response to a tweet"""
        
        if self.ai_responses_count >= self.max_ai_responses_per_hour:
            return None
        
        try:
            if OPENAI_API_KEY:
                return self.generate_openai_response(original_tweet)
            elif HUGGINGFACE_API_KEY:
                return self.generate_huggingface_response(original_tweet)
            else:
                return self.generate_simple_response(original_tweet)
                
        except Exception as e:
            self.log(f"❌ AI response generation failed: {e}")
            return None
    
    def generate_openai_response(self, original_tweet):
        """Generate response using GPT"""
        
        try:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""
            Generate a thoughtful, engaging response to this tweet. Keep it under 280 characters.
            Be helpful, truthful, and add value to the conversation.
            
            Original tweet: "{original_tweet}"
            
            Generate a response that:
            - Adds value or insight
            - Is conversational 
            - Uses appropriate emojis (1-2 max)
            - Sounds natural, not robotic
            """
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                
                # Remove quotes if AI added them
                ai_response = ai_response.strip('"')
                
                self.log(f"🧠 Generated AI response: {ai_response[:50]}...")
                return ai_response
            
            return None
            
        except Exception as e:
            self.log(f"❌ OpenAI response generation failed: {e}")
            return None
    
    def generate_huggingface_response(self, original_tweet):
        """Generate response using Hugging Face (simpler)"""
        
        # For free tier, we'll use a simpler approach
        templates = [
            "lol no fr!",
            "Thanks boo",
            "This is so true! More people need to hear this", 
            "Couldn't agree more! Well said 💯",
            "lmao yess"
        ]
        
        # Simple context-aware selection
        text_lower = original_tweet.lower()
        
        if 'tutorial' in text_lower or 'learn' in text_lower:
            return "Thanks U"
        elif 'tip' in text_lower or 'advice' in text_lower:
            return "This is exactly what I needed to hear"
        elif 'question' in text_lower or '?' in original_tweet:
            return "Would love to see the responses 🤔"
        else:
            return random.choice(templates)
    
    def generate_simple_response(self, original_tweet):
        """Simple response generation (no AI API)"""
        
        responses = [
            "Interesting perspective! 🤔",
            "This is helpful",
            "god is good",
            "lol like literally, ion like that"
        ]
        
        return random.choice(responses)
    
    def smart_retweet_with_ai(self, search_term):
        """Find tweets and use AI to decide what to retweet"""
        
        try:
            self.log(f"🔍 AI-powered search for: {search_term}")
            
            tweets = self.client.search_recent_tweets(
                query=f"{search_term} -is:retweet lang:en",
                max_results=20,
                tweet_fields=["public_metrics", "created_at", "author_id"]
            )
            
            if not tweets.data:
                self.log("📭 No tweets found")
                return 0
            
            retweets_made = 0
            
            for tweet in tweets.data:
                
                if tweet.id in self.retweeted_ids:
                    continue
                    
                if self.retweet_count >= self.max_retweets_per_hour:
                    break
                
                # AI Analysis
                self.log(f"🧠 Analyzing tweet: {tweet.text[:50]}...")
                ai_analysis = self.analyze_tweet_with_ai(tweet.text)
                
                if ai_analysis['should_retweet']:
                    
                    # Decide whether to retweet or quote tweet with AI response
                    action_choice = random.choice(['retweet', 'quote_tweet', 'retweet'])
                    
                    if action_choice == 'quote_tweet' and self.ai_responses_count < self.max_ai_responses_per_hour:
                        # Quote tweet with AI-generated response
                        ai_comment = self.generate_ai_response(tweet.text)
                        
                        if ai_comment:
                            try:
                                self.client.create_tweet(
                                    text=ai_comment,
                                    quote_tweet_id=tweet.id
                                )
                                self.ai_responses_count += 1
                                self.log(f"✅ Quote tweeted with AI: '{ai_comment}'")
                            except Exception as e:
                                self.log(f"❌ Quote tweet failed: {e}")
                                continue
                        else:
                            # Fallback to regular retweet
                            self.client.retweet(tweet.id)
                            self.log("✅ Retweeted (AI comment failed)")
                    else:
                        # Regular retweet
                        try:
                            self.client.retweet(tweet.id)
                            self.log(f"✅ Retweeted: {ai_analysis['reason']}")
                        except Exception as e:
                            self.log(f"❌ Retweet failed: {e}")
                            continue
                    
                    self.retweeted_ids.add(tweet.id)
                    self.retweet_count += 1
                    retweets_made += 1
                    
                    # Natural delay
                    time.sleep(random.randint(60, 120))
                    
                else:
                    self.log(f"⏭️ Skipped: {ai_analysis['reason']}")
            
            return retweets_made
            
        except Exception as e:
            self.log(f"❌ AI search error: {e}")
            return 0
    
    def create_ai_original_content(self):
        """Generate original tweets using AI"""
        
        try:
            if not OPENAI_API_KEY:
                self.log("⏭️ No OpenAI key for original content")
                return False
            
            # Topics for original content
            topics = [
                "#cybersersecurity",
            "#burkinofaso",
            "#baddies", 
            "#INNIT",
            "#TALMBOUTINNIT",
            "#COULDABEENRECORDS",
            "#TEA",
            "#Couldabeenhouse",
            "#juice",
            "#nickjfuentes",
            "Ibrahimtraore",
            "#Onepiece",
            "#bleach",
            "#loveisland" 
            "anti-racism"
            ]
            
            topic = random.choice(topics)
            
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""
            Create an engaging, original tweet about {topic}.
            
            Requirements:
            - Under 280 characters
            - Sometimes Educational or insightful
            - Include 1-2 relevant emojis once every several tweets
            - Rarely hashtags (they look spammy)
            """
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 80,
                "temperature": 0.8
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                tweet_content = result['choices'][0]['message']['content'].strip().strip('"')
                
                # Post the original tweet
                self.client.create_tweet(text=tweet_content)
                self.log(f"✅ Posted AI-generated original tweet: {tweet_content}")
                return True
            
            return False
            
        except Exception as e:
            self.log(f"❌ AI original content failed: {e}")
            return False
    
    def run_ai_bot_cycle(self):
        """Main AI bot cycle"""
        
        # Reset hourly counters
        current_hour = datetime.now().hour
        if not hasattr(self, 'last_hour') or self.last_hour != current_hour:
            self.retweet_count = 0
            self.ai_responses_count = 0
            self.last_hour = current_hour
            self.log("🔄 New hour - counters reset")
        
        # Your interests
        interests = [
            "#foreign affairs",
            "#AI machinelearning",
            "#politics",
            "#christianity",
            "#one piece"
        ]
        
        total_activity = 0
        
        # AI-powered retweeting
        for interest in interests:
            if self.retweet_count < self.max_retweets_per_hour:
                retweets = self.smart_retweet_with_ai(interest)
                total_activity += retweets
                time.sleep(180)  # 3 minutes between searches
        
        # Occasionally create original content (if OpenAI available)
        if random.random() < 0.3:  # 30% chance
            if self.create_ai_original_content():
                total_activity += 1
        
        self.log(f"📊 AI cycle complete - Total activity: {total_activity}")
        self.log(f"    Retweets: {self.retweet_count}/{self.max_retweets_per_hour}")
        self.log(f"    AI responses: {self.ai_responses_count}/{self.max_ai_responses_per_hour}")
        
        return total_activity
    
    def run_forever(self):
        """Main loop with AI enhancements"""
        
        self.log("🚀 Starting AI-Enhanced Twitter Bot")
        
        # Check what AI capabilities are available
        if OPENAI_API_KEY:
            self.log("✅ OpenAI GPT available - Full AI features enabled!")
        elif HUGGINGFACE_API_KEY:
            self.log("✅ Hugging Face available - Free AI features enabled!")
        else:
            self.log("⚠️ No AI APIs - Using intelligent fallback analysis")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                self.log(f"🤖 AI Bot Cycle #{cycle} - {datetime.now().strftime('%H:%M:%S')}")
                
                activity = self.run_ai_bot_cycle()
                
                if activity == 0:
                    self.log("😴 No activity this cycle - bot might be rate limited")
                
                # Smart wait time based on activity
                if activity > 3:
                    wait_minutes = random.randint(25, 35)  # Longer wait after high activity
                else:
                    wait_minutes = random.randint(15, 25)  # Normal wait
                
                self.log(f"⏰ Sleeping {wait_minutes} minutes...")
                time.sleep(wait_minutes * 60)
                
            except KeyboardInterrupt:
                self.log("🛑 AI Bot stopped by user")
                break
            except Exception as e:
                self.log(f"❌ AI Bot error: {e}")
                time.sleep(300)  # 5 minute recovery wait

def test_ai_setup():
    """Test AI and Twitter setup"""
    
    # Test Twitter connection
    try:
        client = tweepy.Client(bearer_token=BEARER_TOKEN)
        me = client.get_me()
        print(f"✅ Twitter connected: @{me.data.username}")
    except Exception as e:
        print(f"❌ Twitter connection failed: {e}")
        return False
    
    # Test AI capabilities
    if OPENAI_API_KEY:
        print("✅ OpenAI key detected - Premium AI features available")
    elif HUGGINGFACE_API_KEY:
        print("✅ Hugging Face key detected - Free AI features available")
    else:
        print("⚠️ No AI keys - Will use intelligent fallback analysis")
    
    return True

def run_bot():
    while True:
        print("Bot thread is running...")
        time.sleep(60)