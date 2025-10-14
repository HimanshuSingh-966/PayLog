# PayLog AI - Quick Setup Guide

## 🚀 Get Started in 5 Minutes!

### Step 1: Create Your .env File

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Then edit `.env` with your actual values:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
GOOGLE_SHEETS_CREDS={"type":"service_account","project_id":"paylog-123"...}
SPREADSHEET_ID=1a2b3c4d5e6f7g8h9i0j
OPENROUTER_API_KEY=sk-or-v1-1234567890abcdef
PORT=8000
```

### Step 2: Get Your API Keys

#### 🤖 Telegram Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the prompts to name your bot
4. Copy the token (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### 📊 Google Sheets Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "PayLog")
3. Enable Google Sheets API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
4. Create Service Account:
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Name it "paylog-bot"
   - Click "Create and Continue"
   - Skip permissions (click "Continue")
   - Click "Done"
5. Generate JSON Key:
   - Click on your service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Select "JSON"
   - Download the file
6. Copy the entire JSON content (as a single line) to `GOOGLE_SHEETS_CREDS` in your `.env`

#### 📄 Create Google Spreadsheet
1. Go to [Google Sheets](https://sheets.google.com/)
2. Create a new blank spreadsheet
3. Name it "PayLog Data" or similar
4. Copy the Spreadsheet ID from URL:
   - URL looks like: `https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit`
   - Copy just the ID part
5. Share the spreadsheet:
   - Click "Share" button
   - Add the service account email (from your JSON file, looks like: `paylog-bot@paylog-123.iam.gserviceaccount.com`)
   - Give "Editor" permission

#### 🤖 OpenRouter API Key
1. Go to [OpenRouter](https://openrouter.ai/)
2. Sign up or log in
3. Go to "API Keys" section
4. Create a new API key
5. Copy the key (starts with `sk-or-v1-`)
6. Add some credits to your account (for AI features)

### Step 3: Install & Run

The dependencies are already installed. Just run:

```bash
python main.py
```

You should see:
```
Starting HTTP server on port 8000
Google Sheets initialized successfully
PayLog AI Bot started!
```

### Step 4: Test Your Bot

1. Open Telegram
2. Search for your bot (the username you created with BotFather)
3. Send `/start`
4. Try these commands:
   - "Spent 500 on groceries"
   - "Yesterday paid 1000 for dinner"
   - "Show insights"

## 🎯 Quick Test Commands

Once your bot is running, try these in Telegram:

### Basic Transactions
```
Spent 500 on groceries at DMart
Yesterday I paid 1000 for dinner
Add 50000 salary received
```

### AI Features
```
Show me food expenses from last week
💡 Insights (click the button)
```

### Custom Aliases
```
set alias gro for groceries
sub 500 gro
```

### Lending
```
Click "🤝 Lending" → "💸 Lend Money"
Follow the prompts
```

## 🔍 Troubleshooting

### Bot Not Starting

**Issue**: `BOT_TOKEN environment variable is required`
- ✅ Make sure `.env` file exists in project root
- ✅ Verify `BOT_TOKEN` is set correctly
- ✅ No quotes around the token value

**Issue**: `GOOGLE_SHEETS_CREDS not found`
- ✅ Copy entire JSON as single line (no line breaks)
- ✅ Make sure it starts with `{"type":"service_account"`

### Google Sheets Not Working

**Issue**: Permission denied or 403 errors
- ✅ Share spreadsheet with service account email
- ✅ Give "Editor" permission
- ✅ Verify `SPREADSHEET_ID` is correct

**Issue**: API not enabled
- ✅ Enable Google Sheets API in Cloud Console
- ✅ Wait 1-2 minutes for activation

### AI Features Not Working

**Issue**: No AI responses or parsing
- ✅ Verify `OPENROUTER_API_KEY` is set
- ✅ Check you have credits in OpenRouter account
- ✅ Test with simple command: "spent 100 on food"

## 📚 What's Included

### Core Modules
- `main.py` - Main bot with Telegram integration
- `ai_service.py` - Gemini Flash 2.0 AI integration
- `analytics.py` - Spending analytics & insights
- `user_prefs.py` - User preferences & settings

### Documentation
- `README.md` - Full project documentation
- `SETUP.md` - This setup guide
- `replit.md` - Technical architecture details

### Configuration
- `.env.example` - Template for environment variables
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore rules

## ✨ Features Overview

### Tier 1: Smart Logging
✅ Natural language: "spent 500 on groceries"
✅ Time recognition: "yesterday paid 1000"
✅ Custom aliases: "gro" → "groceries"

### Tier 2: Analytics
✅ Daily averages & trends
✅ Category breakdown
✅ Spending forecasts
✅ Smart alerts

### Tier 3: Context Awareness
✅ AI learns patterns
✅ Smart suggestions
✅ Context memory

### Tier 4: Wallet Intelligence
✅ Burn rate analysis
✅ Transfer suggestions
✅ Balance alerts

### Tier 5: Lending 2.0
✅ Track lending
✅ Auto reminders
✅ Pattern analysis

### Tier 6: Reports
✅ Time-based reports
✅ Transaction history
✅ Export features

### Tier 7: Convenience
✅ Undo transactions
✅ Quick shortcuts
✅ Frequent items

### Tier 8: Intelligence
✅ Anomaly detection
✅ Predictions
✅ Financial health

## 🎉 You're All Set!

Your intelligent expense tracker is ready. Start by sending `/start` to your bot on Telegram!

For detailed documentation, see [README.md](README.md)

---

**Need Help?** Check the main README or review the logs if something isn't working.
