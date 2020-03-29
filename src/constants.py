from pathlib import Path

NATIONAL_DATA_JSON_URL = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-andamento-nazionale.json"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
PROJECT_BASE_PATH = Path(__file__).parent.parent
LATEST_EXECUTION_DATE_FILE_PATH = PROJECT_BASE_PATH / ".last_exec"
TEMP_FILES_PATH = PROJECT_BASE_PATH / "tmp"
UPDATE_CHECK_INTERVAL_MINUTES = 3
CHART_BLUE = "#636EFA"
CHART_BLUE_TRANSPARENT = "rgba(97, 107, 250, 0.4)"
CHART_RED = "#EF553B"
CHART_GREEN = "#00CC96"