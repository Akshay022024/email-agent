import logging
import json
import azure.functions as func
from datetime import datetime, timedelta
import re

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    try:
        # Parse JSON from Power Automate
        req_body = req.get_json()
        logging.info(f"Request body type: {type(req_body)}")
        logging.info(f"Request body content: {str(req_body)[:500]}...")  # Log first 500 chars
        
        if not req_body:
            return func.HttpResponse(
                "Please pass inbox and sent email data in the request body",
                status_code=400
            )
          # Handle different data formats from Power Automate
        if isinstance(req_body, str):
            try:
                req_body = json.loads(req_body)
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON string: {e}")
                return func.HttpResponse(f"Invalid JSON format: {e}", status_code=400)
        
        inbox_emails = req_body.get('inbox', [])
        sent_emails = req_body.get('sent', [])
        
        # Additional logging for debugging
        logging.info(f"Inbox emails type: {type(inbox_emails)}, count: {len(inbox_emails) if isinstance(inbox_emails, list) else 'N/A'}")
        logging.info(f"Sent emails type: {type(sent_emails)}, count: {len(sent_emails) if isinstance(sent_emails, list) else 'N/A'}")
        
        # Log first few emails for debugging
        if isinstance(inbox_emails, list) and len(inbox_emails) > 0:
            logging.info(f"First inbox email sample: {str(inbox_emails[0])[:200]}...")
        if isinstance(sent_emails, list) and len(sent_emails) > 0:            logging.info(f"First sent email sample: {str(sent_emails[0])[:200]}...")
        
        # Ensure we have lists
        if not isinstance(inbox_emails, list):
            logging.warning(f"inbox_emails is not a list, it's {type(inbox_emails)}")
            inbox_emails = []
        if not isinstance(sent_emails, list):
            logging.warning(f"sent_emails is not a list, it's {type(sent_emails)}")
            sent_emails = []
            
        # Filter inbox emails mentioning "Akshay" or "@sahithin" or from "sahithi"
        important_inbox = []
        sahithi_emails_needing_reply = []
        
        logging.info("Starting to process inbox emails...")
          # Log the structure of the first email to understand what fields are available
        if len(inbox_emails) > 0:
            logging.info(f"Available email fields: {list(inbox_emails[0].keys())}")
            # Check for navigation-related fields
            nav_fields = ['id', 'internetMessageId', 'webLink', 'conversationId', 'messageId']
            available_nav_fields = {field: inbox_emails[0].get(field) for field in nav_fields if field in inbox_emails[0]}
            logging.info(f"Navigation fields available: {available_nav_fields}")
            logging.info(f"Full first email structure: {str(inbox_emails[0])}")
        
        for i, email in enumerate(inbox_emails):
            try:
                # Safely get email fields with defaults
                subject = str(email.get('subject', '')).lower()
                body = str(email.get('bodyPreview', '')).lower()
                  # Handle different email structures - check for 'from' or 'sender' fields
                from_field = email.get('from', email.get('sender', ''))
                sender = ''
                sender_email = ''
                
                if isinstance(from_field, dict):
                    # Standard Outlook API format with nested structure
                    email_address_field = from_field.get('emailAddress', from_field)
                    if isinstance(email_address_field, dict):
                        sender = str(email_address_field.get('name', '')).lower()
                        sender_email = str(email_address_field.get('address', '')).lower()
                    else:
                        sender = str(from_field.get('name', '')).lower()
                        sender_email = str(from_field.get('address', '')).lower()
                elif isinstance(from_field, str) and from_field:                    # Power Automate format - from field is just the email address string
                    sender_email = from_field.lower()
                    # Extract name from email if possible (before @ symbol)
                    if '@' in sender_email:
                        sender = sender_email.split('@')[0].replace('.', ' ').replace('_', ' ')
                    else:
                        sender = sender_email
                
                received_date_str = email.get('receivedDateTime', '')
                
                # Check if email is from Sahithi and might need a reply
                is_from_sahithi = ('sahithi' in sender or 'sahithi' in sender_email)
                
                # Check if it's an important email (mentions Akshay, @sahithin, or important keywords)
                important_keywords = ['akshay', '@sahithin', 'action required', 'important', 'urgent', 
                                    'deadline', 'asap', 'priority', 'critical', 'time sensitive']
                
                is_important = any(keyword in subject or keyword in body for keyword in important_keywords)
                
                # Get additional fields for navigation
                email_id = email.get('id', '')
                internet_message_id = email.get('internetMessageId', '')
                web_link = email.get('webLink', '')
                conversation_id = email.get('conversationId', '')
                  # Create navigation link (prefer webLink if available, otherwise construct OWA link)
                nav_link = ''
                if web_link:
                    nav_link = web_link
                elif email_id:
                    # Construct Outlook Web App link using email ID
                    nav_link = f"https://outlook.office.com/mail/inbox/id/{email_id}"
                elif internet_message_id:
                    # Alternative: use search by message ID
                    nav_link = f"https://outlook.office.com/mail/search/id/{internet_message_id}"
                
                if is_important or is_from_sahithi:
                    # Get sender info for display
                    if isinstance(from_field, str) and from_field:
                        sender_display = sender.title() if sender else 'Unknown Sender'
                        sender_email_display = from_field  # Use original email string
                    else:
                        sender_display = sender.title() if sender else 'Unknown Sender'
                        sender_email_display = sender_email if sender_email else 'unknown@email.com'
                    
                    email_data = {
                        'subject': email.get('subject', 'No Subject'),
                        'sender': sender_display,
                        'sender_email': sender_email_display,
                        'received': received_date_str,
                        'preview': email.get('bodyPreview', '')[:150] + '...' if len(email.get('bodyPreview', '')) > 150 else email.get('bodyPreview', ''),
                        'is_from_sahithi': is_from_sahithi,
                        'nav_link': nav_link
                    }
                    
                    if is_from_sahithi:
                        # Check if it's older than 1 day (might need reply)
                        try:
                            received_date = datetime.fromisoformat(received_date_str.replace('Z', '+00:00'))
                            one_day_ago = datetime.now() - timedelta(days=1)
                            if received_date.replace(tzinfo=None) < one_day_ago:
                                sahithi_emails_needing_reply.append(email_data)
                        except Exception as date_error:
                            logging.warning(f"Error parsing date {received_date_str}: {date_error}")
                    
                    important_inbox.append(email_data)
                    
            except Exception as email_error:
                logging.warning(f"Error processing inbox email {i+1}: {email_error}")
                continue
        
        logging.info(f"Finished processing. Found {len(important_inbox)} important emails.")
          # Identify sent emails older than 2 days with no replies
        two_days_ago = datetime.now() - timedelta(days=2)
        old_sent_emails = []
        
        for email in sent_emails:
            try:
                sent_date_str = email.get('sentDateTime', '')
                if sent_date_str:
                    try:
                        sent_date = datetime.fromisoformat(sent_date_str.replace('Z', '+00:00'))
                        if sent_date.replace(tzinfo=None) < two_days_ago:
                            # Check if this email might need follow-up
                            subject = email.get('subject', '')
                            recipients = email.get('toRecipients', [])
                            
                            # Safely extract recipient names
                            recipient_names = []
                            if isinstance(recipients, list):
                                for r in recipients:
                                    if isinstance(r, dict):
                                        email_addr = r.get('emailAddress', {})
                                        if isinstance(email_addr, dict):
                                            name = email_addr.get('name', '')
                                            if name:
                                                recipient_names.append(name)
                            
                            old_sent_emails.append({
                                'subject': subject,
                                'recipients': ', '.join(recipient_names) if recipient_names else 'Unknown',
                                'sent': sent_date_str,
                                'preview': email.get('bodyPreview', '')[:100] + '...' if len(email.get('bodyPreview', '')) > 100 else email.get('bodyPreview', '')
                            })
                    except Exception as date_error:
                        logging.warning(f"Error parsing sent date {sent_date_str}: {date_error}")
                        continue
            except Exception as email_error:
                logging.warning(f"Error processing sent email: {email_error}")
                continue
          # Format HTML table with all sections
        html_report = f"""        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Daily Email Summary Report</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: #ffffff;
                    border-radius: 15px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                
                .header {{
                    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                
                .header h1 {{
                    font-size: 2.5em;
                    margin-bottom: 10px;
                    font-weight: 300;
                }}
                
                .header .subtitle {{
                    font-size: 1.1em;
                    opacity: 0.8;
                }}
                
                .content {{
                    padding: 30px;
                }}
                
                .summary {{
                    background: linear-gradient(135deg, #e8f4f8 0%, #d6eaf8 100%);
                    padding: 25px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    border-left: 5px solid #3498db;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
                }}
                
                .summary-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-top: 15px;
                }}
                
                .summary-item {{
                    text-align: center;
                    padding: 15px;
                    background: rgba(255,255,255,0.7);
                    border-radius: 8px;
                }}
                
                .summary-number {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #2c3e50;
                    display: block;
                }}
                
                .summary-label {{
                    font-size: 0.9em;
                    color: #7f8c8d;
                    margin-top: 5px;
                }}
                
                h2 {{
                    color: #2c3e50;
                    font-size: 1.8em;
                    margin: 30px 0 20px 0;
                    padding-bottom: 10px;
                    border-bottom: 3px solid #3498db;
                    position: relative;
                }}
                
                h2::before {{
                    content: '';
                    position: absolute;
                    bottom: -3px;
                    left: 0;
                    width: 60px;
                    height: 3px;
                    background: #e74c3c;
                }}
                
                .section {{
                    margin-bottom: 40px;
                }}
                
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                }}
                
                th {{
                    background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
                    color: white;
                    font-weight: 600;
                    padding: 18px 15px;
                    text-align: left;
                    font-size: 0.95em;
                    letter-spacing: 0.5px;
                }}
                
                td {{
                    padding: 15px;
                    border-bottom: 1px solid #ecf0f1;
                    vertical-align: top;
                }}
                  tr:hover {{
                    transform: translateY(-1px);
                    transition: all 0.2s ease;
                }}
                
                .urgent {{
                    background: linear-gradient(135deg, #ffebee 0%, #fce4ec 100%);
                    border-left: 5px solid #e74c3c;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                }}
                
                .sahithi-row {{
                    background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
                    border-left: 4px solid #ff9800;
                }}
                
                .email-link {{
                    display: inline-block;
                    background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                    color: white;
                    padding: 8px 15px;
                    text-decoration: none;
                    border-radius: 25px;
                    font-size: 0.85em;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    box-shadow: 0 3px 10px rgba(52, 152, 219, 0.3);
                }}
                
                .email-link:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
                    text-decoration: none;
                    color: white;
                }}
                
                .urgent-link {{
                    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                    box-shadow: 0 3px 10px rgba(231, 76, 60, 0.3);
                }}
                
                .urgent-link:hover {{
                    box-shadow: 0 5px 15px rgba(231, 76, 60, 0.4);
                }}
                
                .subject-cell {{
                    font-weight: 600;
                    color: #2c3e50;
                    max-width: 300px;
                }}
                
                .sender-cell {{
                    font-weight: 500;
                    color: #34495e;
                }}
                
                .email-cell {{
                    font-size: 0.9em;
                    color: #7f8c8d;
                }}
                
                .date-cell {{
                    font-size: 0.9em;
                    color: #95a5a6;
                    white-space: nowrap;
                }}
                
                .preview-cell {{
                    font-size: 0.9em;
                    color: #7f8c8d;
                    line-height: 1.4;
                    max-width: 250px;
                }}
                
                .no-emails {{
                    text-align: center;
                    padding: 40px;
                    color: #7f8c8d;
                    font-style: italic;
                    background: #f8f9fa;
                    border-radius: 10px;
                    margin: 20px 0;
                }}
                
                @media (max-width: 768px) {{
                    .container {{
                        margin: 10px;
                        border-radius: 10px;
                    }}
                    
                    .header h1 {{
                        font-size: 2em;
                    }}
                    
                    .content {{
                        padding: 20px;
                    }}
                    
                    table {{
                        font-size: 0.9em;
                    }}
                    
                    th, td {{
                        padding: 10px 8px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📧 Daily Email Summary Report</h1>
                    <div class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
                </div>
                
                <div class="content">
                    <div class="summary">
                        <h3 style="margin-bottom: 15px; color: #2c3e50;">📊 Summary Overview</h3>
                        <div class="summary-grid">
                            <div class="summary-item">
                                <span class="summary-number">{len(important_inbox)}</span>
                                <div class="summary-label">Important Inbox</div>
                            </div>
                            <div class="summary-item">
                                <span class="summary-number">{len(sahithi_emails_needing_reply)}</span>
                                <div class="summary-label">Urgent Replies Needed</div>
                            </div>
                            <div class="summary-item">
                                <span class="summary-number">{len(old_sent_emails)}</span>
                                <div class="summary-label">Follow-ups Required</div>
                            </div>
                        </div>                    </div>
                    
                    <div class="section">
                        <h2>🚨 URGENT: Sahithi's Emails Needing Reply (>1 day old)</h2>
        """
        
        if sahithi_emails_needing_reply:
            html_report += """
            <div class="urgent">
            <table>
                <tr>
                    <th>Subject</th>
                    <th>From</th>
                    <th>Email</th>
                    <th>Received</th>
                    <th>Preview</th>
                    <th>Open Email</th>
                </tr>
            """
            for email in sahithi_emails_needing_reply:
                open_link = f'<a href="{email["nav_link"]}" target="_blank" class="email-link urgent-link">Open Email</a>' if email.get("nav_link") else "N/A"
                html_report += f"""
                <tr class="sahithi-row">
                    <td class="subject-cell"><strong>{email['subject']}</strong></td>
                    <td class="sender-cell"><strong>{email['sender']}</strong></td>
                    <td class="email-cell">{email['sender_email']}</td>
                    <td class="date-cell">{email['received']}</td>
                    <td class="preview-cell">{email['preview']}</td>
                    <td>{open_link}</td>
                </tr>
                """
            html_report += "</table></div>"
        else:
            html_report += "<p>✅ No urgent emails from Sahithi needing replies.</p>"
        
        html_report += "<h2>🔍 All Important Inbox Emails</h2>"
        
        if important_inbox:
            html_report += """
            <table>
                <tr>
                    <th>Subject</th>
                    <th>Sender</th>
                    <th>Email</th>
                    <th>Received</th>
                    <th>Preview</th>
                    <th>Open Email</th>
                </tr>
            """
            for email in important_inbox:
                row_class = "sahithi-row" if email.get('is_from_sahithi') else ""
                open_link = f'<a href="{email["nav_link"]}" target="_blank" class="email-link">Open Email</a>' if email.get("nav_link") else "N/A"
                html_report += f"""
                <tr class="{row_class}">
                    <td class="subject-cell">{email['subject']}</td>
                    <td class="sender-cell">{email['sender']}</td>
                    <td class="email-cell">{email['sender_email']}</td>
                    <td class="date-cell">{email['received']}</td>
                    <td class="preview-cell">{email['preview']}</td>
                    <td>{open_link}</td>
                </tr>
                """
            html_report += "</table>"
        else:
            html_report += "<p>No important emails found in inbox.</p>"
        
        html_report += "<h2>⏰ Old Sent Emails (Older than 2 days - May need follow-up)</h2>"
        
        if old_sent_emails:
            html_report += """
            <table>
                <tr>
                    <th>Subject</th>
                    <th>Recipients</th>
                    <th>Sent Date</th>
                    <th>Preview</th>
                </tr>
            """
            for email in old_sent_emails:
                html_report += f"""
                <tr>
                    <td>{email['subject']}</td>
                    <td>{email['recipients']}</td>
                    <td>{email['sent']}</td>
                    <td>{email['preview']}</td>
                </tr>
                """
            html_report += "</table>"
        else:
            html_report += "<p>No old sent emails found that need follow-up.</p>"
        
        html_report += """
        </body>
        </html>
        """
        
        # Return HTML as plain string (not email sending)
        return func.HttpResponse(
            html_report,
            status_code=200,
            headers={'Content-Type': 'text/html'}
        )
        
    except Exception as e:
        logging.error(f"Error processing emails: {str(e)}")
        return func.HttpResponse(
            f"Error processing emails: {str(e)}",
            status_code=500
        )
