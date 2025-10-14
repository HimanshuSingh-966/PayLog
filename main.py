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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
GOOGLE_SHEETS_CREDS = os.getenv('GOOGLE_SHEETS_CREDS')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
PORT = int(os.getenv('PORT', 8000))

# Check required environment variables
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")
if not GOOGLE_SHEETS_CREDS:
    logger.warning("GOOGLE_SHEETS_CREDS not found - Google Sheets functionality will be disabled")
if not SPREADSHEET_ID:
    logger.warning("SPREADSHEET_ID not found - Google Sheets functionality will be disabled")

# Simple HTTP handler for health checks
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Expense Tracker Bot is running!')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass

def start_web_server():
    """Start a simple HTTP server for health checks"""
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    logger.info(f"Starting HTTP server on port {PORT}")
    server.serve_forever()

class ExpenseTracker:
    def __init__(self):
        self.gc = None
        self.spreadsheet = None
        self.transactions_sheet = None
        self.lending_sheet = None
        self.init_google_sheets()
        
    def init_google_sheets(self):
        """Initialize Google Sheets connection"""
        try:
            if not GOOGLE_SHEETS_CREDS or not SPREADSHEET_ID:
                logger.warning("Google Sheets credentials or Spreadsheet ID missing")
                return
                
            # Parse credentials from environment variable
            creds_dict = json.loads(GOOGLE_SHEETS_CREDS)
            credentials = Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://spreadsheets.google.com/feeds',
                       'https://www.googleapis.com/auth/drive']
            )
            self.gc = gspread.authorize(credentials)
            self.spreadsheet = self.gc.open_by_key(SPREADSHEET_ID)
            
            # Get or create sheets
            try:
                self.transactions_sheet = self.spreadsheet.worksheet('transactions')
            except gspread.WorksheetNotFound:
                self.transactions_sheet = self.spreadsheet.add_worksheet(
                    title='transactions', rows=1000, cols=7
                )
                # Add headers
                self.transactions_sheet.append_row([
                    'date', 'type', 'category', 'amount', 'description', 'balance_total', 'balance_wallet'
                ])
            
            try:
                self.lending_sheet = self.spreadsheet.worksheet('lending')
            except gspread.WorksheetNotFound:
                self.lending_sheet = self.spreadsheet.add_worksheet(
                    title='lending', rows=1000, cols=7
                )
                # Add headers
                self.lending_sheet.append_row([
                    'date', 'person', 'amount', 'status', 'description', 'return_date', 'return_to'
                ])
                
            logger.info("Google Sheets initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing Google Sheets: {e}")
            logger.warning("Bot will continue without Google Sheets functionality")

    def get_current_balances(self):
        """Get current balances from the last transaction"""
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

    def add_transaction(self, transaction_type, category, amount, description):
        """Add a transaction to Google Sheets"""
        try:
            total_balance, wallet_balance = self.get_current_balances()
            
            # Update balances based on transaction type
            if category == 'total':
                if transaction_type == 'add':
                    total_balance += amount
                else:
                    total_balance -= amount
            elif category == 'wallet':
                if transaction_type == 'add':
                    wallet_balance += amount
                else:
                    wallet_balance -= amount
            
            # Add transaction to sheet
            now = datetime.now()
            row_data = [
                now.strftime('%d/%m/%Y'),
                transaction_type,
                category,
                amount,
                description,
                total_balance,
                wallet_balance
            ]
            
            if self.transactions_sheet:
                self.transactions_sheet.append_row(row_data)
            
            return total_balance, wallet_balance
            
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return 0, 0

    def add_lending(self, person, amount, description):
        """Add lending record to Google Sheets"""
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
        """Mark lending as returned and update balances"""
        try:
            if not self.lending_sheet:
                return False
                
            records = self.lending_sheet.get_all_records()
            
            # Find matching lending record
            for i, record in enumerate(records):
                if (record['person'] == person and 
                    float(record['amount']) == amount and 
                    record['status'] == 'lent'):
                    
                    # Update the record
                    row_num = i + 2  # +2 because sheets are 1-indexed and we have headers
                    self.lending_sheet.update_cell(row_num, 4, 'returned')  # status column
                    self.lending_sheet.update_cell(row_num, 6, datetime.now().strftime('%d/%m/%Y'))  # return_date
                    self.lending_sheet.update_cell(row_num, 7, return_to)  # return_to
                    
                    # Add to balances
                    self.add_transaction('add', return_to, amount, f'Returned by {person}')
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error returning lending: {e}")
            return False

    def get_history(self, period):
        """Get transaction history for specified period"""
        try:
            if not self.transactions_sheet:
                return "Google Sheets not connected. Please check configuration."
                
            records = self.transactions_sheet.get_all_records()
            if not records:
                return "No transactions found."
            
            now = datetime.now()
            filtered_records = []
            
            for record in records:
                try:
                    # Convert the date field to string to ensure compatibility
                    date_str = str(record['date'])
                    record_date = datetime.strptime(date_str, '%d/%m/%Y')
                    
                    if period == 'day':
                        if record_date.date() == now.date():
                            filtered_records.append(record)
                    elif period == 'week':
                        if record_date >= now - timedelta(days=7):
                            filtered_records.append(record)
                    elif period == 'month':
                        if record_date >= now - timedelta(days=30):
                            filtered_records.append(record)
                    elif period == 'year':
                        if record_date >= now - timedelta(days=365):
                            filtered_records.append(record)
                    else:
                        filtered_records.append(record)
                except:
                    continue
            
            if not filtered_records:
                return f"No transactions found for the last {period}."
            
            history = f"📊 Transaction History ({period.upper()}):\n\n"
            for record in filtered_records[-10:]:  # Show last 10 transactions
                history += f"📅 {record['date']}\n"
                history += f"💰 {record['type'].title()} ₹{record['amount']} from {record['category']}\n"
                history += f"📝 {record['description']}\n"
                history += f"💳 Total: ₹{record['balance_total']}, Wallet: ₹{record['balance_wallet']}\n\n"
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return "Error retrieving history. Please try again."

    def get_summary(self):
        """Get overall financial summary"""
        try:
            if not self.transactions_sheet or not self.lending_sheet:
                return "Google Sheets not connected. Please check configuration."
            
            # Get transaction records
            transaction_records = self.transactions_sheet.get_all_records()
            lending_records = self.lending_sheet.get_all_records()
            
            if not transaction_records:
                return "No transactions recorded yet."
            
            total_balance, wallet_balance = self.get_current_balances()
            
            # Calculate totals
            total_income = sum(float(record['amount']) for record in transaction_records if record['type'] == 'add')
            total_expense = sum(float(record['amount']) for record in transaction_records if record['type'] == 'subtract')
            
            # Lending summary
            total_lent = sum(float(record['amount']) for record in lending_records if record['status'] == 'lent')
            total_returned = sum(float(record['amount']) for record in lending_records if record['status'] == 'returned')
            pending_returns = total_lent - total_returned
            
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
   • Total Lent: ₹{total_lent:,.2f}
   • Total Returned: ₹{total_returned:,.2f}
   • Pending Returns: ₹{pending_returns:,.2f}
━━━━━━━━━━━━━━━━━━━━━
            """
            return summary
            
        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return "Error retrieving summary. Please try again."

    def export_data_as_text(self):
        """Export data as formatted text since we can't send files"""
        try:
            if not self.transactions_sheet or not self.lending_sheet:
                return "Google Sheets not connected."
            
            transactions = self.transactions_sheet.get_all_records()
            lending = self.lending_sheet.get_all_records()
            
            export_text = "📊 **EXPORTED DATA**\n\n"
            export_text += "💰 **TRANSACTIONS:**\n"
            export_text += "Date | Type | Category | Amount | Description | Total Balance | Wallet Balance\n"
            export_text += "─" * 80 + "\n"
            
            for t in transactions[-20:]:  # Last 20 transactions
                export_text += f"{t['date']} | {t['type']} | {t['category']} | ₹{t['amount']} | {t['description']} | ₹{t['balance_total']} | ₹{t['balance_wallet']}\n"
            
            export_text += "\n🤝 **LENDING:**\n"
            export_text += "Date | Person | Amount | Status | Description | Return Date | Return To\n"
            export_text += "─" * 70 + "\n"
            
            for l in lending:
                export_text += f"{l['date']} | {l['person']} | ₹{l['amount']} | {l['status']} | {l['description']} | {l['return_date']} | {l['return_to']}\n"
            
            return export_text
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return "Error exporting data. Please try again."

# Global tracker instance
tracker = ExpenseTracker()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    if not update.message:
        return
    
    # Clear any existing user data
    context.user_data.clear()
        
    keyboard = [
        [KeyboardButton("💰 Total Stack"), KeyboardButton("👛 Wallet")],
        [KeyboardButton("🤝 Lending"), KeyboardButton("📊 Reports")],
        [KeyboardButton("📋 Summary"), KeyboardButton("📁 Export Data")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_msg = """
🎯 **Welcome to Your Personal Expense Tracker!**

📱 **Main Features:**
• 💰 **Total Stack** - Manage your main money storage
• 👛 **Wallet** - Track your pocket money
• 🤝 **Lending** - Track money lent to others
• 📊 **Reports** - View transaction history
• 📋 **Summary** - Get financial overview

🌐 **Data Storage:** Google Sheets (Persistent & Secure)

🚀 **Quick Start:**
Choose an option from the menu below to begin tracking your expenses!
    """
    
    await update.message.reply_text(welcome_msg, reply_markup=reply_markup)

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu selections"""
    if not update.message or not update.message.text:
        return
        
    text = update.message.text
    
    # Initialize user_data if it doesn't exist
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
        
        await update.message.reply_text(
            f"🏦 **{text}**\n💰 Current Balance: ₹{current_balance:,.2f}\n\n⬇️ What would you like to do?",
            reply_markup=reply_markup
        )
    
    elif text == "🤝 Lending":
        keyboard = [
            [InlineKeyboardButton("💸 Lend Money", callback_data="lend_money"),
             InlineKeyboardButton("💰 Money Returned", callback_data="money_returned")]
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
             InlineKeyboardButton("📅 Year", callback_data="history_year")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📊 **Transaction Reports**\n\n⬇️ Select time period:",
            reply_markup=reply_markup
        )
    
    elif text == "📋 Summary":
        await update.message.reply_text("⏳ Generating summary...")
        summary = tracker.get_summary()
        await update.message.reply_text(summary)
    
    elif text == "📁 Export Data":
        await update.message.reply_text("⏳ Exporting data...")
        export_data = tracker.export_data_as_text()
        await update.message.reply_text(export_data)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses"""
    query = update.callback_query
    if not query or not query.data:
        return
        
    await query.answer()
    
    data = query.data
    
    # Initialize user_data if it doesn't exist
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    
    if data.startswith('add_') or data.startswith('subtract_'):
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
            "👤 Please enter the person's name to whom you're lending money:\n\n"
            "💡 Example: John or Sarah"
        )
        context.user_data['action'] = 'lend'
        context.user_data['waiting_for'] = 'person_name'
    
    elif data == 'money_returned':
        await query.edit_message_text(
            "💰 **Money Returned**\n\n"
            "👤 Please enter the name of the person who returned money:\n\n"
            "💡 Example: John or Sarah"
        )
        context.user_data['action'] = 'return'
        context.user_data['waiting_for'] = 'return_person'
    
    elif data.startswith('history_'):
        period = data.split('_')[1]
        await query.edit_message_text("⏳ Loading transaction history...")
        history = tracker.get_history(period)
        await query.edit_message_text(history)

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text inputs for transactions"""
    if not update.message or not update.message.text:
        await handle_menu(update, context)
        return
    
    # Initialize user_data if it doesn't exist
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    
    if 'waiting_for' not in context.user_data:
        await handle_menu(update, context)
        return
    
    waiting_for = context.user_data['waiting_for']
    text = update.message.text.strip()
    
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
                f"📝 Please enter a description for this transaction:\n\n"
                f"💡 Example: Salary, Food, Shopping, etc."
            )
            context.user_data['waiting_for'] = 'description'
        except ValueError:
            await update.message.reply_text(
                "❌ Please enter a valid number for the amount.\n\n"
                "💡 Example: 500 or 1500.50"
            )
    
    elif waiting_for == 'description':
        description = text
        action = context.user_data.get('action', 'add')
        category = context.user_data.get('category', 'total')
        amount = context.user_data.get('amount', 0)
        
        # Show processing message
        processing_msg = await update.message.reply_text("⏳ Processing transaction...")
        
        total_balance, wallet_balance = tracker.add_transaction(action, category, amount, description)
        
        action_text = "Added to" if action == "add" else "Subtracted from"
        category_text = "Total Stack" if category == "total" else "Wallet"
        
        await processing_msg.edit_text(
            f"✅ **Transaction Successful!**\n\n"
            f"💰 Amount: ₹{amount:,.2f} {action_text.lower()} {category_text.lower()}\n"
            f"📝 Description: {description}\n\n"
            f"💳 **Updated Balances:**\n"
            f"   • Total Stack: ₹{total_balance:,.2f}\n"
            f"   • Wallet: ₹{wallet_balance:,.2f}\n"
            f"   • Combined: ₹{total_balance + wallet_balance:,.2f}"
        )
        
        # Clear context
        context.user_data.clear()
    
    elif waiting_for == 'person_name':
        context.user_data['person'] = text
        await update.message.reply_text(
            f"👤 **Lending to: {text}**\n\n"
            f"💰 Please enter the amount you're lending:\n\n"
            f"💡 Example: 500 or 1500.50"
        )
        context.user_data['waiting_for'] = 'lend_amount'
    
    elif waiting_for == 'lend_amount':
        try:
            amount = float(text)
            if amount <= 0:
                await update.message.reply_text("❌ Please enter a positive amount.")
                return
                
            context.user_data['amount'] = amount
            person = context.user_data.get('person', 'Unknown')
            
            await update.message.reply_text(
                f"👤 **Person:** {person}\n"
                f"💰 **Amount:** ₹{amount:,.2f}\n\n"
                f"📝 Please enter a description for this lending:\n\n"
                f"💡 Example: Emergency, Business, Personal, etc."
            )
            context.user_data['waiting_for'] = 'lend_description'
        except ValueError:
            await update.message.reply_text(
                "❌ Please enter a valid number for the amount.\n\n"
                "💡 Example: 500 or 1500.50"
            )
    
    elif waiting_for == 'lend_description':
        person = context.user_data.get('person', 'Unknown')
        amount = context.user_data.get('amount', 0)
        description = text
        
        # Show processing message
        processing_msg = await update.message.reply_text("⏳ Recording lending...")
        
        tracker.add_lending(person, amount, description)
        
        await processing_msg.edit_text(
            f"✅ **Lending Recorded Successfully!**\n\n"
            f"👤 **Person:** {person}\n"
            f"💰 **Amount:** ₹{amount:,.2f}\n"
            f"📝 **Description:** {description}\n\n"
            f"💡 Use 'Money Returned' option when {person} returns the money."
        )
        
        context.user_data.clear()
    
    elif waiting_for == 'return_person':
        context.user_data['return_person'] = text
        await update.message.reply_text(
            f"👤 **Money returned by: {text}**\n\n"
            f"💰 Please enter the amount returned:\n\n"
            f"💡 Example: 500 or 1500.50"
        )
        context.user_data['waiting_for'] = 'return_amount'
    
    elif waiting_for == 'return_amount':
        try:
            amount = float(text)
            if amount <= 0:
                await update.message.reply_text("❌ Please enter a positive amount.")
                return
                
            context.user_data['return_amount'] = amount
            person = context.user_data.get('return_person', 'Unknown')
            
            keyboard = [
                [InlineKeyboardButton("💰 Total Stack", callback_data="return_to_total"),
                 InlineKeyboardButton("👛 Wallet", callback_data="return_to_wallet")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"👤 **Person:** {person}\n"
                f"💰 **Amount:** ₹{amount:,.2f}\n\n"
                f"🏦 **Where should the returned money be added?**\n\n"
                f"⬇️ Choose destination:",
                reply_markup=reply_markup
            )
            context.user_data['waiting_for'] = 'return_destination'
        except ValueError:
            await update.message.reply_text(
                "❌ Please enter a valid number for the amount.\n\n"
                "💡 Example: 500 or 1500.50"
            )

async def handle_return_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle return destination selection"""
    query = update.callback_query
    if not query or not query.data:
        return
        
    await query.answer()
    
    # Initialize user_data if it doesn't exist
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    
    destination = 'total' if query.data == 'return_to_total' else 'wallet'
    person = context.user_data.get('return_person', 'Unknown')
    amount = context.user_data.get('return_amount', 0)
    
    # Show processing message
    await query.edit_message_text("⏳ Processing return...")
    
    success = tracker.return_lending(person, amount, destination)
    
    if success:
        total_balance, wallet_balance = tracker.get_current_balances()
        destination_text = "Total Stack" if destination == "total" else "Wallet"
        
        await query.edit_message_text(
            f"✅ **Money Return Recorded Successfully!**\n\n"
            f"👤 **Returned by:** {person}\n"
            f"💰 **Amount:** ₹{amount:,.2f}\n"
            f"🏦 **Added to:** {destination_text}\n\n"
            f"💳 **Updated Balances:**\n"
            f"   • Total Stack: ₹{total_balance:,.2f}\n"
            f"   • Wallet: ₹{wallet_balance:,.2f}\n"
            f"   • Combined: ₹{total_balance + wallet_balance:,.2f}"
        )
    else:
        await query.edit_message_text(
            f"❌ **No Matching Lending Record Found**\n\n"
            f"👤 **Person:** {person}\n"
            f"💰 **Amount:** ₹{amount:,.2f}\n\n"
            f"💡 Please check if the person name and amount match exactly with your lending records."
        )
    
    context.user_data.clear()

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Try to send error message to user if possible
    if update and hasattr(update, 'effective_message') and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ **An error occurred!**\n\n"
                "Please try again or use /start to restart the bot."
            )
        except:
            pass  # If we can't send message, just log the error

def main():
    """Main function to run the bot"""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found in environment variables!")
        return
    
    # Start HTTP server in a separate thread
    server_thread = threading.Thread(target=start_web_server, daemon=True)
    server_thread.start()
        
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers in the correct order
    application.add_handler(CommandHandler("start", start))
    
    # Handle callback queries first (inline buttons)
    application.add_handler(CallbackQueryHandler(handle_return_destination, pattern=r'^return_to_'))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Handle text messages (but not commands)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print(f"🚀 Expense Tracker Bot is running with Google Sheets storage on port {PORT}...")
    print("📱 Bot is ready to receive messages!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
