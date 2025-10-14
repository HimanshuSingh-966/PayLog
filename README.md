# 💰 PayLog AI - Intelligent Expense Tracker

> Your personal AI-powered financial assistant on Telegram

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![AI](https://img.shields.io/badge/AI-Gemini%20Flash%202.0-orange.svg)](https://openrouter.ai/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🌟 Overview

PayLog AI is an advanced Telegram bot that transforms expense tracking with artificial intelligence. Simply type naturally - "spent 500 on groceries at DMart" - and the AI understands, categorizes, and tracks everything automatically.

## ✨ Key Features

### 🤖 AI-Powered Intelligence
- **Natural Language Processing** - Type expenses as you speak
- **Smart Category Recognition** - AI learns your spending patterns  
- **Predictive Analytics** - Forecast month-end spending
- **Anomaly Detection** - Get alerts for unusual expenses
- **Context Memory** - Bot remembers your recent transactions

### 💰 Smart Money Management
- **Dual Wallets** - Separate Total Stack & Wallet tracking
- **Auto Balancing** - Get transfer suggestions when wallet is low
- **Burn Rate Analysis** - Know how many days your money will last
- **Spending Insights** - AI-generated financial advice

### 🎯 Personal Analytics
- Daily/weekly/monthly spending averages
- Category breakdown with percentages
- Trend analysis (increasing/decreasing/stable)
- Budget alerts and spending caps
- Financial health scoring

### 🤝 Smart Lending
- Track money lent to friends
- Auto reminders for pending returns
- Lending pattern analysis
- Settlement suggestions

### ⚙️ Convenience
- Custom aliases ("gro" → "groceries")
- Frequent transaction shortcuts
- Undo last transaction
- Context-aware follow-ups
- Multi-period reports

## 🚀 Quick Start

### Prerequisites

1. **Telegram Bot Token**
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Use `/newbot` command and follow instructions
   - Copy your bot token

2. **Google Sheets Setup**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project and enable Google Sheets API
   - Create a Service Account and download JSON credentials
   - Create a Google Spreadsheet
   - Share spreadsheet with service account email

3. **OpenRouter API Key**
   - Sign up at [OpenRouter](https://openrouter.ai/)
   - Get your API key from dashboard
   - This powers the Gemini Flash 2.0 AI features

### Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   GOOGLE_SHEETS_CREDS={"type":"service_account","project_id":"..."}
   SPREADSHEET_ID=your_google_spreadsheet_id
   OPENROUTER_API_KEY=your_openrouter_api_key
   PORT=8000
   ```

   **Note**: 
   - `GOOGLE_SHEETS_CREDS` should be the entire JSON content from your service account file (as a single line)
   - `SPREADSHEET_ID` is the long string in your spreadsheet URL between `/d/` and `/edit`

3. **Run the bot**
   ```bash
   python main.py
   ```

## 💬 Usage Examples

### Natural Language Transactions
```
You: "Spent 500 on groceries at DMart"
Bot: ✅ Expense Recorded!
     💰 Amount: ₹500
     📂 Category: groceries
     🏪 Merchant: DMart
     ...

You: "Yesterday I paid 1000 for dinner"
Bot: ✅ Expense Recorded!
     📅 Date: 13 Oct 2025
     💰 Amount: ₹1,000
     ...

You: "Add 50000 salary received"
Bot: ✅ Income Added!
     💰 Amount: ₹50,000
     ...
```

### Smart Queries
```
You: "Show me food expenses from last week"
Bot: 📊 Expenses (Last 7 days):
     📅 10/10/2025 | ₹500 - Lunch at cafe
     📅 12/10/2025 | ₹800 - Dinner with friends
     ...
```

### Custom Aliases
```
You: "set alias gro for groceries"
Bot: ✅ Alias set: 'gro' → 'groceries'

You: "sub 500 gro"
Bot: ✅ Expense Recorded!
     📂 Category: groceries
     ...
```

## 📊 AI Features

### Smart Insights
Get AI-powered analysis of your spending:
- Daily averages and trends
- Category-wise breakdown
- Personalized recommendations
- Spending forecasts

### Anomaly Detection
```
⚠️ High spending alert! 
You spent ₹10,000 on shopping - that's 5x your daily average
```

### Predictive Analytics
```
📈 At current rate, you'll spend ₹25,000 this month
📊 Your groceries spending increased 20% this month
⏳ At current rate, your wallet cash lasts 8 more days
```

## 🏗️ Architecture

### Core Modules

- **main.py** - Telegram bot with AI integration
- **ai_service.py** - Gemini Flash 2.0 API integration
- **analytics.py** - Statistical analysis & calculations
- **user_prefs.py** - User preferences & settings

### Tech Stack

- Python 3.11
- python-telegram-bot (Telegram API)
- OpenRouter (AI/LLM)
- Google Sheets (Data storage)
- pandas (Analytics)

## 📈 Feature Tiers

### ✅ Tier 1: Smart Transaction Logging
- Natural language parsing
- Time recognition
- Voice support (placeholder)
- Custom aliases
- Frequent transactions

### ✅ Tier 2: Personal Analytics & Insights
- Daily averages
- Category breakdown
- Trend analysis
- Spending forecasts
- Smart alerts

### ✅ Tier 3: Contextual Awareness
- Pattern learning
- Merchant recognition
- Context memory
- Smart suggestions

### ✅ Tier 4: Multi-Wallet Intelligence
- Transfer suggestions
- Burn rate analysis
- Usage patterns
- Balance alerts

### ✅ Tier 5: Lending 2.0
- Lending tracking
- Auto reminders
- Analytics
- Pattern analysis

### ✅ Tier 6: Export & Reports
- Time-based reports
- Transaction history
- Multiple formats

### ✅ Tier 7: Convenience Features
- Undo transactions
- Quick shortcuts
- Smart settings

### ✅ Tier 8: Data Intelligence
- Anomaly detection
- Forecasting
- Financial health
- Predictive insights

## 🔒 Privacy & Security

- All sensitive data stored in environment variables
- Google Sheets secured via Service Account
- Local user preferences (no cloud storage of personal settings)
- Privacy-first AI processing
- Secure API key management

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram bot token from @BotFather | ✅ Yes |
| `GOOGLE_SHEETS_CREDS` | Service account JSON credentials | ✅ Yes |
| `SPREADSHEET_ID` | Google Spreadsheet ID | ✅ Yes |
| `OPENROUTER_API_KEY` | OpenRouter API key | ✅ Yes |
| `PORT` | HTTP server port (default: 8000) | ❌ No |

## 🛠️ Troubleshooting

### Bot not starting
- Check if `BOT_TOKEN` is set in `.env`
- Ensure `.env` file is in the project root
- Verify all required dependencies are installed

### Google Sheets not updating
- Verify `GOOGLE_SHEETS_CREDS` is valid JSON
- Check if spreadsheet is shared with service account email
- Ensure `SPREADSHEET_ID` is correct

### AI features not working
- Verify `OPENROUTER_API_KEY` is set
- Check OpenRouter API credits/quota
- Review logs for API errors

## 📚 Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize bot and show menu |
| Natural text | Type expenses naturally |
| Menu buttons | Use visual interface |

## 🎯 Roadmap

### Phase 1 (Current) ✅
- All 8 tiers of features
- AI integration
- Analytics & insights
- Smart lending

### Phase 2 (Upcoming)
- Full voice transcription
- PDF reports with charts
- Group expense splitting
- Receipt photo processing
- Encrypted auto-backup
- Tax-ready exports

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Gemini Flash 2.0](https://ai.google.dev/) - Powerful AI model
- [OpenRouter](https://openrouter.ai/) - AI API access
- [python-telegram-bot](https://python-telegram-bot.org/) - Telegram bot framework
- Google Sheets - Reliable data storage

---

**Made with ❤️ for smart personal finance tracking**
