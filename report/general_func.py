import numpy as np
import pandas as pd
from datetime import datetime
from report.api import cw_raw_download
from report.config import CRYPTO_LIST, FIAT_LIST, TRADE_TYPE


def taxation_db(input_db):

    db = input_db.copy()
    db = db.loc[db.FlowType_Num != "1"]
    db = db.loc[db.FlowType_Num != "7"]
    db = db.loc[db.FlowType_Num != "8"]
    db = db[["Date", "Currency", "Price"]]

    max_date = datetime.now()
    min_date = min(db["Date"])

    db["Date"] = [datetime.strftime(x, "%Y-%m-%d")
                  for x in db["Date"]]
    time_list = pd.date_range(start=min_date, end=max_date)
    time_df = pd.DataFrame(time_list, columns=["Date"])
    time_df["Date"] = [datetime.strftime(x, "%Y-%m-%d")
                       for x in time_df["Date"]]

    list_of_ccy = list(np.array(db["Currency"].unique()))
    new_df = pd.DataFrame(time_list, columns=["Date"])
    conv_df = pd.DataFrame()

    date_to_look = "01-01-" + str(max_date.year)
    for ccy in list_of_ccy:
        if ((ccy == "EUR") | (ccy == "USD")):
            pass
        else:
            ccy_pair = ccy.lower() + "eur"
            # downloading the 01/01/yyyy
            open_price = np.array(cw_raw_download(
                ccy_pair, date_to_look)["Open"])[0]
            ccy_db = db.loc[db.Currency == ccy]
            grouped = ccy_db.groupby(by=["Date"]).sum()
            grouped = grouped.cumsum()
            merged = pd.merge(time_df, grouped, on="Date", how="left")
            merged = merged.rename(columns={'Price': ccy})
            merged = merged.fillna(method='bfill')
            merged = merged.fillna(method='ffill')
            new_df[ccy] = merged[ccy]

            col_name = ccy + "_conv"
            new_df[col_name] = merged[ccy] * open_price
            conv_df[col_name] = merged[ccy] * open_price

    new_df["Year"] = [x.year for x in new_df["Date"]]

    conv_df["total"] = conv_df.sum(axis=1)
    conv_df["Date"] = new_df["Date"]
    conv_df["Year"] = new_df["Year"]
    conv_df = conv_df.loc[conv_df.Year == max_date.year]
    conv_df = conv_df[["Date", "total"]]
    conv_df["Rolling Avg"] = conv_df["total"].rolling(window=7).mean()

    conv_df = conv_df.fillna(0)
    new_df = new_df.loc[new_df.Year == max_date.year]

    max_holding_value = max(conv_df["Rolling Avg"])
    print(max_holding_value)
    print(x)

    return max_holding_value


def complete_year_list(y_list):

    min_y = min(y_list)
    max_y = max(y_list)

    complete_y = []

    for i in range(min_y, max_y + 1):
        complete_y.append(i)

    return complete_y


def extend_pivot_header(pivot_df, y_list, filled_value):

    incomplete_y = pivot_df.columns
    complete_y = complete_year_list(y_list)

    for el in incomplete_y:
        complete_y.remove(el)

    missing_y = complete_y

    for y in missing_y:
        pivot_df[y] = filled_value

    pivot_df = pivot_df.reindex(sorted(pivot_df.columns), axis=1)

    return pivot_df


def check_new_ccy(df, col_to_check):

    dff = df.copy()
    ccy_list = list(np.array(dff[col_to_check].unique()))
    intersect_crypto = list(set(CRYPTO_LIST).intersection(ccy_list))
    print(intersect_crypto)
    intersect_fiat = list(set(FIAT_LIST).intersection(ccy_list))
    intersect = intersect_crypto.extend(intersect_fiat)
    if len(intersect) < len(ccy_list):
        new_ccy = list(set(ccy_list) - set(intersect))
        print(new_ccy)
        errstr = "There is a new currency/s to register: " + new_ccy
        return errstr
    else:
        return True


def get_key(dict_, val):

    for key, value in dict_.items():
        for val_ in value:
            if val == val_:
                return key

    return "no_values"


def define_trade_type(db_):

    db_["TradeType"] = [get_key(TRADE_TYPE, x) for x in db_["FlowType_Num"]]

    return db_
