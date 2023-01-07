print("(",end="")
for i in ("MEAN","STD","MIN","MEDIAN","MAX"):
    for j in ("ACCX","ACCY","ACCZ","GYRX","GYRY","GYRZ","MAGX","MAGY","MAGZ","UID"):
        print(f'"{j}_{i}"', end=",")
print(")")