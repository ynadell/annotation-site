from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# The ID of your Google Sheet
SPREADSHEET_ID = '1QgiTl4XhDOKkbhQZJvwi9ZKsbw5z1YcFoj3QEeUOetw'

# The range in A1 notation
RANGE_NAME = 'Sheet1'

# The values to write
VALUES = [['Hello', 'World']]

# Path to your service account key file
SERVICE_ACCOUNT_FILE = 'credentials.json'

# Authenticate and build the service
credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
service = build('sheets', 'v4', credentials=credentials)

# Write to the Google Sheet
request = service.spreadsheets().values().append(
    spreadsheetId=SPREADSHEET_ID,
    range=RANGE_NAME,
    valueInputOption='RAW',
    insertDataOption='INSERT_ROWS',
    body={'values': VALUES}
)
response = request.execute()

print(response)
