# Email Summary Azure Function

A production-ready Azure Function that processes emails sent from Power Automate, filters for important/urgent messages, and generates a professional HTML summary report with direct email navigation links.

## 📁 Project Structure

```
email_summary_function/
├── host.json                    # Azure Functions host configuration
├── local.settings.json         # Local development settings
├── requirements.txt             # Python dependencies
├── test_function.py            # Local testing script
└── process_emails/             # Main function directory
    ├── function.json           # Function binding configuration
    └── __init__.py            # Main function code
```

## ✨ Features

- **Smart Email Filtering**: Automatically identifies important emails using keyword-based filtering
- **Professional HTML Reports**: Modern, responsive design with gradient styling
- **Direct Email Navigation**: Clickable "Open Email" buttons that link directly to emails in Outlook
- **Sahithi Email Prioritization**: Special handling for urgent emails requiring replies
- **Robust Error Handling**: Comprehensive logging and exception handling
- **Power Automate Integration**: Seamless integration with Microsoft Power Automate workflows

## 🚀 Key Functionality

### Email Filtering Criteria
- Emails mentioning "Akshay" or "@sahithin"
- Important keywords: urgent, action required, deadline, ASAP, priority, critical
- Special tracking for emails from Sahithi requiring replies (>1 day old)
- Follow-up tracking for old sent emails (>2 days old)

### HTML Report Sections
1. **Summary Overview**: Count of important emails, urgent replies needed, and follow-ups required
2. **Urgent Emails**: Sahithi's emails needing reply with red "Open Email" buttons
3. **Important Inbox**: All important emails with blue "Open Email" buttons
4. **Old Sent Emails**: Emails that may need follow-up

### Navigation Features
- **Direct Email Links**: Uses Outlook Web App links when available
- **Smart Link Construction**: Falls back to constructed links using email ID or message ID
- **New Tab Opening**: All email links open in new tabs for seamless workflow

## 🛠️ Technical Details

### Dependencies
```
azure-functions==1.11.2
azure-functions-worker==1.0.0
```

### Power Automate Integration
- Accepts JSON payload with `inbox` and `sent` email arrays
- Handles both standard Outlook API and Power Automate data formats
- Robust parsing for different email field structures

### Error Handling
- Comprehensive logging for debugging
- Graceful handling of missing or malformed data
- Fallback values for all critical fields

## 📋 Usage

### Local Testing
```powershell
cd email_summary_function
python test_function.py
```

### Azure Deployment
1. Deploy to Azure Functions
2. Configure Power Automate to send POST requests to the function endpoint
3. Function returns HTML response that can be used in email notifications

## 🎯 Production Ready

This function is fully tested and production-ready with:
- ✅ Complete email processing logic
- ✅ Professional HTML formatting
- ✅ Direct email navigation
- ✅ Robust error handling
- ✅ Power Automate compatibility
- ✅ Responsive design
- ✅ Clean, maintainable code

## 📧 Sample Output

The function generates a beautiful HTML email summary with:
- Modern gradient design
- Responsive tables
- Professional styling
- Clickable navigation buttons
- Color-coded urgency levels

Perfect for daily email management and ensuring no important messages are missed!
