import tweepy

client = tweepy.Client(bearer_token='AAAAAAAAAAAAAAAAAAAAACHvcgEAAAAA9lDgALcD%2FZRxz%2BFrzuc6B7IxJqc%3DnBTsObUCrmc50dlBlB81QMnqnab8oj5Oo7uy4uXMi7vVUOEJAu',wait_on_rate_limit=True)

i = 2180

fo = open('Biden_tweet_id.txt','r',encoding='UTF-8')
y = fo.readlines()

fw=open('Biden_vertex1.txt','r')
# Replace Tweet ID
for data in fw:
	id = data.replace("[",'').replace("]",'')
	id = int(id)

	f = open('retweet_time%d.txt'%i,'a+',encoding='UTF-8')

	for tweet in tweepy.Paginator(
		client.get_users_tweets, 
		id=id,
		end_time='2022-06-18T00:00:00Z',
		start_time='2022-06-09T00:00:00Z',
		tweet_fields=['context_annotations','created_at','referenced_tweets'],
		expansions=['referenced_tweets.id'], 
		max_results=100).flatten(limit=10000):
			x = str(tweet.referenced_tweets)
			u = x.replace('[<ReferencedTweet id=','').replace(' type=','').replace('replied_to]','').replace('retweeted]','').replace('quoted]','')
			for z in y:
				if u in z:
					print(tweet.id,tweet.created_at,u,file=f)
	i = i+1