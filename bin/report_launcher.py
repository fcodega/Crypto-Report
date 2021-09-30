from datetime import datetime
import pandas as pd
from pathlib import Path

from report.db_func import trt_compile_db
from report.report_func import LIFO_definition, define_trans_df, define_dep_wit_df


x = pd.read_csv(Path("input", "trt_test.csv"))
x = x.fillna("no_item")

# db creation
y = trt_compile_db(x)

# gains and losses
z = define_trans_df(y)
w = LIFO_definition(z)
print(w)

# depo and withdraw
v = define_dep_wit_df(y)
print(v)