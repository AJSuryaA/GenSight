import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def pandas_eda(df):
    print("Shape:", df.shape)
    print("\nColumns:", df.columns.tolist())
    print("\nInfo:")
    print(df.info())
    print("\nMissing values:")
    print(df.isnull().sum())
    print("\nDuplicate rows:", df.duplicated().sum())
    print("\nSummary statistics:")
    print(df.describe(include='all').T)
    print("\nUnique values per column:")
    print(df.nunique())
    # Correlation matrix for numeric columns
    print("\nCorrelation Matrix:")
    df_n= df.select_dtypes(include=["number"])
    print(df_n.corr())
    # Visualizations
    sns.histplot(df_n.iloc[:,0])
    plt.title('Histogram of first numeric column')
    plt.show()

# Use like:
# pandas_eda(df)  # where df is your loaded DataFrame
