# PayLog AI - Intelligent Expense Tracker

## Overview
PayLog AI is an advanced Telegram-based expense tracking bot powered by Gemini Flash 2.0 AI. It provides natural language transaction parsing, predictive analytics, smart insights, and personalized financial recommendations.

## Recent Changes
- **October 14, 2025**: Complete AI-powered upgrade implemented
  - Integrated Gemini Flash 2.0 via OpenRouter API
  - Added natural language parsing for transactions
  - Implemented 8 tiers of smart features
  - Created analytics and user preferences modules
  - Enhanced Telegram bot with AI capabilities

## User Preferences
- All data stored in Google Sheets for persistence and accessibility
- User preferences saved locally (aliases, goals, spending limits)
- Privacy-first approach with local calculations
- Telegram-only interface for simplicity

## Project Architecture

### Core Modules

#### 1. main.py
Main bot application with Telegram handlers and AI integration.

Key Features:
- Natural language transaction parsing
- Voice message support (placeholder for future)
- Smart menu navigation
- Context-aware conversations
- Quick transaction shortcuts

#### 2. ai_service.py
Gemini Flash 2.0 AI integration via OpenRouter.

Capabilities:
- Natural language parsing
- Spending insights generation
- Category suggestions
- Anomaly detection
- Financial forecasting
- Lending pattern analysis

#### 3. analytics.py
Statistical analysis and calculations.

Functions:
- Daily average spending
- Category breakdown
- Trend detection
- Month-end forecasting
- Burn rate calculation
- Frequent transaction detection
- Lending analytics

#### 4. user_prefs.py
User preferences and settings management.

Features:
- Custom aliases (shortcuts)
- Spending limits per category
- Personal goals tracking
- Context memory
- Alert settings
- Transaction history patterns

### Tech Stack
- **Backend**: Python 3.11
- **Bot Framework**: python-telegram-bot
- **AI Service**: OpenRouter (Gemini Flash 2.0)
- **Database**: Google Sheets (via gspread)
- **Analytics**: pandas, python-dateutil
- **Config**: python-dotenv

## Feature Tiers Implemented

### Tier 1: Smart Transaction Logging ✅
- Natural language parsing ("spent 500 on groceries at DMart")
- Time recognition ("yesterday I paid 1000")
- Voice message support (placeholder)
- Frequent transaction shortcuts
- Custom alias system
- Smart autocomplete

### Tier 2: Personal Analytics & Insights ✅
- Daily spending averages
- Category breakdown with percentages
- Expense trend analysis
- Spending forecasts
- Budget comparisons
- Smart alerts (spike warnings)
- Weekly/monthly summaries

### Tier 3: Contextual Awareness ✅
- AI learns spending patterns
- Merchant/location recognition
- Recurring expense detection
- Context memory for follow-ups
- Transaction history search
- Smart category suggestions

### Tier 4: Multi-Wallet Intelligence ✅
- Transfer suggestions
- Low balance alerts
- Usage pattern tracking
- Burn rate calculations
- Days-left predictions
- Wallet-specific analytics

### Tier 5: Lending 2.0 ✅
- Lending tracking with status
- Return management
- Lending analytics
- Pattern analysis (avg amount, return time)
- AI-powered insights
- Pending person tracking

### Tier 6: Export & Reports ✅
- Time-based reports (day/week/month/year)
- Transaction history
- Lending reports
- Financial summaries
- Text export format

### Tier 7: Convenience Features ✅
- Undo last transaction
- Quick add from frequent transactions
- Context-aware follow-ups
- Smart settings management
- Alias management

### Tier 8: Data Intelligence ✅
- Anomaly detection
- Spending spike alerts
- Historical forecasting
- Category trend analysis
- Financial health scoring
- Predictive insights

## Setup Instructions

### Required Environment Variables
Create a `.env` file with:
```
BOT_TOKEN=your_telegram_bot_token
GOOGLE_SHEETS_CREDS={"type":"service_account"...}
SPREADSHEET_ID=your_spreadsheet_id
OPENROUTER_API_KEY=your_openrouter_api_key
PORT=8000
```

### Getting API Keys

1. **Telegram Bot Token**:
   - Message @BotFather on Telegram
   - Use `/newbot` command
   - Copy the token

2. **Google Sheets**:
   - Create service account in Google Cloud Console
   - Enable Google Sheets API
   - Download JSON credentials
   - Share spreadsheet with service account email

3. **OpenRouter API Key**:
   - Sign up at openrouter.ai
   - Get API key from dashboard
   - Supports Gemini Flash 2.0

### Running the Bot
```bash
python main.py
```

## Usage Examples

### Natural Language Commands
```
"Spent 500 on groceries at DMart"
"Yesterday I paid 1000 for dinner"
"Add 5000 salary received"
"Show me food expenses from last week"
"Lent 2000 to John for trip"
```

### Setting Aliases
```
"set alias gro for groceries"
"set alias fuel for petrol"
```

### Quick Actions
- Use menu buttons for guided flow
- Type naturally for AI parsing
- Access frequent transactions for one-tap
- Use undo for mistakes

## AI Features

### Natural Language Understanding
The bot uses Gemini Flash 2.0 to:
- Extract amounts, categories, and merchants
- Recognize time references
- Suggest categories based on patterns
- Understand context and follow-ups

### Smart Insights
AI provides:
- Spending pattern analysis
- Trend detection
- Personalized recommendations
- Anomaly warnings
- Financial health assessment

### Predictive Analytics
- Month-end spending forecasts
- Burn rate calculations
- Days-left predictions
- Category trend projections

## Data Storage

### Google Sheets Structure

**Transactions Sheet**:
- date, type, category, amount, description
- balance_total, balance_wallet, merchant

**Lending Sheet**:
- date, person, amount, status
- description, return_date, return_to

### Local Storage
User preferences stored in `user_prefs_{user_id}.json`:
- Aliases
- Spending limits
- Goals
- Context memory
- Transaction patterns

## Development Notes

### Architecture Decisions
- Python-only implementation for simplicity
- Telegram-first interface (no web UI)
- Google Sheets for cross-device accessibility
- Local AI processing where possible
- Privacy-focused design

### Future Enhancements
- Full voice transcription support
- PDF report generation with charts
- Group expense splitting
- Encrypted auto-backup
- Tax-ready exports
- Receipt photo processing (vision AI)

## Project Status
✅ All 8 tiers of features implemented
✅ AI integration complete
✅ Analytics module ready
✅ User preferences system active
✅ Telegram bot fully functional

## Maintenance
- User preferences auto-save to JSON files
- Google Sheets for transaction persistence
- Logs available for debugging
- Environment variables for security
