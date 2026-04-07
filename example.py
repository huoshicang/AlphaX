from eastmoney import get_day, indicators, overwrite_csv


df = get_day("002639",begin_date="20100101",to_df=True)
print(overwrite_csv(indicators(df), "002639.csv"))

