import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

print("Environment Setup Successful!")
print(f"Pandas Version: {pd.__version__}")

# A tiny test plot to see if visualization works
data = {'Month': ['Jan', 'Feb', 'Mar'], 'Visitors': [100, 150, 200]}
df = pd.DataFrame(data)
sns.barplot(x='Month', y='Visitors', data=df)
plt.title("Test: Everest Trekking Forecast Base")
plt.show()