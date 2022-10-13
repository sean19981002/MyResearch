import pandas as pd
import tweepy
import requests
import datetime
import json
import matplotlib.pyplot as plt
from IPython.display import display
from threading import Thread
from functions import *

class MyThread(Thread):
    def __init__(self, func, args):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args
        self.result = 0
    def run(self):
        self.result = self.func(*self.args)

    def get_results(self):
        return self.result



class Data_crawl:

    def __init__(self, token:list):
        self.client = [] #  list of tweepy.client auth objects
        self.token = token # list of multiple tokens
        today = filename = str(datetime.date.today()) # 用當天日期當作檔案名稱
        self.filename = 'Biden/' + today + '/' + today
        self.tweets_df : pd.DataFrame

    def Get_Tweets_Dataframe(self, query:str, tweet_fields:list):
        # 時間格式需要符合 twitter 的格式：Year-Month-date + "T" + Hour:Minute:Second + "Z"
        end_time  = datetime.datetime.today() # end time is today's 00:00
        end_time = end_time.strftime('%Y-%m-%dT')
        end_time = end_time + "00:00:00Z"

        start_time = datetime.datetime.today() - datetime.timedelta(days= 8) # start time is 7 days ago
        start_time = start_time.strftime('%Y-%m-%dT')
        start_time = start_time + "00:00:00Z"

        api_key = 'I3N75MY5qJxCvSrLWe0ZG4vQk'
        api_key_secret = 'Q3GC8Vr6F2FNqwh7v8rWoDNnA1Qqnn4RjkJ6STVtAQLamw4qCs'
        bearer_token = 'AAAAAAAAAAAAAAAAAAAAAIPvbAEAAAAApt3kcfjyiVBOLVWMbi1Fu6CLL24%3DuIMwpFYplQqMd68VXXv4eU954tnOQu5vljRnV3xL292k4F5sFR'
        access_token = '1467171706754453504-EJx2MzY1RtEGHXf3hqBZkANnsc4hA2'
        access_token_secret = 'VpVdfP1WhID2nas76BXRTMdXXOTvx1BPO1J9LDYs9QM65'

        client = tweepy.Client(
            bearer_token = bearer_token,
            consumer_key = api_key,
            consumer_secret = api_key_secret,
            access_token = access_token,
            access_token_secret = access_token_secret,
            return_type = requests.Response
        )
        tweets = client.search_recent_tweets(
            query = query,
            tweet_fields = tweet_fields,
            max_results = 100
        )

        # convert to dataframe
        tweets = tweets.json() # Save data as dictionary
        tweets_data = tweets['data'] # Extract "data" value from dictionary
        tweet_df = pd.json_normalize(tweets_data)
        tweet_df['author_id'] = tweet_df['author_id'].astype('str')
        tweet_df['id'] = tweet_df['id'].astype('str')
        with open(self.filename + '.xlsx', 'w') as f:
            xlsx_writer = pd.ExcelWriter(self.filename  + ".xlsx", engine = 'xlsxwriter') # 寫進 excel 用的
            tweet_df.to_excel(xlsx_writer, sheet_name='Biden') # 先把 Biden 專業上的 tweet sheet 存檔
            xlsx_writer.save()
        self.tweets_df = tweet_df
        return tweet_df



    def Get_Retweeters_MultiThread(self, filename:str):
        # choose how many pieces
        tweet_list = list(self.tweets_df['id'])
        pieces = int(len(tweet_list) / len(self.token))
        if len(tweet_list) % len(self.token) > 0:
            pieces += 1
        # slicing list into pieces
        tweet_list = list(chunks(tweet_list, pieces))
        values = []

        # multi threading 
        threads = []
        for i in range(len(self.token)):
            t = MyThread(func=Get_Retweeters, args=(tweet_list[i], i, self.token[i], filename, ))
            threads.append(t)
        # start running
        for i in range(len(self.token)):
            time.sleep(60 * i) # avoid resource not enough
            threads[i].start()
        # join() for wait all threads done.
        for i in range(len(self.token)):
            threads[i].join()
        # get return values
        #for i in range(pieces):
        #   values.append(threads[i].get_results())
    
    def Get_Followers_MultiThread(self, filename:str):
        pass

