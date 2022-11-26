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

    def __init__(self, token:list, file_path:str):
        self.client = [] #  list of tweepy.client auth objects
        self.token = token # list of multiple tokens
        today = filename = str(datetime.date.today()) # 用當天日期當作檔案名稱
        self.file_path = file_path
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



    def Get_Retweeters_Multi(self):
        # choose how many pieces
        tweet_list = list(self.tweets_df['id'])
        pieces = int(len(tweet_list) / len(self.token))
        if len(tweet_list) % len(self.token) > 0:
            pieces += 1
        # slicing list into pieces
        tweet_list = list(chunks(tweet_list, pieces))
        manager = mp.Manager()
        result = manager.dict()
        file_path = self.file_path + 'retweeters/'
        # multi threading 
        process = []
        for i in range(len(self.token)):
            p = mp.Process(target=Get_Retweeters, args=(tweet_list[i], i, self.token[i], file_path, result, ))
            process.append(p)
        # start running
        for i in range(len(self.token)):
            time.sleep(15 * i) # avoid resource not enough
            process[i].start()
        # join() for wait all process done.
        for i in range(len(self.token)):
            process[i].join()
        return dict(result)
    
    
    def Get_Followers_Multi(self, target_users:list):
        paralle = len(self.token)
        file_path = self.file_path + 'followers/'
        process = list()
        manager = mp.Manager()
        result = manager.dict()
        exist = set()
        for i in range(paralle):
            # print(i)
            if path.exists(file_path + "%d_followers.json" % i):
                with open(file_path + "%d_followers.json" % i, "r") as f:
                    file = json.load(f)
                    for key in list(file.keys()):
                        exist.add(int(key))

        # 要取 complement's set of target_users, for deleting exsisted users
        print("Already crawled :", len(exist))
        print("Target users :", len(target_users))   
        target_users = set(target_users) - set(exist)
        print("Rest of:", len(target_users))
        if len(target_users) == 0:
            return
        else:
            target_users = list(target_users)
            exist = list(exist)

        piece = int(len(target_users) / paralle)
        if len(target_users) % paralle > 0:
            piece += 1
        
        user = list(chunks(target_users, piece))
        for i in range(paralle):
            t = mp.Process(
                target=Get_Followers, 
                args=(target_users, user[i], i, self.token[i], file_path, result, exist, ))
            process.append(t)
        
        print("Start collecting followers of target users...")
        for i in range(paralle):
            time.sleep(1)
            process[i].start()

        print("Wait for all process....")
        for i in range(paralle):
            process[i].join()
        
        print("Collecting Done !")
    
    
    def Get_User_Tweets_Multi(self, target_user:list, biden_tweets:list):
        
        exist = set()
        token = self.token
        paralle = len(token)
        process = list() # list saves multi-process
        manager = mp.Manager()
        result = manager.list() # for union results from every process
        piece = int(len(target_user) / paralle)
        file_path = self.file_path + 'user_tweets/'
        if path.exists(file_path):
            for i in range(14):
                if path.exists(file_path + '%d.json'%i): # check files exist or not
                    with open(file_path + '%d.json'%i, 'r') as f:
                        json_file = json.load(f)
                        for key in json_file.keys(): # key is target user's id
                            exist.add(int(key))

            for i in range(14):
                if path.exists(file_path + '%d.txt'%i):
                    with open(file_path + '%d.txt'%i, 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            if '=' not in line:
                                s = line.split(' ')
                                exist.add(int(s[0]))
            exist = list(exist)
            print("Already crawled :", len(exist))
            print("Target users :", len(target_user))

        if len(target_user) == len(exist):
            print("ALL data had already crawled !")
            return

        if len(target_user) % paralle > 0:
            piece += 1
        target_user = list(chunks(target_user, piece))
        
        try:
            for i in range(paralle):
                p = mp.Process(
                    target = Get_User_Tweets,
                    args = (token[i], target_user[i], biden_tweets, i, result, exist, file_path, ))
                process.append(p)
            
            for i in range(paralle):
                time.sleep(i * 10)
                process[i].start()
            
            for i in range(paralle):
                process[i].join()
        
        except:
            print("Process of getting user's tweets crashed !")
        
        finally:
            print("jobs done !")
    
    def Get_User_Profile_Multi(self, target_user:list):
        file_path = self.file_path + "user_profile/"
        paralle = len(self.token)

        exist = set()
        if path.exists(file_path):
            for i in range(14):
                if path.exists(file_path + "%d.json" % i):
                    with open(file_path + "%d.json" % i, 'r') as f:
                        json_obj = json.load(f)
                        for key in json_obj.keys():
                            exist.add(int(key))

        piece = int(len(target_user)/paralle)
        if len(target_user) % paralle > 0:
            piece += 1
        
        print("Target users :", len(target_user))
        print("Already crawled :", len(exist))
        target_user = set(target_user) - set(exist) # complements
        print("Rest of :", len(target_user))
        if len(target_user) == 0:
            return
        else:
            target_user = list(target_user)
    
        user = list(chunks(target_user, piece))
        processes = []
        for i in range(paralle):
            p = mp.Process(target=User_Profile, args=(user[i], self.token[i], i, exist, file_path, ))
            processes.append(p)

        for i in range(paralle):
            processes[i].start()
            
        for i in range(paralle):
            processes[i].join()
        