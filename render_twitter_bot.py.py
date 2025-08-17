import tweepy
import json
import time
import random
import os
from datetime import datetime, timedelta

# Get API credentials from environment variables (secure for cloud)
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')

class CloudTwitterBot:
    """Twitter Bot optimized for cloud deployment"""
    
    def __init__(self):
        # Verify all credentials are loaded
        if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, BEARER_TOKEN]):
            raise ValueError("Missing API credentials! Check environment variables.")
        
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
        self.max_retweets_per_hour = 8  # Conservative for 24/7 operation
        self.retweeted_tweets = set()
        self.last_hour = datetime.now().hour
        
        print(f"🤖 Cloud Twitter Bot initialized at {datetime.now()}")
        
    def log_activity(self, message):
        """Log activity with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")
        
    def is_quality_tweet(self, tweet):
        """Check if tweet meets quality standards"""
        if tweet.id in self.retweeted_tweets:
            return False
            
        # Avoid spam indicators
        spam_words = ["buy now", "click here", "free money", "urgent", "limited time"]
        if any(word in tweet.text.lower() for word in spam_words):
            return False
            
        # Must have minimum length
        if len(tweet.text.strip()) < 20:
            return False
            
        return True
    
    def retweet_trending_content(self, keywords):
        """Find and retweet trending content"""
        try:
            self.log_activity(f"🔍 Searching for: {keywords}")
            
            tweets = self.client.search_recent_tweets(
                query=f"{keywords} -is:retweet -is:reply lang:en",
                max_results=20,
                tweet_fields=["created_at", "author_id", "public_metrics"],
                expansions=["author_id"]
            )
            
            if not tweets.data:
                self.log_activity(f"📭 No tweets found for: {keywords}")
                return 0
            
            # Sort by engagement
            sorted_tweets = sorted(
                tweets.data, 
                key=lambda t: t.public_metrics.get('like_count', 0) + t.public_metrics.get('retweet_count', 0) * 2,
                reverse=True
            )
            
            retweeted = 0
            for tweet in sorted_tweets[:3]:  # Only top 3
                if self.retweet_count >= self.max_retweets_per_hour:
                    break
                    
                if self.is_quality_tweet(tweet):
                    try:
                        self.client.retweet(tweet.id)
                        self.retweeted_tweets.add(tweet.id)
                        self.retweet_count += 1
                        retweeted += 1
                        
                        self.log_activity(f"✅ Retweeted: {tweet.text[:50]}...")
                        time.sleep(random.randint(60, 120))  # Natural delay
                        
                    except Exception as e:
                        self.log_activity(f"❌ Retweet failed: {e}")
            
            return retweeted
            
        except Exception as e:
            self.log_activity(f"❌ Search error: {e}")
            return 0
    
    def run_bot_cycle(self):
        """Run one complete bot cycle"""
        
        # Reset hourly counter
        current_hour = datetime.now().hour
        if self.last_hour != current_hour:
            self.retweet_count = 0
            self.last_hour = current_hour
            self.log_activity("🔄 Hourly counter reset")
        
        # Your interests - CUSTOMIZE THESE!
        topics = [
            "#cybesersecurity",
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
        ]
        
        total_retweets = 0
        for topic in topics:
            if self.retweet_count < self.max_retweets_per_hour:
                retweets = self.retweet_trending_content(topic)
                total_retweets += retweets
                time.sleep(180)  # 3 minutes between topics
        
        self.log_activity(f"📊 Cycle complete. Retweets: {total_retweets}, Hour total: {self.retweet_count}")
        return total_retweets
    
    def run_forever(self):
        """Main loop for 24/7 operation"""
        self.log_activity("🚀 Starting 24/7 bot operation")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                self.log_activity(f"🔄 Starting cycle #{cycle}")
                
                # Run bot cycle
                self.run_bot_cycle()
                
                # Wait before next cycle (20-40 minutes)
                wait_minutes = random.randint(20, 40)
                self.log_activity(f"⏰ Waiting {wait_minutes} minutes until next cycle")
                time.sleep(wait_minutes * 60)
                
            except KeyboardInterrupt:
                self.log_activity("🛑 Bot stopped by user")
                break
            except Exception as e:
                self.log_activity(f"❌ Unexpected error: {e}")
                self.log_activity("⏳ Waiting 5 minutes before retry")
                time.sleep(300)  # Wait 5 minutes before retry

def test_credentials():
    """Test if API credentials work"""
    try:
        client = tweepy.Client(bearer_token=BEARER_TOKEN)
        me = client.get_me()
        print(f"✅ Credentials working! Connected as: @{me.data.username}")
        return True
    except Exception as e:
        print(f"❌ Credential test failed: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("       TWITTER BOT - CLOUD DEPLOYMENT")
    print("="*60)
    
    # Test credentials first
    if test_credentials():
        # Start the bot
        bot = CloudTwitterBot()
        bot.run_forever()
    else:
        print("🚫 Cannot start bot without valid credentials")
        print("Make sure all environment variables are set!")