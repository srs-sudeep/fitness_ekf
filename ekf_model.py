import numpy as np
import pandas as pd
def apply_ekf(HR):
    n = len(HR)

    # Model coefficients
    a1, b1, c1 = 4.5714, 384.4286, 7887.1  # exercise
    a2, b2, c2 = 4.5714, 384.4286, 7899.76 # recovery
    gamma = 0.022
    sigma = 18.88

    # Initialization
    CT = np.zeros(n)
    V = np.zeros(n)
    HR_ma = np.zeros(n)
    delta_HR = np.zeros(n)
    A = np.zeros(n)

    CT = np.zeros(n)
    CT[:4] = 36.97 


    V[3] = 0

    HR_ma[0:4] = [1, 2, 3, 4]  
    for t in range(4, n):
        HR_ma[t] = np.mean(HR[t-4:t+1])
        delta_HR[t] = HR_ma[t] - HR_ma[t-4]

        ct = CT[t-1]
        v = V[t-1] + gamma**2

        if delta_HR[t] < 0:
            A[t] = 39
            c = -2 * a2 * ct + b2
            k = (v * c) / (v * c**2 + sigma**2)
            HR_model = -a2 * ct**2 + b2 * ct - c2
        else:
            A[t] = 40
            c = -2 * a1 * ct + b1
            k = (v * c) / (v * c**2 + sigma**2)
            HR_model = -a1 * ct**2 + b1 * ct - c1

        CT[t] = ct + k * (HR[t] - HR_model)
        V[t] = (1 - k * c) * v

    # Output
    print("Estimated Core Temperature (°C):")
    print(np.round(CT, 2))
    return CT


df = pd.read_excel("/home/uchiha-kamal/desktop/fitness_ekf/manas.xlsx")

# Get 2nd column (index 1), skipping the first row (index 0)
hr_values=df.iloc[1:, 1]

# Filter until first 0 or NaN
hr_list = []
for val in hr_values:
    if pd.isna(val) or val == 0:
        break
    hr_list.append(val)

# Convert to NumPy array
HR = np.array(hr_list)
print(HR)
apply_ekf(HR)