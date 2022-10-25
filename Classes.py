import pandas as pd
import tweepy
import requests
import datetime
import json
import matplotlib.pyplot as plt
from IPython.display import display
from threading import Thread
from functions import *
from os import path


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

    def Get_Tweets_Dataframe(self, query='', tweet_fields=[], wanna_download=False, tweet_df=pd.DataFrame()):
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

        if wanna_download:
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
        else:
            self.tweets_df = tweet_df



    def Get_Retweeters_Multi(self, filename:str):
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
    
    def Get_Followers_Multi(self, target_users:list, file_path:str):
        paralle = len(self.token)
        piece = int(len(target_users) / paralle)
        if len(target_users) % paralle > 0:
            piece += 1
        process = list()
        manager = mp.Manager()
        result = manager.dict()
        user = list( chunks(target_users, piece) )
        exist = list()
        for i in range(paralle):
            # print(i)
            if path.exists(file_path + "%d_followers.json" % i):
                with open(file_path + "%d_followers.json" % i, "r") as f:
                    file = json.load(f)
                    exist.extend( list(file.keys()) )
        print("Targets who Already finishing capture : %d" % len(exist))
        print("Start dispatching multi process...")
        for i in range(paralle):
            t = mp.Process(
                target=Get_Followers, 
                args=(target_users, user[i], i, self.token[i], file_path, result, exist, ))
            process.append(t)
        
        print("Start collecting followers of target users...")
        for i in range(paralle):
            time.sleep(i * 40) # wait some time for avoiding process crash
            process[i].start()

        print("Wait for all process....")
        for i in range(paralle):
            process[i].join()
        
        print("Collecting Done !")
        #return result # dict {user_id : [followers]}
    
    
    def Get_User_Tweets_Multi(self, file_path:str, target_user:list):
        paralle = len(self.token)
        process = list() # list saves multi-process
        manager = mp.Manager()
        result = manager.list() # for union results from every process
        biden_tweets = list(self.tweets_df['id'])
        piece = int(len(target_user) / paralle)
        if len(target_user) % paralle > 0:
            piece += 1
        target_user = list(chunks(target_user, piece))
        for i in range(paralle):
            p = mp.Process(
                target = Get_User_Tweets,
                args = (self.token[i], target_user[i], biden_tweets, i, result))
            process.append(p)
        
        for i in range(paralle):
            process[i].start()
        
        for i in range(paralle):
            process[i].join()
        
        #with open(file_path + "TargetUserTweet_total.json", 'w') as f:
        #    x = json.dumps(result.copy())
        #    json.dump(x, f, indent=True)
        
        return result
