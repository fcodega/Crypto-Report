from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from report.api import report_rates
from report.config import (CRYPTO_LIST, DEPO_DF_HEADER, FIAT_LIST,
                           TRANSACTION_DF_HEADER)
from report.db_func import compile_total_db
from report.excel_func import report_to_excel
from report.general_func import extend_pivot_header, taxation_db

# ##### report launcher ########


def report_launch(client_name, output_name, lang, **kwargs):
    '''
    ouput name variable is a string that has to finish with .xlsx
    each variable has to be named e.g. trt_df = file name
    variable names (keys) for raw files are: trt_df, pro_df, bit_df, coin_df
    and for hype is: hype_db

    '''

    tot_db = compile_total_db(lang, **kwargs)
    
    # gains and losses
    g_view = gains_and_losses_view(tot_db)

    # depo and withdraw
    depo_view = define_dep_wit_df(tot_db)

    # flows view
    flow_view, c_list, y_list = define_flows_view(tot_db)

    # summary view
    fiat_fund, fiat_inv, crypto_hold, trading = summary_view(tot_db, g_view)

    spec_path_tot = Path("output", output_name)

    report_to_excel(client_name, spec_path_tot, lang, tot_db, g_view,
                    depo_view, flow_view, c_list, y_list, fiat_fund,
                    fiat_inv, crypto_hold, trading)


# ### Summary View #####

def summary_fiat(client_db, typology):

    db = client_db.copy()
    db["Year"] = [x.year for x in db["Date"]]
    year_list = list(np.array(db["Year"].unique()))

    list_of_ccy = list(np.array(db["Currency"].unique()))
    only_fiat = list(set(FIAT_LIST).intersection(list_of_ccy))

    db_fiat = db.loc[db.Currency.isin(only_fiat)]

    if typology == "funding":
        f_num_1 = "1"
        f_num_2 = "7"
        sub_db = db_fiat.loc[(db_fiat.FlowType_Num == f_num_1) |
                             (db_fiat.FlowType_Num == f_num_2)]
    elif typology == "investment":
        f_num_1 = "5"
        f_num_2 = "3"
        f_num_3 = "6"
        sub_db = db_fiat.loc[(db_fiat.FlowType_Num == f_num_1) |
                             (db_fiat.FlowType_Num == f_num_2) |
                             (db_fiat.FlowType_Num == f_num_3)]

    sub_db.sort_values(by=['Date'], inplace=True, ascending=True)
    if typology == "investment":
        sub_db["Price"] = [-x for x in sub_db["Price"]]

    grouped = sub_db.groupby(by=["Currency", "Year"]).sum()
    grouped = grouped.reset_index(level=['Currency', 'Year'])

    fiat_pivot = grouped.pivot(
        index=["Currency"], columns="Year", values="Price")

    fiat_pivot = extend_pivot_header(fiat_pivot, year_list, 0.0)

    return fiat_pivot


def summary_crypto(client_db):

    db = client_db.copy()
    db["Year"] = [x.year for x in db["Date"]]
    year_list = list(np.array(db["Year"].unique()))

    list_of_ccy = list(np.array(db["Currency"].unique()))
    only_crypto = list(set(CRYPTO_LIST).intersection(list_of_ccy))

    db_crypto = db.loc[db.Currency.isin(only_crypto)]

    sub_db = db_crypto.loc[(db_crypto.FlowType_Num == "6") |
                           (db_crypto.FlowType_Num == "4") |
                           (db_crypto.FlowType_Num == "5") |
                           (db_crypto.FlowType_Num == "3") |
                           (db_crypto.FlowType_Num == "2")
                           ]
    sub_db.sort_values(by=['Date'], inplace=True, ascending=True)

    grouped = sub_db.groupby(by=["Currency", "Year"]).sum()
    grouped = grouped.reset_index(level=['Currency', 'Year'])

    crypto_pivot = grouped.pivot(
        index=["Currency"], columns="Year", values="Price")

    crypto_pivot = extend_pivot_header(crypto_pivot, year_list, 0.0)
    crypto_pivot = crypto_pivot.fillna(0.0)

    return crypto_pivot


def summary_trading(client_db, gain_loss_view):

    db = client_db.copy()
    gl = gain_loss_view.copy()

    db["Year"] = [x.year for x in db["Date"]]
    gl["Year"] = [x.year for x in gl["Date"]]
    year_list = list(np.array(db["Year"].unique()))

    grouped = gl.groupby(by=["Year"]).sum()
    grouped = grouped.reset_index(level=['Year'])
    grouped = grouped[["Year", "Gain/Loss"]]
    grouped["Currency"] = "EUR"
    trading_pivot = grouped.pivot(
        index=["Currency"], columns="Year", values="Gain/Loss")

    trading_pivot = extend_pivot_header(trading_pivot, year_list, 0.0)
    trading_pivot = trading_pivot.fillna(0.0)

    return trading_pivot


def summary_view(client_db, gain_loss_view):

    fiat_fund = summary_fiat(client_db, "funding")
    fiat_inv = summary_fiat(client_db, "investment")
    crypto_hold = summary_crypto(client_db)
    trading = summary_trading(client_db, gain_loss_view)

    return fiat_fund, fiat_inv, crypto_hold, trading


# ### Gains and losses view ###

# --- transaction df -------


def define_trans_df(client_db, exc_rates_df):

    db = client_db.copy()
    db = db.loc[db.TradeType == "Trade"]

    db["Date_str"] = [pd.to_datetime(str(x)) for x in db["Date"]]
    db["Date_str"] = [datetime.strftime(x, "%Y-%m-%d") for x in db["Date_str"]]
    db["Original Currency"] = db["Currency"]
    rates = exc_rates_df.drop(columns=["Currency", "Date"])
    merged_db = pd.merge(db, rates, how="left", on="Date_str")
    merged_db.loc[merged_db.Currency == "USD",
                  "Price"] = merged_db.loc[merged_db.Currency == "USD", "Price"] / merged_db.loc[merged_db.Currency == "USD", "Rate"]
    merged_db.loc[merged_db.Currency == "USD", "Currency"] = "EUR"
    header, crypto_list, crypto_ext = complete_header(merged_db)
    trans_df = pd.DataFrame(columns=header)
    trans_df = double_op_mngm(merged_db, trans_df)
    for i, element in enumerate(crypto_ext):
        trans_df[element] = trans_df[crypto_list[i]]
    trans_df["Art_Exchange_Rate"] = trans_df["Exchange_Rate"]

    return trans_df


def complete_header(client_db):

    db = client_db.copy()

    list_of_ccy = list(np.array(db["Currency"].unique()))
    only_crypto = list(set(CRYPTO_LIST).intersection(list_of_ccy))
    only_crypto_ext = [x+"_residual" for x in only_crypto]

    header_list = TRANSACTION_DF_HEADER
    header_list.extend(list_of_ccy)
    header_list.append("Exchange_Rate")
    header_list.append("Art_Exchange_Rate")
    header_list.append("LIFO_avg_cost")
    header_list.append("Gain/Loss")
    header_list.extend(only_crypto_ext)

    return header_list, only_crypto, only_crypto_ext


def double_op_mngm(client_db, trans_df):

    list_of_trade = list(np.array(client_db["Trade_Num"].unique()))
    trans_df["Trade_Num"] = np.array(client_db["Trade_Num"].unique())

    for t in list_of_trade:

        double_op = client_db.loc[client_db.Trade_Num == t]

        date = np.array(double_op.head(1)["Date"])[0]
        exchange = np.array(double_op.head(1)["Exchange"])[0]

        trans_df.loc[trans_df.Trade_Num == t, "Date"] = date
        trans_df.loc[trans_df.Trade_Num == t, "Exchange"] = exchange

        first_ccy = np.array(double_op.head(1)["Currency"])[0]
        first_amount = np.array(double_op.head(1)["Price"])[0]
        second_ccy = np.array(double_op.tail(1)["Currency"])[0]
        second_amount = np.array(double_op.tail(1)["Price"])[0]
        trans_df.loc[trans_df.Trade_Num == t, first_ccy] = first_amount
        trans_df.loc[trans_df.Trade_Num == t, second_ccy] = second_amount
        if first_ccy in FIAT_LIST:
            num = first_amount
            den = second_amount
        else:
            if second_ccy in FIAT_LIST:
                num = second_amount
                den = first_amount
            else:
                num = first_amount
                den = second_amount

        exc_rate = abs(num/den)
        if exc_rate == np.Inf:
            print("infinity")
            exc_rate = 0.0
        else:
            pass
        trans_df.loc[trans_df.Trade_Num == t, "Exchange_Rate"] = exc_rate

    return trans_df


# --- gains and losses df -------


def sell_bought_finder(df):

    no_nan = df.dropna()
    no_nan_col = no_nan.index
    no_nan_col = list(set(CRYPTO_LIST).intersection(no_nan_col))

    if len(no_nan_col) == 2:

        first_ccy = no_nan_col[0]
        second_ccy = no_nan_col[1]
        if df[first_ccy] < 0:
            selled_crypto = first_ccy
            selled_amount = df[first_ccy]
            bought_crypto = second_ccy
            bought_amount = df[second_ccy]
        else:
            selled_crypto = second_ccy
            selled_amount = df[second_ccy]
            bought_crypto = first_ccy
            bought_amount = df[first_ccy]

        return selled_crypto, selled_amount, bought_crypto, bought_amount

    elif len(no_nan_col) == 1:

        first_ccy = "EUR"
        second_ccy = no_nan_col[0]

        selled_crypto = second_ccy
        selled_amount = df[second_ccy]
        bought_crypto = first_ccy
        bought_amount = df[first_ccy]

        return selled_crypto, selled_amount, bought_crypto, bought_amount


def LIFO_definition(trans_df):

    dff = trans_df.copy()
    dff.sort_values(by=['Date', "Trade_Num"],
                    inplace=True, ascending=[True, True])

    for index, row in dff.iterrows():

        if row["EUR"] < 0:
            pass
        elif row["EUR"] is np.NaN:

            sell_trade = row["Trade_Num"]
            sell_date = row["Date"]

            (selled_crypto, selled_amount, _,
             bought_amount) = sell_bought_finder(row)

            dff = LIFO_search_residual(
                dff, selled_crypto, selled_amount, bought_amount, sell_date, sell_trade, typology="crypto-crypto")

        elif row["EUR"] > 0:

            sell_trade = row["Trade_Num"]
            sell_date = row["Date"]

            (selled_crypto, selled_amount, _,
             bought_amount) = sell_bought_finder(row)

            dff = LIFO_search_residual(
                dff, selled_crypto, selled_amount, bought_amount, sell_date, sell_trade, typology="fiat-crypto")

    return dff


def LIFO_search_residual(tot_df, selled_crypto, selled_amount, bought_amount, sell_date, sell_trade, typology):

    previuos_df = tot_df.loc[tot_df.Date < sell_date]
    previuos_df = previuos_df.fillna(0)
    previuos_df.sort_values(by=['Date'], inplace=True, ascending=False)

    selled_crypto_res = selled_crypto + "_residual"
    selled_amount_res = abs(selled_amount)

    exc_art_sell = tot_df.loc[tot_df.Trade_Num ==
                              sell_trade, "Art_Exchange_Rate"]

    num = 0
    for index, row in previuos_df.iterrows():

        trade_num = row["Trade_Num"]
        exc_rate = row["Exchange_Rate"]
        exc_art = row["Art_Exchange_Rate"]
        row_amount = row[selled_crypto_res]

        if row[selled_crypto_res] > 0:

            res = row[selled_crypto_res] - selled_amount_res
            if res >= 0:
                tot_df.loc[tot_df.Trade_Num ==
                           trade_num, selled_crypto_res] = res
                num = num + exc_art*selled_amount_res

                break
            else:
                tot_df.loc[tot_df.Trade_Num ==
                           trade_num, selled_crypto_res] = 0
                num = num + exc_art*row_amount

                selled_amount_res = abs(res)

    if typology == "crypto-crypto":

        artificial_exc = num/bought_amount
        tot_df.loc[tot_df.Trade_Num == sell_trade,
                   "Art_Exchange_Rate"] = artificial_exc

    elif typology == "fiat-crypto":
        lifo_cost = num / abs(selled_amount)
        tot_df.loc[tot_df.Trade_Num == sell_trade,
                   "LIFO_avg_cost"] = lifo_cost
        tot_df.loc[tot_df.Trade_Num == sell_trade,
                   "Gain/Loss"] = (exc_art_sell - lifo_cost)*abs(selled_amount)

    return tot_df


# ---- final result

def gains_and_losses_view(input_db):

    db = input_db.copy()
    exc_rate = report_rates(input_db)
    transaction_df = define_trans_df(db, exc_rate)
    view_df = LIFO_definition(transaction_df)
    view_df["Date"] = [pd.to_datetime(str(x)) for x in view_df["Date"]]

    return view_df

# ##########################################

# ### DEPOSIT AND WITHDRAWAL VIEW ------------


def define_dep_wit_df(client_db):

    db = client_db.copy()
    db_fiat = db.loc[(db.Currency == "EUR") | (db.Currency == "USD")]
    sub_db = db_fiat.loc[(db_fiat.FlowType_Num == "1") |
                         (db_fiat.FlowType_Num == "7")]
    sub_db.sort_values(by=['Date'], inplace=True, ascending=True)

    df = pd.DataFrame(columns=DEPO_DF_HEADER)
    df["Action"] = sub_db["FlowType"]
    df["Currency"] = sub_db["Currency"]
    df["Year"] = [x.year for x in sub_db["Date"]]
    df["Date"] = sub_db["Date"]
    df["Exchange"] = sub_db["Exchange"]
    df["Amount"] = sub_db["Price"]

    df = df[DEPO_DF_HEADER]

    return df


# ##########################################

# ### FLOWS VIEW ------------

def define_flows_view(client_total_db):

    db = client_total_db.copy()

    db["Year"] = [x.year for x in db["Date"]]

    db = db.groupby(by=["Currency", "Year", "FlowType"]).sum()
    db = db.reset_index(level=['Currency', 'Year', "FlowType"])

    currency_list = list(np.array(db["Currency"].unique()))
    year_list = list(np.array(db["Year"].unique()))

    flow_pivot = db.pivot(
        index=["Currency", "FlowType"], columns="Year", values="Price")

    return flow_pivot, currency_list, year_list
