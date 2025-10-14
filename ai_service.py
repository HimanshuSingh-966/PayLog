import os
import requests
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class GeminiAIService:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "google/gemini-2.0-flash-exp:free"
        
    def _make_request(self, messages: List[Dict], temperature: float = 0.7) -> Optional[str]:
        if not self.api_key:
            logger.warning("OpenRouter API key not configured")
            return None
            
        try:
            response = requests.post(
                url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"AI request failed: {e}")
            return None
    
    def parse_natural_language(self, text: str) -> Dict[str, Any]:
        prompt = f"""Parse this expense transaction text and extract structured information.

Transaction text: "{text}"

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
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                parsed = json.loads(json_match.group())
                return parsed
            return self._fallback_parse(text)
        except:
            return self._fallback_parse(text)
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        amount_match = re.search(r'₹?\s*(\d+(?:\.\d+)?)', text)
        amount = amount_match.group(1) if amount_match else ""
        
        category = ""
        categories = ["groceries", "grocery", "food", "transport", "shopping", "bills", "entertainment", "fuel", "petrol"]
        for cat in categories:
            if cat in text.lower():
                category = cat if cat != "grocery" else "groceries"
                break
        
        return {
            "amount": amount,
            "category": category,
            "description": text,
            "merchant": "",
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
        return response or "Unable to generate insights at this time."
    
    def detect_spending_spike(self, amount: float, daily_average: float, category: str) -> Optional[str]:
        if amount >= daily_average * 3:
            return f"⚠️ High spending alert! You spent ₹{amount:,.2f} on {category} - that's {amount/daily_average:.1f}x your daily average of ₹{daily_average:,.2f}"
        return None
    
    def suggest_category(self, description: str, amount: float, historical_patterns: List[Dict]) -> str:
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
        return "other"
    
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
        return response or "At current rate, maintain your spending pace."
    
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
        return response or "Continue tracking your lending carefully."
    
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
        return response or f"Savings rate: {(savings/income*100) if income > 0 else 0:.1f}%"
    
    def detect_anomaly(self, amount: float, category: str, historical_avg: float) -> Optional[str]:
        if amount > historical_avg * 5:
            return f"🔔 Unusual transaction detected! ₹{amount:,.2f} for {category} is much higher than your average of ₹{historical_avg:,.2f}. Please confirm this is correct."
        return None
