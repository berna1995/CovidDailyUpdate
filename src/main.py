import requests
import constants
import twitter
import os
import datetime
import schedule
import time
import logging
from dotenv import load_dotenv

def process_latest(json_data):
    last_day = json_data[len(json_data) - 1]
    prev_day = json_data[len(json_data) - 2]
    processed_data = {}
    processed_data["active_total_cases"] = last_day["totale_attualmente_positivi"]
    processed_data["active_total_cases_delta"] = last_day["totale_attualmente_positivi"] - prev_day["totale_attualmente_positivi"]
    processed_data["active_total_cases_delta_percentage"] = (100 * processed_data["active_total_cases_delta"]) / prev_day["totale_attualmente_positivi"]
    processed_data["hospitalized"] = last_day["totale_ospedalizzati"]
    processed_data["hospitalized_delta"] = last_day["totale_ospedalizzati"] - prev_day["totale_ospedalizzati"]
    processed_data["hospitalized_delta_percentage"] = (100 * processed_data["hospitalized_delta"]) / prev_day["totale_ospedalizzati"]
    processed_data["intensive_care"] = last_day["terapia_intensiva"]
    processed_data["intensive_care_delta"] = last_day["terapia_intensiva"] - prev_day["terapia_intensiva"]
    processed_data["intensive_case_delta_percentage"] = (100 * processed_data["intensive_care_delta"]) / prev_day["terapia_intensiva"]
    processed_data["deaths"] = last_day["deceduti"]
    processed_data["deaths_delta"] = last_day["deceduti"] - prev_day["deceduti"]
    processed_data["deaths_delta_percentage"] = (100 * processed_data["deaths_delta"]) / prev_day["deceduti"]
    return processed_data

def get_trend_icon(value):
    if value > 0:
        return "📈"
    elif value == 0:
        return "0️⃣"
    else:
        return "📉"

def tweet_updates(processed_data):
    api = twitter.Api(consumer_key=os.getenv("TWITTER_CONSUMER_API_KEY"),
                  consumer_secret=os.getenv("TWITTER_CONSUMER_SECRET_KEY"),
                  access_token_key=os.getenv("TWITTER_ACCESS_TOKEN_KEY"),
                  access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET_KEY"))

    tweet = "🦠 Aggiornamento Giornaliero Covid-19\n\n" \
            "{0} Totale casi attivi: {1} ({2:+d}) ({3:+.2f}%)\n" \
            "{4} Totale ospedalizzati: {5} ({6:+d}) ({7:+.2f}%)\n" \
            "{8} Totali terapia intensiva: {9} ({10:+d}) ({11:+.2f}%)\n" \
            "{12} Totale morti: {13} ({14:+d}) ({15:+.2f}%)\n\n" \
            "#Covid19Italy #CovidDailyUpdates"

    formatted_tweet = tweet.format(get_trend_icon(processed_data["active_total_cases_delta"]), 
                                   processed_data["active_total_cases"], 
                                   processed_data["active_total_cases_delta"],
                                   processed_data["active_total_cases_delta_percentage"],
                                   get_trend_icon(processed_data["hospitalized_delta"]),
                                   processed_data["hospitalized"],
                                   processed_data["hospitalized_delta"],
                                   processed_data["hospitalized_delta_percentage"],
                                   get_trend_icon(processed_data["intensive_care_delta"]),
                                   processed_data["intensive_care"],
                                   processed_data["intensive_care_delta"],
                                   processed_data["intensive_case_delta_percentage"],
                                   get_trend_icon(processed_data["deaths_delta"]),
                                   processed_data["deaths"],
                                   processed_data["deaths_delta"],
                                   processed_data["deaths_delta_percentage"])

    api.PostUpdate(formatted_tweet)

def parse_date(str):
    return datetime.datetime.strptime(str, constants.DATE_FORMAT)

def read_last_date_updated(fpath):
    try:
        with open(fpath, "r") as file:
            return parse_date(file.readline())
    except IOError:
        return None
    
def write_last_date_updated(fpath, date):
    try:
        with open(fpath, "w+") as file:
            date_str = date.strftime(constants.DATE_FORMAT)
            file.writelines(date_str)
    except IOError as e:
        logging.error(e)

def check_for_new_data():
    logging.info("Checking for new data...")
    req = requests.get(constants.NATIONAL_DATA_JSON_URL)

    if req.status_code == 200:
        json_data = req.json()
        last_data_date = parse_date(json_data[len(json_data) - 1]["data"])
        last_exec_date = read_last_date_updated(constants.LATEST_EXECUTION_DATE_FILE_PATH)

        if last_data_date > last_exec_date:
            logging.info("New data found, processing and tweeting...")
            processed_data = process_latest(json_data)
            tweet_updates(processed_data)
            write_last_date_updated(constants.LATEST_EXECUTION_DATE_FILE_PATH, last_data_date)
            logging.info("New data tweeted successfully.")
        else: 
            logging.info("No updates found.")
    else:
        logging.warn("Got " + req.status_code + " status code")

def main():
    load_dotenv()
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(module)s - %(message)s", level=logging.DEBUG)

    job = schedule.every(constants.UPDATE_CHECK_INTERVAL_MINUTES).minutes.do(check_for_new_data)
    job.run()

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()