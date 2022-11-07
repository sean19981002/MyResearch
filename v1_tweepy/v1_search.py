import configparser
import tweepy
from twython import Twython
from tweepy.auth import OAuth2AppHandler
import json
# Read in configs
configs = configparser.ConfigParser()
configs.read('config.ini')
keys = configs['TWITTER']
consumer_key = keys['api_key']
consumer_secret = keys['api_key_secret']
access_token = keys['access_token']
access_secret = keys['access_token_secret']

# Authenticate Tweepy connection to Twitter API
auth = OAuth2AppHandler(consumer_key, consumer_secret)
#auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, parser=tweepy.parsers.JSONParser())

json_data = dict()
count = 0
#f = open('Biden_tweet1.txt','w',encoding='UTF-8')
for status in tweepy.Cursor(api.user_timeline, screen_name='POTUS',count=1000).items(1000):
    s = json.dumps(status)
    s = json.loads(s)
    json_data[count] = s
    count += 1
    
with open("Biden.json", "w") as f:
    json.dump(json_data, f, indent=True)
