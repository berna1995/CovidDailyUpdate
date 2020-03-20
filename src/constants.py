import os

NATIONAL_DATA_JSON_URL = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-andamento-nazionale.json"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LATEST_EXECUTION_DATE_FILE_PATH = os.path.abspath(__file__ +  "/../../.last_exec")
UPDATE_CHECK_INTERVAL_MINUTES = 5