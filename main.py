import logging
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import gspread
from google.oauth2.service_account import Credentials
import json
from dotenv import load_dotenv
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import re
import csv
import io
from ai_service import GeminiAIService
from analytics import ExpenseAnalytics
from user_prefs import UserPreferences

load_dotenv()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
GOOGLE_SHEETS_CREDS = os.getenv('GOOGLE_SHEETS_CREDS')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
PORT = int(os.getenv('PORT', 8000))

if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable is required")
    logger.info("Please set BOT_TOKEN in your .env file and restart the bot")
    import sys
    sys.exit(0)
if not GOOGLE_SHEETS_CREDS:
    logger.warning("GOOGLE_SHEETS_CREDS not found - Google Sheets functionality will be disabled")
if not SPREADSHEET_ID:
    logger.warning("SPREADSHEET_ID not found - Google Sheets functionality will be disabled")

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'PayLog AI Bot is running!')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def start_web_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    logger.info(f"Starting HTTP server on port {PORT}")
    server.serve_forever()

class ExpenseTracker:
    def __init__(self):
        self.gc = None
        self.spreadsheet = None
        self.transactions_sheet = None
        self.lending_sheet = None
        self.ai_service = GeminiAIService()
        self.init_google_sheets()
        
    def init_google_sheets(self):
        try:
            if not GOOGLE_SHEETS_CREDS or not SPREADSHEET_ID:
                logger.warning("Google Sheets credentials or Spreadsheet ID missing")
                return
                
            creds_dict = json.loads(GOOGLE_SHEETS_CREDS)
            credentials = Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://spreadsheets.google.com/feeds',
                       'https://www.googleapis.com/auth/drive']
            )
            self.gc = gspread.authorize(credentials)
            self.spreadsheet = self.gc.open_by_key(SPREADSHEET_ID)
            
            try:
                self.transactions_sheet = self.spreadsheet.worksheet('transactions')
            except gspread.WorksheetNotFound:
                self.transactions_sheet = self.spreadsheet.add_worksheet(
                    title='transactions', rows=1000, cols=9
                )
                self.transactions_sheet.append_row([
                    'date', 'type', 'wallet_type', 'amount', 'description', 'balance_total', 'balance_wallet', 'category', 'merchant'
                ])
            
            try:
                self.lending_sheet = self.spreadsheet.worksheet('lending')
            except gspread.WorksheetNotFound:
                self.lending_sheet = self.spreadsheet.add_worksheet(
                    title='lending', rows=1000, cols=7
                )
                self.lending_sheet.append_row([
                    'date', 'person', 'amount', 'status', 'description', 'return_date', 'return_to'
                ])
                
            logger.info("Google Sheets initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing Google Sheets: {e}")
            logger.warning("Bot will continue without Google Sheets functionality")

    def get_current_balances(self):
        try:
            if self.transactions_sheet:
                records = self.transactions_sheet.get_all_records()
                if records:
                    last_record = records[-1]
                    return float(last_record.get('balance_total', 0)), float(last_record.get('balance_wallet', 0))
            return 0, 0
        except Exception as e:
            logger.error(f"Error getting balances: {e}")
            return 0, 0

    def add_transaction(self, transaction_type, wallet_type, amount, description, category='', merchant='', date_override=None):
        try:
            total_balance, wallet_balance = self.get_current_balances()
            
            if wallet_type == 'total':
                if transaction_type == 'add':
                    total_balance += amount
                else:
                    total_balance -= amount
            elif wallet_type == 'wallet':
                if transaction_type == 'add':
                    wallet_balance += amount
                else:
                    wallet_balance -= amount
            
            trans_date = date_override if date_override else datetime.now()
            row_data = [
                trans_date.strftime('%d/%m/%Y'),
                transaction_type,
                wallet_type,
                amount,
                description,
                total_balance,
                wallet_balance,
                category,
                merchant
            ]
            
            if self.transactions_sheet:
                self.transactions_sheet.append_row(row_data)
            
            return total_balance, wallet_balance
            
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return 0, 0

    def get_all_transactions(self):
        try:
            if self.transactions_sheet:
                return self.transactions_sheet.get_all_records()
            return []
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            return []

    def get_all_lending(self):
        try:
            if self.lending_sheet:
                return self.lending_sheet.get_all_records()
            return []
        except Exception as e:
            logger.error(f"Error getting lending: {e}")
            return []

    def add_lending(self, person, amount, description):
        try:
            now = datetime.now()
            row_data = [
                now.strftime('%d/%m/%Y'),
                person,
                amount,
                'lent',
                description,
                '',
                ''
            ]
            
            if self.lending_sheet:
                self.lending_sheet.append_row(row_data)
                
        except Exception as e:
            logger.error(f"Error adding lending: {e}")

    def return_lending(self, person, amount, return_to):
        try:
            if not self.lending_sheet:
                return False
                
            records = self.lending_sheet.get_all_records()
            
            for i, record in enumerate(records):
                if (record['person'] == person and 
                    float(record['amount']) == amount and 
                    record['status'] == 'lent'):
                    
                    row_num = i + 2
                    self.lending_sheet.update_cell(row_num, 4, 'returned')
                    self.lending_sheet.update_cell(row_num, 6, datetime.now().strftime('%d/%m/%Y'))
                    self.lending_sheet.update_cell(row_num, 7, return_to)
                    
                    self.add_transaction('add', return_to, amount, f'Returned by {person}', category='lending')
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error returning lending: {e}")
            return False

    def undo_last_transaction(self):
        try:
            if not self.transactions_sheet:
                return False, "Sheets not connected"
            
            records = self.transactions_sheet.get_all_records()
            if len(records) < 1:
                return False, "No transactions to undo"
            
            last_row = len(records) + 1
            self.transactions_sheet.delete_rows(last_row)
            return True, "Last transaction undone successfully"
            
        except Exception as e:
            logger.error(f"Error undoing transaction: {e}")
            return False, str(e)

    def export_to_csv(self, transactions):
        """Export transactions to CSV format"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Date', 'Type', 'Wallet', 'Amount', 'Category', 'Description', 'Merchant'])
        
        for t in transactions:
            writer.writerow([
                t.get('date', ''),
                t.get('type', ''),
                t.get('wallet_type', ''),
                t.get('amount', ''),
                t.get('category', ''),
                t.get('description', ''),
                t.get('merchant', '')
            ])
        
        return output.getvalue()

tracker = ExpenseTracker()
user_preferences = {}

def get_user_prefs(user_id: int) -> UserPreferences:
    if user_id not in user_preferences:
        user_preferences[user_id] = UserPreferences(user_id)
    return user_preferences[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return
    
    if context.user_data:
        context.user_data.clear()
    user_id = update.message.from_user.id
    prefs = get_user_prefs(user_id)
        
    keyboard = [
        [KeyboardButton("💰 Total Stack"), KeyboardButton("👛 Wallet")],
        [KeyboardButton("🤝 Lending"), KeyboardButton("📊 Reports")],
        [KeyboardButton("📋 Summary"), KeyboardButton("💡 Insights")],
        [KeyboardButton("⚙️ Settings"), KeyboardButton("🔄 Undo Last")],
        [KeyboardButton("⚡ Quick Add"), KeyboardButton("📤 Export Data")],
        [KeyboardButton("📝 Batch Entry"), KeyboardButton("🎯 My Goals")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_msg = """
🎯 **Welcome to PayLog AI - Your Intelligent Expense Tracker!**

🤖 **AI-Powered Features:**
• 💬 Natural language input - just type naturally!
• 🎤 Voice message support
• 📈 Smart insights and predictions
• 🎯 Spending alerts and goals
• 🧠 Learns your patterns

📱 **Main Features:**
• 💰 Total Stack & 👛 Wallet management
• 📝 Batch entry for multiple transactions
• 🤝 Smart lending tracking
• 📊 Intelligent reports
• 💡 AI-powered insights
• ⚡ Quick add with presets
• 📤 Export to CSV

🚀 **Try saying:**
"Spent 500 on groceries at DMart"
"Yesterday I paid 1000 for dinner"
"Show me food expenses from last week"

Choose an option below or just type naturally!
    """
    
    await update.message.reply_text(welcome_msg, reply_markup=reply_markup)

async def handle_natural_language(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if not update.message or not update.message.from_user:
        return
    user_id = update.message.from_user.id
    prefs = get_user_prefs(user_id)
    
    aliases = prefs.get_all_aliases()
    for shortcut, full in aliases.items():
        if shortcut in text.lower():
            text = text.lower().replace(shortcut, full)
    
    if any(keyword in text.lower() for keyword in ['spent', 'paid', 'bought', 'subtract', 'sub']):
        if update.message:
            await update.message.reply_text("🤖 Analyzing your expense...")
        
        parsed = tracker.ai_service.parse_natural_language(text)
        
        if not parsed.get('amount'):
            if update.message:
                await update.message.reply_text("❌ Couldn't extract amount. Please try: 'Spent 500 on groceries'")
            return
        
        amount = float(parsed['amount'])
        category = parsed.get('category', 'other')
        description = parsed.get('description', text)
        merchant = parsed.get('merchant', '')
        
        if not category or category == 'other':
            history = prefs.get_history_patterns()
            if history:
                category = tracker.ai_service.suggest_category(description, amount, history)
        
        context_data = prefs.get_context()
        wallet_type = context_data.get('last_wallet', 'wallet')
        
        trans_date = datetime.now()
        time_ref = parsed.get('time_reference', 'today').lower()
        if 'yesterday' in time_ref:
            trans_date = datetime.now() - timedelta(days=1)
        elif 'week' in time_ref and 'last' in time_ref:
            trans_date = datetime.now() - timedelta(days=7)
        
        total_bal, wallet_bal = tracker.add_transaction('subtract', wallet_type, amount, description, category=category, merchant=merchant, date_override=trans_date)
        
        prefs.add_to_history(description, category, amount)
        prefs.update_context(category=category, amount=amount, wallet=wallet_type)
        
        transactions = tracker.get_all_transactions()
        daily_avg = ExpenseAnalytics.calculate_daily_average(transactions)
        
        alert_msg = ""
        if daily_avg > 0:
            spike_alert = tracker.ai_service.detect_spending_spike(amount, daily_avg, category)
            if spike_alert:
                alert_msg = f"\n\n{spike_alert}"
        
        anomaly_alert = tracker.ai_service.detect_anomaly(amount, category, daily_avg)
        if anomaly_alert:
            alert_msg += f"\n\n{anomaly_alert}"
        
        if update.message:
            await update.message.reply_text(
                f"✅ **Expense Recorded!**\n\n"
                f"💰 Amount: ₹{amount:,.2f}\n"
                f"📂 Category: {category}\n"
                f"🏪 Merchant: {merchant if merchant else 'N/A'}\n"
                f"📅 Date: {trans_date.strftime('%d %b %Y')}\n"
                f"📝 Description: {description}\n\n"
                f"💳 **Updated Balances:**\n"
                f"   • Total: ₹{total_bal:,.2f}\n"
                f"   • Wallet: ₹{wallet_bal:,.2f}"
                f"{alert_msg}"
            )
        
    elif any(keyword in text.lower() for keyword in ['add', 'received', 'income', 'salary']):
        if update.message:
            await update.message.reply_text("🤖 Processing income...")
        
        parsed = tracker.ai_service.parse_natural_language(text)
        
        if not parsed.get('amount'):
            if update.message:
                await update.message.reply_text("❌ Couldn't extract amount.")
            return
        
        amount = float(parsed['amount'])
        description = parsed.get('description', text)
        
        context_data = prefs.get_context()
        wallet_type = context_data.get('last_wallet', 'total')
        
        total_bal, wallet_bal = tracker.add_transaction('add', wallet_type, amount, description, category='income')
        
        if update.message:
            await update.message.reply_text(
                f"✅ **Income Added!**\n\n"
                f"💰 Amount: ₹{amount:,.2f}\n"
                f"📝 {description}\n\n"
                f"💳 New Balance: ₹{total_bal if wallet_type=='total' else wallet_bal:,.2f}"
            )
        
    elif 'show' in text.lower() or 'expenses' in text.lower():
        if update.message:
            await update.message.reply_text("📊 Fetching your expenses...")
        
        transactions = tracker.get_all_transactions()
        
        if 'week' in text.lower():
            period_days = 7
        elif 'month' in text.lower():
            period_days = 30
        else:
            period_days = 1
        
        cutoff = datetime.now() - timedelta(days=period_days)
        filtered = [t for t in transactions if datetime.strptime(str(t['date']), '%d/%m/%Y') >= cutoff]
        
        if not filtered:
            if update.message:
                await update.message.reply_text(f"No transactions found for the last {period_days} days.")
            return
        
        response = f"📊 **Expenses (Last {period_days} days):**\n\n"
        for t in filtered[-10:]:
            response += f"📅 {t['date']} | ₹{t['amount']} - {t['description']}\n"
        
        if update.message:
            await update.message.reply_text(response)
    
    else:
        context_data = prefs.get_context()
        if context_data.get('last_category'):
            if any(word in text.lower() for word in ['add', 'more', 'that', 'same']):
                try:
                    amount_match = re.search(r'(\d+(?:\.\d+)?)', text)
                    if amount_match:
                        amount = float(amount_match.group(1))
                        category = context_data['last_category']
                        wallet_type = context_data.get('last_wallet', 'wallet')
                        
                        total_bal, wallet_bal = tracker.add_transaction('subtract', wallet_type, amount, text, category=category)
                        
                        if update.message:
                            await update.message.reply_text(
                                f"✅ Added ₹{amount} to {category}!\n"
                                f"💳 Balance: ₹{total_bal if wallet_type=='total' else wallet_bal:,.2f}"
                            )
                        return
                except:
                    pass
        
        if update.message:
            await update.message.reply_text(
                "🤔 I didn't understand that. Try:\n"
                "• 'Spent 500 on groceries'\n"
                "• 'Yesterday paid 1000 for dinner'\n"
                "• 'Show me food expenses'"
            )

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or not update.message.from_user:
        return
        
    text = update.message.text
    user_id = update.message.from_user.id
    
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    
    if text in ["💰 Total Stack", "👛 Wallet"]:
        context.user_data['category'] = 'total' if text == "💰 Total Stack" else 'wallet'
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Money", callback_data=f"add_{context.user_data['category']}"),
             InlineKeyboardButton("➖ Subtract Money", callback_data=f"subtract_{context.user_data['category']}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        total_balance, wallet_balance = tracker.get_current_balances()
        current_balance = total_balance if context.user_data['category'] == 'total' else wallet_balance
        
        transactions = tracker.get_all_transactions()
        burn_rate, days_left = ExpenseAnalytics.get_burn_rate(wallet_balance, transactions)
        
        msg = f"🏦 **{text}**\n💰 Current Balance: ₹{current_balance:,.2f}\n\n"
        
        if text == "👛 Wallet":
            msg += f"📊 Burn rate: ₹{burn_rate:.2f}/day\n"
            if days_left < 999:
                msg += f"⏳ Days left: {days_left}\n\n"
            
            if wallet_balance < 100:
                suggestion = tracker.ai_service.suggest_wallet_transfer(wallet_balance, total_balance, "")
                if suggestion:
                    msg += f"{suggestion}\n\n"
        
        msg += "⬇️ What would you like to do?"
        
        await update.message.reply_text(msg, reply_markup=reply_markup)
    
    elif text == "💡 Insights":
        await update.message.reply_text("🤖 Generating AI insights...")
        
        transactions = tracker.get_all_transactions()
        if not transactions:
            await update.message.reply_text("📊 No data yet. Start tracking expenses!")
            return
        
        recent_trans = transactions[-50:]
        trans_data = "\n".join([f"{t['date']}: ₹{t['amount']} - {t['description']} ({t['category']})" 
                                for t in recent_trans])
        
        insights = tracker.ai_service.get_spending_insights(trans_data, "month")
        
        daily_avg = ExpenseAnalytics.calculate_daily_average(transactions)
        category_breakdown = ExpenseAnalytics.get_category_breakdown(transactions)
        forecast, pace = ExpenseAnalytics.forecast_month_end(transactions)
        
        report = f"💡 **AI Insights**\n\n"
        report += f"📊 **Quick Stats:**\n"
        report += f"• Daily average: ₹{daily_avg:.2f}\n"
        report += f"• Month forecast: ₹{forecast:.2f} ({pace} pace)\n\n"
        
        if category_breakdown:
            report += "📂 **Category Breakdown:**\n"
            for cat, pct in sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]:
                report += f"• {cat}: {pct:.1f}%\n"
            report += f"\n"
        
        report += f"🤖 **AI Analysis:**\n{insights}"
        
        await update.message.reply_text(report)
    
    elif text == "⚡ Quick Add":
        keyboard = [
            [InlineKeyboardButton("₹50 Coffee", callback_data="quick_50_food"),
             InlineKeyboardButton("₹100 Snacks", callback_data="quick_100_food")],
            [InlineKeyboardButton("₹500 Groceries", callback_data="quick_500_groceries"),
             InlineKeyboardButton("₹500 Fuel", callback_data="quick_500_fuel")],
            [InlineKeyboardButton("₹200 Transport", callback_data="quick_200_transport"),
             InlineKeyboardButton("₹1000 Shopping", callback_data="quick_1000_shopping")],
            [InlineKeyboardButton("⭐ My Frequent", callback_data="frequent_trans")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚡ **Quick Add Transaction**\n\n"
            "Choose a preset or see your frequent transactions:",
            reply_markup=reply_markup
        )
    
    elif text == "📤 Export Data":
        keyboard = [
            [InlineKeyboardButton("📅 This Week", callback_data="export_week"),
             InlineKeyboardButton("🗓️ This Month", callback_data="export_month")],
            [InlineKeyboardButton("📆 All Time", callback_data="export_all")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📤 **Export Data to CSV**\n\n"
            "Choose a time period:",
            reply_markup=reply_markup
        )
    
    elif text == "🤝 Lending":
        keyboard = [
            [InlineKeyboardButton("💸 Lend Money", callback_data="lend_money"),
             InlineKeyboardButton("💰 Money Returned", callback_data="money_returned")],
            [InlineKeyboardButton("📊 Lending Analytics", callback_data="lending_analytics")],
            [InlineKeyboardButton("⏰ Pending Reminders", callback_data="lending_reminders")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤝 **Lending Management**\n\n⬇️ Choose an action:",
            reply_markup=reply_markup
        )
    
    elif text == "📊 Reports":
        keyboard = [
            [InlineKeyboardButton("📅 Today", callback_data="history_day"),
             InlineKeyboardButton("📆 Week", callback_data="history_week")],
            [InlineKeyboardButton("🗓️ Month", callback_data="history_month"),
             InlineKeyboardButton("📅 Year", callback_data="history_year")],
            [InlineKeyboardButton("📈 Trends", callback_data="show_trends")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📊 **Transaction Reports**\n\n⬇️ Select time period:",
            reply_markup=reply_markup
        )
    
    elif text == "📋 Summary":
        await update.message.reply_text("⏳ Generating summary...")
        
        transactions = tracker.get_all_transactions()
        lending = tracker.get_all_lending()
        
        if not transactions:
            await update.message.reply_text("No data yet.")
            return
        
        total_balance, wallet_balance = tracker.get_current_balances()
        
        total_income = sum(float(t['amount']) for t in transactions if t['type'] == 'add')
        total_expense = sum(float(t['amount']) for t in transactions if t['type'] == 'subtract')
        
        lending_stats = ExpenseAnalytics.analyze_lending(lending)
        
        summary = f"""
📊 **FINANCIAL SUMMARY**
━━━━━━━━━━━━━━━━━━━━━
💰 **Current Balances:**
   • Total Stack: ₹{total_balance:,.2f}
   • Wallet: ₹{wallet_balance:,.2f}
   • Combined: ₹{total_balance + wallet_balance:,.2f}

📈 **Transaction Summary:**
   • Total Income: ₹{total_income:,.2f}
   • Total Expenses: ₹{total_expense:,.2f}
   • Net: ₹{total_income - total_expense:,.2f}

🤝 **Lending Summary:**
   • Total Lent: ₹{lending_stats['total_lent']:,.2f}
   • Returned: ₹{lending_stats['total_returned']:,.2f}
   • Pending: ₹{lending_stats['pending']:,.2f}
━━━━━━━━━━━━━━━━━━━━━
        """
        await update.message.reply_text(summary)
    
    elif text == "⚙️ Settings":
        keyboard = [
            [InlineKeyboardButton("🏷️ Manage Aliases", callback_data="manage_aliases")],
            [InlineKeyboardButton("🎯 Set Goals", callback_data="set_goals")],
            [InlineKeyboardButton("🔔 Alert Settings", callback_data="alert_settings")],
            [InlineKeyboardButton("⭐ Frequent Transactions", callback_data="frequent_trans")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚙️ **Settings & Preferences**\n\n⬇️ Choose an option:",
            reply_markup=reply_markup
        )
    
    elif text == "🔄 Undo Last":
        success, message = tracker.undo_last_transaction()
        if success:
            await update.message.reply_text(f"✅ {message}")
        else:
            await update.message.reply_text(f"❌ {message}")
    
    elif text == "📝 Batch Entry":
        await update.message.reply_text(
            "📝 **Batch Entry Mode**\n\n"
            "Enter multiple transactions, one per line:\n\n"
            "**Format:** amount category description\n\n"
            "**Example:**\n"
            "500 groceries weekly shopping\n"
            "200 fuel petrol refill\n"
            "100 food lunch\n\n"
            "Send your transactions now:"
        )
        context.user_data['waiting_for'] = 'batch_transactions'
    
    elif text == "🎯 My Goals":
        prefs = get_user_prefs(user_id)
        goals = prefs.get_active_goals()
        
        if not goals:
            keyboard = [
                [InlineKeyboardButton("➕ Add Goal", callback_data="add_goal")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "🎯 **Your Goals**\n\n"
                "No goals set yet.\n\n"
                "💡 Set goals to track savings, spending limits, or financial targets!",
                reply_markup=reply_markup
            )
        else:
            msg = "🎯 **Your Active Goals:**\n\n"
            for i, goal in enumerate(goals[:5], 1):
                msg += f"{i}. **{goal['description']}**\n"
                msg += f"   Target: ₹{goal['target']:,.2f}\n"
                if goal.get('deadline'):
                    msg += f"   Deadline: {goal['deadline']}\n"
                msg += f"   Type: {goal['type']}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("➕ Add New Goal", callback_data="add_goal")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(msg, reply_markup=reply_markup)
    
    else:
        await handle_natural_language(update, context, text)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return
        
    await query.answer()
    data = query.data
    
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    
    if data.startswith('quick_'):
        parts = data.split('_')
        amount = float(parts[1])
        category = parts[2]
        
        total_bal, wallet_bal = tracker.add_transaction('subtract', 'wallet', amount, f"Quick: {category}", category=category)
        
        await query.edit_message_text(
            f"✅ Quick transaction added!\n"
            f"💰 ₹{amount} - {category}\n"
            f"💳 Wallet: ₹{wallet_bal:,.2f}"
        )
    
    elif data.startswith('export_'):
        period = data.split('_')[1]
        transactions = tracker.get_all_transactions()
        
        if period == 'week':
            days = 7
        elif period == 'month':
            days = 30
        else:
            days = 99999
        
        cutoff = datetime.now() - timedelta(days=days)
        filtered = [t for t in transactions if datetime.strptime(str(t['date']), '%d/%m/%Y') >= cutoff]
        
        csv_data = tracker.export_to_csv(filtered)
        
        await query.edit_message_text(
            f"📊 **Export Ready!**\n\n"
            f"Period: {period}\n"
            f"Transactions: {len(filtered)}\n\n"
            f"CSV Data:\n```\n{csv_data[:500]}...\n```\n\n"
            f"💡 Copy the data above and save as .csv file"
        )
    
    elif data == 'lending_reminders':
        lending = tracker.get_all_lending()
        pending = [l for l in lending if l['status'] == 'lent']
        
        if not pending:
            await query.edit_message_text("✅ No pending loans!")
            return
        
        reminders = "⏰ **Pending Loan Reminders:**\n\n"
        
        for loan in pending:
            loan_date = datetime.strptime(str(loan['date']), '%d/%m/%Y')
            days_ago = (datetime.now() - loan_date).days
            
            status_emoji = "⚠️" if days_ago > 14 else "📌"
            reminders += f"{status_emoji} **{loan['person']}**\n"
            reminders += f"   Amount: ₹{float(loan['amount']):,.2f}\n"
            reminders += f"   Days ago: {days_ago}\n"
            reminders += f"   Note: {loan['description']}\n\n"
        
        await query.edit_message_text(reminders)
    
    elif data.startswith('add_') or data.startswith('subtract_'):
        action, category = data.split('_')
        context.user_data['action'] = action
        context.user_data['category'] = category
        context.user_data['waiting_for'] = 'amount'
        
        action_text = "add to" if action == "add" else "subtract from"
        category_text = "Total Stack" if category == "total" else "Wallet"
        
        await query.edit_message_text(
            f"💰 **{action_text.title()} {category_text}**\n\n"
            f"💵 Please enter the amount to {action_text} {category_text.lower()}:\n\n"
            f"💡 Example: 500 or 1500.50"
        )
    
    elif data == 'lend_money':
        await query.edit_message_text(
            "💸 **Lend Money**\n\n"
            "👤 Please enter the person's name:\n\n"
            "💡 Example: John"
        )
        context.user_data['action'] = 'lend'
        context.user_data['waiting_for'] = 'person_name'
    
    elif data == 'money_returned':
        await query.edit_message_text(
            "💰 **Money Returned**\n\n"
            "👤 Please enter the name of the person who returned money:\n\n"
            "💡 Example: John"
        )
        context.user_data['action'] = 'return'
        context.user_data['waiting_for'] = 'return_person'
    
    elif data == 'lending_analytics':
        await query.edit_message_text("🤖 Analyzing lending patterns...")
        
        lending = tracker.get_all_lending()
        stats = ExpenseAnalytics.analyze_lending(lending)
        
        lending_text = "\n".join([f"{l['date']}: ₹{l['amount']} to {l['person']} ({l['status']})" for l in lending[-20:]])
        
        ai_analysis = tracker.ai_service.analyze_lending_patterns(lending_text)
        
        report = f"""
🤝 **Lending Analytics**

📊 **Statistics:**
• Total Lent: ₹{stats['total_lent']:,.2f}
• Total Returned: ₹{stats['total_returned']:,.2f}
• Pending: ₹{stats['pending']:,.2f}
• Avg Amount: ₹{stats['avg_amount']:,.2f}
• Avg Return Time: {stats['avg_return_days']:.0f} days

👥 **Pending from:**
"""
        for p in stats['pending_persons'][:5]:
            report += f"• {p['person']}: ₹{p['amount']:,.2f}\n"
        
        report += f"\n🤖 **AI Insights:**\n{ai_analysis}"
        
        await query.edit_message_text(report)
    
    elif data.startswith('history_'):
        period = data.split('_')[1]
        await query.edit_message_text("⏳ Loading history...")
        
        transactions = tracker.get_all_transactions()
        now = datetime.now()
        
        period_map = {'day': 1, 'week': 7, 'month': 30, 'year': 365}
        days = period_map.get(period, 30)
        
        cutoff = now - timedelta(days=days)
        filtered = [t for t in transactions if datetime.strptime(str(t['date']), '%d/%m/%Y') >= cutoff]
        
        if not filtered:
            await query.edit_message_text(f"No transactions in the last {period}.")
            return
        
        history = f"📊 **Transaction History ({period.upper()}):**\n\n"
        for t in filtered[-15:]:
            history += f"📅 {t['date']}\n"
            trans_type = str(t['type']).title() if isinstance(t['type'], str) else t['type']
            history += f"💰 {trans_type} ₹{t['amount']} - {t['description']}\n"
            if t.get('merchant'):
                history += f"🏪 {t['merchant']}\n"
            history += f"\n"
        
        await query.edit_message_text(history)
    
    elif data == 'show_trends':
        await query.edit_message_text("📈 Analyzing trends...")
        
        transactions = tracker.get_all_transactions()
        
        categories = set(t.get('category', 'other') for t in transactions if t['type'] == 'subtract')
        
        trends = "📈 **Spending Trends (4 weeks):**\n\n"
        for cat in list(categories)[:5]:
            cat_str = str(cat) if cat else 'other'
            trend = ExpenseAnalytics.detect_trend(transactions, cat_str, 4)
            trends += f"• {cat_str}: {trend}\n"
        
        await query.edit_message_text(trends)
    
    elif data == 'manage_aliases':
        user_id = query.from_user.id
        prefs = get_user_prefs(user_id)
        
        aliases = prefs.get_all_aliases()
        
        msg = "🏷️ **Your Aliases:**\n\n"
        if aliases:
            for shortcut, full in aliases.items():
                msg += f"• {shortcut} → {full}\n"
            msg += "\n"
        else:
            msg += "No aliases set yet.\n\n"
        
        msg += "💡 To add alias, type:\n'set alias gro for groceries'"
        
        await query.edit_message_text(msg)
    
    elif data == 'frequent_trans':
        await query.edit_message_text("⭐ Finding frequent transactions...")
        
        transactions = tracker.get_all_transactions()
        frequent = ExpenseAnalytics.get_frequent_transactions(transactions, 8)
        
        if not frequent:
            await query.edit_message_text("No frequent transactions found yet.")
            return
        
        keyboard = []
        for ft in frequent[:6]:
            btn_text = f"₹{ft['amount']} - {ft['description'][:20]}"
            callback = f"quick_{ft['amount']}_{ft['category']}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⭐ **Quick Add Frequent:**", reply_markup=reply_markup)
    
    elif data == 'add_goal':
        await query.edit_message_text(
            "🎯 **Add New Goal**\n\n"
            "Reply with goal details in this format:\n\n"
            "**Format:** type target description [deadline]\n\n"
            "**Types:** savings, spending_limit, investment\n\n"
            "**Example:**\n"
            "savings 50000 Save for vacation 2025-12-31\n"
            "spending_limit 5000 Monthly food budget"
        )
        context.user_data['waiting_for'] = 'goal_details'

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        await handle_menu(update, context)
        return
    
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    
    if not update.message or not update.message.from_user:
        return
    user_id = update.message.from_user.id
    prefs = get_user_prefs(user_id)
    text = update.message.text.strip()
    
    if text.lower().startswith('set alias'):
        match = re.match(r'set alias (\w+) for (.+)', text.lower())
        if match:
            shortcut, full = match.groups()
            prefs.add_alias(shortcut, full)
            await update.message.reply_text(f"✅ Alias set: '{shortcut}' → '{full}'")
            return
    
    if 'waiting_for' not in context.user_data:
        await handle_menu(update, context)
        return
    
    waiting_for = context.user_data['waiting_for']
    
    if waiting_for == 'amount':
        try:
            amount = float(text)
            if amount <= 0:
                await update.message.reply_text("❌ Please enter a positive amount.")
                return
                
            context.user_data['amount'] = amount
            action = context.user_data.get('action', 'add')
            category = context.user_data.get('category', 'total')
            
            action_text = "adding to" if action == "add" else "subtracting from"
            category_text = "Total Stack" if category == "total" else "Wallet"
            
            await update.message.reply_text(
                f"💰 **₹{amount:,.2f}** will be {action_text} {category_text}\n\n"
                f"📝 Please enter a description:\n\n"
                f"💡 Example: Salary, Groceries, etc."
            )
            context.user_data['waiting_for'] = 'description'
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number.")
    
    elif waiting_for == 'description':
        description = text
        action = context.user_data.get('action', 'add')
        category = context.user_data.get('category', 'total')
        amount = context.user_data.get('amount', 0)
        
        processing_msg = await update.message.reply_text("⏳ Processing...")
        
        wallet_type = context.user_data.get('category', 'total')
        total_balance, wallet_balance = tracker.add_transaction(action, wallet_type, amount, description, category='manual')
        
        action_text = "Added to" if action == "add" else "Subtracted from"
        category_text = "Total Stack" if wallet_type == "total" else "Wallet"
        
        await processing_msg.edit_text(
            f"✅ **Transaction Successful!**\n\n"
            f"💰 Amount: ₹{amount:,.2f} {action_text.lower()} {category_text.lower()}\n"
            f"📝 Description: {description}\n\n"
            f"💳 **Updated Balances:**\n"
            f"   • Total Stack: ₹{total_balance:,.2f}\n"
            f"   • Wallet: ₹{wallet_balance:,.2f}"
        )
        
        context.user_data.clear()
    
    elif waiting_for == 'person_name':
        context.user_data['person'] = text
        await update.message.reply_text(
            f"👤 **Lending to: {text}**\n\n"
            f"💵 Please enter the amount:\n\n"
            f"💡 Example: 5000"
        )
        context.user_data['waiting_for'] = 'lend_amount'
    
    elif waiting_for == 'lend_amount':
        try:
            amount = float(text)
            context.user_data['lend_amount'] = amount
            await update.message.reply_text(
                f"💸 **Lending ₹{amount:,.2f} to {context.user_data['person']}**\n\n"
                f"📝 Please enter a description:\n\n"
                f"💡 Example: Personal loan, Dinner split, etc."
            )
            context.user_data['waiting_for'] = 'lend_description'
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid amount.")
    
    elif waiting_for == 'lend_description':
        person = context.user_data['person']
        amount = context.user_data['lend_amount']
        
        tracker.add_lending(person, amount, text)
        
        await update.message.reply_text(
            f"✅ **Lending Recorded!**\n\n"
            f"👤 Person: {person}\n"
            f"💰 Amount: ₹{amount:,.2f}\n"
            f"📝 Description: {text}\n\n"
            f"💡 Use 'Money Returned' when they pay you back!"
        )
        context.user_data.clear()
    
    elif waiting_for == 'return_person':
        context.user_data['return_person'] = text
        await update.message.reply_text(
            f"👤 **Money from: {text}**\n\n"
            f"💵 Please enter the amount returned:\n\n"
            f"💡 Example: 5000"
        )
        context.user_data['waiting_for'] = 'return_amount'
    
    elif waiting_for == 'goal_details':
        try:
            parts = text.strip().split(None, 3)
            if len(parts) >= 3:
                goal_type = parts[0]
                target = float(parts[1])
                description = parts[2]
                deadline = parts[3] if len(parts) > 3 else None
                
                prefs.add_goal(goal_type, target, description, deadline)
                
                await update.message.reply_text(
                    f"✅ **Goal Added!**\n\n"
                    f"🎯 Type: {goal_type}\n"
                    f"💰 Target: ₹{target:,.2f}\n"
                    f"📝 {description}\n" +
                    (f"📅 Deadline: {deadline}\n" if deadline else "")
                )
            else:
                await update.message.reply_text(
                    "❌ Invalid format. Please use:\n"
                    "type target description [deadline]"
                )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        
        context.user_data.clear()
    
    elif waiting_for == 'batch_transactions':
        lines = text.strip().split('\n')
        success_count = 0
        failed_lines = []
        
        for line in lines:
            try:
                parts = line.strip().split(None, 2)
                if len(parts) >= 2:
                    amount = float(parts[0])
                    category = parts[1].lower()
                    description = parts[2] if len(parts) > 2 else f"{category} expense"
                    
                    tracker.add_transaction('subtract', 'wallet', amount, description, category=category)
                    success_count += 1
                else:
                    failed_lines.append(line)
            except:
                failed_lines.append(line)
        
        result_msg = f"✅ **Batch Entry Complete!**\n\n"
        result_msg += f"✓ Successfully added: {success_count} transactions\n"
        
        if failed_lines:
            result_msg += f"❌ Failed to parse: {len(failed_lines)} lines\n\n"
            result_msg += "Failed lines:\n"
            for fl in failed_lines[:5]:
                result_msg += f"• {fl}\n"
        
        await update.message.reply_text(result_msg)
        context.user_data.clear()
    
    elif waiting_for == 'return_amount':
        try:
            amount = float(text)
            context.user_data['return_amount'] = amount
            
            keyboard = [
                [InlineKeyboardButton("💰 Total Stack", callback_data="return_to_total"),
                 InlineKeyboardButton("👛 Wallet", callback_data="return_to_wallet")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"💰 **₹{amount:,.2f} returned by {context.user_data['return_person']}**\n\n"
                f"⬇️ Where would you like to add this money?",
                reply_markup=reply_markup
            )
            context.user_data['waiting_for'] = 'return_destination'
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid amount.")

async def handle_return_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    if not context.user_data:
        context.user_data = {}
    person = context.user_data.get('return_person')
    amount = context.user_data.get('return_amount')
    
    return_to = 'total' if query.data == 'return_to_total' else 'wallet'
    
    success = tracker.return_lending(person, amount, return_to)
    
    if success:
        await query.edit_message_text(
            f"✅ **Money Return Recorded!**\n\n"
            f"👤 From: {person}\n"
            f"💰 Amount: ₹{amount:,.2f}\n"
            f"💳 Added to: {'Total Stack' if return_to == 'total' else 'Wallet'}\n\n"
            f"📊 Updated balances accordingly!"
        )
    else:
        await query.edit_message_text(
            f"❌ Could not find matching lending record.\n"
            f"Please check the person's name and amount."
        )
    
    if context.user_data:
        context.user_data.clear()

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.voice:
        return
    
    await update.message.reply_text(
        "🎤 Voice message received!\n\n"
        "💡 For now, please type your expense. Full voice transcription coming soon!"
    )

def main():
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set. Exiting application.")
        import sys
        sys.exit(1)
    application = Application.builder().token(BOT_TOKEN).build()    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    application.add_handler(CallbackQueryHandler(handle_return_destination, pattern='^return_to_'))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("PayLog AI Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
