import os

NATIONAL_DATA_JSON_URL = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-andamento-nazionale.json"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
LATEST_EXECUTION_DATE_FILE_PATH = __file__ +  "/../../.last_exec"
TEMP_FILES_PATH = __file__ + "/../../tmp"
UPDATE_CHECK_INTERVAL_MINUTES = 5
CHART_BLUE = "#636EFA"
CHART_RED = "#EF553B"
CHART_GREEN = "#00CC96"