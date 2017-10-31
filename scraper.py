from twython import Twython, TwythonStreamer
from processor import processTweet
from bs4 import BeautifulSoup
from keys import retrieveKeys
from datetime import datetime
import requests
import pickle
import json
import time
import sys
import re
import os
 	
def getMaxTweets(screen_name):
	""" Finds number of tweets by scraping the web page of the Twitter profile"""
	# look-up account
	html = requests.get('http://twitter.com/' + screen_name)
	
	# if 404: exit
	if html.status_code == 404:
		sys.exit('404: Handle "%s" does not exist' % screen_name)
		
	# get max num tweets
	soup = BeautifulSoup(html.content, 'html.parser')
	try:
		num_tweets = soup.find('a', {'data-nav' : 'tweets'})['title']
	except TypeError:
		banned = pickle.load(open('data/banned.p', 'rb'))
		banned.append(screen_name)
		pickle.dump(banned, open('banned.p', 'wb'))
		return None

	num_tweets = re.sub('[a-zA-Z.]', '', num_tweets)
	
	# find last tweet
	tweets = soup.findAll('li', { 'data-item-type' : 'tweet'})
	id = re.sub('[a-zA-Z-]', '', tweets[0]['id'])
	
	# return result
	return {'lis': [int(id)],
			'num_tweets': int(num_tweets)
			}
	
def crawlList(owner, slug):
	twitter = connectTwitter()

	data = twitter.get_list_members(owner_screen_name=owner, count=5000, slug=slug)

	accounts = data['users']	

	print slug, 'has %i accounts' % len(data['users'])
	return [account['screen_name'] for account in accounts if account['protected'] != True]
	

def crawlAccount(target):
	""" crawl targeted twitter account, save tweets to SQL """

	# check if accounts has been crawled before
	# list files in dir
	files = [f for f in os.listdir('data') if os.path.isfile('data/' + f)]

	if os.path.isfile('banned.p'):
		if target in pickle.load(open('banned.p', 'rb')):
			print '@%s is banned: has account, but zero tweets.' % target
			return

	""" Hier een keer bouwen dat als data ouder dan een dag is ff update """
		
	print 'Crawling tweets from @%s...' % target
	data = getMaxTweets(target)

	num_tweets = data['num_tweets']
	lis = data['lis']

	raw_data = []

	twitter = connectTwitter()	
	
	print '%s tweeted %i times. Need %i requests.' % (target, data['num_tweets'], 1 + (data['num_tweets']/200))
		
	for i in range(num_tweets/200 + 1):
		user_timeline = twitter.get_user_timeline(screen_name=target, count=200, max_id=lis[-1], include_rts=False, exclude_replies=True)
	
		for tweet in user_timeline:
				
			lis.append(tweet['id'])
			
			# save to SQL
			processTweet(target, tweet)
	return raw_data

def connectTwitter():
	auth = retrieveKeys()

	print 'Authenticating with Twitter... ', 
	twitter = Twython(auth['APP_KEY'], auth['APP_SECRET'])

	if twitter:
		print 'Authenticated.'
	else:
		sys.exit('Error with Twitter API')

	return twitter

if __name__ == '__main__':
	target = raw_input('Enter a handle! (hit enter to quit)\n> ')
	data = crawlAccount(target)
	print 'Found %i tweets for %s' % (len(data), target)
