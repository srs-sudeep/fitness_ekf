import os
import datetime
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import numpy as np

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

    all_heart_rate_averages = {}

    if 'dataSource' in data_sources:
        for data_source in data_sources['dataSource']:
            source_id = data_source['dataStreamId']
            data_type = data_source.get('dataType', {}).get('name', '')

            if source_id != "raw:com.google.heart_rate.bpm:com.huami.watch.hmwatchmanager:heartbeat_data_source":
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
                    chunk_size = 60
                    num_chunks = len(heart_rates) // chunk_size
                    min_avg = [round(np.mean(heart_rates[i*chunk_size:(i+1)*chunk_size]), 2)
                                     for i in range(num_chunks)]

                    all_heart_rate_averages[source_id] = min_avg
                    print(f"Found {len(heart_rates)} measurements → {len(min_avg)} minute-averaged values")
                else:
                    print("No heart rate data found in this source")

            except Exception as e:
                print(f"Error accessing this data source: {str(e)}")
    else:
        print("No data sources found.")

    return all_heart_rate_averages

def apply_ekf(HR):
    a1, b1, c1 = 4.5714, 384.4286, 7887.1  # exercise model
    a2, b2, c2 = 4.5714, 384.4286, 7899.76 # recovery model
    gamma = 0.022
    sigma = 18.88

    n = len(HR)
    CT = np.zeros(n)
    V = np.zeros(n)
    HR_ma = np.zeros(n)
    delta_HR = np.zeros(n)
    A = np.zeros(n)

    CT = np.zeros(n)
    CT[:4] = 36.97 
    HR_ma[0:4] = [1, 2, 3, 4] #false moving average
    V[3] = 0

    for t in range(4, n):
        HR_ma[t] = np.mean(HR[t-4:t+1])
        delta_HR[t] = HR_ma[t] - HR_ma[t-4]

        ct = CT[t-1]
        v = V[t-1] + gamma**2

        if delta_HR[t] < 0:
            A[t] = 39
            c = -2 * a2 * ct + b2
            k = (v * c) / (v * c**2 + sigma**2)
            HR_model = -a2 * ct**2 + b2 * ct - c2
        else:
            A[t] = 40
            c = -2 * a1 * ct + b1
            k = (v * c) / (v * c**2 + sigma**2)
            HR_model = -a1 * ct**2 + b1 * ct - c1

        CT[t] = ct + k * (HR[t] - HR_model)
        V[t] = (1 - k * c) * v

    return CT

def main():
    creds = authenticate_google_fit()
    all_heart_rates = get_heart_rate_data(creds)

    if all_heart_rates:
        for source, rates in all_heart_rates.items():
            print(f"\nRunning EKF on Source: {source}")
            print(f"1-minute averaged rates count: {len(rates)}")

            if len(rates) < 5:
                    pad_value = rates[-1] if rates else 80.0
                    while len(rates) < 5:
                        rates.append(pad_value)
            CT = apply_ekf(rates)            

            print("\nCore Temperature Estimates:")
            for temp in CT:
                print(f"{temp:.2f}°C")
    else:
        print("No heart rate data found in any source.")

if __name__ == '__main__':
    main()

