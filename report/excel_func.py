from datetime import datetime

import numpy as np
import pandas as pd

from report.config import (CRYPTO_LIST, CRYPTO_LIST_RES, DB_HEADER,
                           DEPO_DF_HEADER, FIAT_LIST, FORMAT_DICT,
                           LIFO_VIEW_START)
from report.general_func import complete_year_list, extend_pivot_header

# ###### main function to create and write excel files ##########


def report_to_excel(client_name, file_name, lang, db, lifo_view, depo_withdraw_df, flow_df, ccy_list, y_list, fund_df, inv_df, crypto_df, trading_df):

    if lang == "ita":
        sum_name = "Riassunto"
        flow_name = "01. Overiview Flussi"
        gl_name = "02. Trade, Guadagni e Perdite"
        dw_name = "03. Depositi e Prelievi Fiat"
    elif lang == "eng":
        sum_name = "Summary"
        flow_name = "01. Flows overview"
        gl_name = "02.Trades, gains & losses"
        dw_name = "03.Fiat deposits & withdrawals"

    with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:

        summary_view(client_name, lang, writer, sum_name,
                     fund_df, inv_df, crypto_df, trading_df)

        flows_to_excel(writer, lang, flow_name, flow_df, ccy_list, y_list)

        gain_and_loss_to_exc(writer, lang, gl_name,
                             lifo_view, LIFO_VIEW_START[0], LIFO_VIEW_START[1])

        depo_withdraw_to_excel(
            writer, lang, dw_name, depo_withdraw_df)

        db_to_excel(writer, '99.Export', db)


# ----------- single sheets part ---------------

# ------ Summary view

def summary_view(client_name, lang, writer_obj, sheet_name, funding_df, inv_df, crypto_df, trading_df):

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

    worksheet.insert_image('B1', 'checksig_logo.png', {
                           'x_scale': 0.3, 'y_scale': 0.3})
    worksheet.write(1, 1, "Crypto Dossier", format_big)
    worksheet.write(3, 1, client_name, format_orange)
    if lang == "ita":
        # --- Italian
        worksheet.write(4, 1, "Status: Definitivo per la visione al cliente")
        worksheet.write(5, 1, "Aggiornato al " + today)
        worksheet.write(6, 1, "Prodotto il " + today)
    elif lang == "eng":
        # ---- English
        worksheet.write(4, 1, "Status: Final for client review")
        worksheet.write(5, 1, "Updated as of " + today)
        worksheet.write(6, 1, "Data as of " + today)
    for i in range(2, last_col):

        worksheet.write(3, i, "", format_bg_grey)
        worksheet.write(9, i, "", f_b)

    if lang == "ita":
        worksheet.write(9, 1, "Riassunto del Dossier",
                        f_bottom)
    elif lang == "eng":
        worksheet.write(9, 1, "Dossier overview",
                        f_bottom)

    row_start = 11
    row_padding = 3

    # funding
    if lang == "ita":
        title = "Finanziamenti"
        subtitle = "Fondi Fiat depositati sull'Exchange meno fondi Fiat prelevati dall'Exchange"
    elif lang == "eng":
        title = "Funding"
        subtitle = "Fiat funds deposited on Exchanges, minus Fiat withdrawn from Exchanges"
    row_end = summary_compile(
        workbook, worksheet, title, subtitle, funding_df, row_start)

    # investment
    if lang == "ita":
        title = "Investimenti"
        subtitle = "Fondi Fiat spesi per l'acquisto di crittovalute meno fondi Fiat ottenuti dalla vendita di crittovalute"
    elif lang == "eng":
        title = "Investment"
        subtitle = "Fiat funds spent to buy cryptocurrency, minus Fiat funds obtained by selling cryptocurrency"
    new_start = row_end + row_padding
    row_end = summary_compile(
        workbook, worksheet, title, subtitle, inv_df, new_start)

    # crypto holding
    if lang == "ita":
        title = "Possedimenti Crypto"
        subtitle = "Crittovalute acquistate con fiat o altre crittovalute meno crittovalute vendute o spese come commissioni"
    elif lang == "eng":
        title = "Crypto Holdings"
        subtitle = "Crypto funds bought with fiat or crypto, minus crypto funds sold or spent as fees"
    new_start = row_end + row_padding
    row_end = summary_compile(
        workbook, worksheet, title, subtitle, crypto_df, new_start)

    # trading gains and losses
    if lang == "ita":
        title = "Attività di trading, guadagni e perdite"
        subtitle = "Guadagni/Perdite nette in Fiat basate sul metodologia LIFO"
    elif lang == "eng":
        title = "Trading gains & losses"
        subtitle = "Net gains/losses based on LIFO, excluding cryto-crypto trades"
    new_start = row_end + row_padding
    row_end = summary_compile(
        workbook, worksheet, title, subtitle, trading_df, new_start)

    # columns width operations
    worksheet.set_column("A:A", 2)
    worksheet.set_column("C:I", 15)
    worksheet.set_column("K:K", 15)
    worksheet.set_row(0, 70)


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


# ----------- client Database view


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


# ------- Gains and Losses View


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


def gain_and_loss_to_exc(writer_obj, lang, sheet_name, df, start_row, start_col):

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
    if lang == "eng":
        title = "Transactions"
    elif lang == "ita":
        title = "Transazioni"

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


# ------- Flows View

def flows_to_excel(writer_obj, lang, sheet_name, flow_df, currency_list, year_list):

    # workook definition and sheet creation
    workbook = writer_obj.book
    worksheet = workbook.add_worksheet(sheet_name)

    # format definition
    format_word = workbook.add_format(FORMAT_DICT.get('lifo_word'))

    worksheet.hide_gridlines(2)
    if lang == "ita":
        worksheet.write(1, 1, "Flussi", format_word)
    elif lang == "eng":
        worksheet.write(1, 1, "Flows", format_word)

    start_row = 3
    start_col = 1
    below_padding = 3

    # fiat part
    last_row, _ = flows_compile(workbook, worksheet, flow_df, currency_list,
                                year_list, start_row, start_col, typology="fiat")

    # crypto part
    start_row = last_row + below_padding
    _, last_col = flows_compile(workbook, worksheet, flow_df, currency_list,
                                year_list, start_row, start_col, typology="crypto")

    worksheet.set_column(last_col, last_col, 15)
    worksheet.set_column('B:B', 35)


def flows_compile(workbook, worksheet, flow_df, currency_list, year_list, start_row, start_col, typology):

    year_list_ = [int(x) for x in year_list]
    year_list_ = complete_year_list(year_list_)
    year_list_.sort()

    if typology == "fiat":
        ccy_list = list(set(FIAT_LIST).intersection(currency_list))
        header_list = ["Fiat"]
        header_list.extend(year_list_)
    elif typology == "crypto":
        ccy_list = list(set(CRYPTO_LIST).intersection(currency_list))
        header_list = ["Crypto"]
        header_list.extend(year_list_)

    format_head = workbook.add_format(FORMAT_DICT.get('header_light_blue'))
    format_bottom = workbook.add_format(FORMAT_DICT.get('bottom'))
    format_bold = workbook.add_format(FORMAT_DICT.get('big_bold'))
    format_border = workbook.add_format(FORMAT_DICT.get('dashed_border'))
    format_plus = workbook.add_format(FORMAT_DICT.get('dashed_plus'))
    format_plus_bold = workbook.add_format(FORMAT_DICT.get('dashed_plus_plus'))
    format_negative = workbook.add_format(FORMAT_DICT.get('negative_number'))

    # header
    for i, element in enumerate(header_list):
        worksheet.write(start_row, start_col + i, element, format_head)

    worksheet.write(start_row, start_col + i + 2, "Cumulated", format_head)

    row_count = 0
    for c in ccy_list:

        # borders
        for j, _ in enumerate(header_list):
            if j < len(header_list) - 1:

                worksheet.write(start_row + 1 + row_count, start_col +
                                j + 1, "", format_bottom)

        worksheet.write(start_row + 1 + row_count,
                        start_col + j + 2, "", format_bottom)

        # currency definition
        worksheet.write(start_row + 2 + row_count, start_col, c, format_bold)

        # df operation
        sub_df = flow_df.loc[c]
        sub_df = extend_pivot_header(sub_df, year_list_, 0.0)

        shape_df = flow_df.loc[c].shape

        sub_df["Cumulated"] = sub_df.sum(axis=1)

        if typology == "crypto":
            last_row_name = "Net " + c + " acquired on Exchanges"
            temp_last = net_crypto_acq(sub_df, last_row_name)

        sub_df = sub_df.append(sub_df.sum(
            numeric_only=True).rename("Net flow from/to Exchanges"), ignore_index=False)
        if typology == "crypto":
            sub_df = sub_df.append(temp_last, ignore_index=False)
        sub_df = sub_df.fillna(0.0)

        row_sum_df = sub_df.copy()
        row_sum_df = row_sum_df[["Cumulated"]]
        row_sum_df.reset_index(inplace=True, drop=True)
        sub_df = sub_df.drop(columns=["Cumulated"])
        sub_df.index.names = ['FlowType']
        sub_df = sub_df.reset_index(level=["FlowType"])

        for index, row in sub_df.iterrows():

            iter_list = np.array(row)
            i = 0
            if iter_list[0].startswith("Net") is True:

                for el in iter_list:
                    r = start_row + 3 + row_count + index
                    c = start_col + i
                    worksheet.write(r, c, el, format_plus)
                    worksheet.conditional_format(r, c, r, c, {'type': 'cell',
                                                              'criteria': '<',
                                                              'value': 0,
                                                              'format': format_negative})
                    i = i+1
            else:
                for el in iter_list:
                    r = start_row + 3 + row_count + index
                    c = start_col + i
                    worksheet.write(r, c, el, format_border)
                    worksheet.conditional_format(r, c, r, c, {'type': 'cell',
                                                              'criteria': '<',
                                                              'value': 0,
                                                              'format': format_negative})
                    i = i+1

        for index, row in row_sum_df.iterrows():

            el = np.array(row)
            r = start_row + 3 + row_count + index
            c = start_col + i + 1
            if ((typology == "fiat") & (index == shape_df[0])):
                worksheet.write(r, c, el, format_plus_bold)
                worksheet.conditional_format(r, c, r, c, {'type': 'cell',
                                                          'criteria': '<',
                                                          'value': 0,
                                                          'format': format_negative})
            elif ((typology == "crypto") & ((index == shape_df[0]) | (index == shape_df[0] + 1))):
                worksheet.write(r, c, el, format_plus_bold)
                worksheet.conditional_format(r, c, r, c, {'type': 'cell',
                                                          'criteria': '<',
                                                          'value': 0,
                                                          'format': format_negative})
            else:
                worksheet.write(r, c, el, format_border)
                worksheet.conditional_format(r, c, r, c, {'type': 'cell',
                                                          'criteria': '<',
                                                          'value': 0,
                                                          'format': format_negative})

        if typology == "crypto":
            row_count = row_count + shape_df[0] + 4
        elif typology == "fiat":
            row_count = row_count + shape_df[0] + 3

        last_row = index + start_row + 3
        last_col = start_col + i + 1

    return last_row, last_col


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


def depo_withdraw_to_excel(writer_obj, lang, sheet_name, df):

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
    if lang == "ita":
        title = "Depositi e Prelievi Fiat"
        subtitle = "Fondi Fiat depositati/prelevati da Exchange"
    elif lang == "eng":
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
        iter_list = np.array(row)
        i = 0
        for el in iter_list:
            worksheet.write(6 + index, 1 + i, el, format_border)
            i = i+1

    worksheet.set_column("B:B", 35)
    worksheet.set_column("E:E", 20)
    worksheet.set_column('D:D', 17)
    worksheet.set_column('K:K', 17)

# --------
# Glossario


def glossary(writer_obj, lang, sheet_name):

    workbook = writer_obj.book
    worksheet = workbook.add_worksheet(sheet_name)

    worksheet.hide_gridlines(2)

    # format
    format_word = workbook.add_format(
        FORMAT_DICT.get('lifo_word'))
    format_header = workbook.add_format(FORMAT_DICT.get('header_light_blue'))
    format_border = workbook.add_format(FORMAT_DICT.get('dashed_border'))
    if lang == "ita":
        title = "Glossario"
    elif lang == "eng":
        title = "Glossary"
    worksheet.write(2, 1, title, format_word)

    return None
