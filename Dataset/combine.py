import pandas as pd
import glob

# files = glob.glob(r"E:\Arya\My Python programms\ML_Course\Dataset\*.parquet")
# print(f"Merging {len(files)} parquet files...")

# df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
# df.to_parquet(r"E:\Arya\My Python programms\ML_Course\Dataset\combined.parquet")

# print("✅ Combined successfully!")
df = pd.read_parquet(r"E:\Arya\My Python programms\ML_Course\STC_fortran_to_cpp\Dataset\combined.parquet")
print(df.head())     # View last 5 rows
print(df.tail())
print(df.columns)    # See column names
print(df.shape)