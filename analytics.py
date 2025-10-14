import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)

class ExpenseAnalytics:
    @staticmethod
    def calculate_daily_average(transactions: List[Dict], days: int = 30) -> float:
        if not transactions:
            return 0.0
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_expenses = [
            float(t['amount']) for t in transactions
            if t['type'] == 'subtract' and 
            datetime.strptime(str(t['date']), '%d/%m/%Y') >= cutoff_date
        ]
        
        return sum(recent_expenses) / days if days > 0 else 0.0
    
    @staticmethod
    def get_category_breakdown(transactions: List[Dict], period_days: int = 30) -> Dict[str, float]:
        cutoff_date = datetime.now() - timedelta(days=period_days)
        category_totals = defaultdict(float)
        
        for t in transactions:
            try:
                if t['type'] == 'subtract':
                    trans_date = datetime.strptime(str(t['date']), '%d/%m/%Y')
                    if trans_date >= cutoff_date:
                        category = t.get('category', 'other') or 'other'
                        amount = float(t['amount'])
                        category_totals[category] += amount
            except:
                continue
        
        total = sum(category_totals.values())
        if total == 0:
            return {}
        
        return {cat: (amt/total)*100 for cat, amt in category_totals.items()}
    
    @staticmethod
    def detect_trend(transactions: List[Dict], category: str = None, weeks: int = 4) -> str:
        if len(transactions) < 2:
            return "Not enough data"
        
        now = datetime.now()
        week_totals = []
        
        for week_offset in range(weeks):
            week_start = now - timedelta(weeks=week_offset+1)
            week_end = now - timedelta(weeks=week_offset)
            
            week_total = 0
            for t in transactions:
                try:
                    trans_date = datetime.strptime(str(t['date']), '%d/%m/%Y')
                    if week_start <= trans_date < week_end and t['type'] == 'subtract':
                        t_category = t.get('category', 'other') or 'other'
                        if category is None or t_category == category:
                            week_total += float(t['amount'])
                except:
                    continue
            week_totals.append(week_total)
        
        if len(week_totals) < 2:
            return "stable"
        
        week_totals.reverse()
        
        recent_avg = sum(week_totals[-2:]) / 2
        older_avg = sum(week_totals[:2]) / 2
        
        if older_avg == 0:
            return "increasing" if recent_avg > 0 else "stable"
        
        change = ((recent_avg - older_avg) / older_avg) * 100
        
        if change > 15:
            return f"increasing {abs(change):.0f}%"
        elif change < -15:
            return f"decreasing {abs(change):.0f}%"
        else:
            return "stable"
    
    @staticmethod
    def forecast_month_end(transactions: List[Dict]) -> Tuple[float, str]:
        now = datetime.now()
        month_start = now.replace(day=1)
        days_elapsed = (now - month_start).days + 1
        days_in_month = (now.replace(month=now.month+1, day=1) - timedelta(days=1)).day if now.month < 12 else 31
        
        month_expenses = sum(
            float(t['amount']) for t in transactions
            if t['type'] == 'subtract' and 
            datetime.strptime(str(t['date']), '%d/%m/%Y') >= month_start
        )
        
        daily_rate = month_expenses / days_elapsed if days_elapsed > 0 else 0
        forecast = daily_rate * days_in_month
        
        pace = "normal"
        if daily_rate > 1000:
            pace = "high"
        elif daily_rate < 300:
            pace = "low"
        
        return forecast, pace
    
    @staticmethod
    def get_burn_rate(wallet_balance: float, transactions: List[Dict], days: int = 7) -> Tuple[float, int]:
        cutoff = datetime.now() - timedelta(days=days)
        
        wallet_expenses = sum(
            float(t['amount']) for t in transactions
            if t['type'] == 'subtract' and 
            t.get('wallet_type') == 'wallet' and
            datetime.strptime(str(t['date']), '%d/%m/%Y') >= cutoff
        )
        
        daily_burn = wallet_expenses / days if days > 0 else 0
        days_left = int(wallet_balance / daily_burn) if daily_burn > 0 else 999
        
        return daily_burn, days_left
    
    @staticmethod
    def get_frequent_transactions(transactions: List[Dict], limit: int = 10) -> List[Dict]:
        if not transactions:
            return []
        
        recent = transactions[-100:]
        
        transaction_patterns = []
        for t in recent:
            if t['type'] == 'subtract':
                amount = float(t['amount'])
                desc = str(t.get('description', '')).lower()
                category = t.get('category', 'other') or 'other'
                
                pattern = f"{desc}_{category}_{amount}"
                transaction_patterns.append({
                    'pattern': pattern,
                    'amount': amount,
                    'category': category,
                    'description': desc
                })
        
        pattern_counts = Counter(tp['pattern'] for tp in transaction_patterns)
        
        frequent = []
        seen_patterns = set()
        for tp in transaction_patterns:
            if tp['pattern'] in seen_patterns:
                continue
            if pattern_counts[tp['pattern']] >= 2:
                frequent.append({
                    'amount': tp['amount'],
                    'category': tp['category'],
                    'description': tp['description'],
                    'count': pattern_counts[tp['pattern']]
                })
                seen_patterns.add(tp['pattern'])
        
        return sorted(frequent, key=lambda x: x['count'], reverse=True)[:limit]
    
    @staticmethod
    def analyze_lending(lending_records: List[Dict]) -> Dict[str, any]:
        if not lending_records:
            return {
                'total_lent': 0,
                'total_returned': 0,
                'pending': 0,
                'avg_amount': 0,
                'avg_return_days': 0,
                'pending_persons': []
            }
        
        total_lent = sum(float(r['amount']) for r in lending_records if r['status'] == 'lent')
        total_returned = sum(float(r['amount']) for r in lending_records if r['status'] == 'returned')
        pending = total_lent - total_returned
        
        amounts = [float(r['amount']) for r in lending_records]
        avg_amount = sum(amounts) / len(amounts) if amounts else 0
        
        return_times = []
        for r in lending_records:
            if r['status'] == 'returned' and r.get('return_date'):
                try:
                    lent_date = datetime.strptime(str(r['date']), '%d/%m/%Y')
                    return_date = datetime.strptime(str(r['return_date']), '%d/%m/%Y')
                    days = (return_date - lent_date).days
                    return_times.append(days)
                except:
                    continue
        
        avg_return_days = sum(return_times) / len(return_times) if return_times else 0
        
        pending_persons = []
        person_totals = defaultdict(float)
        for r in lending_records:
            if r['status'] == 'lent':
                person_totals[r['person']] += float(r['amount'])
        
        for person, amount in person_totals.items():
            if amount > 0:
                pending_persons.append({'person': person, 'amount': amount})
        
        return {
            'total_lent': total_lent,
            'total_returned': total_returned,
            'pending': pending,
            'avg_amount': avg_amount,
            'avg_return_days': avg_return_days,
            'pending_persons': sorted(pending_persons, key=lambda x: x['amount'], reverse=True)
        }
