# Crypto-Report

Install the repository and its prerequisites into a
python virtual environment; e.g. from the root folder:

Bash shell

    python -m venv venv
    source venv/bin/activate
    pip install --upgrade -r requirements.txt
    pip install --upgrade -e ./

Windows CMD or PowerShell:

    python -m venv venv
    .\venv\Scripts\activate
    pip install --upgrade -r requirements.txt
    pip install --upgrade -e ./

Windows Git bash shell:

    python -m venv venv
    cd ./venv/Scripts
    . activate
    cd ../..
    pip install --upgrade -r requirements.txt
    pip install --upgrade -e ./


# Dossier generation

In order to generate a dossier follow the steps:

1) Upload all the needed files in "input" folder
    
    The code can manage the file coming from different Exchanges:
    - The Rock Trading: a CSV format file is needed to perform the computation
    - Coinbase-pro: the CSV format of the file "account.csv" is needed to perform the computation
    - Bitstamp: a CSV format file is needed to perform the computation
    - Coinbase: to perform the computation the code nneds the standard coinbase report in CSV format and
      the complete report in PDF format
    - Hype: this Exchange does not provide a report, the user has to manually insert the values in the specified template
      as specified below    
         
2) Assign the right name to each variable corresponding to a specific file in the report_launcher.py script, otherwise write None
3) Add the client name and the client code (if needed) in the report_launcher.py script
4) Run the the report_launcher.py script: the output will be uploaded in the "output" folder

## How to insert manually the values for all the Exchanges without a report

The code can manage a specifically structured file in XLSX format containing all the information in the proper way.
all the operation can be divided into four main clusters:
1) Deposit 
   - field "FlowType" : "1 - Deposito su Exchange"
   - field "FlowType_Num: "1"
   - field "Trade_Num": "hype_depo_" + a number starting from 0 to N (0 is the oldest deposit)
   - field "Currency: with the currency of the deposit operation
2) Withdrawal
   - field "FlowType" : "7 - Prelievo da Exchange"
   - field "FlowType_Num: "7"
   - field "Trade_Num": "hype_wit_" + a number starting from 0 to N (0 is the oldest withdrawal)
   - field "Currency: with the currency of the withdrawn operation
3) Fees (always related to other operations)
   - field "FlowType" : "6 - Pagamento di fee su Exchange"
   - field "FlowType_Num: "6"
   - field "Trade_Num": "hype_fee_" + a number starting from 0 to N (0 is the oldest deposit)
   - field "Currency: with the currency in which the fee is paid
4) Trade
    Each trade generates three different rows specifically:
    - buy operation
        - field "FlowType" : "2 - Acquisto con fiat su Exchange" or "3 - Ottenuto vendendo cryptocurrency"
        - field "FlowType_Num": "2" or "3"
        - field "Trade_Num": "hype_trade_" + a number starting from 0 to N (0 is the oldest deposit)
        - field "Currency: with the currency of the buy leg
    - sell operation
        - field "FlowType" : "5 - Spesa per acquisto cryptocurrency" or "4 - Vendita per fiat su Exchange"
        - field "FlowType_Num": "5" or "4"
        - field "Trade_Num": "hype_trade_" + a number starting from 0 to N (0 is the oldest deposit)
        - field "Currency: with the currency of the sell leg
    - related fees
       - field "FlowType" : "6 - Pagamento di fee su Exchange"
       - field "FlowType_Num: "6"
       - field "Trade_Num": "hype_fee_" + a number starting from 0 to N (0 is the oldest deposit)
       - field "Currency: with the currency in which the fee is paid
