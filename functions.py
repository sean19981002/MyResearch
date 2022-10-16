import sys
import threading
from unittest import result
import pandas as pd
import tweepy
import requests
import datetime
import json
import matplotlib.pyplot as plt
from IPython.display import display
from threading import Thread
import time
import queue 
import multiprocessing as mp
from tqdm import tqdm
import datetime

# if there are multiple json file need to be union，use ths function.
def union_JSON_files(file_list:list):
    # load retweeters file
    retweeter_dict = dict() 
    for filename in file_list:
        with open(filename, 'r') as f:
            json_file = json.load(f)
            for tweet_id in json_file:
                retweeter_dict[tweet_id] = json_file[tweet_id]
    return retweeter_dict

# Slicing list into chunks, each chunk has n elements.
def chunks(xs, n):
        n = max(1, n)
        return (xs[i:i+n] for i in range(0, len(xs), n))

# split dict into many pieces, store each piece of dict into a return list.
def split_dictionary(input_dict, chunk_size):
    res = []
    new_dict = {}
    for k, v in input_dict.items():
        if len(new_dict) < chunk_size:
            new_dict[k] = v
        else:
            res.append(new_dict)
            new_dict = {k: v}
    res.append(new_dict)
    return res



# get retweeters with only one token
def Get_Retweeters(tweet_list:list, index:int, token:str, file_path:str, result):
        """
        this api will return a dict. 
        keys are Tweet ID.
        values are a list of the retweeters of this Tweet.
        the dict will save as .json file, file name is [client_index]_retweeters.json
        """
        dict_retweet_id = {} # storing dict -> tweet id:[list of retweeters]
        client = tweepy.Client(bearer_token=token, wait_on_rate_limit=True)
        f = open(file_path + str(index) + '_retweeters.json', 'w')

        for tweet_id in tweet_list: # getting retweeter's id
            RetweeterID_list = [] # 創一個空的 list，用來存放此篇 tweet 的 retweeter 的 user id
            #  利用 tweet ID 搜尋轉推此貼文的 retweeters
            for retweeter in tweepy.Paginator(client.get_retweeters, tweet_id).flatten():
                RetweeterID_list.append(retweeter.id)
            
            dict_retweet_id[tweet_id] = RetweeterID_list
            t = json.dump(dict_retweet_id, f, indent=True) # write json file
            result |= dict_retweet_id
        f.close()
    
# get follwers of everyusers
def Get_Followers(user:list, index:int, token:str, file_path:str, result):
    """
    this api will return a dict.
    key is user_id.
    value is list of follwers of this user.
    the dict will save as .json file, file name is [index]_follower.json
    """
    dict_followers = {} # key:user_id, value:list of follwers
    client = tweepy.Client(bearer_token=token, wait_on_rate_limit=True)
    # get followers id
    f = open(file_path + '_' + str(index) + '_follwer.json', 'w')

    for user_id in user:
        followers_list = []
        # 利用 user_id 去尋找此 user 的 followers, 並存進 list
        for follower in tweepy.Paginator(client.get_users_followers, user_id).flatten(limit=1000000000):
            followers_list.append(follower.id)
        
        dict_followers[user_id] = followers_list
        t = json.dump(dict_followers, f, indent=True) # write json file
        result |= dict_followers
    f.close()




# Counting how many retweets the users had, will append dict into mp.manager's list
def UserRetweetCount(retweeter_dict:dict, retweeters:list, q:mp.Queue, requests_count:int, seq_id:int, result):
    # send sub-list into here
    user_retweet_count = dict.fromkeys(retweeters, 0)
    total = len(retweeters) * requests_count # total iterations

    # if user has retweeted this tweet, the mapped value will plus 1
    
    for tweet_id in retweeter_dict.keys():
        for user_id in retweeters:
            if user_id in retweeter_dict[tweet_id]:
                user_retweet_count[user_id] += 1
    result.update(user_retweet_count)
    #q.put(user_retweet_count)



def UserRetweetCount_MultiCore(parallelism:int, retweeters:list, retweeter_dict:dict, requests_count:int):
    # thread's parrelle degree
    pieces = int(len(retweeters) / parallelism)
    if int(len(retweeters)) % parallelism > 0:
        pieces += 1
    retweeters_list = list( chunks(retweeters, pieces) ) # slicing list into pieces
    threads = []
    q = mp.Queue() # for collecting the output values of each process
    manager = mp.Manager()
    result = manager.dict()

    print("Parrelle degree: ", len(retweeters_list))
    # start multi threading
    print("Start dispatching Multi-Process....")
    for i in range(parallelism):
         # adding threads into list
        t = mp.Process(target=UserRetweetCount, args=(retweeter_dict, retweeters_list[i], q, requests_count, i, result))
        threads.append(t)

    print("Start running all sub-process......")
    for i in range(parallelism):
        threads[i].start()
        
    print("Wait for resulst of all sub-process......")
    for i in range(parallelism):
        threads[i].join() # wait for all threads done
    
    # Union the results from every thread
    print("Jobs done ! Start union all results")
    """for _ in range(parallelism):
        return_value = q.get()
        result |= return_value
    """
    
    return result


def FindTargetUser(bound:int, retweeters:dict, result):

    for i in retweeters.keys():
        if retweeters[i] > bound:
            result.append(i)

def FindTargetUser_MultiCore(bound:int, retweeters:dict):
    paralle = 8
    process = list()
    manager = mp.Manager()
    result = manager.list()

    # slicing dict into 8 pieces
    chunk_size = int(len(retweeters))
    if chunk_size % 8 > 0:
        chunk_size = int(chunk_size/8)
        chunk_size += 1
    else:
        chunk_size = int(chunk_size/8)
    # every element in this list is an dict with equal size(except the last one)
    retweeters_chunked_list = split_dictionary(input_dict=retweeters, chunk_size=chunk_size)

    print("Parralle degree", paralle)
    for i in range(paralle):
        t = mp.Process(
            target=FindTargetUser,
            args=(bound, retweeters_chunked_list[i], result)
        )
        process.append(t)
    
    print("Start running all sub-process")
    for i in range(paralle):
        process[i].start()
    
    print("Wait for resulst of all sub-process......")
    for i in range(paralle):
        process[i].join() # wait for all processes are done.

    return list(result)


def Get_User_Tweets(token:str, target_users:list, biden_tweets:list, num:int, result):
    """
    This api is for searching the the tweet's wall of target users,
    to see which post of their's are the retweets of Biden's tweets in last 7 days.
    the result will be a dict -> {user_id : list(their tweets id) }.
    The length of every list of target users should be equal to their retweet count.
    """
    user_tweet_id = dict()
    client = tweepy.Client(
        bearer_token = token,
        wait_on_rate_limit = True 
    )
    
    for id in target_users:
        for tweet in tweepy.Paginator(
            client.get_users_tweets, 
            id=id, 
            end_time='2022-10-11T00:00:00Z',
            start_time='2022-10-03T00:00:00Z',
            tweet_fields=['context_annotations','created_at','referenced_tweets'],
            expansions=['referenced_tweets.id'], 
            max_results=100):

            ref_tweet = str(tweet.referenced_tweets)
            ref_tweet = ref_tweet.replace('[<ReferencedTweet id=','').replace(' type=','').replace('replied_to]','').replace('retweeted]','').replace('quoted]','')
            


