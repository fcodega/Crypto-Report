import io
from datetime import datetime

import numpy as np
import pandas as pd
from requests import get

# function that downloads the exchange rates from the ECB web page and returns a matrix (pd.DataFrame) that
# indicates: on the first column the date, on the second tha exchange rate vakue eutro based,
# on the third the currency, on the fourth the currency of denomination (always 'EUR')
# key_curr_vector expects a list of currency in International Currency Formatting (ex. USD, GBP, JPY, CAD,...)
# the functions diplays the information better for a single day data retrival, however can works with multiple date
# regarding the other default variables consult the ECB api web page
# start_period has to be in YYYY-MM-DD format


def ECB_rates_extractor(
    key_curr_vector,
    start_period,
    end_period=None,
    freq="D",
    curr_den="EUR",
    type_rates="SP00",
    series_var="A",
):

    # set end_period = start_period if empty, so that is possible to perform daily download
    if end_period is None:
        end_period = start_period

    # API settings
    entrypoint = "https://sdw-wsrest.ecb.europa.eu/service/"
    resource = "data"
    flow_ref = "EXR"
    param = {"startPeriod": start_period, "endPeriod": end_period}

    exc_rate_list = pd.DataFrame()
    # turning off a pandas warning about slicing of DF
    pd.options.mode.chained_assignment = None

    for currency in key_curr_vector:
        key = (
            freq + "." + currency + "." + curr_den + "." + type_rates + "." + series_var
        )
        request_url = entrypoint + resource + "/" + flow_ref + "/" + key

        # API call
        response = get(request_url, params=param,
                       headers={"Accept": "text/csv"})

        # if data is empty, it is an holiday, therefore exit
        try:

            df = pd.read_csv(io.StringIO(response.text))

        except pd.errors.EmptyDataError:

            break

        main_df = df.filter(
            ["TIME_PERIOD", "OBS_VALUE", "CURRENCY", "CURRENCY_DENOM"], axis=1
        )

        if exc_rate_list.size == 0:

            exc_rate_list = main_df

        else:

            exc_rate_list = exc_rate_list.append(
                main_df, sort=True)

    exc_rate_list.reset_index(drop=True, inplace=True)

    return exc_rate_list


def ECB_clean_series(raw_rate_df, start_period, end_period):

    rate_df = raw_rate_df.copy()
    rate_df = rate_df.rename(columns={"TIME_PERIOD": "Date",
                                      "OBS_VALUE": "Rate",
                                      "CURRENCY": "Currency"})
    # defining the array of date to be used
    date_complete = date_gen(start_period, end_period)
    print(date_complete)
    merged = pd.merge(date_complete, rate_df, how="left", on="Date")
    merged = merged.fillna(method='ffill')
    merged = merged.fillna(method='bfill')
    merged["Currency"] = merged["Currency"] + "/" + merged["CURRENCY_DENOM"]
    merged = merged.drop(columns=["CURRENCY_DENOM"])
    merged["Date_str"] = merged["Date"]

    return merged


def date_gen(start_date, end_date=None):

    if end_date is None:

        end_date = datetime.now().strftime("%m-%d-%Y")

    date_index = pd.date_range(start_date, end_date)

    date_ll = [datetime.strftime(date, "%Y-%m-%d") for date in date_index]
    date_ll = np.array(date_ll)

    date_df = pd.DataFrame(columns=["Date"])
    date_df["Date"] = date_ll

    return date_df


def exchange_rates_definition(list_of_ccy, start_period, end_period):

    raw_rates = ECB_rates_extractor(list_of_ccy, start_period, end_period)

    complete_rates = ECB_clean_series(raw_rates, start_period, end_period)

    return complete_rates


def report_rates(input_db):

    start_date = np.array(input_db["Date"].head(1))[0]
    start_date = pd.to_datetime(str(start_date))
    end_date = np.array(input_db["Date"].tail(1))[0]
    end_date = pd.to_datetime(str(end_date))
    start_date = datetime.strftime(start_date, "%Y-%m-%d")
    end_date = datetime.strftime(end_date, "%Y-%m-%d")
    rates = exchange_rates_definition(["USD"], start_date, end_date)

    return rates
