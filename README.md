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
    └── __init__.py            # Main function code (570+ lines)
```

### File Descriptions

| File | Purpose | When Used |
|------|---------|-----------|
| **`__init__.py`** | Main function logic - email processing, filtering, HTML generation | Every function execution |
| **`function.json`** | Defines HTTP trigger, security level, and response binding | Function startup |
| **`host.json`** | Global Azure Functions settings (timeout, extensions) | Function app startup |
| **`requirements.txt`** | Python package dependencies | Deployment & local setup |
| **`local.settings.json`** | Local development configuration (not deployed) | Local development only |
| **`test_function.py`** | Sample data testing script | Local testing & debugging |

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
```txt
azure-functions>=1.11.2
azure-functions-worker>=1.0.0
requests>=2.28.0
```

### System Requirements
- **Python**: 3.8, 3.9, or 3.10
- **Azure Functions Core Tools**: v4.x
- **Node.js**: 16+ (for Azure Functions Core Tools)
- **ngrok** (optional, for Power Automate testing)

### Power Automate Integration
- Accepts JSON payload with `inbox` and `sent` email arrays
- Handles both standard Outlook API and Power Automate data formats
- Robust parsing for different email field structures

### Error Handling
- Comprehensive logging for debugging
- Graceful handling of missing or malformed data
- Fallback values for all critical fields

## 🔧 Troubleshooting

### Common Issues

#### Function Won't Start
```bash
# Check if Azure Functions Core Tools is installed
func --version

# If not installed, install it:
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

#### Python Dependencies Issues
```bash
# Make sure you're in the right directory
cd email_summary_function

# Check if requirements.txt exists
ls requirements.txt

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### Power Automate Can't Connect
```bash
# Make sure function is running
func start

# Create tunnel for external access
ngrok http 7071

# Use the HTTPS URL from ngrok in Power Automate
# Example: https://abc123.ngrok.io/api/process_emails
```

#### Testing Script Fails
```bash
# Make sure function is running first
func start

# In another terminal:
python test_function.py

# If still fails, check the function logs in the first terminal
```

### Logs and Debugging
```bash
# Start function with verbose logging
func start --verbose

# Check function logs in Azure portal (for deployed functions)
# Application Insights > Logs > traces
```

## � Quick Start

### 1. Clone the Repository
```bash
# Clone the repository
git clone <repository-url>
cd email-summary-function

# Navigate to the function directory
cd email_summary_function
```

### 2. Install Prerequisites
```bash
# Install Azure Functions Core Tools (choose your OS)

# Windows (using npm):
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Windows (using Chocolatey):
choco install azure-functions-core-tools

# Mac (using Homebrew):
brew tap azure/functions
brew install azure-functions-core-tools@4

# Linux (using npm):
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

### 3. Install Python Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 4. Local Testing
```bash
# Start Azure Functions locally
func start

# In another terminal, test the function
python test_function.py
```

### 6. Verify Installation
```bash
# Check Azure Functions version
func --version
# Should show: 4.x.x

# Check Python version
python --version
# Should show: Python 3.8+ 

# Test function startup
func start
# Should show: Functions: process_emails: [POST] http://localhost:7071/api/process_emails

# Test function with sample data
python test_function.py
# Should show: ✅ Function executed successfully!
```

## 🔒 Environment Setup

### Local Settings Configuration
Create or verify `local.settings.json`:
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "",
    "FUNCTIONS_WORKER_RUNTIME": "python"
  }
}
```

### Python Virtual Environment (Recommended)
```bash
# Create isolated environment
python -m venv email-function-env

# Activate (Windows)
email-function-env\Scripts\activate

# Activate (Mac/Linux)  
source email-function-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

## 📋 Usage

### Local Development Workflow
```bash
# 1. Start the function
func start

# 2. Test with sample data
python test_function.py

# 3. Make code changes (function auto-reloads)
# 4. Test again immediately
```

### Azure Deployment
```bash
# Deploy to Azure (requires Azure CLI login)
az login
func azure functionapp publish <your-function-app-name>

# Your function will be available at:
# https://<your-function-app-name>.azurewebsites.net/api/process_emails
```

### Power Automate Configuration
1. Create a scheduled Power Automate flow
2. Add "Get emails (V3)" actions for inbox and sent items
3. Add HTTP POST action with URL pointing to your function
4. Configure request body:
```json
{
  "inbox": @{body('Get_emails_(V3)')?['value']},
  "sent": @{body('Get_emails_(V3)_2')?['value']}
}
```

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
