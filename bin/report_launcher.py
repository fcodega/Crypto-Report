from report.report_func import report_launch


# input variable name

trt_df = "TRT_mascioli.csv"
kraken_df = "kraken_mascioli.csv"
pro_df = None  # "pro_michele.csv.csv"
bit_df = None
coin_transaction_csv = None  # "coinbase_CS_P_54.csv"
coin_account_pdf = None  # "mick_acc.pdf"  # "FC_coin.pdf"
coin_transaction_pdf = None  # "mick_trans.pdf"  # "FC_transaction.pdf"  #
manual_entry_db = "conio_mascioli.xlsx"

# output variable name

client_name = "Simone Mascioli"
client_code = None
if client_code is None:
    client_code = client_name
report_name = client_code + " - Crypto Dossier.xlsx"

report_launch(client_name, report_name, lang="ita", trt_df=trt_df,
              manual_entry_db=manual_entry_db, pro_df=pro_df, kraken_df=kraken_df,
              bit_df=bit_df, coin_account_pdf=coin_account_pdf,
              coin_transaction_pdf=coin_transaction_pdf,
              coin_transaction_csv=coin_transaction_csv)
