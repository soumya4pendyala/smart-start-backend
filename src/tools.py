import requests
import os
from langchain_core.tools import tool

# Placeholder for actual API calls
JIRA_API_URL = "https://your-company.atlassian.net/rest/api/2/issue"
JIRA_USER = "your-jira-email"
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN") # Store this securely!

CAB_SERVICE_API_URL = "https://api.yourcabservice.com/v1/bookings"
CAB_SERVICE_API_KEY = os.getenv("CAB_API_KEY")

import random
import string
import secrets
import string
import datetime

def generate_secure_id(length=10):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_cab_number():
    state_code = "TS"
    rto_code = random.randint(1, 99)
    series = ''.join(random.choices(string.ascii_uppercase, k=2))
    number = random.randint(1000, 9999)
    return f"{state_code}{rto_code:02d}{series}{number}"

def generate_otp(length=4):
    return ''.join(random.choices(string.digits, k=length))

def book_cab(pickup: str, destination: str, time: str) -> str:
    """Books a cab for the specified route and time."""
    print(f"--- Calling Cab Service API ---")
    # In a real scenario, you would make an API call like this:
    # headers = {"Authorization": f"Bearer {CAB_SERVICE_API_KEY}"}
    # payload = {"pickup": pickup, "destination": destination, "time": time}
    # response = requests.post(CAB_SERVICE_API_URL, json=payload, headers=headers)
    # if response.status_code == 201:
    #     return f"Successfully booked a cab from {pickup} to {destination} for {time}."
    # else:
    #     return f"Failed to book cab. Service returned: {response.text}"
    cab_number = generate_cab_number()
    otp = generate_otp()
    booking_id = generate_secure_id()
    return (
        f"CAB BOOKED: From {pickup} to {destination} at {time}. Booking ID: {booking_id}\n"
        f"Cab Number: {cab_number}\n"
        f"OTP for driver verification: {otp}"
    )



def create_ticket(description: str, summary: str) -> str:
    """Creates an IT support ticket in Jira or a similar system."""
    print(f"--- Calling Jira API ---")
    # In a real scenario, you would make an API call like this:
    # auth = (JIRA_USER, JIRA_TOKEN)
    # headers = {"Accept": "application/json", "Content-Type": "application/json"}
    # payload = {
    #     "fields": {
    #         "project": {"key": "IT"},
    #         "summary": summary,
    #         "description": description,
    #         "issuetype": {"name": "Task"}
    #     }
    # }
    # response = requests.post(JIRA_API_URL, json=payload, headers=headers, auth=auth)
    # if response.status_code == 201:
    #     ticket_key = response.json()['key']
    #     return f"Successfully created ticket {ticket_key} with summary: '{summary}'."
    # else:
    #     return f"Failed to create ticket. Jira returned: {response.text}"
    prefix = "INC"
    number = random.randint(1000000, 9999999)
    ticket_id = f"{prefix}{number}"

    # Optionally include a timestamp or mock sys_id
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        f"Ticket Created with Ticket id : {ticket_id} at {timestamp}."
        f"Summary: {{summary}}\n"
        f"You can check the status in here IT@LBG."   
    }

