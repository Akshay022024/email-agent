import requests
import json

def test_function():
    # Sample email data structure with Sahithi emails
    test_data = {
        "inbox": [
            {
                "subject": "Meeting with Akshay tomorrow",
                "from": {
                    "emailAddress": {
                        "name": "John Doe",
                        "address": "john@example.com"
                    }
                },
                "receivedDateTime": "2025-06-20T10:30:00Z",
                "bodyPreview": "Hi, I wanted to confirm our meeting with Akshay tomorrow at 2 PM."
            },
            {
                "subject": "Project Update Required",
                "from": {
                    "emailAddress": {
                        "name": "Sahithi N",
                        "address": "sahithin@kensium.com"
                    }
                },
                "receivedDateTime": "2025-06-18T09:15:00Z",  # 2 days old - needs reply
                "bodyPreview": "Hi Akshay, I need the project update by end of day. Please send the latest status report."
            },
            {
                "subject": "Urgent: Client Meeting Tomorrow",
                "from": {
                    "emailAddress": {
                        "name": "Sahithi N",
                        "address": "sahithin@kensium.com"
                    }
                },
                "receivedDateTime": "2025-06-19T14:30:00Z",  # 1 day old - needs reply
                "bodyPreview": "Hi, we have a client meeting tomorrow at 10 AM. Please prepare the presentation and send me the slides."
            },
            {
                "subject": "Regular Newsletter",
                "from": {
                    "emailAddress": {
                        "name": "Newsletter Service",
                        "address": "news@service.com"
                    }
                },
                "receivedDateTime": "2025-06-20T08:00:00Z",
                "bodyPreview": "This week's newsletter with industry updates."
            },
            {
                "subject": "Please review @sahithin",
                "from": {
                    "emailAddress": {
                        "name": "Jane Smith",
                        "address": "jane@example.com"
                    }
                },
                "receivedDateTime": "2025-06-20T11:15:00Z",
                "bodyPreview": "Please send the report to @sahithin for review and approval."
            }
        ],
        "sent": [
            {
                "subject": "Follow up on proposal",
                "toRecipients": [
                    {
                        "emailAddress": {
                            "name": "Client A",
                            "address": "clienta@company.com"
                        }
                    }
                ],
                "sentDateTime": "2025-06-17T14:00:00Z",
                "bodyPreview": "Hi, just following up on the proposal we sent last week."
            },
            {
                "subject": "Daily standup notes",
                "toRecipients": [
                    {
                        "emailAddress": {
                            "name": "Team",
                            "address": "team@company.com"
                        }
                    }
                ],
                "sentDateTime": "2025-06-20T09:00:00Z",
                "bodyPreview": "Here are today's standup notes and action items."
            }
        ]
    }      # Test locally (make sure your function is running with 'func start')
    url = "http://localhost:7071/api/process_emails"
    
    try:
        response = requests.post(url, json=test_data, headers={'Content-Type': 'application/json'})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Save the HTML response to a file for viewing
        if response.status_code == 200:
            with open('test_output.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("HTML output saved to test_output.html")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the function. Make sure it's running with 'func start'")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_function()
