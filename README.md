# WhatsApp Fantasy Football Bot 🏈⚽

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

A WhatsApp bot for managing Fantasy Football (Soccer) player picks with automated deadline tracking, Google Sheets integration, and group management features.

## ✨ Features

- 📱 **WhatsApp Integration**: Players submit picks via WhatsApp messages
- 📊 **Google Sheets Storage**: Automatic storage and tracking of all picks
- ⏰ **Deadline Management**: Automatic deadline enforcement and reminders  
- 🎯 **Gameweek Tracking**: Supports full Premier League season schedule
- 👥 **User Management**: Support for multiple players with custom names
- 📈 **Admin Controls**: Summary reports and player status management
- 🔄 **Automated Scheduling**: Background tasks for deadline summaries

## 🚀 Quick Deploy

### Option 1: Deploy to Railway (Recommended)
1. Click the "Deploy on Railway" button above
2. Connect your GitHub account
3. Set up the required environment variables (guided setup)
4. Your bot will be live in minutes!

### Option 2: Manual Setup

#### Prerequisites
- [Twilio Account](https://console.twilio.com) with WhatsApp Business API access
- [Google Cloud Project](https://console.cloud.google.com) with Sheets API enabled
- Google Sheets document for storing picks

#### Installation

1. **Clone & Install**
```bash
git clone <your-repo-url>
cd whatsapp-4ts-bot
pip install -r requirements.txt
```

2. **Environment Setup**
```bash
cp .env.example .env
# Edit .env with your credentials (see Configuration section)
```

3. **Run Locally**
```bash
python app.py
```

## ⚙️ Configuration

### Required Environment Variables

| Variable | Description | How to Get |
|----------|-------------|------------|
| `TWILIO_ACCOUNT_SID` | Your Twilio Account SID | [Twilio Console](https://console.twilio.com) |
| `TWILIO_AUTH_TOKEN` | Your Twilio Auth Token | [Twilio Console](https://console.twilio.com) |
| `ADMIN_PHONE` | Admin phone number (with country code) | Your WhatsApp number (e.g. +1234567890) |
| `GOOGLE_PROJECT_ID` | Google Cloud Project ID | [Google Cloud Console](https://console.cloud.google.com) |
| `GOOGLE_PRIVATE_KEY_ID` | Service Account Key ID | Service Account JSON file |
| `GOOGLE_PRIVATE_KEY` | Service Account Private Key | Service Account JSON file |
| `GOOGLE_CLIENT_EMAIL` | Service Account Email | Service Account JSON file |
| `GOOGLE_CLIENT_ID` | Service Account Client ID | Service Account JSON file |
| `GOOGLE_SHEET_ID` | Google Sheets Document ID | Copy from Sheets URL |

### Setting Up Twilio WhatsApp
1. Create a [Twilio account](https://console.twilio.com)
2. Enable WhatsApp Business API
3. Get your Account SID and Auth Token
4. Configure webhook URL: `https://your-domain.railway.app/webhook`

### Setting Up Google Sheets
1. Create a [Google Cloud Project](https://console.cloud.google.com)
2. Enable Google Sheets API
3. Create a Service Account and download JSON key
4. Create a Google Sheets document
5. Share the sheet with your service account email
6. Copy the Sheet ID from the URL

### Configuring Players
Edit `config/settings.py` to add your players:
```python
USER_MAP = {
    "+1234567890": "Player Name",
    "+0987654321": "Another Player",
}
```

## 📱 How to Use

### For Players
Send your 4 player picks via WhatsApp:
```
Haaland
Salah  
Saka
Palmer
```

### Available Commands
- **Show fixtures**: `fixtures` or `show fixtures`
- **Admin summary**: `summary` or `show picks` (admin only)
- **Active players**: `show active` (admin only)

### For Admins
- Get pick summaries before deadlines
- Manage gameweeks and deadlines
- View player participation status

## 🗓️ Gameweek Management

The bot automatically tracks Premier League gameweeks and deadlines. Deadlines are configured in `config/settings.py` and can be customized for your league schedule.

## 🛠️ Development

### Project Structure
```
├── app.py                 # Main Flask application
├── config/
│   ├── settings.py       # Configuration and gameweek schedule
│   └── validation.py     # Environment validation
├── services/             # Business logic
├── models/              # Data models
├── utils/               # Helper functions
└── requirements.txt     # Python dependencies
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your credentials

# Run with auto-reload
python app.py
```

## 📊 API Endpoints

- `POST /webhook` - WhatsApp webhook for incoming messages
- `GET /health` - Health check and current gameweek status  
- `GET /summary` - Trigger manual summary (admin only)
- `GET /gameweek-info` - Current gameweek information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - feel free to use this project for your own fantasy leagues!

## 🆘 Troubleshooting

### Common Issues

**Environment validation failed**
- Check all required environment variables are set
- Ensure admin phone number starts with country code (+)

**Google Sheets connection failed**
- Verify service account has access to the sheet
- Check that Google Sheets API is enabled
- Ensure private key format is correct (with \n newlines)

**Twilio webhook not receiving messages**  
- Verify webhook URL is correctly configured
- Check Twilio WhatsApp sandbox setup
- Ensure your Railway domain is accessible

**Bot not responding to messages**
- Check Twilio credentials are correct
- Verify phone numbers are in correct format
- Check Railway logs for errors

### Getting Help
- Check the [Issues](../../issues) page for common problems
- Review Railway deployment logs
- Test individual components using the API endpoints

---

Built with ❤️ for fantasy football enthusiasts everywhere!
