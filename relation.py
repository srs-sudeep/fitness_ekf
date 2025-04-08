import os
import datetime
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import matplotlib.pyplot as plt

# The scopes required to access heart rate data
SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.activity.write",
    "https://www.googleapis.com/auth/fitness.heart_rate.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.write"
]

def authenticate_google_fit():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def get_heart_rate_data(creds):
    service = build('fitness', 'v1', credentials=creds)
    data_sources = service.users().dataSources().list(userId='me').execute()

    ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now = datetime.datetime.now(ist)
    end_time = (now + datetime.timedelta(days=1)).isoformat()
    start_time = (now - datetime.timedelta(days=31)).isoformat()

    clean_start_time = start_time.replace('+05:30', '')
    dataset_id = f"{int(datetime.datetime.strptime(clean_start_time, '%Y-%m-%dT%H:%M:%S.%f').timestamp() * 1000000000)}-{int(now.timestamp() * 1000000000)}"

    all_heart_rates = {}

    if 'dataSource' in data_sources:
        for data_source in data_sources['dataSource']:
            source_id = data_source['dataStreamId']
            data_type = data_source.get('dataType', {}).get('name', '')

            if 'heart' not in data_type.lower() or 'heart_minutes' in data_type.lower():
                continue

            print(f"\nFound heart rate data source: {source_id}")
            print(f"Data type: {data_type}")

            try:
                data = service.users().dataSources().datasets().get(
                    userId='me',
                    dataSourceId=source_id,
                    datasetId=dataset_id).execute()

                heart_rate_points = data.get('point', [])
                heart_rates = []

                for point in heart_rate_points:
                    for value in point.get('value', []):
                        heart_rate = value.get('fpVal')
                        if heart_rate:
                            heart_rates.append(heart_rate)

                if heart_rates:
                    all_heart_rates[source_id] = heart_rates
                    print(f"Found {len(heart_rates)} measurements")
                else:
                    print("No heart rate data found in this source")

            except Exception as e:
                print(f"Error accessing this data source: {str(e)}")
    else:
        print("No data sources found.")

    return all_heart_rates

def plot_heart_rates(heart_rate_data):
    plt.figure(figsize=(12, 6))
    for source, values in heart_rate_data.items():
        label = source.split(':')[-1]  # Simplify source name
        plt.plot(values, marker='o', label=label)

    plt.xlabel('Time Index')
    plt.ylabel('Heart Rate (BPM)')
    plt.title('Heart Rate Comparison by Data Source')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def main():
    creds = authenticate_google_fit()
    all_heart_rates = get_heart_rate_data(creds)

    if all_heart_rates:
        print("\nHeart rate data for the last 24 hours:")
        for source, rates in all_heart_rates.items():
            print(f"\nSource: {source}")
            for rate in rates:
                print(f"{rate} BPM")

        plot_heart_rates(all_heart_rates)
    else:
        print("No heart rate data found in any source.")

if __name__ == '__main__':
    main()
