import requests
import twitter
import os
import datetime
import schedule
import time
import logging
import tempfile
import pytz
import plotly.io
import plotly.graph_objects as go
from bot import constants
from pathlib import Path
from dotenv import load_dotenv

# Logger setup

log = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - %(module)s - %(message)s"))
log.setLevel(logging.DEBUG)
log.addHandler(handler)

# Classes


class ChartManager:

    def __init__(self):
        self.charts = []

    def add(self, chart: go.Figure):
        self.charts.append(chart)

    def generate_images(self, path: Path):
        images_paths = []
        for i in range(0, len(self.charts)):
            fname = "chart_" + str(i) + ".png"
            fpath = str(path / fname)
            self.charts[i].write_image(fpath)
            images_paths.append(fpath)
        return images_paths

# Functions


def process_latest(json_data):
    last_day = json_data[len(json_data) - 1]
    prev_day = json_data[len(json_data) - 2]
    processed_data = {}
    processed_data["active_total_cases"] = last_day["totale_positivi"]
    processed_data["active_total_cases_delta"] = last_day["totale_positivi"] - \
        prev_day["totale_positivi"]
    processed_data["active_total_cases_delta_percentage"] = (
        100 * processed_data["active_total_cases_delta"]) / prev_day["totale_positivi"]
    processed_data["hospitalized"] = last_day["totale_ospedalizzati"]
    processed_data["hospitalized_delta"] = last_day["totale_ospedalizzati"] - \
        prev_day["totale_ospedalizzati"]
    processed_data["hospitalized_delta_percentage"] = (
        100 * processed_data["hospitalized_delta"]) / prev_day["totale_ospedalizzati"]
    processed_data["intensive_care"] = last_day["terapia_intensiva"]
    processed_data["intensive_care_delta"] = last_day["terapia_intensiva"] - \
        prev_day["terapia_intensiva"]
    processed_data["intensive_case_delta_percentage"] = (
        100 * processed_data["intensive_care_delta"]) / prev_day["terapia_intensiva"]
    processed_data["deaths"] = last_day["deceduti"]
    processed_data["deaths_delta"] = last_day["deceduti"] - \
        prev_day["deceduti"]
    processed_data["deaths_delta_percentage"] = (
        100 * processed_data["deaths_delta"]) / prev_day["deceduti"]
    return processed_data


def get_trend_icon(value):
    if value > 0:
        return "📈"
    elif value == 0:
        return "0️⃣"
    else:
        return "📉"


def tweet_updates(processed_data, charts_updates):
    api = twitter.Api(consumer_key=os.getenv("TWITTER_CONSUMER_API_KEY"),
                      consumer_secret=os.getenv("TWITTER_CONSUMER_SECRET_KEY"),
                      access_token_key=os.getenv("TWITTER_ACCESS_TOKEN_KEY"),
                      access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET_KEY"))

    tweet = "🦠🇮🇹 Aggiornamento Giornaliero Covid-19\n\n" \
            "{0} Totale casi attivi: {1} ({2:+d}) ({3:+.2f}%)\n" \
            "{4} Totale ospedalizzati: {5} ({6:+d}) ({7:+.2f}%)\n" \
            "{8} Totali terapia intensiva: {9} ({10:+d}) ({11:+.2f}%)\n" \
            "{12} Totale morti: {13} ({14:+d}) ({15:+.2f}%)\n\n" \
            "#COVID2019 #CovidDailyUpdates"

    formatted_tweet = tweet.format(get_trend_icon(processed_data["active_total_cases_delta"]),
                                   processed_data["active_total_cases"],
                                   processed_data["active_total_cases_delta"],
                                   processed_data["active_total_cases_delta_percentage"],
                                   get_trend_icon(
                                       processed_data["hospitalized_delta"]),
                                   processed_data["hospitalized"],
                                   processed_data["hospitalized_delta"],
                                   processed_data["hospitalized_delta_percentage"],
                                   get_trend_icon(
                                       processed_data["intensive_care_delta"]),
                                   processed_data["intensive_care"],
                                   processed_data["intensive_care_delta"],
                                   processed_data["intensive_case_delta_percentage"],
                                   get_trend_icon(
                                       processed_data["deaths_delta"]),
                                   processed_data["deaths"],
                                   processed_data["deaths_delta"],
                                   processed_data["deaths_delta_percentage"])

    api.PostUpdate(formatted_tweet, media=charts_updates)


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
        log.error(e)


def convert_datetime_to_tz(date_time, tz_src_str, tz_dst_str):
    tz_src = pytz.timezone(tz_src_str)
    tz_dst = pytz.timezone(tz_dst_str)
    src_date = tz_src.localize(date_time)
    return src_date.astimezone(tz_dst)


def generate_graphs(json_data):
    dates = list(map(lambda x: convert_datetime_to_tz(
        parse_date(x["data"]), "utc", "Europe/Rome").date(), json_data))
    positives_active = list(map(lambda x: x["totale_positivi"], json_data))
    deaths = list(map(lambda x: x["deceduti"], json_data))
    healed = list(map(lambda x: x["dimessi_guariti"], json_data))
    icu = list(map(lambda x: x["terapia_intensiva"], json_data))
    non_icu = list(
        map(lambda x: x["totale_ospedalizzati"] - x["terapia_intensiva"], json_data))
    home_isolated = list(map(lambda x: x["isolamento_domiciliare"], json_data))
    new_positives = list(map(lambda x: x["nuovi_positivi"], json_data))

    tests = list(map(lambda x: x["tamponi"], json_data))
    for i in range(len(tests) - 1, 0, -1):
        tests[i] = tests[i] - tests[i-1]
    new_healed = list(map(lambda x: x["dimessi_guariti"], json_data))
    for i in range(len(new_healed) - 1, 0, -1):
        new_healed[i] = new_healed[i] - new_healed[i-1]
    new_deaths = list(map(lambda x: x["deceduti"], json_data))
    for i in range(len(new_deaths) - 1, 0, -1):
        new_deaths[i] = new_deaths[i] - new_deaths[i-1]

    constants.TEMP_FILES_PATH.mkdir(parents=True, exist_ok=True)
    chart_mgr = ChartManager()

    plotly.io.orca.config.default_scale = 2.0

    # Chart 1
    graph = go.Figure()
    graph.add_trace(go.Scatter(x=dates, y=positives_active, mode="lines+markers",
                               name="Contagiati Attivi", line=dict(color=constants.CHART_BLUE)))
    graph.add_trace(go.Scatter(x=dates, y=deaths, mode="lines+markers",
                               name="Deceduti", line=dict(color=constants.CHART_RED)))
    graph.add_trace(go.Scatter(x=dates, y=healed, mode="lines+markers",
                               name="Guariti", line=dict(color=constants.CHART_GREEN)))
    graph.update_layout(
        title="COVID2019 Italia - contagiati attivi, deceduti e guariti",
        title_x=0.5,
        showlegend=True,
        autosize=True,
        legend=dict(orientation="h", xanchor="center",
                    yanchor="top", x=0.5, y=-0.25),
        margin=dict(l=30, r=30, t=60, b=150)
    )
    graph.update_yaxes(rangemode="normal", automargin=True, ticks="outside")
    graph.update_xaxes(tickangle=90, type="date", tickformat='%d-%m-%y',
                       ticks="outside", tick0=dates[0], tickmode="linear", automargin=True)
    graph.add_annotation(
        xref="paper",
        yref="paper",
        x=0,
        yanchor="top",
        xanchor="left",
        align="left",
        y=-0.36,
        showarrow=False,
        font=dict(size=10),
        text="<br>Fonte dati: Protezione Civile Italiana + elaborazioni<br>Generato da: github.com/berna1995/CovidDailyUpdateBot"
    )
    chart_mgr.add(graph)

    # Chart 2
    graph = go.Figure()
    graph.add_trace(go.Bar(x=dates, y=icu, name="Ospedalizzati TI",
                           marker=dict(color=constants.CHART_RED)))
    graph.add_trace(go.Bar(x=dates, y=non_icu, name="Ospedalizzati Non TI",
                           marker=dict(color=constants.CHART_BLUE)))
    graph.add_trace(go.Bar(x=dates, y=home_isolated,
                           name="Isolamento Domiciliare", marker=dict(color=constants.CHART_GREEN)))
    graph.update_layout(
        title="COVID2019 Italia - ospedalizzati e isolamento domiciliare dei positivi",
        title_x=0.5,
        showlegend=True,
        autosize=True,
        legend=dict(orientation="h", xanchor="center",
                    yanchor="top", x=0.5, y=-0.25),
        margin=dict(l=30, r=30, t=60, b=150),
        barmode="stack",
        bargap=0
    )
    graph.update_yaxes(rangemode="normal", automargin=True, ticks="outside")
    graph.update_xaxes(tickangle=90, type="date", tickformat='%d-%m-%y', ticks="outside",
                       rangemode="normal", tick0=dates[0], tickmode="linear", automargin=True)
    graph.add_annotation(
        xref="paper",
        yref="paper",
        x=0,
        yanchor="top",
        xanchor="left",
        align="left",
        y=-0.36,
        showarrow=False,
        font=dict(size=10),
        text="<br>Fonte dati: Protezione Civile Italiana + elaborazioni<br>Generato da: github.com/berna1995/CovidDailyUpdateBot"
    )
    chart_mgr.add(graph)

    # Chart 3
    graph = go.Figure()
    graph.add_trace(go.Bar(x=dates, y=tests, name="Tamponi Effettuati",
                           marker=dict(color=constants.CHART_BLUE)))
    graph.add_trace(go.Bar(x=dates, y=new_positives,
                           name="Nuovi Infetti", marker=dict(color=constants.CHART_RED)))
    graph.update_layout(
        title="COVID2019 Italia - tamponi effettuati giornalmente e nuovi infetti",
        title_x=0.5,
        showlegend=True,
        autosize=True,
        legend=dict(orientation="h", xanchor="center",
                    yanchor="top", x=0.5, y=-0.25),
        margin=dict(l=30, r=30, t=60, b=150),
        barmode="group",
        bargap=0
    )
    graph.update_yaxes(rangemode="normal", automargin=True, ticks="outside")
    graph.update_xaxes(tickangle=90, type="date", tickformat='%d-%m-%y', ticks="outside",
                       rangemode="normal", tick0=dates[0], tickmode="linear", automargin=True)
    graph.add_annotation(
        xref="paper",
        yref="paper",
        x=0,
        yanchor="top",
        xanchor="left",
        align="left",
        y=-0.36,
        showarrow=False,
        font=dict(size=10),
        text="<br>Fonte dati: Protezione Civile Italiana + elaborazioni<br>Generato da: github.com/berna1995/CovidDailyUpdateBot"
    )
    chart_mgr.add(graph)

    # Chart 4
    graph = go.Figure()
    graph.add_trace(go.Scatter(x=dates, y=new_positives, mode="lines+markers",
                               name="Infetti", line=dict(color=constants.CHART_BLUE)))
    graph.add_trace(go.Scatter(x=dates, y=new_healed, mode="lines+markers",
                               name="Guariti", line=dict(color=constants.CHART_GREEN)))
    graph.add_trace(go.Scatter(x=dates, y=new_deaths, mode="lines+markers",
                               name="Morti", line=dict(color=constants.CHART_RED)))
    graph.update_layout(
        title="COVID2019 Italia - nuovi guariti, morti, infetti",
        title_x=0.5,
        showlegend=True,
        autosize=True,
        legend=dict(orientation="h", xanchor="center",
                    yanchor="top", x=0.5, y=-0.25),
        margin=dict(l=30, r=30, t=60, b=150)
    )
    graph.update_yaxes(rangemode="normal", automargin=True, ticks="outside")
    graph.update_xaxes(tickangle=90, type="date", tickformat='%d-%m-%y',
                       ticks="outside", tick0=dates[0], tickmode="linear", automargin=True)
    graph.add_annotation(
        xref="paper",
        yref="paper",
        x=0,
        yanchor="top",
        xanchor="left",
        align="left",
        y=-0.36,
        showarrow=False,
        font=dict(size=10),
        text="<br>Fonte dati: Protezione Civile Italiana + elaborazioni<br>Generato da: github.com/berna1995/CovidDailyUpdateBot"
    )
    chart_mgr.add(graph)

    return chart_mgr.generate_images(constants.TEMP_FILES_PATH)


def check_for_new_data():
    log.info("Checking for new data...")
    req = requests.get(constants.NATIONAL_DATA_JSON_URL)

    if req.status_code == 200:
        json_data = req.json()
        last_data_date = parse_date(json_data[len(json_data) - 1]["data"])
        last_exec_date = read_last_date_updated(
            constants.LATEST_EXECUTION_DATE_FILE_PATH)

        if last_exec_date == None or last_data_date > last_exec_date:
            log.info("New data found, processing and tweeting...")
            charts_paths = generate_graphs(json_data)
            processed_data = process_latest(json_data)
            #tweet_updates(processed_data, charts_paths)
            write_last_date_updated(
                constants.LATEST_EXECUTION_DATE_FILE_PATH, last_data_date)
            log.info("New data tweeted successfully.")
        else:
            log.info("No updates found.")
    else:
        log.warn("Got " + req.status_code + " status code.")

# Main Loop


def main():
    load_dotenv(verbose=False, override=False)

    job = schedule.every(constants.UPDATE_CHECK_INTERVAL_MINUTES).minutes.do(
        check_for_new_data)
    job.run()

    while True:
        schedule.run_pending()
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            log.info("Received SIGINT, closing...")
            return


if __name__ == "__main__":
    main()
