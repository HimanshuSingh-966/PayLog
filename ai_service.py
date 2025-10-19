import os
import requests
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import re
import time

logger = logging.getLogger(__name__)

class GeminiAIService:
    def __init__(self):
        # Google AI Studio Configuration (Primary for Render - Most Reliable)
        self.google_ai_key = os.getenv('GOOGLE_AI_API_KEY')
        self.google_ai_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
        # Groq Configuration (Backup - Fast and Generous)
        self.groq_key = os.getenv('GROQ_API_KEY')
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        self.groq_model = "llama-3.1-8b-instant"
        
        # OpenRouter Configuration (Fallback)
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.openrouter_model = "google/gemini-2.0-flash-exp:free"
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests
        
        # Determine which provider to use
        self.active_provider = self._determine_provider()
        logger.info(f"🚀 AI Service initialized for Render with provider: {self.active_provider}")
        
    def _determine_provider(self) -> str:
        """Determine which AI provider to use based on available API keys"""
        if self.google_ai_key:
            logger.info("✅ Google AI Studio (Primary) detected - 1,500 req/day")
            return "google"
        elif self.groq_key:
            logger.info("✅ Groq (Backup) detected - 14,400 req/day")
            return "groq"
        elif self.openrouter_key:
            logger.info("⚠️ Only OpenRouter available - 200 req/day (limited)")
            return "openrouter"
        else:
            logger.warning("❌ No AI API keys configured - using fallback regex parser")
            return "fallback"
    
    def _rate_limit(self):
        """Simple rate limiting to avoid hitting API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request_google(self, messages: List[Dict], temperature: float = 0.7) -> Optional[str]:
        """Make request to Google AI Studio (Direct Gemini API)"""
        try:
            self._rate_limit()
            
            # Convert messages to Gemini format
            prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            
            url = f"{self.google_ai_url}?key={self.google_ai_key}"
            
            response = requests.post(
                url=url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": 1024,
                    }
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
            return None
            
        except Exception as e:
            logger.error(f"Google AI request failed: {e}")
            return None
    
    def _make_request_groq(self, messages: List[Dict], temperature: float = 0.7) -> Optional[str]:
        """Make request to Groq API"""
        try:
            self._rate_limit()
            
            response = requests.post(
                url=self.groq_url,
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.groq_model,
                    "messages": messages,
                    "temperature": temperature,
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Groq request failed: {e}")
            return None
    
    def _make_request_openrouter(self, messages: List[Dict], temperature: float = 0.7) -> Optional[str]:
        """Make request to OpenRouter API"""
        try:
            self._rate_limit()
            
            response = requests.post(
                url=self.openrouter_url,
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/paylog-ai",
                    "X-Title": "PayLog AI"
                },
                json={
                    "model": self.openrouter_model,
                    "messages": messages,
                    "temperature": temperature,
                },
                timeout=30
            )
            
            if response.status_code == 429:
                logger.warning("OpenRouter rate limit hit (200/day exceeded)")
                return None
                
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"OpenRouter request failed: {e}")
            return None
    
    def _make_request(self, messages: List[Dict], temperature: float = 0.7) -> Optional[str]:
        """Make AI request with automatic fallback between providers"""
        
        # Try primary provider first
        if self.active_provider == "google":
            response = self._make_request_google(messages, temperature)
            if response:
                return response
            # Fallback to Groq
            if self.groq_key:
                logger.info("⚠️ Google AI failed, falling back to Groq")
                response = self._make_request_groq(messages, temperature)
                if response:
                    return response
            # Fallback to OpenRouter
            if self.openrouter_key:
                logger.info("⚠️ Groq failed, falling back to OpenRouter")
                return self._make_request_openrouter(messages, temperature)
                
        elif self.active_provider == "groq":
            response = self._make_request_groq(messages, temperature)
            if response:
                return response
            # Fallback to Google
            if self.google_ai_key:
                logger.info("⚠️ Groq failed, falling back to Google AI")
                response = self._make_request_google(messages, temperature)
                if response:
                    return response
            # Fallback to OpenRouter
            if self.openrouter_key:
                logger.info("⚠️ Google AI failed, falling back to OpenRouter")
                return self._make_request_openrouter(messages, temperature)
                
        elif self.active_provider == "openrouter":
            response = self._make_request_openrouter(messages, temperature)
            if response:
                return response
            # Try other providers
            if self.google_ai_key:
                logger.info("⚠️ OpenRouter failed, falling back to Google AI")
                response = self._make_request_google(messages, temperature)
                if response:
                    return response
            if self.groq_key:
                logger.info("⚠️ Google AI failed, falling back to Groq")
                return self._make_request_groq(messages, temperature)
        
        # All providers failed
        logger.warning("❌ All AI providers failed - using fallback regex parser")
        return None
    
    def parse_natural_language(self, text: str) -> Dict[str, Any]:
        prompt = f"""Parse this expense transaction text and extract structured information.

                    Transaction text: '{text}'
                    
                    Extract:
                    1. amount (numeric value only)
                    2. category (groceries, food, transport, shopping, bills, entertainment, fuel, etc.)
                    3. description (what was bought/paid for)
                    4. merchant/location (if mentioned)
                    5. time_reference (today, yesterday, last week, specific date - return "today" if not mentioned)
                    
                    Return ONLY a JSON object with these exact keys: amount, category, description, merchant, time_reference
                    If something is not mentioned, use empty string.
                    
                    Example output: {{"amount": "500", "category": "groceries", "description": "monthly groceries", "merchant": "DMart", "time_reference": "today"}}"""

        messages = [{"role": "user", "content": prompt}]
        response = self._make_request(messages, temperature=0.3)
        
        if not response:
            return self._fallback_parse(text)
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                parsed = json.loads(json_match.group())
                return parsed
            return self._fallback_parse(text)
        except:
            return self._fallback_parse(text)
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Enhanced fallback parser with better pattern matching"""
        # Extract amount
        amount_match = re.search(r'₹?\s*(\d+(?:\.\d+)?)', text)
        amount = amount_match.group(1) if amount_match else ""
        
        # Category detection with comprehensive patterns
        category = ""
        category_keywords = {
            "groceries": ["grocery", "groceries", "supermarket", "dmart", "reliance", "big bazaar", "more", "star bazaar"],
            "food": ["food", "lunch", "dinner", "breakfast", "meal", "restaurant", "cafe", "zomato", "swiggy", "burger", "pizza", "biryani"],
            "transport": ["transport", "uber", "ola", "metro", "bus", "auto", "taxi", "travel", "cab", "rapido"],
            "fuel": ["fuel", "petrol", "diesel", "gas", "cng"],
            "shopping": ["shopping", "clothes", "amazon", "flipkart", "mall", "myntra", "ajio", "purchase"],
            "bills": ["bill", "electricity", "water", "internet", "mobile", "recharge", "broadband", "wifi"],
            "entertainment": ["movie", "entertainment", "netflix", "spotify", "prime", "hotstar", "game", "concert"],
            "health": ["medicine", "doctor", "hospital", "pharmacy", "medical", "clinic", "apollo", "health"]
        }
        
        text_lower = text.lower()
        for cat, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                category = cat
                break
        
        # Merchant extraction - look for "at", "from", "in"
        merchant = ""
        merchant_keywords = ["at", "from", "in", "@"]
        for keyword in merchant_keywords:
            if keyword in text_lower:
                parts = text_lower.split(keyword)
                if len(parts) > 1:
                    potential_merchant = parts[1].strip().split()[0]
                    if len(potential_merchant) > 2:  # Avoid single letters
                        merchant = potential_merchant.title()
                    break
        
        return {
            "amount": amount,
            "category": category if category else "other",
            "description": text,
            "merchant": merchant,
            "time_reference": "today"
        }
    
    def get_spending_insights(self, transactions_data: str, period: str = "month") -> str:
        prompt = f"""Analyze these expense transactions and provide personalized insights.

Period: {period}
Transactions data:
{transactions_data}

Provide:
1. Daily average spending
2. Top spending categories with percentages
3. Notable trends (increases/decreases)
4. Brief financial advice (2-3 sentences max)

Keep response concise and personal. Use rupee symbol ₹."""

        messages = [{"role": "user", "content": prompt}]
        response = self._make_request(messages, temperature=0.7)
        return response or "Unable to generate insights at this time. Your spending patterns look normal."
    
    def detect_spending_spike(self, amount: float, daily_average: float, category: str) -> Optional[str]:
        if amount >= daily_average * 3:
            return f"⚠️ High spending alert! You spent ₹{amount:,.2f} on {category} - that's {amount/daily_average:.1f}x your daily average of ₹{daily_average:,.2f}"
        return None
    
    def suggest_category(self, description: str, amount: float, historical_patterns: List[Dict]) -> str:
        if not historical_patterns:
            return self._fallback_parse(description).get('category', 'other')
        
        patterns_text = "\n".join([f"- {p['desc']}: {p['cat']}" for p in historical_patterns[:10]])
        
        prompt = f"""Based on these past transactions, suggest the most likely category for this new transaction.

Past patterns:
{patterns_text}

New transaction:
Description: {description}
Amount: ₹{amount}

Return ONLY the category name (groceries, food, transport, shopping, bills, entertainment, fuel, etc.)"""

        messages = [{"role": "user", "content": prompt}]
        response = self._make_request(messages, temperature=0.3)
        
        if response:
            category = response.strip().lower()
            return category
        
        # Fallback: use pattern matching
        return self._fallback_parse(description).get('category', 'other')
    
    def generate_forecast(self, transactions_data: str) -> str:
        prompt = f"""Based on this spending history, forecast the month-end total.

Transaction history:
{transactions_data}

Provide:
1. Estimated month-end spending
2. Current pace/burn rate
3. Days left in month consideration

Keep response brief (2-3 sentences). Use ₹ symbol."""

        messages = [{"role": "user", "content": prompt}]
        response = self._make_request(messages, temperature=0.5)
        return response or "At current rate, maintain your spending pace to stay within budget."
    
    def analyze_lending_patterns(self, lending_data: str) -> str:
        prompt = f"""Analyze lending patterns and provide insights.

Lending history:
{lending_data}

Provide:
1. Average lending amount
2. Average return time
3. Total pending vs returned
4. Brief recommendation

Keep response concise. Use ₹ symbol."""

        messages = [{"role": "user", "content": prompt}]
        response = self._make_request(messages, temperature=0.6)
        return response or "Continue tracking your lending carefully. Consider setting reminders for overdue amounts."
    
    def suggest_wallet_transfer(self, wallet_balance: float, total_balance: float, 
                                 spending_pattern: str) -> Optional[str]:
        if wallet_balance < 100:
            suggested_amount = 2000
            return f"💡 Your wallet is low (₹{wallet_balance}). Consider transferring ₹{suggested_amount} from Total Stack."
        return None
    
    def calculate_financial_health(self, income: float, expenses: float, 
                                    savings: float, period: str = "month") -> str:
        prompt = f"""Calculate financial health score and provide brief advice.

Period: {period}
Income: ₹{income}
Expenses: ₹{expenses}
Savings: ₹{savings}

Provide:
1. Savings rate percentage
2. Expense ratio assessment
3. Brief advice (2 sentences)

Keep concise. Use ₹ symbol."""

        messages = [{"role": "user", "content": prompt}]
        response = self._make_request(messages, temperature=0.6)
        
        if not response:
            savings_rate = (savings/income*100) if income > 0 else 0
            return f"Savings rate: {savings_rate:.1f}%. {'Great job!' if savings_rate > 20 else 'Try to save more.'}"
        
        return response
    
    def detect_anomaly(self, amount: float, category: str, historical_avg: float) -> Optional[str]:
        if historical_avg > 0 and amount > historical_avg * 5:
            return f"🔔 Unusual transaction detected! ₹{amount:,.2f} for {category} is much higher than your average of ₹{historical_avg:,.2f}. Please confirm this is correct."
        return None
