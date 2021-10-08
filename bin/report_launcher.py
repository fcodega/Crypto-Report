from datetime import datetime
from report.excel_func import db_to_excel, gain_and_loss_to_exc, report_to_excel
from report.config import BITSTAMP_MONTH
import pandas as pd
from pathlib import Path


from report.db_func import bit_read_csv, bitstamp_compile_db, coinbasepro_compile_db, compile_total_db, get_key, trt_compile_db
from report.report_func import LIFO_definition, define_flows_view, define_trans_df, define_dep_wit_df, gains_and_losses_view


# trt = pd.read_csv(Path("input", "trt_test_.csv"))
# trt = trt.fillna("0")
# # db creation
# trt_db = trt_compile_db(trt)
# print(trt_db)


# pro = pd.read_csv(Path("input", "pro_account_test.csv"))
# pro_db = coinbasepro_compile_db(pro)
# print(pro_db)

# bit = pd.read_csv(Path("input", "bitstamp_test.csv"),
#                   sep=",", skiprows=1)
# bit_db = bitstamp_compile_db(bit)
# print(bit_db)
tot_db = compile_total_db(trt_df="trt_test.csv", pro_df="pro_account_test.csv")
print(tot_db)
# tot_db = trt_db.append([pro_db, bit_db])
# # gains and losses
g_view = gains_and_losses_view(tot_db)

# # depo and withdraw
depo_view = define_dep_wit_df(tot_db)
print(depo_view)

# bit_db = bitstamp_compile_db(bit_)
# print(bit_db)

z, c_list, y_list = define_flows_view(tot_db)


file_name_tot = "report_test.xlsx"
spec_path_tot = Path("output", file_name_tot)

report_to_excel(spec_path_tot, tot_db, g_view, depo_view, z, c_list, y_list)
