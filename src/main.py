import requests
import constants
import twitter
import os
from dotenv import load_dotenv
load_dotenv()

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
        return "⬆"
    elif value == 0:
        return "↔"
    else:
        return "⬇"

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

req = requests.get(constants.NATIONAL_DATA_JSON_URL)

if req.status_code == 200:
    json_data = req.json()
    processed_data = process_latest(json_data)
    tweet_updates(processed_data)
    