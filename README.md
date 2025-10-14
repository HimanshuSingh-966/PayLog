# 💰PayLog - A Telegram Expense Tracker Bot

A comprehensive Telegram bot for tracking personal(physical) expenses using Google Sheets as the backend storage. Track your cash flow between different sources, manage lending, and get detailed financial reports.

## ✨ Features

### 💰 Money Management
- **Total Stack & Wallet**: Track money in two separate locations
- **Add/Subtract**: Easy money transactions with descriptions
- **Real-time Balances**: Always know your current financial status

### 🤝 Lending System
- **Lend Money**: Record money lent to friends/family
- **Track Returns**: Mark when money is returned and where to add it
- **Persistent Records**: All lending data stored in Google Sheets

### 📊 Reports & Analytics
- **Time-based Reports**: View transactions for today, week, month, or year
- **Financial Summary**: Complete overview of income, expenses, and lending
- **Export Data**: Get formatted text export of all your data

### 🌐 Google Sheets Integration
- **Persistent Storage**: All data stored in Google Sheets
- **Real-time Sync**: Instant updates across all devices
- **Backup**: Your data is safe in the cloud
- **Accessible**: View/edit data directly in Google Sheets

## 🚀 Quick Start

### Prerequisites
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Google Service Account with Sheets API access
- Google Spreadsheet ID

### 🤖 Create Telegram Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Use `/newbot` command
3. Choose a name and username for your bot
4. Copy the bot token

### 📊 Setup Google Sheets
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Sheets API
4. Create a Service Account:
   - Go to IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Give it a name and description
   - Click "Create and Continue"
   - Skip role assignment (click "Continue")
   - Click "Done"
5. Generate JSON key:
   - Click on your service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose JSON format
   - Download the JSON file
6. Create a Google Spreadsheet:
   - Go to [Google Sheets](https://sheets.google.com/)
   - Create a new spreadsheet
   - Copy the spreadsheet ID from URL (between `/d/` and `/edit`)
   - Share the spreadsheet with your service account email (found in JSON)

## 🔧 Installation

### Local Development
```bash
# Clone the repository
git clone https://github.com/HimanshuSingh-966/PayLog.git
cd PayLog

# Install dependencies
pip install -r requirements.txt

# Run the bot
python main.py
```

### Environment Variables
Create a `.env` file with the following variables:

```env
BOT_TOKEN=your_telegram_bot_token_here
GOOGLE_SHEETS_CREDS={"type":"service_account","project_id":"your-project",...}
SPREADSHEET_ID=your_google_spreadsheet_id_here
```

**Important**: The `GOOGLE_SHEETS_CREDS` should be the entire JSON content from your service account key file, formatted as a single line.

## 🌐 Deployment on Render

### Method 1: Using Render Dashboard
1. Fork this repository to your GitHub account
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Configure the service:
   - **Name**: `expense-tracker-bot`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
6. Add Environment Variables:
   - `BOT_TOKEN`: Your Telegram bot token
   - `GOOGLE_SHEETS_CREDS`: Your service account JSON (as single line)
   - `SPREADSHEET_ID`: Your Google Spreadsheet ID
7. Click "Create Web Service"

### Method 2: Using render.yaml (Infrastructure as Code)
The `render.yaml` file in this repository will automatically configure your deployment.

1. Fork this repository
2. Connect to Render
3. Render will automatically detect and deploy using the YAML configuration
4. Add your environment variables in the Render dashboard

## 📱 Bot Usage

### Main Menu
- **💰 Total Stack**: Manage your main money storage
- **👛 Wallet**: Track your pocket money  
- **🤝 Lending**: Record money lent to others
- **📊 Reports**: View transaction history
- **📋 Summary**: Get financial overview
- **📁 Export Data**: Export all your data

### Transaction Flow
1. Choose **Total Stack** or **Wallet**
2. Click **Add Money** or **Subtract Money**
3. Enter amount when prompted
4. Enter description for the transaction
5. Transaction is saved to Google Sheets

### Lending Flow
1. Choose **🤝 Lending**
2. Click **💸 Lend Money**
3. Enter person's name
4. Enter amount
5. Enter description
6. When money is returned:
   - Click **💰 Money Returned**
   - Enter person's name and amount
   - Choose where to add the returned money

## 📊 Google Sheets Structure

The bot creates two worksheets in your spreadsheet:

### Transactions Sheet
- **date**: Transaction date
- **type**: add/subtract
- **category**: total/wallet
- **amount**: Transaction amount
- **description**: User-provided description
- **balance_total**: Total stack balance after transaction
- **balance_wallet**: Wallet balance after transaction

### Lending Sheet
- **date**: Lending date
- **person**: Person's name
- **amount**: Amount lent
- **status**: lent/returned
- **description**: Lending description
- **return_date**: Date when returned
- **return_to**: Where the money was added (total/wallet)

## 🔒 Security & Privacy

- All sensitive data is stored in environment variables
- Google Service Account provides secure API access
- No data is stored locally on the server
- Telegram bot token is kept secure
- Google Sheets data is private to your account

## 🚨 Troubleshooting

### Common Issues

**Bot not responding:**
- Check if `BOT_TOKEN` is correctly set
- Ensure the bot is running on your server

**Google Sheets not updating:**
- Verify `GOOGLE_SHEETS_CREDS` is valid JSON
- Check if spreadsheet is shared with service account email
- Ensure `SPREADSHEET_ID` is correct

**Deployment fails:**
- Check all environment variables are set
- Verify requirements.txt is present
- Check build logs for specific errors

### Getting Help
If you encounter issues:
1. Check the logs in your deployment platform
2. Verify all environment variables are correctly set
3. Ensure your Google Sheets permissions are correct
4. Test the bot locally first

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for the Telegram Bot API wrapper
- [gspread](https://github.com/burnash/gspread) for Google Sheets integration
- [Render](https://render.com/) for easy deployment platform

---

**Made with ❤️ for better expense tracking**
