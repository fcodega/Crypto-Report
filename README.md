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


## Dossier generation

In order to generate a dossier follow the steps:

# 1) Upload all the needed files in "input" folder
    The code can manage the file coming from different Exchanges:
    - The Rock Trading: a CSV format file is needed to perform the computation
    - Coinbase-pro: the CSV format of the file "account.csv" is needed to perform the computation
    - Bitstamp: a CSV format file is needed to perform the computation
    - Coinbase: to perform the computation the code nneds the standard coinbase report in CSV format and the complete report in PDF format
    - Hype: this Exchange does not provide a report, the user has to manually insert the values in the specified template
    
# 2) In the report_launcher.py script assign the right name to each variable, otherwise write None
# 3) In the report_launcher.py script add the client name and the client code
# 4) Run the the report_launcher.py script: the output will be uploaded in the "output" folder