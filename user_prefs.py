import json
import os
from typing import Dict, Any, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class UserPreferences:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.prefs_file = f"user_prefs_{user_id}.json"
        self.data = self._load_prefs()
    
    def _load_prefs(self) -> Dict:
        if os.path.exists(self.prefs_file):
            try:
                with open(self.prefs_file, 'r') as f:
                    return json.load(f)
            except:
                logger.error(f"Failed to load preferences for user {self.user_id}")
        
        return {
            'aliases': {},
            'frequent_transactions': [],
            'spending_limits': {},
            'goals': [],
            'alert_settings': {
                'spike_multiplier': 3,
                'weekly_summary': True,
                'monthly_warning': True
            },
            'context': {
                'last_category': '',
                'last_amount': 0,
                'last_wallet': 'wallet'
            },
            'transaction_history': []
        }
    
    def _save_prefs(self):
        try:
            with open(self.prefs_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
    
    def add_alias(self, shortcut: str, full_text: str):
        self.data['aliases'][shortcut.lower()] = full_text.lower()
        self._save_prefs()
    
    def get_alias(self, shortcut: str) -> Optional[str]:
        return self.data['aliases'].get(shortcut.lower())
    
    def get_all_aliases(self) -> Dict[str, str]:
        return self.data['aliases']
    
    def set_spending_limit(self, category: str, limit: float, period: str = 'daily'):
        if 'spending_limits' not in self.data:
            self.data['spending_limits'] = {}
        self.data['spending_limits'][category] = {
            'limit': limit,
            'period': period
        }
        self._save_prefs()
    
    def get_spending_limit(self, category: str) -> Optional[Dict]:
        return self.data.get('spending_limits', {}).get(category)
    
    def add_goal(self, goal_type: str, target: float, description: str, deadline: Optional[str] = None):
        from datetime import datetime
        goal = {
            'type': goal_type,
            'target': target,
            'description': description,
            'deadline': deadline,
            'created': str(datetime.now().date())
        }
        if 'goals' not in self.data:
            self.data['goals'] = []
        self.data['goals'].append(goal)
        self._save_prefs()
    
    def get_active_goals(self) -> list:
        return self.data.get('goals', [])
    
    def update_context(self, category: Optional[str] = None, amount: Optional[float] = None, wallet: Optional[str] = None):
        if category:
            self.data['context']['last_category'] = category
        if amount:
            self.data['context']['last_amount'] = amount
        if wallet:
            self.data['context']['last_wallet'] = wallet
        self._save_prefs()
    
    def get_context(self) -> Dict:
        return self.data.get('context', {})
    
    def add_to_history(self, description: str, category: str, amount: float):
        if 'transaction_history' not in self.data:
            self.data['transaction_history'] = []
        
        self.data['transaction_history'].append({
            'desc': description,
            'cat': category,
            'amt': amount
        })
        
        if len(self.data['transaction_history']) > 100:
            self.data['transaction_history'] = self.data['transaction_history'][-100:]
        
        self._save_prefs()
    
    def get_history_patterns(self) -> list:
        return self.data.get('transaction_history', [])
    
    def toggle_alert(self, alert_type: str, enabled: bool):
        if 'alert_settings' not in self.data:
            self.data['alert_settings'] = {}
        self.data['alert_settings'][alert_type] = enabled
        self._save_prefs()
    
    def get_alert_settings(self) -> Dict:
        return self.data.get('alert_settings', {
            'spike_multiplier': 3,
            'weekly_summary': True,
            'monthly_warning': True
        })
