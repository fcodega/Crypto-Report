import numpy as np

from report.config import CRYPTO_LIST, FIAT_LIST


def complete_year_list(y_list):

    min_y = min(y_list)
    max_y = max(y_list)

    complete_y = []

    for i in range(min_y, max_y + 1):
        complete_y.append(i)

    return complete_y


def extend_pivot_header(pivot_df, y_list, filled_value):

    incomplete_y = pivot_df.columns
    complete_y = complete_year_list(y_list)

    for el in incomplete_y:
        complete_y.remove(el)

    missing_y = complete_y

    for y in missing_y:
        pivot_df[y] = filled_value

    pivot_df = pivot_df.reindex(sorted(pivot_df.columns), axis=1)

    return pivot_df


def check_new_ccy(df, col_to_check):

    dff = df.copy()
    ccy_list = list(np.array(dff[col_to_check].unique()))
    intersect_crypto = list(set(CRYPTO_LIST).intersection(ccy_list))
    print(intersect_crypto)
    intersect_fiat = list(set(FIAT_LIST).intersection(ccy_list))
    intersect = intersect_crypto.extend(intersect_fiat)
    if len(intersect) < len(ccy_list):
        new_ccy = list(set(ccy_list) - set(intersect))
        print(new_ccy)
        errstr = "There is a new currency/s to register: " + new_ccy
        return errstr
    else:
        return True
