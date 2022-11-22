import sys
import pandas as pd
import tweepy
import requests
import datetime
import json
import matplotlib.pyplot as plt
import time
import multiprocessing as mp
import re
from os import path


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


def FindReferencedID(s:str):
    integers = [str(i) for i in range(10)] # for recognize numbers or characters. 
    ref_id = ''
    try:
        id_pos = re.search("id=", s).end() # find the end position of "id="
        for i in range(id_pos, len(s)):
            if s[i] == ' ':
                return ref_id
            if s[i] in integers:
                ref_id += s[i]
    except:
        return ref_id


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
    return dict(result)

def FindTargetUser(bound:int, retweeters:dict, result):

    for i in retweeters.keys():
        if retweeters[i] > bound:
            result.append(int(i))

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



#======================= Down here is for Classes.py  ==========================================================


# get retweeters with only one token
def Get_Retweeters(tweet_list:list, index:int, token:str, file_path:str, result):
        """
        this api will return a dict. 
        keys are Tweet ID.
        values are a list of the retweeters of this Tweet.
        the dict will save as .json file, file name is [client_index]_retweeters.json
        """
        dict_retweet_id = dict()  # storing dict -> tweet id:[list of retweeters]
        exist = list()
        if path.exists(file_path + "%d_retweeters.json" % index):
            with open(file_path + "%d_retweeters.json" % index, "r") as f:
                dict_retweet_id = json.load(f)
                exist = list(dict_retweet_id.keys())

        client = tweepy.Client(bearer_token=token, wait_on_rate_limit=True)
        try:
            for tweet_id in tweet_list: # getting retweeter's id
                RetweeterID_list = [] # 創一個空的 list，用來存放此篇 tweet 的 retweeter 的 user id
                #  利用 tweet ID 搜尋轉推此貼文的 retweeters
                if tweet_id in exist:
                    continue

                for retweeter in tweepy.Paginator(client.get_retweeters, tweet_id).flatten():
                    RetweeterID_list.append(retweeter.id)
                
                dict_retweet_id[tweet_id] = RetweeterID_list

                with open(file_path + str(index) + '_retweeters.json', 'w') as f:
                    json.dump(dict_retweet_id, f, indent=True)
        
            result.update(dict_retweet_id)

        except Exception as e:
            with open("%d.txt" % index, "w") as f:
                f.write(str(e))
        
        



# get follwers of everyusers
def Get_Followers(target_users:list, user:list, index:int, token:str, file_path:str, result, exist:list):
    """
    this api will return a dict.
    key is user_id.
    value is list of follwers of this user.
    the dict will save as .json file, file name is [index]_follower.json
    """
    dict_followers = dict() # key:user_id, value:list of follwers
    if path.exists(file_path + "%d_followers.json" % index):
        with open(file_path + "%d_followers.json" % index, "r") as f:
            dict_followers = json.load(f)
    
    client = tweepy.Client(bearer_token=token, wait_on_rate_limit=True)
    try:
        # get followers id
        for user_id in user:

            followers_list = []
            if user_id in exist: # some targets may finish crawling already.
                continue # then we don't have to craw the followers of this one.
            print(datetime.datetime.now(), "Process %d current :"%index, user_id)
            sys.stdout.flush()

            # 利用 user_id 去尋找此 user 的 followers, 並存進 list
            for follower in tweepy.Paginator(client.get_users_followers, user_id, max_results=1000).flatten():
                if follower.id in target_users:
                    followers_list.append(follower.id)
            
            with open(file_path + "%d_followers.json" % index, "w") as f:
                dict_followers[user_id] = followers_list
                json.dump(dict_followers, f, indent=True) # write json file
            
            result.update(dict_followers)
    
    except: # find those targets who hasn't get follower's list
        
        with open(file_path + "%d_followers.json" % index, "w") as f:
            json.dump(dict_followers, f, indent=True) # write json file
        
        result.update(dict_followers)
        print("process-%d has crashed !" % index)
        sys.stdout.flush()
        
 


def Get_User_Tweets(token:str, target_users:list, biden_tweets:list, num:int, result, exist:list, file_path:str):
    """
    This api is for searching the the tweet's wall of target users,
    to see which post of their's are the retweets of Biden's tweets in last 7 days.
    the result will be a dict -> {user_id : list(their tweets id) }.
    The length of every list of target users should be equal to their retweet count.
    """


    client = tweepy.Client(
        bearer_token = token,
        wait_on_rate_limit = True 
    )
    

    print("process %d waiting..." % num)
    sys.stdout.flush()
    print("process %d start running !\n" % num)
    sys.stdout.flush()

    if not path.exists(file_path):
        print("%d process path not exist" % num)
        sys.stdout.flush()
        return # if this folder doesn't exist, return
    try:
        for id in target_users:
            if id not in exist:
                colloection = list()
                value = list()
                for tweet in tweepy.Paginator(
                    client.get_users_tweets, 
                    id=id, 
                    end_time='2022-11-13T00:00:00Z',
                    start_time='2022-11-03T00:00:00Z',
                    tweet_fields=['created_at','referenced_tweets'],
                    expansions=['referenced_tweets.id'],
                    max_results=100).flatten():

                    # parsing the referenced_tweet from <Referenced...> into id only
                    s = str(tweet.referenced_tweets)

                    if "id" in s: # if this tweet of the user has retweet any tweet
                        ref_tweet = FindReferencedID(s=s)
                        if ref_tweet != '':
                            ref_tweet = int(ref_tweet)
                            if ref_tweet in biden_tweets:
                                # for txt
                                tmp = [id, ref_tweet, tweet.id, tweet.created_at] 
                                colloection.append(tmp)
                
               
                if len(colloection) > 0: # for txt
                # append referenced tweets for user     
                    with open(file_path + "%d.txt" % num, "a") as f:
                        for i in colloection:
                            for j in i:
                                f.write(str(j) + " ")                        
                            f.write("\n")
                        f.write("=" * 80)
                        f.write("\n")
                else:
                    with open(file_path + "%d.txt" % num, "a") as f:
                        f.write(str(id) + " None\n")
                        f.write("=" * 80)
                        f.write("\n")
                


    except Exception as e:
        with open(file_path + "%d_unfinish.txt" % num, "a") as f:
            f.write(str(e) + "\n")
            f.write("=" * 40) 
            f.write("\n" + str(i))
        print("Process %d has crashed !" % num)
        sys.stdout.flush()      


def User_Profile(user:list, token:str, index:int, exist:set, file_path:str):

    result = dict()
    client = tweepy.Client(
        bearer_token = token,
        wait_on_rate_limit = True
    )
    current_id = 0

    for id in user: # iterate user id
        current_id = id
        profile = client.get_user( 
                id = id,
                user_fields = ['profile_image_url','location','entities','public_metrics','verified','created_at','protected']
            )

        try:
            # returned values from tweepy.Client.get_user()
            location = str(profile.data.location)
            followers_count = int(profile.data.public_metrics['followers_count'])
            following_count = int(profile.data.public_metrics['following_count'])
            tweet_count = int(profile.data.public_metrics['tweet_count'])
            created_at = str(profile.data.created_at)
            verified = profile.data.verified
            protected = profile.data.protected

            tmp_dict = {
                    "location" : location,
                    "followers_count" : followers_count,
                    "following_count" : following_count,
                    "tweet_count" : tweet_count,
                    "verified" : verified,
                    "created_at" : created_at,
                    'protected' : protected
                }
            result[id] = tmp_dict
        
        except:
            result[id] = None

        finally:
            with open(file_path + "%d.json"%index, "w") as f:
                json.dump(result, f, indent=2)
