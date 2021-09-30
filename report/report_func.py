import pandas as pd
import numpy as np
from datetime import datetime

from report.config import DEPO_DF_HEADER, TRANSACTION_DF_HEADER, FIAT_LIST, CRYPTO_LIST


# ### Gains and losses view ###

# --- transaction df -------

def define_trans_df(client_db):

    db = client_db.copy()
    db = db.loc[db.TradeType == "Trade"]

    header, crypto_list, crypto_ext = complete_header(db)
    trans_df = pd.DataFrame(columns=header)
    trans_df = double_op_mngm(db, trans_df)
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

        trans_df.loc[trans_df.Trade_Num == t, "Exchange_Rate"] = abs(num/den)

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

    dff["DateString"] = [x[:19] for x in dff["Date"]]
    dff["Date"] = [datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
                   for x in dff["DateString"]]
    dff.sort_values(by=['Date'], inplace=True, ascending=True)

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
    # print(sell_trade)
    # print(selled_amount)
    num = 0
    for index, row in previuos_df.iterrows():

        trade_num = row["Trade_Num"]
        exc_rate = row["Exchange_Rate"]
        exc_art = row["Art_Exchange_Rate"]
        # row_amount = row[selled_crypto]
        row_amount = row[selled_crypto_res]

        if row[selled_crypto_res] > 0:

            res = row[selled_crypto_res] - selled_amount_res
            if res >= 0:
                tot_df.loc[tot_df.Trade_Num ==
                           trade_num, selled_crypto_res] = res
                num = num + exc_art*selled_amount_res
                # print("maggiore")
                # print(row_amount)
                # print(selled_amount_res)
                # print(exc_art)
                # print(num)
                break
            else:
                tot_df.loc[tot_df.Trade_Num ==
                           trade_num, selled_crypto_res] = 0
                num = num + exc_art*row_amount
                # print("minore")
                # print(row_amount)
                # print(exc_art)
                # print(num)
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


# def LIFO_logic(trans_df):

#     # find all fiat used for operation
#     col_list = trans_df.columns
#     fiat_op_list = list(set(FIAT_LIST).intersection(col_list))
#     crypto_op_list = list(set(CRYPTO_LIST).intersection(col_list))

#     for fiat in fiat_op_list:

#         buy_crypto_df = trans_df.loc[trans_df[fiat] < 0]
#         sell_crypto_df = trans_df.loc[trans_df[fiat] > 0]

#         for index, row in sell_crypto_df.iterrows():

#             sell_date = np.array(row["date"])
#             sell_no_nan = row.dropna(axis=1)
#             sell_no_nan_col = sell_no_nan.columns
#             crypto_selled = list(
#                 set(CRYPTO_LIST).intersection(sell_no_nan_col))[0]
#             other_crypto = crypto_op_list.remove(crypto_selled)

#             buy_crypto_spec = buy_crypto_df.drop(columns=other_crypto)

#     return None


# def LIFO_crypto_crypto():

#     return None


# ##########################################

# ### DEPOSIT AND WITHDRAWAL VIEW ------------


def define_dep_wit_df(client_db):

    db = client_db.copy()

    db["DateString"] = [x[:19] for x in db["Date"]]
    db["Date"] = [datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
                  for x in db["DateString"]]

    sub_db_1 = db.loc[db.FlowType_Num == "1"]
    sub_db_2 = db.loc[db.FlowType_Num == "7"]
    sub_db = sub_db_1.append(sub_db_2)

    sub_db.sort_values(by=['Date'], inplace=True, ascending=True)

    df = pd.DataFrame(columns=DEPO_DF_HEADER)
    df["Action"] = sub_db["FlowType"]
    df["Currency"] = sub_db["Currency"]
    df["Year"] = [x.year for x in sub_db["Date"]]
    df["Date"] = sub_db["Date"]
    df["Exchange"] = sub_db["Exchange"]
    df["Amount"] = sub_db["Price"]

    return df


# ##########################################

# ### FLOWS VIEW ------------
