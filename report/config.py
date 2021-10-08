
FIAT_LIST = ["EUR", "USD"]

CRYPTO_LIST = ["BTC", "ETH", "DOGE", "XRP", "DOG", "BCH", "BSV", "LTC"]

CRYPTO_LIST_RES = [
    "BTC_residual",
    "ETH_residual",
    "DOGE_residual",
    "XRP_residual",
    "DOG_residual",
    "BCH_residual",
    "BSV_residual",
    "LTC_residual"
]

CRYPTO_FIAT_DICT = {"Crypto": CRYPTO_LIST,
                    "Fiat": FIAT_LIST,
                    }

TRT_DICT = {"paid_commission": "6 - Pagamento di fee su Exchange",
            "transfer_sent": "5 - Spesa per acquisto cryptocurrency",
            "transfer_received": "2 - Acquisto con fiat su Exchange"
            }

TRT_DICT_TOT = {
    "Fiat-Crypto_paid_commission": "6 - Paid as fees to Exchanges",
    "Fiat-Crypto_released_currency_to_fund": "5 - Spent to buy cryptocurrency",
    "Fiat-Crypto_sold_currency_to_fund": "2 - Bought with fiat on the Exchange",
    "Crypto-Fiat_paid_commission": "6 - Paid as fees to Exchanges",
    "Crypto-Fiat_acquired_currency_from_fund": "2 - Bought with fiat on the Exchange",
    "Crypto-Fiat_bought_currency_from_fund": "5 - Spent to buy cryptocurrency",
    "Crypto-Crypto_paid_commission": "6 - Paid as fees to Exchanges",
    "Crypto-Crypto_acquired_currency_from_fund": "3 - Obtained selling cryptocurrency",
    "Crypto-Crypto_bought_currency_from_fund": "5 - Spent to buy other cryptocurrency",
    "Crypto-Fiat_released_currency_to_fund": "4 - Sold for fiat on the Exchange",
    "Crypto-Fiat_sold_currency_to_fund": "3 - Obtained selling cryptocurrency",
    "Fiat-Crypto_acquired_currency_from_fund": "3 - Obtained selling cryptocurrency",
    "Fiat-Crypto_bought_currency_from_fund": "4 - Sold for fiat on the Exchange",
    "Deposits, withdrawals, fees, transfers_atm_payment": "1 - Deposited on Exchanges",
    "Deposits, withdrawals, fees, transfers_paid_commission": "6 - Paid as fees to Exchanges",
    "Deposits, withdrawals, fees, transfers_withdraw": "7 - Withdrawn from Exchanges"

}

BITSTAMP_CSV_HAEDER = ["Type", "Datetime", "Account",
                       "Amount", "Value", "Rate", "Fee", "Sub Type"]

BITSTAMP_MONTH = {
    "01": ["Jan"],
    "02": ["Feb"],
    "03": ["Mar"],
    "04": ["Apr"],
    "05": ["May"],
    "06": ["Jun"],
    "07": ["Jul"],
    "08": ["Aug"],
    "09": ["Sep"],
    "10": ["Oct"],
    "11": ["Nov"],
    "12": ["Dec"]
}
# DB general variables

TRADE_TYPE = {
    "Trade": ["2", "3", "4", "5"],
    "Other": ["1", "6", "7"]
}

FLOW_TYPE_LIST_ENG = [
    "1 - Deposited on Exchanges",
    "2 - Bought with fiat on the Exchange",
    "3 - Obtained selling cryptocurrency",
    "4 - Sold for fiat on the Exchange",
    "5 - Spent to buy cryptocurrency",
    "6 - Paid as fees to Exchanges",
    "7 - Withdrawn from Exchanges"
]

FLOW_TYPE_LIST_ITA = [
    "1 - Deposito su Exchange",
    "2 - Acquisto con fiat su Exchange",
    "3 - Ottenuto vendendo cryptocurrency",
    "4 - Vendita per fiat su Exchange",
    "5 - Spesa per acquisto cryptocurrency",
    "6 - Pagamento di fee su Exchange",
    "7 - Prelievo da Exchange"
]

DB_HEADER = [
    "Exchange",
    "Date",
    "Currency",
    "Price",
    "ID",
    "FlowType",
    "FlowType_Num",
    "TradeType",
    "Trade_Num"
]

# REPORT VARIABLES

TRANSACTION_DF_HEADER = [
    "Exchange",
    "Date",
    "Trade_Num"
]

DEPO_DF_HEADER = [
    "Action",
    "Currency",
    "Payment_type",
    "Date",
    "Year",
    "Sender",
    "Beneficiary",
    "Exchange",
    "Amount",
    "Timestamp_Exchange",
    "Statement"

]


# EXCEL VARIABLES

LIFO_VIEW_START = [4, 1]

FORMAT_DICT = {

    'header_gray': {'bg_color': '#999999',
                    'font_color': '#FFFFFF',
                    'font_size': 12,
                    'align': 'center',
                    'valign': 'vcenter',
                    'bold': True,
                    'top': 2,
                    'bottom': 2},

    'header_light_blue': {'bg_color': '#3DC6EC',
                          'font_color': '#000000',
                          'font_size': 12,
                          'align': 'center',
                          'valign': 'vcenter',
                          'bold': True,
                          'top': 2,
                          'bottom': 2},

    'neg_eur': {'bg_color': '#FFC7CE',
                'font_color': '#9C0006',
                'num_format': '#,##0.00'
                },

    'pos_eur': {'bg_color': '#C6EFCE',
                'font_color': '#006100',
                'num_format': '#,##0.00'
                },

    'neutral_gray': {'bg_color': '#E9E8E6'
                     },

    'lifo_word': {
        'bold': True,
        'font_color': '#FF5733',
        'font_size': 14,
    },

    'dashed_border': {
        'top': 3,
        'bottom': 3

    },
    'no_border': {
        'border': 0

    },

    'top_bottom': {
        'top': 2,
        'bottom': 2
    },

    'big_bold': {
        'font_size': 12,
        'bold': True,
    }

}
