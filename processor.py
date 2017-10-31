import sqlite3
import json
import sys
import os

class Tweet():
    def __init__(self, tweet):
        self.text = tweet['text']
        self.id = tweet['id']
        self.retweet_count = tweet['retweet_count']
        self.favorite_count = tweet['favorite_count']
        self.created_at = tweet['created_at']
        self.screen_name = tweet['user']['screen_name']
        self.followers_count = tweet['user']['followers_count']

    def insert(self, target):
    	conn = sqlite3.connect('smi.db')
    	c = conn.cursor()
        c.execute("INSERT INTO tweets (screen_name, followers_count, tweetText, id, favorite_count, retweet_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (self.screen_name, self.followers_count, self.text, self.id, self.favorite_count, self.retweet_count, self.created_at)	)
        conn.commit()

    def show(self):
    	return [self.text, self.id, self.retweet_count, self.favorite_count, self.created_at]

def processTweet(target, tweet_json):
	if not os.path.isfile('smi.db'):
		conn = sqlite3.connect('smi.db')
		c = conn.cursor()
		c.execute('''CREATE TABLE tweets (screen_name text, followers_count int, tweetText text, id int, favorite_count int, retweet_count int, created_at date)'''.format(target))
	
	conn = sqlite3.connect('smi.db')
	c = conn.cursor()
	ids = c.execute('SELECT id FROM tweets').fetchall()

	tweet = Tweet(tweet_json)

	if tweet.id not in ids:
		tweet.insert(target)

if __name__ == '__main__':
	target = raw_input('Input target Twitter-handle to add to database:\n> ')

	crawlAccount(target)
