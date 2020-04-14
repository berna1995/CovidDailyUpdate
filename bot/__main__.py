import datetime
import logging
import os
import time
from pathlib import Path

import plotly.graph_objects as go
import plotly.io
from plotly.subplots import make_subplots
import pytz
import requests
import schedule
import twitter
from dotenv import load_dotenv

from bot import config
from bot.processing import DataProcessor
from bot.indicators import DeltaIndicator
from bot.indicators import DeltaPercentageIndicator
from bot.indicators import MovingAverageIndicator

# Global variables / constants

DEBUG_MODE = False

CHART_BLUE = "#636EFA"
CHART_BLUE_TRANSPARENT = "rgba(97, 107, 250, 0.4)"
CHART_RED = "#EF553B"
CHART_GREEN = "#00CC96"

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


def get_trend_icon(value):
    if value > 0:
        return "📈"
    elif value == 0:
        return "0️⃣"
    else:
        return "📉"


def tweet_updates(dp: DataProcessor, chart_paths):
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

    active_total_cases = dp.get("total_active_positives", start=dp.size() - 2)
    active_total_cases_delta = DeltaIndicator(active_total_cases).get_last()
    active_total_cases_delta_percentage = DeltaPercentageIndicator(
        active_total_cases).get_last()
    total_hospitalized = dp.get("total_hospitalized", start=dp.size() - 2)
    total_hospitalized_delta = DeltaIndicator(total_hospitalized).get_last()
    total_hospitalized_delta_percentage = DeltaPercentageIndicator(
        total_hospitalized).get_last()
    total_ic = dp.get("total_intensive_care", start=dp.size() - 2)
    total_ic_delta = DeltaIndicator(total_ic).get_last()
    total_ic_delta_percentage = DeltaPercentageIndicator(total_ic).get_last()
    total_deaths = dp.get("total_deaths", start=dp.size() - 2)
    total_deaths_delta = DeltaIndicator(total_deaths).get_last()
    total_deaths_delta_percentage = DeltaPercentageIndicator(
        total_deaths).get_last()

    formatted_tweet = tweet.format(get_trend_icon(active_total_cases_delta),
                                   active_total_cases[1],
                                   active_total_cases_delta,
                                   active_total_cases_delta_percentage,
                                   get_trend_icon(total_hospitalized_delta),
                                   total_hospitalized[1],
                                   total_hospitalized_delta,
                                   total_hospitalized_delta_percentage,
                                   get_trend_icon(total_ic_delta),
                                   total_ic[1],
                                   total_ic_delta,
                                   total_ic_delta_percentage,
                                   get_trend_icon(total_deaths_delta),
                                   total_deaths[1],
                                   total_deaths_delta,
                                   total_deaths_delta_percentage)

    if DEBUG_MODE:
        log.debug(formatted_tweet)
    else:
        api.PostUpdate(formatted_tweet, media=chart_paths)


def read_last_date_updated(fpath):
    try:
        with open(fpath, "r") as file:
            return datetime.datetime.strptime(file.readline(), config.DATE_FORMAT)
    except IOError:
        return None


def write_last_date_updated(fpath, date):
    try:
        with open(fpath, "w+") as file:
            date_str = date.strftime(config.DATE_FORMAT)
            file.writelines(date_str)
    except IOError as e:
        log.error(e)


def generate_graphs(dp: DataProcessor):
    dates = list(map(lambda x: x.date(), dp.get("date")))
    positives_active = dp.get("total_active_positives")
    deaths = dp.get("total_deaths")
    healed = dp.get("total_recovered")
    icu = dp.get("total_intensive_care")
    non_icu = dp.get("total_hospitalized_non_ic")
    home_isolated = dp.get("total_home_confinement")
    new_positives = dp.get("new_infected")
    tests = DeltaIndicator(dp.get("total_tests")).get_all()
    new_healed = DeltaIndicator(dp.get("total_recovered")).get_all()
    new_deaths = DeltaIndicator(dp.get("total_deaths")).get_all()

    MOVING_AVG_DAYS = 5

    new_healed_moving_avg = MovingAverageIndicator(
        new_healed, MOVING_AVG_DAYS).get_all()[MOVING_AVG_DAYS - 1:]
    new_deaths_moving_avg = MovingAverageIndicator(
        new_deaths, MOVING_AVG_DAYS).get_all()[MOVING_AVG_DAYS - 1:]
    new_positives_moving_avg = MovingAverageIndicator(
        new_positives, MOVING_AVG_DAYS).get_all()[MOVING_AVG_DAYS - 1:]
    dates_moving_avg = dates[MOVING_AVG_DAYS - 1:]

    config.TEMP_FILES_PATH.mkdir(parents=True, exist_ok=True)
    chart_mgr = ChartManager()

    plotly.io.orca.config.default_scale = 2.0

    # Chart 1
    graph = go.Figure()
    graph.add_trace(go.Scatter(x=dates, y=positives_active, mode="lines+markers",
                               name="Contagiati Attivi", line=dict(color=CHART_BLUE)))
    graph.add_trace(go.Scatter(x=dates, y=deaths, mode="lines+markers",
                               name="Deceduti", line=dict(color=CHART_RED)))
    graph.add_trace(go.Scatter(x=dates, y=healed, mode="lines+markers",
                               name="Guariti", line=dict(color=CHART_GREEN)))
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
    graph = make_subplots(rows=1, cols=3)
    graph.add_trace(go.Bar(x=dates, y=icu, name="Ospedalizzati TI",
                           marker=dict(color=CHART_RED)), row=1, col=1)
    graph.add_trace(go.Bar(x=dates, y=non_icu, name="Ospedalizzati Non TI",
                           marker=dict(color=CHART_BLUE)), row=1, col=2)
    graph.add_trace(go.Bar(x=dates, y=home_isolated,
                           name="Isolamento Domiciliare", marker=dict(color=CHART_GREEN)), row=1, col=3)
    graph.update_layout(
        title="COVID2019 Italia - ospedalizzati e isolamento domiciliare dei positivi",
        title_x=0.5,
        showlegend=True,
        autosize=True,
        legend=dict(orientation="h", xanchor="center",
                    yanchor="top", x=0.5, y=-0.25),
        margin=dict(l=30, r=30, t=60, b=150),
        bargap=0
    )
    graph.update_yaxes(rangemode="normal", automargin=True, ticks="outside")
    graph.update_xaxes(tickangle=90, type="date", tickformat='%d-%m-%y', ticks="outside",
                       nticks=10, tickmode="auto", automargin=True)
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
                           marker=dict(color=CHART_BLUE)))
    graph.add_trace(go.Bar(x=dates, y=new_positives,
                           name="Nuovi Infetti", marker=dict(color=CHART_RED)))
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
    graph.add_trace(go.Scatter(x=dates_moving_avg, y=new_positives_moving_avg, mode="lines+markers",
                               name="Infetti", line=dict(color=CHART_BLUE)))
    graph.add_trace(go.Scatter(x=dates_moving_avg, y=new_healed_moving_avg, mode="lines+markers",
                               name="Guariti", line=dict(color=CHART_GREEN)))
    graph.add_trace(go.Scatter(x=dates_moving_avg, y=new_deaths_moving_avg, mode="lines+markers",
                               name="Morti", line=dict(color=CHART_RED)))
    graph.update_layout(
        title="COVID2019 Italia - nuovi guariti, morti, infetti [media mobile {0}gg]".format(
            MOVING_AVG_DAYS),
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

    return chart_mgr.generate_images(config.TEMP_FILES_PATH)


def check_for_new_data():
    log.info("Checking for new data...")
    req = requests.get(config.NATIONAL_DATA_JSON_URL)

    if req.status_code == 200:
        dp = DataProcessor.initialize(req.content, config.DATE_FORMAT)
        last_data_date = dp.get("date", start=dp.size() - 1)[0]
        last_exec_date = read_last_date_updated(
            config.LATEST_EXECUTION_DATE_FILE_PATH)

        if last_exec_date is None or last_data_date > last_exec_date or DEBUG_MODE:
            log.info("New data found, processing and tweeting...")
            dp.localize_dates("UTC", "Europe/Rome")
            charts_paths = generate_graphs(dp)
            tweet_updates(dp, charts_paths)
            if not DEBUG_MODE:
                write_last_date_updated(
                    config.LATEST_EXECUTION_DATE_FILE_PATH, last_data_date)
            log.info("New data tweeted successfully.")
        else:
            log.info("No updates found.")
    else:
        log.warn("Got " + req.status_code + " status code.")

# Main Loop


def main():
    load_dotenv(verbose=False, override=False)

    if os.getenv("DEBUG") is not None:
        log.debug("Debug mode")
        global DEBUG_MODE
        DEBUG_MODE = True
        check_for_new_data()
        exit(0)

    job = schedule.every(config.UPDATE_CHECK_INTERVAL_MINUTES).minutes.do(
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
