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
                      # Create smart preview with read more functionality
                    full_preview = email.get('bodyPreview', '')
                    short_preview = full_preview[:100] + '...' if len(full_preview) > 100 else full_preview
                    
                    email_data = {
                        'subject': email.get('subject', 'No Subject'),
                        'sender': sender_display,
                        'sender_email': sender_email_display,
                        'received': received_date_str,
                        'preview_short': short_preview,
                        'preview_full': full_preview,
                        'has_long_preview': len(full_preview) > 100,
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
                              # Create smart preview with read more functionality
                            full_preview = email.get('bodyPreview', '')
                            short_preview = full_preview[:80] + '...' if len(full_preview) > 80 else full_preview
                            
                            old_sent_emails.append({
                                'subject': subject,
                                'recipients': ', '.join(recipient_names) if recipient_names else 'Unknown',
                                'sent': sent_date_str,
                                'preview_short': short_preview,
                                'preview_full': full_preview,
                                'has_long_preview': len(full_preview) > 80
                            })
                    except Exception as date_error:
                        logging.warning(f"Error parsing sent date {sent_date_str}: {date_error}")
                        continue
            except Exception as email_error:
                logging.warning(f"Error processing sent email: {email_error}")
                continue        # Helper function to create preview cell with read more functionality
        def create_preview_cell(email_data, index):
            if not email_data.get('has_long_preview', False):
                return f'<td class="preview-cell">{email_data.get("preview_short", "")}</td>'
            
            return f'''<td class="preview-cell">
                <div class="preview-short" id="short-{index}">{email_data.get("preview_short", "")}</div>
                <div class="preview-full" id="full-{index}" style="display: none;">{email_data.get("preview_full", "")}</div>
                <span class="read-more-btn" onclick="togglePreview(this, '{index}')">Read More</span>
            </td>'''
        
        # Format HTML table with all sections
        html_report = f"""<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="color-scheme" content="light dark">
            <title>Daily Email Summary Report</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, system-ui, sans-serif;
                    line-height: 1.6;
                    color: #1a1a1a;
                    background: #ffffff;
                    min-height: 100vh;
                    padding: 20px;
                    transition: all 0.3s ease;
                }}
                
                /* Dark mode styles */
                @media (prefers-color-scheme: dark) {{
                    body {{
                        color: #e5e5e5;
                        background: #0d1117;
                    }}
                    
                    .container {{
                        background: #161b22 !important;
                        border: 1px solid #30363d;
                    }}
                    
                    .summary {{
                        background: #21262d !important;
                        border-left-color: #58a6ff !important;
                    }}
                    
                    .summary-item {{
                        background: rgba(56, 139, 253, 0.1) !important;
                        border: 1px solid #30363d;
                    }}
                    
                    .summary-number {{
                        color: #f0f6fc !important;
                    }}
                    
                    .summary-label {{
                        color: #8b949e !important;
                    }}
                    
                    h2 {{
                        color: #f0f6fc !important;
                        border-bottom-color: #58a6ff !important;
                    }}
                    
                    th {{
                        background: #21262d !important;
                        color: #f0f6fc !important;
                        border-bottom: 1px solid #30363d;
                    }}
                    
                    td {{
                        border-bottom-color: #30363d !important;
                    }}
                    
                    table {{
                        background: #0d1117 !important;
                        border: 1px solid #30363d;
                    }}
                    
                    .urgent {{
                        background: rgba(248, 81, 73, 0.1) !important;
                        border-left-color: #f85149 !important;
                    }}
                    
                    .sahithi-row {{
                        background: rgba(255, 191, 0, 0.1) !important;
                        border-left-color: #ffbf00 !important;
                    }}
                    
                    .subject-cell {{
                        color: #f0f6fc !important;
                    }}
                    
                    .sender-cell {{
                        color: #e6edf3 !important;
                    }}
                    
                    .email-cell, .preview-cell {{
                        color: #8b949e !important;
                    }}
                    
                    .date-cell {{
                        color: #7d8590 !important;
                    }}
                    
                    .no-emails {{
                        background: #21262d !important;
                        color: #8b949e !important;
                        border: 1px solid #30363d;
                    }}
                }}
                
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                    overflow: hidden;
                    border: 1px solid #f3f4f6;
                }}
                
                .header {{
                    background: #1a1a1a;
                    color: #ffffff;
                    padding: 32px;
                    text-align: center;
                    border-bottom: 1px solid #374151;
                }}
                
                .header h1 {{
                    font-size: 2.25rem;
                    margin-bottom: 8px;
                    font-weight: 700;
                    letter-spacing: -0.025em;
                }}
                
                .header .subtitle {{
                    font-size: 1rem;
                    opacity: 0.85;
                    font-weight: 400;
                }}
                
                .content {{
                    padding: 32px;
                }}
                
                .summary {{
                    background: #f8fafc;
                    padding: 24px;
                    border-radius: 8px;
                    margin-bottom: 32px;
                    border-left: 4px solid #3b82f6;
                    border: 1px solid #e2e8f0;
                }}
                
                .summary h3 {{
                    color: #1e293b;
                    margin-bottom: 16px;
                    font-weight: 600;
                    font-size: 1.125rem;
                }}
                
                .summary-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 16px;
                    margin-top: 16px;
                }}
                
                .summary-item {{
                    text-align: center;
                    padding: 16px;
                    background: rgba(59, 130, 246, 0.05);
                    border-radius: 6px;
                    border: 1px solid #e2e8f0;
                }}
                
                .summary-number {{
                    font-size: 1.875rem;
                    font-weight: 700;
                    color: #1e293b;
                    display: block;
                    line-height: 1;
                }}
                
                .summary-label {{
                    font-size: 0.875rem;
                    color: #64748b;
                    margin-top: 4px;
                    font-weight: 500;
                }}
                
                h2 {{
                    color: #1e293b;
                    font-size: 1.5rem;
                    margin: 32px 0 16px 0;
                    padding-bottom: 8px;
                    border-bottom: 2px solid #3b82f6;
                    font-weight: 600;
                    letter-spacing: -0.025em;
                }}
                
                .section {{
                    margin-bottom: 40px;
                }}
                
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 16px 0;
                    background: #ffffff;
                    border-radius: 8px;
                    overflow: hidden;
                    border: 1px solid #e2e8f0;
                }}
                
                th {{
                    background: #1e293b;
                    color: #ffffff;
                    font-weight: 600;
                    padding: 16px;
                    text-align: left;
                    font-size: 0.875rem;
                    letter-spacing: 0.025em;
                    text-transform: uppercase;
                }}
                
                td {{
                    padding: 16px;
                    border-bottom: 1px solid #f1f5f9;
                    vertical-align: top;
                }}
                
                tr:hover {{
                    background: #f8fafc;
                    transition: background-color 0.15s ease;
                }}
                
                .urgent {{
                    background: #fef2f2;
                    border-left: 4px solid #ef4444;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border: 1px solid #fecaca;
                }}
                
                .sahithi-row {{
                    background: #fffbeb;
                    border-left: 4px solid #f59e0b;
                }}
                
                .email-link {{
                    display: inline-block;
                    background: #1e293b;
                    color: #ffffff;
                    padding: 8px 16px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-size: 0.875rem;
                    font-weight: 500;
                    transition: all 0.2s ease;
                    border: 1px solid transparent;
                }}
                
                .email-link:hover {{
                    background: #334155;
                    transform: translateY(-1px);
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    text-decoration: none;
                    color: #ffffff;
                }}
                
                .urgent-link {{
                    background: #dc2626;
                    color: #ffffff;
                }}
                
                .urgent-link:hover {{
                    background: #b91c1c;
                }}
                
                .subject-cell {{
                    font-weight: 600;
                    color: #1e293b;
                    max-width: 300px;
                }}
                
                .sender-cell {{
                    font-weight: 500;
                    color: #374151;
                }}
                
                .email-cell {{
                    font-size: 0.875rem;
                    color: #6b7280;
                    font-family: ui-monospace, SFMono-Regular, 'SF Mono', monospace;
                }}
                
                .date-cell {{
                    font-size: 0.875rem;
                    color: #9ca3af;
                    white-space: nowrap;
                }}
                
                .preview-cell {{
                    font-size: 0.875rem;
                    color: #6b7280;
                    line-height: 1.5;
                    max-width: 300px;
                    position: relative;
                }}
                
                .preview-text {{
                    display: block;
                }}
                
                .preview-short {{
                    display: block;
                }}
                
                .preview-full {{
                    display: none;
                }}
                
                .read-more-btn {{
                    color: #3b82f6;
                    cursor: pointer;
                    font-weight: 500;
                    text-decoration: underline;
                    font-size: 0.75rem;
                    margin-top: 4px;
                    display: inline-block;
                }}
                
                .read-more-btn:hover {{
                    color: #2563eb;
                }}
                
                .no-emails {{
                    text-align: center;
                    padding: 40px;
                    color: #6b7280;
                    font-style: italic;
                    background: #f9fafb;
                    border-radius: 8px;
                    margin: 20px 0;
                    border: 1px solid #e5e7eb;
                }}
                
                @media (max-width: 768px) {{
                    body {{
                        padding: 10px;
                    }}
                    
                    .container {{
                        margin: 0;
                        border-radius: 8px;
                    }}
                    
                    .header {{
                        padding: 24px 16px;
                    }}
                    
                    .header h1 {{
                        font-size: 1.875rem;
                    }}
                    
                    .content {{
                        padding: 20px 16px;
                    }}
                    
                    .summary {{
                        padding: 16px;
                    }}
                    
                    .summary-grid {{
                        grid-template-columns: 1fr;
                        gap: 12px;
                    }}
                    
                    table {{
                        font-size: 0.875rem;
                    }}
                    
                    th, td {{
                        padding: 12px 8px;
                    }}
                    
                    .preview-cell {{
                        max-width: 200px;
                    }}
                    
                    h2 {{
                        font-size: 1.25rem;
                        margin: 24px 0 12px 0;
                    }}
                }}
                
                /* Print styles */
                @media print {{
                    body {{
                        background: white;
                        color: black;
                    }}
                    
                    .container {{
                        box-shadow: none;
                        border: 1px solid #ccc;
                    }}
                    
                    .email-link {{
                        background: #333 !important;
                        -webkit-print-color-adjust: exact;
                    }}
                }}
            </style>            <script>
                function togglePreview(button, index) {{
                    const shortDiv = document.getElementById('short-' + index);
                    const fullDiv = document.getElementById('full-' + index);
                    
                    if (fullDiv.style.display === 'none' || !fullDiv.style.display) {{
                        shortDiv.style.display = 'none';
                        fullDiv.style.display = 'block';
                        button.textContent = 'Read Less';
                    }} else {{
                        shortDiv.style.display = 'block';
                        fullDiv.style.display = 'none';
                        button.textContent = 'Read More';
                    }}
                }}
            </script>
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
                </tr>            """
            for i, email in enumerate(sahithi_emails_needing_reply):
                open_link = f'<a href="{email["nav_link"]}" target="_blank" class="email-link urgent-link">Open Email</a>' if email.get("nav_link") else "N/A"
                preview_cell = create_preview_cell(email, f"urgent-{i}")
                html_report += f"""
                <tr class="sahithi-row">
                    <td class="subject-cell"><strong>{email['subject']}</strong></td>
                    <td class="sender-cell"><strong>{email['sender']}</strong></td>
                    <td class="email-cell">{email['sender_email']}</td>
                    <td class="date-cell">{email['received']}</td>
                    {preview_cell}
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
                </tr>            """
            for i, email in enumerate(important_inbox):
                row_class = "sahithi-row" if email.get('is_from_sahithi') else ""
                open_link = f'<a href="{email["nav_link"]}" target="_blank" class="email-link">Open Email</a>' if email.get("nav_link") else "N/A"
                preview_cell = create_preview_cell(email, f"inbox-{i}")
                html_report += f"""
                <tr class="{row_class}">
                    <td class="subject-cell">{email['subject']}</td>
                    <td class="sender-cell">{email['sender']}</td>
                    <td class="email-cell">{email['sender_email']}</td>
                    <td class="date-cell">{email['received']}</td>
                    {preview_cell}
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
                </tr>            """
            for i, email in enumerate(old_sent_emails):
                preview_cell = create_preview_cell(email, f"sent-{i}")
                html_report += f"""
                <tr>
                    <td class="subject-cell">{email['subject']}</td>
                    <td class="sender-cell">{email['recipients']}</td>
                    <td class="date-cell">{email['sent']}</td>
                    {preview_cell}
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
