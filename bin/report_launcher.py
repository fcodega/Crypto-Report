from report.report_func import report_launch


# input variable name

trt_df = None  # "trt_michele.csv"
pro_df = None  # "pro_michele.csv.csv"
bit_df = None
coin_df = None  # "coinbase_CS_P_54.csv"
coin_account_pdf = "FC_coin.pdf"
coin_transaction_pdf = "FC_transaction.pdf"  # "FC_coin.pdf"
hype_db = None

# output variable name

client_name = "Francesco Codega"
client_code = None
if client_code is None:
    client_code = client_name
report_name = client_code + " - Crypto Dossier.xlsx"

report_launch(client_name, report_name, lang="ita", trt_df=trt_df,
              hype_db=hype_db, pro_df=pro_df,
              bit_df=bit_df, coin_account_pdf=coin_account_pdf,
              coin_transaction_pdf=coin_transaction_pdf,
              coin_df=coin_df)
