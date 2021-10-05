from datetime import datetime
from report.excel_func import db_to_excel
from report.config import BITSTAMP_MONTH
import pandas as pd
from pathlib import Path
import csv

from report.db_func import bit_read_csv, bitstamp_compile_db, coinbasepro_compile_db, get_key, trt_compile_db
from report.report_func import LIFO_definition, define_trans_df, define_dep_wit_df, gains_and_losses_view


# trt = pd.read_csv(Path("input", "trt_test.csv"))
# trt = trt.fillna("0")
# # db creation
# trt_db = trt_compile_db(trt)
# print(trt_db)


# pro = pd.read_csv(Path("input", "pro_account_test.csv"))
# pro_db = coinbasepro_compile_db(pro)
# print(pro_db)

bit = pd.read_csv(Path("input", "bitstamp_test.csv"),
                  sep=",", skiprows=1)
bit_db = bitstamp_compile_db(bit)
print(bit_db)


# tot_db = trt_db.append([pro_db, bit_db])
# # gains and losses
# g_view = gains_and_losses_view(tot_db)
# print(g_view)

# print(w.tail(10))
# print(w.head(60))

# # depo and withdraw
# v = define_dep_wit_df(y)
# print(v)


# bit_db = bitstamp_compile_db(bit_)
# print(bit_db)

x = bit_db  # bit_db.loc[bit_db.Currency == "BTC"]
x["Year"] = [y.year for y in x["Date"]]

x = x.groupby(by=["Currency", "Year", "FlowType"]).sum()
x = x.reset_index(level=['Currency', 'Year', "FlowType"])
print(x)
# x = x.loc[x["Currency"] == "BTC"]
# print(x)
z = x.pivot(index=["Currency", "FlowType"], columns="Year", values="Price")
print(z)


file_name_tot = "report_test.xlsx"
spec_path_tot = Path("output", file_name_tot)

db_to_excel(spec_path_tot, bit_db)
