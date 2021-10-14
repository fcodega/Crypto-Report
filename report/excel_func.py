from datetime import datetime

import pandas as pd
import numpy as np

from report.config import (CRYPTO_LIST, CRYPTO_LIST_RES, DB_HEADER,
                           DEPO_DF_HEADER, FIAT_LIST, FORMAT_DICT,
                           LIFO_VIEW_START)

# general


def report_to_excel(client_name, file_name, db, lifo_view, depo_withdraw_df, flow_df, ccy_list, y_list, fund_df, inv_df, crypto_df, trading_df):

    with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:

        summary_view(client_name, writer, 'Summary',
                     fund_df, inv_df, crypto_df, trading_df)

        flows_to_excel(writer, '01. Flows overview', flow_df, ccy_list, y_list)

        gain_and_loss_to_exc(writer, '02.Trades, gains & losses',
                             lifo_view, LIFO_VIEW_START[0], LIFO_VIEW_START[1])

        depo_withdraw_to_excel(
            writer, '03.Fiat deposits & withdrawals', depo_withdraw_df)

        db_to_excel(writer, '99.Export', db)


# Database to Excel


def db_to_excel(writer_obj, sheet_name, db):

    db = db.drop(columns=["DateString", "ID"])
    db["Date"] = [str(x) for x in db["Date"]]
    db["Price"] = [float(x) for x in db["Price"]]
    db = db.fillna("-")

    workbook = writer_obj.book
    worksheet = workbook.add_worksheet(sheet_name)

    worksheet.hide_gridlines(2)

    format_grey = workbook.add_format(FORMAT_DICT.get('header_gray'))
    format_border = workbook.add_format(FORMAT_DICT.get('dashed_border'))
    format_number = workbook.add_format(FORMAT_DICT.get('only_number'))

    # shape_tuple = db.shape
    # row_end = shape_tuple[0]
    # col_end = shape_tuple[1]
    # for j in range(0, row_end):
    #     for i in range(0, col_end):
    #         worksheet.write(j, i, "", format_border)

    for i, element in enumerate(list(db.columns)):
        worksheet.write(0, 0 + i, element, format_grey)

    for index, row in db.iterrows():

        iter_list = np.array(row)
        i = 0
        for el in iter_list:
            worksheet.write(1 + index, 0 + i, el, format_border)
            i = i+1

    worksheet.set_column('B:B', 20)
    worksheet.set_column('D:D', 10, format_number)
    worksheet.set_column('E:E', 35)
# -------
# Gains and Losses to Excel


def gain_and_loss_reorder(df):

    df = df.drop(columns=["Trade_Num", "Art_Exchange_Rate"])
    res_list = list(set(CRYPTO_LIST_RES).intersection(df.columns))
    df = df.drop(columns=res_list)

    fiat_list = list(set(FIAT_LIST).intersection(df.columns))
    crypto_list = list(set(CRYPTO_LIST).intersection(df.columns))
    reordered_df_h = ["Exchange", "Date"]
    reordered_df_h.extend(fiat_list)
    reordered_df_h.extend(crypto_list)
    reordered_df_h.extend(["Exchange_Rate", "LIFO_avg_cost", "Gain/Loss"])
    reordered_df = df[reordered_df_h]

    return reordered_df


def gain_and_loss_to_exc(writer_obj, sheet_name, df, start_row, start_col):

    df = gain_and_loss_reorder(df)
    df["Date"] = [str(x) for x in df["Date"]]

    df = df.fillna("-")
    df.reset_index(drop=True, inplace=True)

    workbook = writer_obj.book
    worksheet = workbook.add_worksheet(sheet_name)

    worksheet.hide_gridlines(2)

    shape_tuple = df.shape
    df_row = shape_tuple[0]

    format_word = workbook.add_format(
        FORMAT_DICT.get('lifo_word'))
    format_header = workbook.add_format(FORMAT_DICT.get('header_light_blue'))
    format_border = workbook.add_format(FORMAT_DICT.get('dashed_border'))

    title = "Transactions"
    worksheet.write(2, 1, title, format_word)

    # header
    for i, element in enumerate(df.columns):
        worksheet.write(4, 1 + i, element, format_header)

    # values
    for index, row in df.iterrows():

        iter_list = np.array(row)
        i = 0
        for el in iter_list:
            worksheet.write(5 + index, 1 + i, el, format_border)
            i = i+1

    format_sheet_lifo(workbook, worksheet, start_row, start_row + df_row)


def format_sheet_lifo(workbook, worksheet, start_row, last_row):

    format_neg_eur = workbook.add_format(FORMAT_DICT.get('neg_eur'))
    format_pos_eur = workbook.add_format(FORMAT_DICT.get('pos_eur'))
    format_neutral = workbook.add_format(FORMAT_DICT.get('neutral_gray'))
    f_center = workbook.add_format(FORMAT_DICT.get('only_center'))

    worksheet.conditional_format(start_row + 1, 3, last_row, 3, {'type': 'cell',
                                                                 'criteria': '<',
                                                                 'value': 0,
                                                                 'format': format_neg_eur})

    worksheet.conditional_format(start_row + 1, 3, last_row, 3, {'type': 'cell',
                                                                 'criteria': '>',
                                                                 'value': 0,
                                                                 'format': format_pos_eur})

    worksheet.conditional_format(start_row + 1, 3, last_row, 3,  {'type': 'cell',
                                                                  'criteria': '=',
                                                                  'value': 0,
                                                                  'format': format_neutral})

    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:J', None, f_center)
    worksheet.set_column('H:J', 17)


# --------
# Flow View

def flows_to_excel(writer_obj, sheet_name, flow_df, currency_list, year_list):

    start_row = 6
    start_col = 1
    between_pad = 1
    start_row_header = 3
    start_row_coin = 5
    below_padding = 2

    year_list_ = [int(x) for x in year_list]
    year_list_.sort()

    fiat_list = list(set(FIAT_LIST).intersection(currency_list))
    f_header_list = ["Fiat"]
    f_header_list.extend(year_list_)
    crypto_list = list(set(CRYPTO_LIST).intersection(currency_list))
    c_header_list = ["Crypto"]
    c_header_list.extend(year_list_)

    row_sum_df = pd.DataFrame(columns=["Cumulated"])

    # fiat part
    f_row = 0
    for f in fiat_list:

        fiat_sub_df = flow_df.loc[f]
        fiat_sub_df["Cumulated"] = fiat_sub_df.sum(axis=1)
        fiat_sub_df = fiat_sub_df.append(fiat_sub_df.sum(
            numeric_only=True).rename("Net flow from/to Exchanges"), ignore_index=False)

        row_sum_df = fiat_sub_df.copy()
        fiat_sub_df = fiat_sub_df.drop(columns=["Cumulated"])

        fiat_sub_df = fiat_sub_df.reset_index(level=["FlowType"])
        fiat_sub_df.to_excel(
            writer_obj, sheet_name=sheet_name, startrow=start_row + f_row,
            startcol=start_col, index=False, header=False, float_format="%.2f")

        row_sum_df["Cumulated"].to_excel(
            writer_obj, sheet_name=sheet_name, startrow=start_row + f_row,
            startcol=len(f_header_list) + start_col + between_pad, index=False,
            header=False, float_format="%.2f")

        shape_f = flow_df.loc[f].shape
        f_row = f_row + shape_f[0] + 3

    workbook = writer_obj.book
    worksheet = writer_obj.sheets[sheet_name]
    worksheet.hide_gridlines(2)
    format_head = workbook.add_format(FORMAT_DICT.get('header_light_blue'))
    format_top_bottom = workbook.add_format(FORMAT_DICT.get('top_bottom'))
    format_bold = workbook.add_format(FORMAT_DICT.get('big_bold'))
    format_top = workbook.add_format(FORMAT_DICT.get('top'))
    format_border = workbook.add_format(FORMAT_DICT.get('dashed_border'))

    # cycle for fiat word definition
    f_row = 0
    for f in fiat_list:

        worksheet.write(start_row_coin + f_row, start_col, f, format_bold)
        shape_f = flow_df.loc[f].shape
        f_row = f_row + shape_f[0] + 3

    # cycle for fiat header
    for i, element in enumerate(f_header_list):
        worksheet.write(start_row_header, start_col + i, element, format_head)
    for j in range(0, len(f_header_list) + 3):
        worksheet.write(4, j + 1, "", format_top_bottom)

    worksheet.write(start_row_header, i + 3, "Cumulated", format_head)
    worksheet.write(start_row_header, i + 4, "", format_head)

    # cycle for crypto header
    for i, element in enumerate(c_header_list):
        worksheet.write(start_row_coin + f_row + 2,
                        start_col + i, element, format_head)
    for j in range(0, len(f_header_list) + 3):
        worksheet.write(start_row_coin + f_row + 3,
                        j + 1, "", format_top_bottom)
    worksheet.write(start_row_coin + f_row + 2,
                    i + 3, "Cumulated", format_head)
    worksheet.write(start_row_coin + f_row + 2, i + 4, "", format_head)

    # crypto data part
    crypto_start_row = start_row_coin + f_row + 2 + 3
    c_row = 0
    for c in crypto_list:

        crypto_sub_df = flow_df.loc[c]
        crypto_sub_df["Cumulated"] = crypto_sub_df.sum(axis=1)

        last_row_name = "Net " + c + " acquired on Exchanges"
        temp_last = net_crypto_acq(crypto_sub_df, last_row_name)

        # adding two last rows to crypto
        crypto_sub_df = crypto_sub_df.append(crypto_sub_df.sum(
            numeric_only=True).rename("Net flow from/to Exchanges"), ignore_index=False)
        crypto_sub_df = crypto_sub_df.append(temp_last, ignore_index=False)

        row_sum_df = crypto_sub_df.copy()

        crypto_sub_df = crypto_sub_df.drop(columns=["Cumulated"])
        crypto_sub_df.index.names = ['FlowType']
        crypto_sub_df = crypto_sub_df.reset_index(level=["FlowType"])
        crypto_sub_df.to_excel(
            writer_obj, sheet_name=sheet_name, startrow=crypto_start_row + c_row,
            startcol=start_col, index=False, header=False, float_format="%.6f")

        row_sum_df["Cumulated"].to_excel(
            writer_obj, sheet_name=sheet_name, startrow=crypto_start_row + c_row,
            startcol=len(c_header_list) + start_col + between_pad, index=False,
            header=False, float_format="%.6f")

        worksheet.write(crypto_start_row + c_row - 1, 1, c, format_bold)

        for j in range(1, len(c_header_list) + 3):
            worksheet.write(crypto_start_row + c_row - 1,
                            j + 1, "", format_top)

        shape_c = flow_df.loc[c].shape
        c_row = c_row + shape_c[0] + 4

    # ---
    format_word = workbook.add_format(
        FORMAT_DICT.get('lifo_word'))

    worksheet.write(1, 1, "Flows", format_word)
    worksheet.set_column(start_col, len(c_header_list) +
                         start_col, None, format_border)
    worksheet.set_column(len(c_header_list) +
                         start_col + 1, len(c_header_list) +
                         start_col + between_pad, None, format_border)


def net_crypto_acq(sub_df, index_name):

    temp = sub_df.copy()
    temp = temp.reset_index(level=["FlowType"])
    temp["flow_num"] = [str(x[0:1]) for x in temp["FlowType"]]
    temp = temp.loc[temp.flow_num != "1"]
    temp = temp.loc[temp.flow_num != "7"]
    temp = temp.append(temp.sum(
        numeric_only=True).rename(index_name), ignore_index=False)
    temp = temp.drop(columns=["FlowType", "flow_num"])

    net_acq_row = temp.tail(1)
    net_acq_row = net_acq_row.clip(0, net_acq_row.max(), axis=1)

    return net_acq_row

# ----------
# Depo and withdrawal view


def depo_withdraw_to_excel(writer_obj, sheet_name, df):

    df["Date"] = [str(x) for x in df["Date"]]
    df = df.fillna("-")
    df.reset_index(drop=True, inplace=True)

    workbook = writer_obj.book
    worksheet = workbook.add_worksheet(sheet_name)

    worksheet.hide_gridlines(2)

    # format
    format_word = workbook.add_format(
        FORMAT_DICT.get('lifo_word'))
    format_header = workbook.add_format(FORMAT_DICT.get('header_light_blue'))
    format_border = workbook.add_format(FORMAT_DICT.get('dashed_border'))

    title = "Fiat deposits and withdrawals"
    subtitle = "Fiat funds deposited/withdrawn from Exchanges. Statements attached when applicable."
    worksheet.write(2, 1, title, format_word)
    worksheet.write(3, 1, subtitle)

    # header
    for i, element in enumerate(DEPO_DF_HEADER):
        worksheet.write(5, 1 + i, element, format_header)

    # values
    for index, row in df.iterrows():

        iter_list = np.array(row)
        i = 0
        for el in iter_list:
            worksheet.write(6 + index, 1 + i, el, format_border)
            i = i+1

    worksheet.set_column("B:B", 35)
    worksheet.set_column("E:E", 20)
    worksheet.set_column('D:D', 17)
    worksheet.set_column('K:K', 17)


# Summary view

def summary_view(client_name, writer_obj, sheet_name, funding_df, inv_df, crypto_df, trading_df):

    today = datetime.now().strftime("%d/%m/%Y")
    last_col = len(funding_df.columns) + 4

    workbook = writer_obj.book
    worksheet = workbook.add_worksheet(sheet_name)

    worksheet.hide_gridlines(2)

    # format for title and initial part
    format_big = workbook.add_format(
        FORMAT_DICT.get('black_header'))
    format_orange = workbook.add_format(
        FORMAT_DICT.get('orange_header'))
    f_bottom = workbook.add_format(FORMAT_DICT.get('title_bottom'))
    f_b = workbook.add_format(FORMAT_DICT.get('only_bottom'))
    format_bg_grey = workbook.add_format(
        FORMAT_DICT.get('neutral_gray'))

    worksheet.write(1, 1, "Crypto Dossier", format_big)
    worksheet.write(3, 1, client_name, format_orange)
    worksheet.write(4, 1, "Status: Final for client review")
    worksheet.write(5, 1, "Updated as of " + today)
    worksheet.write(6, 1, "Data as of " + today)
    for i in range(2, last_col):

        worksheet.write(3, i, "", format_bg_grey)
        worksheet.write(9, i, "", f_b)

    worksheet.write(9, 1, "Dossier overview",
                    f_bottom)

    row_start = 11
    row_padding = 3

    # funding
    title = "Funding"
    subtitle = "Fiat funds deposited on Exchanges, minus Fiat withdrawn from Exchanges"
    row_end = summary_compile(
        workbook, worksheet, title, subtitle, funding_df, row_start)

    # investment
    title = "Investment"
    subtitle = "Fiat funds spent to buy cryptocurrency, minus Fiat funds obtained by selling cryptocurrency"
    new_start = row_end + row_padding
    row_end = summary_compile(
        workbook, worksheet, title, subtitle, inv_df, new_start)

    # crypto holding
    title = "Crypto Holdings"
    subtitle = "Crypto funds bought with fiat or crypto, minus crypto funds sold or spent as fees"
    new_start = row_end + row_padding
    row_end = summary_compile(
        workbook, worksheet, title, subtitle, crypto_df, new_start)

    # trading gains and losses
    title = "Trading gains & losses"
    subtitle = "Net gains/losses based on LIFO, excluding cryto-crypto trades"
    new_start = row_end + row_padding
    row_end = summary_compile(
        workbook, worksheet, title, subtitle, trading_df, new_start)

    # columns width operations
    worksheet.set_column("A:A", 2)
    worksheet.set_column("C:I", 15)
    worksheet.set_column("K:K", 15)


def summary_compile(workbook, worksheet, title, subtitle, df, row_start):

    format_orange = workbook.add_format(
        FORMAT_DICT.get('orange_header'))
    format_blue_head = workbook.add_format(
        FORMAT_DICT.get('header_light_blue'))
    format_number = workbook.add_format(
        FORMAT_DICT.get('number'))
    format_curr = workbook.add_format(
        FORMAT_DICT.get('currency'))
    format_bg_grey = workbook.add_format(
        FORMAT_DICT.get('neutral_gray'))
    format_negative = workbook.add_format(
        FORMAT_DICT.get('negative_number'))

    worksheet.write(row_start, 1, title, format_orange)
    worksheet.write(
        row_start + 1, 1, subtitle)

    fund_header = list(np.array(df.columns))
    last_col = len(df.columns) + 4

    for i in range(2, last_col):

        worksheet.write(row_start, i, "", format_bg_grey)

    for i, el in enumerate(fund_header):

        worksheet.write(row_start + 3, 2 + i, el, format_blue_head)

    worksheet.write(row_start + 3, 2 + i + 2, "Total", format_blue_head)

    df["Cum"] = df.sum(axis=1)
    col_sum = df.copy()

    df = df.drop(columns=["Cum"])
    df.index.names = ['Currency']
    df = df.reset_index(level=["Currency"])

    for index, row in df.iterrows():
        curr = row["Currency"]

        worksheet.write(index + row_start + 4, 1, curr, format_curr)
        iter_list = np.array(row)
        iter_list = np.delete(iter_list, 0)

        i = 1
        for el in iter_list:
            r = index + row_start + 4
            c = 1 + i
            worksheet.write(r, c, el, format_number)
            worksheet.conditional_format(r, c, r, c, {'type': 'cell',
                                                      'criteria': '<',
                                                      'value': 0,
                                                      'format': format_negative})
            i = i+1

        r_ = index + row_start + 4
        c_ = i + 2
        worksheet.write(r_, c_, np.array(col_sum["Cum"][index]), format_number)
        worksheet.conditional_format(r_, c_, r_, c_, {'type': 'cell',
                                                      'criteria': '<',
                                                      'value': 0,
                                                      'format': format_negative})
    row_end = index + row_start + 4

    return row_end
