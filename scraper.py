from twython import Twython, TwythonStreamer
from processor import processTweet
from bs4 import BeautifulSoup
from keys import retrieveKeys
from datetime import datetime
import requests
import sqlite3
import pickle
import json
import time
import sys
import re
import os

def connectTwitter():
	auth = retrieveKeys()

	print 'Authenticating with Twitter... ', 
	twitter = Twython(auth['APP_KEY'], auth['APP_SECRET'])

	if twitter:
		print 'Authenticated.'
	else:
		sys.exit('Error with Twitter API')

	return twitter
 	
def getMaxTweets(screen_name):
	""" Finds number of tweets by scraping the web page of the Twitter profile"""
	# look-up account
	html = requests.get('http://twitter.com/' + screen_name)
	
	# if 404: exit
	if html.status_code == 404:
		return('404: Handle "%s" does not exist' % screen_name)

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
	

def crawlAccount(target):
	""" crawl targeted twitter account, save tweets to SQL """
		
	print 'Crawling tweets from @%s...' % target
	data = getMaxTweets(target)

	num_tweets = data['num_tweets']
	lis = data['lis']
	twitter = connectTwitter()	
	
	print '%s tweeted %i times. Need %i requests.' % (target, data['num_tweets'], 1 + (data['num_tweets']/200))
	
	tweets = []
	for i in range(num_tweets/200 + 1):
		user_timeline = twitter.get_user_timeline(screen_name=target, count=200, max_id=lis[-1], include_rts=False, exclude_replies=True)
	
		for tweet in user_timeline:
				
			lis.append(tweet['id'])			
			tweets.append(tweet)
	return tweets
