import pandas as pd

from report.config import (CRYPTO_FIAT_DICT, DB_HEADER,
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
# TRT


def trt_compile_db(input_df):

    dff = input_df.copy()
    dff["ID"] = dff.index

    trt_db = pd.DataFrame(columns=DB_HEADER)

    trt_db["ID"] = dff["ID"]
    trt_db["Date"] = dff["Date"]
    trt_db["Exchange"] = "TRT"
    trt_db["Currency"] = dff["Currency"]
    trt_db["Price"] = dff["Price"]
    trt_db["Trade_Num"] = dff["Trade"]

    trt_db = trt_define_flowtype(dff, trt_db)

    trt_db = define_trade_type(trt_db)

    return trt_db


def trt_define_flowtype(df, trt_db):

    dff = df.copy()
    df_w_key = trt_key_constructor(dff)

    trt_db["FlowType"] = df_w_key["Key"].apply(
        lambda x: TRT_DICT_TOT.get(x))

    print(trt_db)

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
            # trt_db.loc[trt_db.Date == row_date,
            #            "Fastlane_flag"] = "Y"
            trt_db.loc[trt_db.Date == row_date,
                       "Trade_Num"] = "FAST" + "_" + str(t_id)
            t_id = t_id + 1
            # op_rows["Flow"] = op_rows["Type"].map(TRT_DICT)
            # merged = pd.merge(trt_db, op_rows, how='left', on="ID")
            # print(merged)
            # trt_db["FlowType"] = merged["FlowType"]

    return trt_db


def trt_key_constructor(df):

    dff = df.copy()

    dff["Pair"] = [get_key(CRYPTO_FIAT_DICT, x[:3]) + "-" +
                   get_key(CRYPTO_FIAT_DICT, x[3:]) for x in dff["Fund"]]
    dff.loc[dff['Pair'] == "no_values-no_values",
            'Pair'] = "Deposits, withdrawals, fees, transfers"
    dff["Key"] = dff["Pair"] + "_" + dff["Type"]

    return dff


# Coinbase
