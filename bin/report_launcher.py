from report.report_func import report_launch


# input variable name

trt_df = "trt_michele.csv"
pro_df = "pro_michele.csv.csv"
bit_df = None
coin_df = "coinbase_m.csv"
coin_pdf = "coinbase_pdf.pdf"
hype_db = None

# output variable name

client_name = "Michele Mandelli"
client_code = None
if client_code is None:
    client_code = client_name
report_name = client_code + " - Crypto Dossier.xlsx"
report_launch(client_name, report_name, lang="ita", trt_df=trt_df,
              hype_db=hype_db, pro_df=pro_df,
              bit_df=bit_df, coin_pdf=coin_pdf,
              coin_df=coin_df)
