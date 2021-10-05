import pandas as pd
import numpy as np
from datetime import date, datetime

from report.config import (BITSTAMP_CSV_HAEDER, BITSTAMP_MONTH, CRYPTO_FIAT_DICT, CRYPTO_LIST, DB_HEADER,
                           TRT_DICT, TRT_DICT_TOT, TRADE_TYPE)

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

# -------
# The Rock Trading


def trt_compile_db(input_df):

    dff = input_df.copy()
    dff["ID"] = dff.index

    trt_db = pd.DataFrame(columns=DB_HEADER)

    trt_db["ID"] = dff["ID"]
    trt_db["Date"] = dff["Date"]
    trt_db["Exchange"] = "TRT"
    trt_db["Currency"] = dff["Currency"]
    trt_db["Price"] = dff["Price"]
    trt_db["Trade_Num"] = ["trt_" + str(int(x)) for x in dff["Trade"]]

    trt_db = trt_define_flowtype(dff, trt_db)
    trt_db = define_trade_type(trt_db)
    trt_db = trt_depo_with_trade_num(trt_db)

    trt_db["DateString"] = [x[:19] for x in trt_db["Date"]]
    trt_db["Date"] = [datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
                      for x in trt_db["DateString"]]

    return trt_db


def trt_define_flowtype(df, trt_db):

    dff = df.copy()
    df_w_key = trt_key_constructor(dff)

    trt_db["FlowType"] = df_w_key["Key"].apply(
        lambda x: TRT_DICT_TOT.get(x))

    trt_db = trt_fastlane_detect(df_w_key, trt_db)

    trt_db["FlowType_Num"] = [str(x[0:1]) for x in trt_db["FlowType"]]

    return trt_db


def trt_fastlane_detect(df, trt_db):

    dff = df.copy()

    t_id = 1
    for index, row in dff.iterrows():

        row_note = row["Note"]

        if row_note[:8] == "FASTLANE":
            row_date = row["Date"]
            op_rows = dff.loc[dff.Date == row_date]
            op_rows["FlowType"] = op_rows["Type"].apply(
                lambda x: TRT_DICT.get(x))
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

# Coinbase


def coinbase_compile_db(input_df):

    df = input_df.copy()

    return None


def coin_conversion_op(input_df):

    conv_op = input_df.loc[input_df["Transacion Type"] == "Convert"]
    conv_op["ID_"] = conv_op.index
    conv_op["Trade_Num"] = ["Conv_" + str(x) for x in conv_op["ID_"]]

    bought = conv_op.copy()
    bought["Quantity Transacted"] = [
        float(x.split(" ")[4]) for x in bought["Notes"]]
    bought["Asset"] = [
        str(x.split(" ")[5]) for x in bought["Notes"]]
    bought["FlowType"] = "3 - Ottenuto vendendo cryptocurrency"

    sold = conv_op.copy()
    sold["Quantity Transacted"] = sold["Quantity Transacted"]*(-1)
    sold["FlowType"] = "5 - Spesa per acquisto cryptocurrency"

    fee = conv_op.copy()
    fee["Quantity Transacted"] = fee["EUR Fees"]
    fee["Asset"] = "EUR"
    fee["FlowType"] = "6 - Pagamento di fee su Exchange"

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


def coin_buy_op(input_df):

    buy_op = input_df.loc[input_df["Transacion Type"] == "Buy"]
    buy_op["ID_"] = buy_op.index
    buy_op["Trade_Num"] = ["Buy_" + str(x) for x in buy_op["ID_"]]

    bought = buy_op.copy()
    bought["FlowType"] = "2 - Bought with fiat on the Exchange"

    sold = buy_op.copy()
    sold["Quantity Transacted"] = sold["EUR Subtotal"]*(-1)
    sold["Asset"] = [str(x.split(" ")[5]) for x in sold["Notes"]]
    sold["FlowType"] = "5 - Spent to buy cryptocurrency"

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


def coin_sell_op(input_df):

    sell_op = input_df.loc[input_df["Transacion Type"] == "Sell"]
    sell_op["ID_"] = sell_op.index
    sell_op["Trade_Num"] = ["Sell_" + str(x) for x in sell_op["ID_"]]

    sold = sell_op.copy()
    sold["Quantity Transacted"] = sold["Quantity Transacted"]*(-1)
    sold["FlowType"] = "4 - Sold for fiat on the Exchange"

    bought = sell_op.copy()
    bought["Quantity Transacted"] = bought["EUR Subtotal"]
    bought["Asset"] = [str(x.split(" ")[5]) for x in bought["Notes"]]
    bought["FlowType"] = "3 - Obtained selling cryptocurrency"

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


# Coinbase-pro

def coinbasepro_compile_db(input_df):

    df = input_df.copy()
    depo = pro_depo_op(df)
    w = pro_withdraw_op(df)
    fee = pro_fee_op(df)
    trade = pro_trade_op(df)

    db = depo.append([w, fee, trade])

    db["DateString"] = [x[:19] for x in db["Date"]]
    db["Date"] = [datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
                  for x in db["DateString"]]

    return db


def pro_depo_op(input_df):

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
    depo_db["FlowType"] = "1 - Deposito su Exchange"
    depo_db["FlowType_Num"] = "1"
    depo_db["TradeType"] = "Other"

    return depo_db


def pro_withdraw_op(input_df):

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
    w_db["FlowType"] = "7 - Withdrawn from Exchanges"
    w_db["FlowType_Num"] = "1"
    w_db["TradeType"] = "Other"

    return w_db


def pro_fee_op(input_df):

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
    fee_db["FlowType"] = "6 - Pagamento di fee su Exchange"
    fee_db["FlowType_Num"] = "6"
    fee_db["TradeType"] = "Other"

    return fee_db


def pro_trade_op(input_df):

    df = input_df.copy()
    trade_df = df.loc[df.type == "match"]
    trade_df["ID"] = trade_df.index

    trade_df = pro_trade_to_flowtype(trade_df)

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


def pro_trade_to_flowtype(input_df):

    input_df["FlowType"] = ""

    trade_id_list = list(np.array(input_df["trade id"].unique()))

    for t in trade_id_list:

        trade_df = input_df.loc[input_df["trade id"] == t]
        ccy_couple = list(np.array(trade_df["amount/balance unit"]))
        if len(list(set(CRYPTO_LIST).intersection(ccy_couple))) == 2:

            for index, row in trade_df.iterrows():
                if row["amount"] < 0:
                    row["FlowType"] = "5 - Spent to buy other cryptocurrency"
                else:
                    row["FlowType"] = "3 - Obtained selling cryptocurrency"

                trade_df.loc[trade_df["amount/balance unit"] ==
                             single_ccy, "FlowType"] = row["FlowType"]

        elif len(list(set(CRYPTO_LIST).intersection(ccy_couple))) == 1:

            for index, row in trade_df.iterrows():
                single_ccy = row["amount/balance unit"]
                if single_ccy in CRYPTO_LIST:
                    if row["amount"] < 0:
                        row["FlowType"] = "4 - Sold for fiat on the Exchange"
                    else:
                        row["FlowType"] = "2 - Bought with fiat on the Exchange"
                else:
                    if row["amount"] < 0:
                        row["FlowType"] = "5 - Spent to buy cryptocurrency"
                    else:
                        row["FlowType"] = "3 - Obtained selling cryptocurrency"

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


def bitstamp_compile_db(input_df):

    df = input_df.copy()

    df = bit_read_csv(df)

    bit_db_w = bit_withdraw_op(df)
    bit_db_depo = bit_depo_op(df)
    bit_db_trade = bit_mkt_op(df)
    bitstamp_db = bit_db_w.append([bit_db_depo, bit_db_trade])

    bitstamp_db["DateString"] = [x.strftime(
        "%Y-%m-%d %H:%M:%S") for x in bitstamp_db["Date"]]

    bitstamp_db.reset_index(drop=True, inplace=True)

    return bitstamp_db


def bit_withdraw_op(input_df):

    df = input_df.copy()
    w_df = df.loc[df.Type == "Withdrawal"]
    w_df.reset_index(drop=True, inplace=True)
    w_df["ID_"] = w_df.index
    w_df["Trade_Num"] = ["bit_withdraw_" + str(x) for x in w_df["ID_"]]

    fee_df = w_df.copy()
    fee_df["Amount"] = fee_df["Fee"]
    fee_df["FlowType"] = "6 - Paid as fees to Exchanges"

    w_df["FlowType"] = "7 - Withdrawn from Exchanges"
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

    return w_db


def bit_depo_op(input_df):

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
    depo_db["FlowType"] = "1 - Deposito su Exchange"
    depo_db["FlowType_Num"] = "1"
    depo_db["TradeType"] = "Other"
    depo_db["FlowType_Num"] = [str(x[0:1]) for x in depo_db["FlowType"]]

    return depo_db


def bit_mkt_op(input_df):

    df = input_df.copy()
    mkt_df = df.loc[df.Type == "Market"]
    mkt_df.reset_index(drop=True, inplace=True)
    mkt_df["ID_"] = mkt_df.index
    mkt_df["Trade_Num"] = ["bit_trade_" + str(x) for x in mkt_df["ID_"]]

    fee_df = mkt_df.copy()
    fee_df["Amount"] = fee_df["Fee"]
    fee_df["FlowType"] = "6 - Paid as fees to Exchanges"

    crypto_df_tot = mkt_df.copy()

    crypto_buy = crypto_df_tot.loc[crypto_df_tot["Sub Type"] == "Buy"]
    crypto_buy["FlowType"] = "2 - Bought with fiat on the Exchange"
    fiat_sell = crypto_buy.copy()
    fiat_sell["Amount"] = crypto_buy["Value"]
    fiat_sell["FlowType"] = "5 - Spent to buy cryptocurrency"
    crypto_buy_tot = crypto_buy.append(fiat_sell)

    crypto_sell = crypto_df_tot.loc[crypto_df_tot["Sub Type"] == "Sell"]
    crypto_sell["FlowType"] = "4 - Sold for fiat on the Exchange"
    crypto_sell["Amount"] = crypto_sell["Amount"]
    fiat_buy = crypto_sell.copy()
    fiat_buy["Amount"] = crypto_sell["Value"]
    fiat_buy["FlowType"] = "3 - Obtained selling cryptocurrency"
    crypto_sell_tot = crypto_sell.append(fiat_buy)

    total_df = crypto_buy_tot.append(crypto_sell_tot)
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

    mkt_db = define_trade_type(mkt_db)

    return mkt_db
