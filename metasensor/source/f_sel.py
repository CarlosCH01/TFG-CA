import matplotlib.pyplot as plt
import pandas as pd
from sklearn import neighbors, metrics
from sklearn.model_selection import train_test_split

import constants as CTS

csv_data = pd.read_csv(CTS.CSV_DIR + "SGN_20230106_112420.csv", index_col=0)

X = csv_data[list(CTS.COLUMN_NAMES[1:-1])]
y = csv_data[["UID"]]

X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=0)
a = csv_data.isna().values
for i in range(len(a)):
    for j in range(len(a[i])):
        if a[i][j]:
            print(i)