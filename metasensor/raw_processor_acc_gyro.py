import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv("acc_gyro.csv")
print(data.head())
print(data.shape)
print(data.info())
print(data.describe())
#data.plot(kind="box", vert=False, figsize=(14,6))
plt.plot([i for i in range(len(data["ACCZ"]))], data["ACCZ"])
plt.xlabel("Tiempo (s*10e-2)")
plt.ylabel("m/s²")
plt.title("Acelerómetro - Eje Z")
plt.show() 
