import json
import pandas as pd

json_dict = dict()
with open('v1_tweepy/Biden.json', 'r') as f:
    json_dict = json.load(f)

keep_datakey = [
    "id_str",
    "created_at",
    "text",
    "retweeted",
    "retweet_count",
    "favorite_count"

]
keep = []
for i in json_dict.keys():
    value = json_dict[i]
    tmp = dict()
    for j in keep_datakey:
        tmp[j] = value[j]
    keep.append(tmp)

df = pd.DataFrame(keep)
# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter('v1_tweepy/dataG.xlsx', engine='openpyxl')
# Convert the dataframe to an XlsxWriter Excel object.
df = df.loc[2:72]
df.to_excel(writer, sheet_name='biden tweets')

writer.save()