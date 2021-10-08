from report.config import CRYPTO_LIST, CRYPTO_LIST_RES, DB_HEADER, DEPO_DF_HEADER, FIAT_LIST, FORMAT_DICT, LIFO_VIEW_START
import pandas as pd


# general

def report_to_excel(file_name, db, lifo_view, depo_withdraw_df, flow_df, ccy_list, y_list):

    with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:

        gain_and_loss_to_exc(writer, '02.Trades, gains & losses',
                             lifo_view, LIFO_VIEW_START[0], LIFO_VIEW_START[1])

        db_to_excel(writer, '99.Export', db)

        depo_withdraw_to_excel(
            writer, '03.Fiat deposits & withdrawals', depo_withdraw_df)

        flows_to_excel(writer, '01. Flows overview', flow_df, ccy_list, y_list)


# Database to Excel


def db_to_excel(writer_obj, sheet_name, db):

    db = db.drop(columns=["DateString"])
    db.to_excel(
        writer_obj, sheet_name=sheet_name, index=False)

    workbook = writer_obj.book
    worksheet = writer_obj.sheets[sheet_name]

    worksheet.hide_gridlines(2)

    format_ = workbook.add_format(FORMAT_DICT.get('header_gray'))
    format_border = workbook.add_format(FORMAT_DICT.get('dashed_border'))

    for i, element in enumerate(DB_HEADER):
        worksheet.write(0, 0 + i, element, format_)

    worksheet.set_column(0, len(DB_HEADER) - 1, None, format_border)
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

    # df = df.drop(columns=["Trade_Num", "Art_Exchange_Rate"])
    # res_list = list(set(CRYPTO_LIST_RES).intersection(df.columns))
    # df = df.drop(columns=res_list)
    # fiat_list = list(set(FIAT_LIST).intersection(df.columns))
    # crypto_list = list(set(CRYPTO_LIST).intersection(df.columns))
    df = gain_and_loss_reorder(df)

    shape_tuple = df.shape
    df_row = shape_tuple[0]
    df_col = shape_tuple[1]

    df.to_excel(
        writer_obj, sheet_name=sheet_name, startrow=start_row,
        startcol=start_col, index=False)

    workbook = writer_obj.book
    worksheet = writer_obj.sheets[sheet_name]

    worksheet.hide_gridlines(2)

    format_word = workbook.add_format(
        FORMAT_DICT.get('lifo_word'))

    format_head = workbook.add_format(FORMAT_DICT.get('header_light_blue'))

    worksheet.write(2, 1, "Transactions", format_word)

    format_sheet_lifo(writer_obj, sheet_name, start_row,
                      start_col, start_row + df_row, start_col + df_col)

    for i, element in enumerate(df.columns):
        worksheet.write(4, 1 + i, element, format_head)


def format_sheet_lifo(writer_obj, sheet_name, start_row, start_col, last_row, last_col):

    workbook = writer_obj.book
    worksheet = writer_obj.sheets[sheet_name]

    format_neg_eur = workbook.add_format(FORMAT_DICT.get('neg_eur'))
    format_pos_eur = workbook.add_format(FORMAT_DICT.get('pos_eur'))
    format_neutral = workbook.add_format(FORMAT_DICT.get('neutral_gray'))
    format_border = workbook.add_format(FORMAT_DICT.get('dashed_border'))
    format_no_border = workbook.add_format(FORMAT_DICT.get('no_border'))

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

    worksheet.set_column(start_col, last_col - 1, None, format_border)


# --------
# Flow View

def flows_to_excel(writer_obj, sheet_name, flow_df, currency_list, year_list):

    fiat_list = list(set(FIAT_LIST).intersection(currency_list))
    f_header_list = ["Fiat"]
    f_header_list.extend(year_list)
    crypto_list = list(set(CRYPTO_LIST).intersection(currency_list))
    c_header_list = ["Crypto"]
    c_header_list.extend(year_list)

    row_sum_df = pd.DataFrame(columns=["Cumulated"])

    for f in fiat_list:

        fiat_sub_df = flow_df.loc[f]
        fiat_sub_df["Cumulated"] = fiat_sub_df.sum(axis=1)
        fiat_sub_df = fiat_sub_df.append(fiat_sub_df.sum(
            numeric_only=True).rename("Net flow from/to Exchanges"), ignore_index=False)

        row_sum_df["Cumulated"] = fiat_sub_df["Cumulated"]

        fiat_sub_df = fiat_sub_df.drop(columns=["Cumulated"])

        fiat_sub_df.to_excel(
            writer_obj, sheet_name=sheet_name, startrow=6,
            startcol=1, index=True, header=False, float_format="%.2f")

        row_sum_df.to_excel(
            writer_obj, sheet_name=sheet_name, startrow=6,
            startcol=len(f_header_list) + 2, index=False,
            header=False, float_format="%.2f")

    workbook = writer_obj.book
    worksheet = writer_obj.sheets[sheet_name]
    worksheet.hide_gridlines(2)
    format_head = workbook.add_format(FORMAT_DICT.get('header_light_blue'))
    format_top_bottom = workbook.add_format(FORMAT_DICT.get('top_bottom'))
    format_bold = workbook.add_format(FORMAT_DICT.get('big_bold'))

    f_row = 0
    for f in fiat_list:

        worksheet.write(5 + f_row, 1, f, format_bold)
        shape_f = flow_df.loc[f].shape
        f_row = f_row + shape_f[0] + 2

    for i, element in enumerate(f_header_list):
        worksheet.write(3, 1 + i, element, format_head)
    for j in range(0, len(f_header_list) + 3):
        worksheet.write(4, j + 1, "", format_top_bottom)

    worksheet.write(3, i + 3, "Cumulated", format_head)
    worksheet.write(3, i + 4, "", format_head)

    for i, element in enumerate(c_header_list):
        worksheet.write(5 + f_row + 2, 1 + i, element, format_head)
    for j in range(0, len(f_header_list) + 3):
        worksheet.write(5 + f_row + 3, j + 1, "", format_top_bottom)
    worksheet.write(5 + f_row + 2, i + 3, "Cumulated", format_head)
    worksheet.write(5 + f_row + 2, i + 4, "", format_head)

    # crypto data part
    crypto_start_row = 5 + f_row + 2 + 3
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

        row_sum_df["Cumulated"] = crypto_sub_df["Cumulated"]

        crypto_sub_df = crypto_sub_df.drop(columns=["Cumulated"])

        crypto_sub_df.to_excel(
            writer_obj, sheet_name=sheet_name, startrow=crypto_start_row + c_row,
            startcol=1, index=True, header=False, float_format="%.6f")

        row_sum_df.to_excel(
            writer_obj, sheet_name=sheet_name, startrow=crypto_start_row + c_row,
            startcol=len(c_header_list) + 2, index=False,
            header=False, float_format="%.6f")

        worksheet.write(crypto_start_row + c_row - 1, 1, c, format_bold)
        shape_c = flow_df.loc[c].shape
        c_row = c_row + shape_c[0] + 3

    # ---
    format_word = workbook.add_format(
        FORMAT_DICT.get('lifo_word'))

    worksheet.write(1, 1, "Flows", format_word)


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

    return net_acq_row

# ----------
# Depo and withdrawal view


def depo_withdraw_to_excel(writer_obj, sheet_name, df):

    df.to_excel(
        writer_obj, sheet_name=sheet_name, index=False, startrow=4, startcol=1)

    workbook = writer_obj.book
    worksheet = writer_obj.sheets[sheet_name]

    worksheet.hide_gridlines(2)

    format_word = workbook.add_format(
        FORMAT_DICT.get('lifo_word'))
    format_ = workbook.add_format(FORMAT_DICT.get('header_light_blue'))
    format_border = workbook.add_format(FORMAT_DICT.get('dashed_border'))

    worksheet.write(2, 1, "Fiat deposits and withdrawals", format_word)
    worksheet.write(
        3, 1, "Fiat funds deposited/withdrawn from Exchanges. Statements attached when applicable.")

    for i, element in enumerate(DEPO_DF_HEADER):
        worksheet.write(4, 1 + i, element, format_)

    worksheet.set_column(1, len(DEPO_DF_HEADER), None, format_border)
