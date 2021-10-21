from datetime import datetime
from logging import exception
from pathlib import Path
import os
import locale
from locale import atof
from typing import final

import numpy as np
import pandas as pd
from tabula import read_pdf

from report.config import (BITSTAMP_CSV_HAEDER, BITSTAMP_MONTH,
                           CRYPTO_FIAT_DICT, CRYPTO_LIST, DB_HEADER, FIAT_LIST,
                           FLOW_TYPE_DICT, TRADE_TYPE, TRT_DICT, TRT_DICT_LANG)
from report.general_func import check_new_ccy

# ----
# general


def get_key(dict_, val):

    for key, value in dict_.items():
        for val_ in value:
            if val == val_:
                return key

    return "no_values"


def define_trade_type(db_):

    db_["TradeType"] = [get_key(TRADE_TYPE, x) for x in db_["FlowType_Num"]]

    return db_


def compile_total_db(lang, **kwargs):
    '''
    each variable has to be named e.g. trt_df = file name
    variable names (keys) for raw files are: trt_df, pro_df, bit_df, coin_df
    and for hype is: hype_db
    and for coinbase PDF is: coin_pdf

    '''

    input_list = []

    for key, value in kwargs.items():

        if key == "trt_df":
            try:
                trt = pd.read_csv(Path("input", value))
                trt = trt.fillna("0")
                trt_db = trt_compile_db(trt, lang)
                input_list.append(trt_db)
            except TypeError:
                pass

        elif key == "pro_df":
            try:
                pro = pd.read_csv(Path("input", value))
                pro_db = coinbasepro_compile_db(pro, lang)
                input_list.append(pro_db)
            except TypeError:
                pass

        elif key == "bit_df":
            try:
                bit = pd.read_csv(Path("input", value),
                                  sep=",")
                bit_db = bitstamp_compile_db(bit, lang)
                input_list.append(bit_db)
            except TypeError:
                pass

        # coinbase transaction history report PDF
        elif key == "coin_df":
            try:
                all_col = pd.read_csv(Path("input", value),
                                      sep='["]*,["]*',
                                      skiprows=7,
                                      # engine='python',
                                      #   usecols=['Timestamp', 'Transaction Type',
                                      #            'Asset', 'Quantity Transacted', 'EUR Spot Price at Transaction',
                                      #            'EUR Subtotal', 'EUR Total (inclusive of fees)', 'EUR Fees']
                                      ).replace('"', '', regex=True)
                print(all_col)
                notes = pd.read_csv(Path("input", value),
                                    sep='["]*,["]*',
                                    skipinitialspace=True,
                                    skiprows=7,
                                    usecols=['Notes']
                                    ).replace(',', '', regex=True)
                all_col["Notes"] = notes["Notes"]
                coin = all_col.copy()

                print(notes)
                coin_db = coinbase_transaction_compile_db(coin, lang)
                input_list.append(coin_db)
            except TypeError:
                pass

        # coinbase transaction history report PDF
        elif key == "coin_transaction_pdf":
            try:
                box = [0, 0, 30 * 28.28, 30 * 28.28]
                raw_trans_0 = read_pdf(Path("input", value), pages=1, area=box)
                raw_trans_tot = read_pdf(
                    Path("input", value), pages='all', area=box)
                coin = coinbase_transaction_pdf_reading(
                    raw_trans_0, raw_trans_tot)
                print(coin)
                coin_db = coinbase_transaction_compile_db(coin, lang)
                input_list.append(coin_db)
            except TypeError:
                pass

        # coinbase Account statement report PDF
        elif key == "coin_account_pdf":
            try:
                raw_coin_pdf = read_pdf(Path("input", value), pages='all')
                coin_pdf = coinbase_account_pdf_reading(raw_coin_pdf)
                coin_pdf_db = coinbase_pdf_compile_db(coin_pdf, lang)
                input_list.append(coin_pdf_db)
            except TypeError:
                pass

        elif key == "hype_db":
            try:
                hype_db = pd.read_excel(
                    Path("input", value), index_col=0)
                hype_db = hype_check_db(hype_db)
                input_list.append(hype_db)
            except TypeError:
                pass

    try:
        total_db = pd.concat(input_list)
        total_db.sort_values(by=['Date', "Trade_Num"],
                             inplace=True, ascending=[True, True])
        total_db.reset_index(drop=True, inplace=True)
    except ValueError:
        errstr = "No input given, use the correct variable names"
        raise ValueError(errstr)

    return total_db

# -------
# The Rock Trading


def trt_compile_db(input_df, lang):

    dff = input_df.copy()
    dff["ID"] = dff.index

    trt_db = pd.DataFrame(columns=DB_HEADER)

    trt_db["ID"] = dff["ID"]
    trt_db["Date"] = dff["Date"]
    trt_db["Exchange"] = "TRT"
    trt_db["Currency"] = dff["Currency"]
    trt_db["Price"] = dff["Price"]
    trt_db["Trade_Num"] = ["trt_" + str(int(x)) for x in dff["Trade"]]
    trt_db = trt_define_flowtype(dff, trt_db, lang)
    trt_db = define_trade_type(trt_db)
    trt_db = trt_depo_with_trade_num(trt_db)

    trt_db["DateString"] = [x[:19] for x in trt_db["Date"]]
    trt_db["Date"] = [datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
                      for x in trt_db["DateString"]]

    return trt_db


def trt_define_flowtype(df, trt_db, lang):

    dff = df.copy()
    df_w_key = trt_key_constructor(dff)

    trt_db["FlowType"] = df_w_key["Key"].apply(
        lambda x: TRT_DICT_LANG.get(lang).get(x))

    trt_db = trt_fastlane_detect(df_w_key, trt_db, lang)
    try:

        trt_db["FlowType_Num"] = [str(x[0:1]) for x in trt_db["FlowType"]]
    except TypeError:
        errstr = "New 'Type' on The Rock Trading input file"
        raise ValueError(errstr)

    return trt_db


def trt_fastlane_detect(df, trt_db, lang):

    dff = df.copy()

    t_id = 1
    for index, row in dff.iterrows():

        row_note = row["Note"]

        if row_note[:8] == "FASTLANE":
            row_date = row["Date"]
            op_rows = dff.loc[dff.Date == row_date]
            op_rows["FlowType"] = op_rows["Type"].apply(
                lambda x: TRT_DICT.get(lang).get(x))
            trt_db.loc[trt_db.Date == row_date,
                       "FlowType"] = op_rows["FlowType"]
            trt_db.loc[trt_db.Date == row_date,
                       "Trade_Num"] = "trt_fast_" + str(t_id)
            t_id = t_id + 1

    return trt_db


def trt_key_constructor(df):

    dff = df.copy()

    dff["Pair"] = [get_key(CRYPTO_FIAT_DICT, x[:3]) + "-" +
                   get_key(CRYPTO_FIAT_DICT, x[3:]) for x in dff["Fund"]]
    dff.loc[dff['Pair'] == "no_values-no_values",
            'Pair'] = "Deposits, withdrawals, fees, transfers"
    dff["Key"] = dff["Pair"] + "_" + dff["Type"]

    return dff


def trt_depo_with_trade_num(df):

    dff = df.copy()
    dff.loc[dff.FlowType_Num == "1", "Trade_Num"] = "trt_depo"

    dff.loc[dff.FlowType_Num == "7", "Trade_Num"] = "trt_withdraw"

    return dff

# --------------------
# Coinbase CSV Report
# --------------------


def coinbase_transaction_compile_db(input_df, lang):

    df = input_df.copy()

    conv = coin_conversion_op(df, lang)
    buy = coin_buy_op(df, lang)
    sell = coin_sell_op(df, lang)
    db = conv.append([buy, sell])

    db["DateString"] = [x[:19] for x in db["Date"]]
    db["Date"] = [datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
                  for x in db["DateString"]]

    db["Exchange"] = "Coinbase"
    # check_new_ccy(db, "Currency")

    return db


def coin_conversion_op(input_df, lang):

    conv_op = input_df.loc[input_df["Transaction Type"] == "Convert"]
    conv_op.reset_index(drop=True, inplace=True)
    conv_op["ID_"] = conv_op.index
    conv_op["Trade_Num"] = [
        "coin_conversion_" + str(x) for x in conv_op["ID_"]]

    bought = conv_op.copy()
    bought["Quantity Transacted"] = [
        float(x.split(" ")[4]) for x in bought["Notes"]]
    bought["Asset"] = [
        str(x.split(" ")[5]) for x in bought["Notes"]]
    bought["FlowType"] = FLOW_TYPE_DICT.get(lang).get("3")

    sold = conv_op.copy()
    sold["Quantity Transacted"] = sold["Quantity Transacted"]*(-1)
    sold["FlowType"] = FLOW_TYPE_DICT.get(lang).get("5")

    fee = conv_op.copy()
    fee["Quantity Transacted"] = fee["EUR Fees"]
    fee["Asset"] = "EUR"
    fee["FlowType"] = FLOW_TYPE_DICT.get(lang).get("6")

    conv_tot = bought.append([sold, fee])
    conv_tot["ID"] = conv_tot.index

    conv_db = pd.DataFrame(columns=DB_HEADER)
    conv_db["Exchange"] = "Coinbase"
    conv_db["Date"] = conv_tot["Timestamp"]
    conv_db["Currency"] = conv_tot["Asset"]
    conv_db["Price"] = conv_tot["Quantity Transacted"]
    conv_db["ID"] = conv_tot["ID"]
    conv_db["Trade_Num"] = conv_tot["Trade_Num"]
    conv_db["FlowType"] = conv_tot["FlowType"]
    conv_db["FlowType_Num"] = [str(x[0:1]) for x in conv_db["FlowType"]]

    conv_db = define_trade_type(conv_db)

    return conv_db


def coin_buy_op(input_df, lang):

    buy_op = input_df.loc[input_df["Transaction Type"] == "Buy"]
    buy_op["ID_"] = buy_op.index
    buy_op["Trade_Num"] = ["coin_buy_" + str(x) for x in buy_op["ID_"]]

    bought = buy_op.copy()
    bought["FlowType"] = FLOW_TYPE_DICT.get(lang).get("2")

    sold = buy_op.copy()
    sold["Quantity Transacted"] = sold["EUR Subtotal"]*(-1)
    sold["Asset"] = [str(x.split(" ")[5]) for x in sold["Notes"]]
    sold["FlowType"] = FLOW_TYPE_DICT.get(lang).get("5")

    buy_tot = bought.append(sold)
    buy_tot["ID"] = buy_tot.index

    buy_db = pd.DataFrame(columns=DB_HEADER)
    buy_db["Exchange"] = "Coinbase"
    buy_db["Date"] = buy_tot["Timestamp"]
    buy_db["Currency"] = buy_tot["Asset"]
    buy_db["Price"] = buy_tot["Quantity Transacted"]
    buy_db["ID"] = buy_tot["ID"]
    buy_db["Trade_Num"] = buy_tot["Trade_Num"]
    buy_db["FlowType"] = buy_tot["FlowType"]
    buy_db["FlowType_Num"] = [str(x[0:1]) for x in buy_db["FlowType"]]

    buy_db = define_trade_type(buy_db)

    return buy_db


def coin_sell_op(input_df, lang):

    sell_op = input_df.loc[input_df["Transaction Type"] == "Sell"]
    sell_op["ID_"] = sell_op.index
    sell_op["Trade_Num"] = ["coin_sell_" + str(x) for x in sell_op["ID_"]]

    sold = sell_op.copy()
    sold["Quantity Transacted"] = sold["Quantity Transacted"]*(-1)
    sold["FlowType"] = FLOW_TYPE_DICT.get(lang).get("4")

    bought = sell_op.copy()
    bought["Quantity Transacted"] = bought["EUR Subtotal"]
    bought["Asset"] = [str(x.split(" ")[5]) for x in bought["Notes"]]
    bought["FlowType"] = FLOW_TYPE_DICT.get(lang).get("3")

    sell_tot = bought.append(sold)
    sell_tot["ID"] = sell_tot.index

    sell_db = pd.DataFrame(columns=DB_HEADER)
    sell_db["Exchange"] = "Coinbase"
    sell_db["Date"] = sell_tot["Timestamp"]
    sell_db["Currency"] = sell_tot["Asset"]
    sell_db["Price"] = sell_tot["Quantity Transacted"]
    sell_db["ID"] = sell_tot["ID"]
    sell_db["Trade_Num"] = sell_tot["Trade_Num"]
    sell_db["FlowType"] = sell_tot["FlowType"]
    sell_db["FlowType_Num"] = [str(x[0:1]) for x in sell_db["FlowType"]]

    sell_db = define_trade_type(sell_db)

    return sell_db

# ---------------------
#  ----- Coinbase-pro
# ---------------------


def coinbasepro_compile_db(input_df, lang):

    df = input_df.copy()
    depo = pro_depo_op(df, lang)
    w = pro_withdraw_op(df, lang)
    fee = pro_fee_op(df, lang)
    trade = pro_trade_op(df, lang)

    db = depo.append([w, fee, trade])

    db["DateString"] = [x[:19] for x in db["Date"]]
    db["Date"] = [datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
                  for x in db["DateString"]]

    return db


def pro_depo_op(input_df, lang):

    df = input_df.copy()
    depo_df = df.loc[df.type == "deposit"]
    depo_df["ID"] = depo_df.index

    depo_db = pd.DataFrame(columns=DB_HEADER)
    depo_db["Date"] = depo_df["time"]
    depo_db["Exchange"] = "Coinbase-pro"
    depo_db["Currency"] = depo_df["amount/balance unit"]
    depo_db["Price"] = depo_df["amount"]
    depo_db["ID"] = depo_df["ID"]
    depo_db["Trade_Num"] = ["pro_depo_" + str(x) for x in depo_db["ID"]]
    depo_db["FlowType"] = FLOW_TYPE_DICT.get(lang).get("1")
    depo_db["FlowType_Num"] = "1"
    depo_db["TradeType"] = "Other"

    return depo_db


def pro_withdraw_op(input_df, lang):

    df = input_df.copy()
    w_df = df.loc[df.type == "withdrawal"]
    w_df["ID"] = w_df.index

    w_db = pd.DataFrame(columns=DB_HEADER)
    w_db["Date"] = w_df["time"]
    w_db["Exchange"] = "Coinbase-pro"
    w_db["Currency"] = w_df["amount/balance unit"]
    w_db["Price"] = w_df["amount"]
    w_db["ID"] = w_df["ID"]
    w_db["Trade_Num"] = ["pro_withdraw_" + str(x) for x in w_db["ID"]]
    w_db["FlowType"] = FLOW_TYPE_DICT.get(lang).get("7")
    w_db["FlowType_Num"] = "7"
    w_db["TradeType"] = "Other"

    return w_db


def pro_fee_op(input_df, lang):

    df = input_df.copy()
    fee_df = df.loc[df.type == "fee"]
    fee_df["ID"] = fee_df.index

    fee_db = pd.DataFrame(columns=DB_HEADER)
    fee_db["Date"] = fee_df["time"]
    fee_db["Exchange"] = "Coinbase-pro"
    fee_db["Currency"] = fee_df["amount/balance unit"]
    fee_db["Price"] = fee_df["amount"]
    fee_db["ID"] = fee_df["ID"]
    fee_db["Trade_Num"] = ["pro_fee" + str(x) for x in fee_df["trade id"]]
    fee_db["FlowType"] = FLOW_TYPE_DICT.get(lang).get("6")
    fee_db["FlowType_Num"] = "6"
    fee_db["TradeType"] = "Other"

    return fee_db


def pro_trade_op(input_df, lang):

    df = input_df.copy()
    trade_df = df.loc[df.type == "match"]
    trade_df["ID"] = trade_df.index

    trade_df = pro_trade_to_flowtype(trade_df, lang)

    trade_db = pd.DataFrame(columns=DB_HEADER)
    trade_db["Date"] = trade_df["time"]
    trade_db["Exchange"] = "Coinbase-pro"
    trade_db["Currency"] = trade_df["amount/balance unit"]
    trade_db["Price"] = trade_df["amount"]
    trade_db["ID"] = trade_df["ID"]
    trade_db["Trade_Num"] = ["pro_trade_" +
                             str(int(x)) for x in trade_df["trade id"]]
    trade_db["FlowType"] = trade_df["FlowType"]
    trade_db["FlowType_Num"] = [str(x[0:1]) for x in trade_db["FlowType"]]
    trade_db = define_trade_type(trade_db)

    return trade_db


def pro_trade_to_flowtype(input_df, lang):

    input_df["FlowType"] = ""

    trade_id_list = list(np.array(input_df["trade id"].unique()))

    for t in trade_id_list:

        trade_df = input_df.loc[input_df["trade id"] == t]
        ccy_couple = list(np.array(trade_df["amount/balance unit"]))
        if len(list(set(CRYPTO_LIST).intersection(ccy_couple))) == 2:

            for index, row in trade_df.iterrows():
                if row["amount"] < 0:
                    row["FlowType"] = FLOW_TYPE_DICT.get(lang).get("5")
                else:
                    row["FlowType"] = FLOW_TYPE_DICT.get(lang).get("3")

                trade_df.loc[trade_df["amount/balance unit"] ==
                             single_ccy, "FlowType"] = row["FlowType"]

        elif len(list(set(CRYPTO_LIST).intersection(ccy_couple))) == 1:

            for index, row in trade_df.iterrows():
                single_ccy = row["amount/balance unit"]
                if single_ccy in CRYPTO_LIST:
                    if row["amount"] < 0:
                        row["FlowType"] = FLOW_TYPE_DICT.get(lang).get("4")
                    else:
                        row["FlowType"] = FLOW_TYPE_DICT.get(lang).get("2")
                else:
                    if row["amount"] < 0:
                        row["FlowType"] = FLOW_TYPE_DICT.get(lang).get("5")
                    else:
                        row["FlowType"] = FLOW_TYPE_DICT.get(lang).get("3")

                trade_df.loc[trade_df["amount/balance unit"] ==
                             single_ccy, "FlowType"] = row["FlowType"]

        input_df.loc[input_df["trade id"] == t,
                     "FlowType"] = trade_df["FlowType"]

    return input_df

# Bitstamp


def bit_read_csv(pandas_read_csv):

    bit_csv = pandas_read_csv.copy()

    input_df = pd.DataFrame(columns=BITSTAMP_CSV_HAEDER)

    for index, row in bit_csv.iterrows():

        row_list = row[0].split(",")
        last_columns = row_list[4:]
        date_columns = row_list[1:4]
        first_column = [row_list[0]]

        # date part
        year = str(date_columns[1][1:5])
        day = str(date_columns[0][6:8])
        month = date_columns[0][1:4]
        hour = date_columns[2][1:9]
        month_ = get_key(BITSTAMP_MONTH, month)
        date_str = year + "-" + month_ + "-" + day + " " + hour
        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M %p")

        # row construction
        row_ = first_column
        first_column.append(date)
        row_ = first_column
        row_.extend(last_columns)
        df_row = pd.DataFrame([np.array(row_)], columns=BITSTAMP_CSV_HAEDER)
        input_df = input_df.append(df_row)

    return input_df


def bitstamp_compile_db(input_df, lang):

    df = input_df.copy()

    df = bit_read_csv(df)
    bit_db_w = bit_withdraw_op(df, lang)
    bit_db_depo = bit_depo_op(df, lang)
    bit_db_trade = bit_mkt_op(df, lang)
    bitstamp_db = bit_db_w.append([bit_db_depo, bit_db_trade])

    bitstamp_db["DateString"] = [x.strftime(
        "%Y-%m-%d %H:%M:%S") for x in bitstamp_db["Date"]]

    bitstamp_db.reset_index(drop=True, inplace=True)

    return bitstamp_db


def bit_withdraw_op(input_df, lang):

    df = input_df.copy()
    w_df = df.loc[df.Type == "Withdrawal"]
    w_df.reset_index(drop=True, inplace=True)
    w_df["ID_"] = w_df.index
    w_df["Trade_Num"] = ["bit_withdraw_" + str(x) for x in w_df["ID_"]]

    fee_df = w_df.copy()
    fee_df["Amount"] = fee_df["Fee"]
    fee_df["FlowType"] = FLOW_TYPE_DICT.get(lang).get("6")

    w_df["FlowType"] = FLOW_TYPE_DICT.get(lang).get("7")
    total_df = w_df.append(fee_df)
    total_df["ID"] = total_df.index

    w_db = pd.DataFrame(columns=DB_HEADER)
    w_db["Date"] = total_df["Datetime"]
    w_db["Exchange"] = "Bitstamp"
    w_db["Currency"] = [str(x.split(" ")[1]) for x in total_df["Amount"]]
    w_db["Price"] = [float(x.split(" ")[0]) for x in total_df["Amount"]]
    w_db["ID"] = total_df["ID"]
    w_db["Trade_Num"] = total_df["Trade_Num"]
    w_db["FlowType"] = total_df["FlowType"]
    w_db["TradeType"] = "Other"
    w_db["FlowType_Num"] = [str(x[0:1]) for x in w_db["FlowType"]]

    w_db.loc[w_db.FlowType_Num == "7",
             "Price"] = w_db.loc[w_db.FlowType_Num == "7", "Price"]*(-1)
    w_db.loc[w_db.FlowType_Num == "6",
             "Price"] = w_db.loc[w_db.FlowType_Num == "6", "Price"]*(-1)

    return w_db


def bit_depo_op(input_df, lang):

    df = input_df.copy()
    depo_df = df.loc[df.Type == "Deposit"]
    depo_df.reset_index(drop=True, inplace=True)
    depo_df["ID"] = depo_df.index

    depo_db = pd.DataFrame(columns=DB_HEADER)
    depo_db["Date"] = depo_df["Datetime"]
    depo_db["Exchange"] = "Bitstamp"
    depo_db["Currency"] = [str(x.split(" ")[1]) for x in depo_df["Amount"]]
    depo_db["Price"] = [float(x.split(" ")[0]) for x in depo_df["Amount"]]
    depo_db["ID"] = depo_df["ID"]
    depo_db["Trade_Num"] = ["bit_depo_" + str(x) for x in depo_db["ID"]]
    depo_db["FlowType"] = FLOW_TYPE_DICT.get(lang).get("1")
    depo_db["FlowType_Num"] = "1"
    depo_db["TradeType"] = "Other"
    depo_db["FlowType_Num"] = [str(x[0:1]) for x in depo_db["FlowType"]]

    return depo_db


def bit_mkt_op(input_df, lang):

    df = input_df.copy()
    mkt_df = df.loc[df.Type == "Market"]
    mkt_df.reset_index(drop=True, inplace=True)
    mkt_df["ID_"] = mkt_df.index
    mkt_df["Trade_Num"] = ["bit_trade_" + str(x) for x in mkt_df["ID_"]]

    # fees part
    fee_df = mkt_df.copy()
    fee_df["Amount"] = fee_df["Fee"]
    fee_df["FlowType"] = FLOW_TYPE_DICT.get(lang).get("6")

    crypto_df_tot = mkt_df.copy()
    # buy leg
    crypto_buy = crypto_df_tot.loc[crypto_df_tot["Sub Type"] == "Buy"]
    crypto_buy["FlowType"] = FLOW_TYPE_DICT.get(lang).get("2")
    fiat_sell = crypto_buy.copy()
    fiat_sell["Amount"] = crypto_buy["Value"]
    fiat_sell["FlowType"] = FLOW_TYPE_DICT.get(lang).get("5")
    crypto_buy_tot = crypto_buy.append(fiat_sell)

    # sell leg
    crypto_sell = crypto_df_tot.loc[crypto_df_tot["Sub Type"] == "Sell"]
    crypto_sell["FlowType"] = FLOW_TYPE_DICT.get(lang).get("4")
    crypto_sell["Amount"] = crypto_sell["Amount"]
    fiat_buy = crypto_sell.copy()
    fiat_buy["Amount"] = crypto_sell["Value"]
    fiat_buy["FlowType"] = FLOW_TYPE_DICT.get(lang).get("3")
    crypto_sell_tot = crypto_sell.append(fiat_buy)

    total_df = crypto_buy_tot.append([crypto_sell_tot, fee_df])
    total_df["ID"] = total_df.index

    mkt_db = pd.DataFrame(columns=DB_HEADER)
    mkt_db["Date"] = total_df["Datetime"]
    mkt_db["Exchange"] = "Bitstamp"
    mkt_db["Currency"] = [str(x.split(" ")[1]) for x in total_df["Amount"]]
    mkt_db["Price"] = [float(x.split(" ")[0]) for x in total_df["Amount"]]
    mkt_db["ID"] = total_df["ID"]
    mkt_db["Trade_Num"] = total_df["Trade_Num"]
    mkt_db["FlowType"] = total_df["FlowType"]
    mkt_db["FlowType_Num"] = [str(x[0:1]) for x in mkt_db["FlowType"]]

    mkt_db.loc[mkt_db.FlowType_Num == "4",
               "Price"] = mkt_db.loc[mkt_db.FlowType_Num == "4", "Price"]*(-1)
    mkt_db.loc[mkt_db.FlowType_Num == "5",
               "Price"] = mkt_db.loc[mkt_db.FlowType_Num == "5", "Price"]*(-1)
    mkt_db.loc[mkt_db.FlowType_Num == "6",
               "Price"] = mkt_db.loc[mkt_db.FlowType_Num == "6", "Price"]*(-1)

    mkt_db = define_trade_type(mkt_db)

    return mkt_db


# ----
# HYPE

def hype_check_db(hype_db):

    hype_db = hype_db.copy()

    hype_db["FlowType_Num"] = [str(x) for x in hype_db["FlowType_Num"]]
    hype_db["Exchange"] = "Hype"

    return hype_db


# --------------------------------------
# ## Coinbase Account statement Report PDF
# --------------------------------------

def coinbase_pdf_compile_db(input_df, lang):

    df = input_df.copy()

    df_clean = coinbase_pdf_cleaning(df)
    depo_db = coinbase_pdf_depo_op(df_clean, lang)
    with_db = coinbase_pdf_withdraw_op(df_clean, lang)
    air_db = coinbase_pdf_airdrop_op(df_clean, lang)

    db = depo_db.append([with_db, air_db])
    db["Date"] = [datetime.strptime(x, "%m/%d/%Y")
                  for x in db["Date"]]
    db["Exchange"] = "Coinbase"
    # check_new_ccy(db, "Currency")

    return db


def coinbase_account_pdf_reading(raw_df):

    df_raw = raw_df.copy()

    header_list = ["Date", "Account",
                   "Transaction", "Amount",
                   "Amount(USD)", "Balance"]
    df = pd.DataFrame(columns=header_list)
    for i in range(0, len(df_raw)):
        i_part = df_raw[i]
        clean_df = i_part.replace('\r', ' ', regex=True)
        clean_df = clean_df.rename(columns={'Amount\r(USD)': "Amount(USD)",
                                            'Amount (USD)': "Amount(USD)"})
        if list(clean_df.columns) == header_list:
            df = df.append(clean_df)

    df.reset_index(inplace=True, drop=True)

    return df


def coinbase_pdf_cleaning(df):

    dff = df.copy()
    dff.reset_index(drop=True, inplace=True)

    dff["ID"] = dff.index
    dff["Type"] = "tbd"
    dff["Currency"] = "tbd"
    dff["Amount_"] = "tbd"
    dff["Currency_2"] = "tbd"
    dff["Amount_2"] = "tbd"

    dff = dff.replace('€', '', regex=True)

    for index, row in dff.iterrows():

        row_id = row["ID"]
        try:
            if row["Transaction"].split(" ")[1] == "sent":
                row["Type"] = "Sent"
            elif row["Transaction"].split(" ")[1] == "received":
                if row["Transaction"].split(" ")[
                        len(row["Transaction"].split(" ")) - 1] == "Coinbase":
                    row["Type"] = "Airdrop"
                elif row["Transaction"].split(" ")[
                        len(row["Transaction"].split(" ")) - 1] == "Referral":
                    print("referral found")
                    row["Type"] = "Airdrop"
                elif ((row["Transaction"].split(" ")[3] == "Cash") & (row["Date"] == "12/14/2017")):
                    print("BCH hard fork found")
                    row["Type"] = "Airdrop"
                else:
                    row["Type"] = "Received"
            elif row["Transaction"].split(" ")[1] == "deposited":
                row["Type"] = "Deposit"
            elif row["Transaction"].split(" ")[1] == "transferred":
                row["Type"] = "Transfer"
            elif row["Transaction"].split(" ")[1] == "purchased":
                row["Type"] = "Trade"
            elif row["Transaction"].split(" ")[1] == "sold":
                row["Type"] = "Trade"
            elif row["Transaction"].split(" ")[1] == "withdrew":
                row["Type"] = "Withdrawal"
            # this one has to be the last #
            elif row["Transaction"].split(" ")[3] == "withdrawal":
                row["Type"] = "Withdrawal"
        except IndexError:
            key = row["Transaction"]
            errstr = "New 'Transaction' on Coinbase PDF input file: '" + key + "'"
            raise KeyError(errstr)

        row["Amount_"] = row["Amount"].split(" ")[0]
        row["Currency"] = row["Amount"].split(" ")[1]
        row["Amount_2"] = row["Amount(USD)"].split(" ")[0]
        row["Currency_2"] = row["Amount(USD)"].split(" ")[1]

        dff.loc[dff.ID == row_id, "Type"] = row["Type"]
        dff.loc[dff.ID == row_id, "Amount_"] = row["Amount_"]
        dff.loc[dff.ID == row_id, "Currency"] = row["Currency"]
        dff.loc[dff.ID == row_id, "Amount_2"] = row["Amount_2"]
        dff.loc[dff.ID == row_id, "Currency_2"] = row["Currency_2"]

    dff["Amount_"] = [float(x.replace(',', '')) for x in dff["Amount_"]]
    dff["Amount_2"] = [float(x.replace(',', '')) for x in dff["Amount_2"]]
    dff.loc[(dff.Type == "Transfer") & (
        dff.Amount_ < 0), "Type"] = "Withdrawal"
    dff.loc[(dff.Type == "Transfer") & (
        dff.Amount_ > 0), "Type"] = "Deposit"

    dff = dff.drop(columns=["Balance", "Amount", "Amount(USD)", "ID"])
    dff = dff.rename(columns={"Amount_": "Amount"})

    return dff


def coinbase_pdf_airdrop_op(input_df, lang):

    df = input_df.copy()
    df = df.drop(columns=["Transaction", "Currency_2", "Amount_2"])

    air_df = df.loc[df.Type == "Airdrop"]
    air_df.reset_index(drop=True, inplace=True)
    air_df["ID"] = air_df.index
    air_df["Trade_Num"] = ["coin_airdrop_" + str(x) for x in air_df["ID"]]

    buy_leg = air_df.copy()
    buy_leg["FlowType"] = FLOW_TYPE_DICT.get(lang).get("2")
    buy_leg["FlowType_Num"] = "2"

    sell_leg = air_df.copy()
    sell_leg["FlowType"] = FLOW_TYPE_DICT.get(lang).get("5")
    sell_leg["FlowType_Num"] = "5"
    sell_leg["Currency"] = "EUR"
    sell_leg["Amount"] = 0.00
    print(sell_leg)
    air_tot = buy_leg.append(sell_leg)
    air_tot.reset_index(drop=True, inplace=True)
    print(air_tot)
    air_db = pd.DataFrame(columns=DB_HEADER)
    air_db["Date"] = air_tot["Date"]
    air_db["Exchange"] = "Coinbase"
    air_db["Currency"] = air_tot["Currency"]
    air_db["Price"] = air_tot["Amount"]
    air_db["ID"] = air_tot.index
    air_db["FlowType_Num"] = air_tot["FlowType_Num"]
    air_db["FlowType"] = air_tot["FlowType"]
    air_db["Trade_Num"] = air_tot["Trade_Num"]
    air_db["TradeType"] = "Trade"

    return air_db


def coinbase_pdf_depo_op(input_df, lang):

    df = input_df.copy()
    df = df.drop(columns=["Transaction", "Currency_2", "Amount_2"])

    depo_df = df.loc[(df.Type == "Deposit") | (df.Type == "Received")]
    depo_df.reset_index(drop=True, inplace=True)
    depo_df["ID"] = depo_df.index

    depo_db = pd.DataFrame(columns=DB_HEADER)
    depo_db["Date"] = depo_df["Date"]
    depo_db["Exchange"] = "Coinbase"
    depo_db["Currency"] = depo_df["Currency"]
    depo_db["Price"] = depo_df["Amount"]
    depo_db["ID"] = depo_df["ID"]
    depo_db["Trade_Num"] = ["coin_depo_" + str(x) for x in depo_db["ID"]]
    depo_db["FlowType"] = FLOW_TYPE_DICT.get(lang).get("1")
    depo_db["FlowType_Num"] = "1"
    depo_db["TradeType"] = "Other"

    return depo_db


def coinbase_pdf_withdraw_op(input_df, lang):

    df = input_df.copy()
    df = df.drop(columns=["Transaction", "Currency_2", "Amount_2"])

    w_df = df.loc[(df.Type == "Sent") | (df.Type == "Withdrawal")]
    w_df.reset_index(drop=True, inplace=True)
    w_df["ID"] = w_df.index

    w_db = pd.DataFrame(columns=DB_HEADER)
    w_db["Date"] = w_df["Date"]
    w_db["Exchange"] = "Coinbase"
    w_db["Currency"] = w_df["Currency"]
    w_db["Price"] = w_df["Amount"]
    w_db["ID"] = w_df["ID"]
    w_db["Trade_Num"] = ["coin_withdraw_" + str(x) for x in w_db["ID"]]
    w_db["FlowType"] = FLOW_TYPE_DICT.get(lang).get("7")
    w_db["FlowType_Num"] = "7"
    w_db["TradeType"] = "Other"

    return w_db


# def coinbase_pdf_trade_op(input_df, lang):

#     df = input_df.copy()
#     df = df.drop(columns=["Transaction", "Currency_2", "Amount_2"])

#     air_df = df.loc[df.Type == "Trade"]
#     air_df.reset_index(drop=True, inplace=True)
#     air_df["ID"] = air_df.index
#     air_df["Trade_Num"] = ["coin_airdrop_" + str(x) for x in air_df["ID"]]

#     buy_leg = air_df.copy()
#     buy_leg["FlowType"] = FLOW_TYPE_DICT.get(lang).get("2")
#     buy_leg["FlowType_Num"] = "2"

#     sell_leg = air_df.copy()
#     sell_leg["FlowType"] = FLOW_TYPE_DICT.get(lang).get("5")
#     sell_leg["FlowType_Num"] = "5"
#     sell_leg["Currency"] = "EUR"
#     sell_leg["Price"] = 0

#     air_tot = buy_leg.append(sell_leg)
#     air_tot.reset_index(drop=True, inplace=True)

#     air_db = pd.DataFrame(columns=DB_HEADER)
#     air_db["Date"] = air_tot["Date"]
#     air_db["Exchange"] = "Coinbase"
#     air_db["Currency"] = air_tot["Currency"]
#     air_db["Price"] = air_tot["Amount"]
#     air_db["ID"] = air_tot.index
#     air_db["FlowType_Num"] = air_tot["FlowType_Num"]
#     air_db["FlowType"] = air_tot["FlowType"]
#     air_db["Trade_Num"] = air_tot["Trade_Num"]
#     air_db["TradeType"] = "Trade"

#     return trade_db

# -----------------------------
# coinbase transaction history report PDF
# --------------------------------
def coinbase_transaction_pdf_reading(raw_df_first_page, raw_df_all):

    df_raw = raw_df_first_page.copy()
    df_raw_all = raw_df_all.copy()

    for i in range(0, len(df_raw)):
        i_part = df_raw[i]
        part_shape = i_part.shape

        i_part = i_part.tail(part_shape[0] - 7)
        i_part = i_part.drop(i_part.columns[part_shape[1] - 1], axis=1)
        i_part = i_part.drop(i_part.columns[3], axis=1)
        i_part.columns = range(i_part.shape[1])
        i_part.reset_index(inplace=True, drop=True)
        only_na = i_part[i_part.isnull().any(axis=1)]
        only_na = only_na.fillna("")
        for index, row in only_na.iterrows():
            if row[1] == "":
                split_row = i_part.iloc[index - 1, 0].split(" ")
                date_part = str(np.array(row.loc[[0]])[0])
                note_part = str(np.array(row.loc[[len(row) - 1]])[0])
                substitute = split_row[0] + \
                    date_part + " " + split_row[1] + " " + split_row[2]
                i_part.iloc[index - 1, 0] = substitute
                i_part.iloc[index - 1,
                            len(row) - 1] = i_part.iloc[index - 1, len(row) - 1] + " " + note_part
            else:
                i_part.iloc[index, 2] = "0 € 0 €"

        i_part = i_part.dropna()

        dff_0 = i_part[0].str.split(" ", 2, expand=True).rename(
            columns={0: 'Timestamp', 1: 'Transaction Type', 2: 'Asset'})
        dff_1 = i_part[1].str.split(" ", 1, expand=True).rename(
            columns={0: 'Quantity Transacted', 1: 'EUR Spot Price at Transaction'})
        dff_2 = i_part[2].str.split(" ", 4, expand=True).rename(
            columns={0: 'Subtotal', 2: 'Total(inclusive of fees)'})
        dff_2["Subtotal"] = [x + " €" for x in dff_2["Subtotal"]]
        dff_2["Total(inclusive of fees)"] = [
            x + " €" for x in dff_2["Total(inclusive of fees)"]]
        dff_2 = dff_2[['Subtotal', 'Total(inclusive of fees)']]
        dff_3 = i_part[3]
        total_first = pd.concat([dff_0, dff_1, dff_2, dff_3],
                                axis=1, ignore_index=True)
        final_df = total_first

    for j in range(1, len(df_raw_all)):
        j_part = df_raw_all[j]
        part_shape = j_part.shape
        j_part = j_part.tail(part_shape[0] - 2)
        j_part = j_part.drop(j_part.columns[6], axis=1)
        j_part.columns = range(j_part.shape[1])
        j_part.reset_index(inplace=True, drop=True)
        only_na = j_part[j_part.isnull().any(axis=1)]
        only_na = only_na.fillna("")

        for index, row in only_na.iterrows():
            if row[1] == "":

                date_part = str(np.array(row.loc[[0]])[0])
                note_part = str(np.array(row.loc[[len(row) - 1]])[0])
                j_part.iloc[index - 1,
                            0] = j_part.iloc[index - 1, 0] + date_part
                j_part.iloc[index - 1,
                            len(row) - 1] = j_part.iloc[index - 1, len(row) - 1] + " " + note_part
            else:
                j_part.iloc[index, 3] = j_part.iloc[index, 3] + " 0 €"
                j_part.iloc[index, 4] = "0 €"

        j_part = j_part.dropna()

        dff_0 = j_part[0]
        dff_1 = j_part[1]
        dff_2 = j_part[2].str.split(" ", 1, expand=True)
        dff_3 = j_part[3].str.split(" ", 1, expand=True)
        dff_4 = j_part[4]
        dff_5 = j_part[5]
        total_all = pd.concat([dff_0, dff_1, dff_2, dff_3,
                              dff_4, dff_5], axis=1, ignore_index=True)
        print(total_all)
        final_df = final_df.append(total_all)
        print(final_df)
    final_df = final_df.rename(columns={
        0: 'Timestamp',
        1: 'Transaction Type',
        2: 'Asset',
        3: 'Quantity Transacted',
        4: "EUR Spot Price at Transaction",
        5: "EUR Subtotal",
        6: "EUR Total(inclusive of fees)",
        7: "Notes"
    })
    final_df.reset_index(drop=True, inplace=True)
    for index, row in final_df.iterrows():
        string_sub = row["EUR Subtotal"].split(" ")[0].replace('.', '')
        string_tot = row["EUR Total(inclusive of fees)"].split(" ")[0].replace(
            '.', '')
        note = row["Notes"].replace(',', '.').replace(' €', '')
        final_df.loc[final_df.index == index, "EUR Subtotal"] = string_sub
        final_df.loc[final_df.index == index,
                     "EUR Total(inclusive of fees)"] = string_tot
        final_df.loc[final_df.index == index, "Notes"] = note

    final_df["EUR Subtotal"] = final_df['EUR Subtotal'].str.replace(
        ',', '.').astype(float)
    final_df["EUR Total(inclusive of fees)"] = final_df['EUR Total(inclusive of fees)'].str.replace(
        ',', '.').astype(float)
    final_df["EUR Fees"] = final_df["EUR Total(inclusive of fees)"] - \
        final_df["EUR Subtotal"]
    final_df["Quantity Transacted"] = [
        float(x) for x in final_df["Quantity Transacted"]]

    return final_df
