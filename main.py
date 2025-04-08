import datetime
import json
import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Google Fit API Scopes
SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.activity.write",
    "https://www.googleapis.com/auth/fitness.heart_rate.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.write"
]

# Path to credentials.json
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def get_authenticated_service():
    """Authenticate and return the Google Fit service."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8000)
        
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("fitness", "v1", credentials=creds)

def get_heart_rate_data():
    """Fetch heart rate data from Google Fit API."""
    service = get_authenticated_service()

    # Google Fit heart rate data source
    DATA_SOURCE = "derived:com.google.active_minutes:com.google.android.gms:aggregated"
    ENDPOINT = f"users/me/dataset:aggregate"

    now = datetime.datetime.utcnow()
    start_time_millis = int((now - datetime.timedelta(days=31)).timestamp() * 1000)  # Last 7 days
    end_time_millis = int(now.timestamp() * 1000)
    print(start_time_millis, end_time_millis)

    body = {
        "aggregateBy": [{"dataTypeName": "com.google.heart_rate.summary", "dataSourceId": "derived:com.google.active_minutes:com.google.android.gms:aggregated"}],
        "bucketByTime": {"durationMillis": 86400000},  # Daily buckets
        "startTimeMillis": start_time_millis,
        "endTimeMillis": end_time_millis,
    }

    response = service.users().dataset().aggregate(userId="me", body=body).execute()
    
    heart_rate_data = []
    if "bucket" in response:
        for bucket in response["bucket"]:
            for dataset in bucket["dataset"]:
                for point in dataset["point"]:
                    heart_rate_value = point["value"][0]["fpVal"]
                    timestamp = datetime.datetime.fromtimestamp(int(point["startTimeNanos"]) / 1e9)
                    heart_rate_data.append({"timestamp": timestamp, "heart_rate": heart_rate_value})

    return heart_rate_data

if __name__ == "__main__":
    data = get_heart_rate_data()
    print(json.dumps(data, indent=2, default=str))
