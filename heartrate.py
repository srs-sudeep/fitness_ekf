import os
import datetime
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# The scopes required to access heart rate data
SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.activity.write",
    "https://www.googleapis.com/auth/fitness.heart_rate.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.write"
]
def authenticate_google_fit():
    creds = None
    # Check if token.json exists (stores user tokens)
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no valid credentials, get new ones through OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

def get_heart_rate_data(creds):
    service = build('fitness', 'v1', credentials=creds)
    data_sources = service.users().dataSources().list(userId='me').execute()
    
    # Create IST timezone (UTC+5:30)
    ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now = datetime.datetime.now(ist)
    
    # Set end time to tomorrow
    end_time = (now + datetime.timedelta(days=1)).isoformat()
    # Set start time to 7 days ago
    start_time = (now - datetime.timedelta(days=31)).isoformat()
    
    # Remove timezone info from the timestamps before parsing
    clean_start_time = start_time.replace('+05:30', '')
    dataset_id = f"{int(datetime.datetime.strptime(clean_start_time, '%Y-%m-%dT%H:%M:%S.%f').timestamp() * 1000000000)}-{int(now.timestamp() * 1000000000)}"
    
    all_heart_rates = {}
    
    if 'dataSource' in data_sources:
        for data_source in data_sources['dataSource']:
            # Check if this data source is related to heart rate
            source_id = data_source['dataStreamId']
            data_type = data_source.get('dataType', {}).get('name', '')
            
            # Skip if not heart-related or if it's heart_minutes
            if 'heart' not in data_type.lower() or 'heart_minutes' in data_type.lower():
                continue
                
            print(f"\nFound heart rate data source: {source_id}")
            print(f"Data type: {data_type}")
            
            try:
                # Request the heart rate data for each source
                data = service.users().dataSources().datasets().get(
                    userId='me', 
                    dataSourceId=source_id, 
                    datasetId=dataset_id).execute()
                
                heart_rate_points = data.get('point', [])
                heart_rates = []
                
                for point in heart_rate_points:
                    for value in point.get('value', []):
                        heart_rate = value.get('fpVal')  # Heart rate in BPM
                        if heart_rate:  # Only append if there's a value
                            heart_rates.append(heart_rate)
                
                if heart_rates:  # Only add to dictionary if we found data
                    all_heart_rates[source_id] = heart_rates
                    print(f"Found {len(heart_rates)} measurements")
                else:
                    print("No heart rate data found in this source")
                    
            except Exception as e:
                print(f"Error accessing this data source: {str(e)}")
    else:
        print("No data sources found.")
    
    return all_heart_rates

def main():
    creds = authenticate_google_fit()
    all_heart_rates = get_heart_rate_data(creds)
    
    if all_heart_rates:
        print("\nHeart rate data for the last 24 hours:")
        for source, rates in all_heart_rates.items():
            print(f"\nSource: {source}")
            for rate in rates:
                print(f"{rate} BPM")
    else:
        print("No heart rate data found in any source.")

if __name__ == '__main__':
    main()






