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
	num_tweets = soup.find('a', {'data-nav' : 'tweets'})['title']
	num_tweets = re.sub('[a-zA-Z.]', '', num_tweets)
	
	# find last tweet
	tweets = soup.findAll('li', { 'data-item-type' : 'tweet'})
	id = re.sub('[a-zA-Z-]', '', tweets[0]['id'])
	
	# return result
	return {'lis': [int(id)],
			'num_tweets': int(num_tweets)
			}
	
def crawlProfile(screen_name):
	twitter = connectTwitter()
	
	user = twitter.show_user(screen_name=screen_name)
	return user

def crawlAccount(target, since_id, exisiting_tweets):
	""" crawl targeted twitter account, save tweets to SQL """

	# get max tweets from Twitter front-end
	data = getMaxTweets(target)
	num_tweets = data['num_tweets']
	lis = data['lis']

	# connect Twitter api
	twitter = connectTwitter()	

	if not since_id:
		print 'Crawling tweets from @%s...' % target
	else:
		# refreshing
		tweets = []
		# calculating how many tweets to be crawled since last time
		num_tweets_to_be_crawled = num_tweets - exisiting_tweets
		print 'Need to fetch %i new tweets...' % num_tweets_to_be_crawled
		for i in range(num_tweets_to_be_crawled/200 + 1):
			user_timeline = twitter.get_user_timeline(screen_name=target, count=200, since_id=since_id, include_rts=False, exclude_replies=True)
		
			for tweet in user_timeline:

				tweets.append(tweet)
		return tweets
	
	print '%s tweeted %i times. Need %i requests.' % (target, data['num_tweets'], 1 + (data['num_tweets']/200))
	
	tweets = []
	for i in range(num_tweets/200 + 1):
		user_timeline = twitter.get_user_timeline(screen_name=target, count=200, max_id=lis[-1], include_rts=False, exclude_replies=True)
	
		for tweet in user_timeline:
				
			lis.append(tweet['id'])			
			tweets.append(tweet)
	return tweets
