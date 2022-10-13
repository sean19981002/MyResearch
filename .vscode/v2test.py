import tweepy

client = tweepy.Client(bearer_token='AAAAAAAAAAAAAAAAAAAAAJKnJgEAAAAAgpYwO66pBtdDUcwjHYnWbMY1ow8%3DJgCTSnmkqVE5M0ywnyoSvMX1Ywpz2ivYnONwQ0Aro7bgby6TUm',wait_on_rate_limit=True)

i = 1

fo=open('WhiteHouse_tweet.txt','r')
# Replace Tweet ID
for data in fo:
	id = data.replace("[",'').replace("]",'')
	id = int(id)

#f=open('biden_retweeter1.txt','a+',encoding='UTF-8')
	f=open('WhiteHouse_retweeter%d.txt'%i,'a+',encoding='UTF-8')
	# retweeters
	for tweet in tweepy.Paginator(client.get_retweeters, id=id, user_fields=['profile_image_url'],max_results=100).flatten(limit=100000):
		print(tweet.id,file=f)
	print(i,file=f)
	i = i+1
	f.close()
fo.close()


"""
id = '1500488822370537480'

users = client.get_retweeters(id=id,user_fields=['profile_image_url'])

print(users)

f=open('biden_retweeter1.txt','a+',encoding='UTF-8')

for user in users.data:
    print(user["id"],file=f)
print('\n', file=f)
f.close()
"""


#把user_fields後面替換成created_at跟user["id"]替換成user["created_at"]可以做到
#試著改成get_retweet看能不能抓到retweet時間