from report.config import DB_HEADER
import pandas as pd
# import xlsxwriter

# Database to Excel


def db_to_excel(file_name, db):

    with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:

        try:

            db.to_excel(
                writer, sheet_name='99.Export', index=False)

            workbook = writer.book
            worksheet = writer.sheets['99.Export']

            format_ = workbook.add_format({'bg_color': '#999999',
                                           'font_color': '#FFFFFF',
                                           'align': 'center',
                                           'valign': 'vcenter',
                                           'bold': True,
                                           'border': 1})

            for i, element in enumerate(DB_HEADER):
                worksheet.write(0, 0 + i, element, format_)

        except UnboundLocalError:
            pass

    return None

# -------
# Gains and Losses to Excel


def gain_and_loss_to_exc(file_name, db):

    with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:

        try:

            db.to_excel(
                writer, sheet_name='02. Transactions, gains and losses', startrow=4,
                startcol=1, index=False)

            workbook = writer.book
            worksheet = writer.sheets['02. Transactions, gains and losses']

            format_ = workbook.add_format({'bg_color': '#3DC6EC',
                                           'font_color': '#000000',
                                           'align': 'center',
                                           'valign': 'vcenter',
                                           'bold': True,
                                           'border': 1})

            for i, element in enumerate(db.columns):
                worksheet.write(4, 1 + i, element, format_)

        except UnboundLocalError:
            pass
    return None


# --------
# Flow View