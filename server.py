from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify
from scraper import crawlAccount
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import numpy as np
import sqlite3
import base64
import os
import re
import io

app = Flask(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'smi.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'

))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

class Tweet():
    def __init__(self, tweet):
        self.tweetText = tweet['text']
        self.id = tweet['id']
        self.retweet_count = tweet['retweet_count']
        self.favorite_count = tweet['favorite_count']
        self.created_at = tweet['created_at']
        self.screen_name = tweet['user']['screen_name'].lower()
        self.followers_count = tweet['user']['followers_count']

    def insert(self):
        with sqlite3.connect('smi.db') as con:
            cur = con.cursor()
            cur.execute("INSERT INTO tweets (screen_name, followers_count, tweetText, id, favorite_count, retweet_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                    (
                    self.screen_name, 
                    self.followers_count, 
                    self.tweetText, 
                    self.id, 
                    self.favorite_count, 
                    self.retweet_count, 
                    self.created_at
                    )   
                )
        con.commit()


def to_datetime(datestring):
    unformatted = datestring

    # Use re to get rid of the milliseconds.
    remove_ms = lambda x:re.sub("\+\d+\s","",x)

    # Make the string into a datetime object.
    mk_dt = lambda x:datetime.strptime(remove_ms(x), "%a %b %d %H:%M:%S %Y")

    # Format your datetime object.
    my_form = lambda x:"{:%d/%m/%Y}".format(mk_dt(x))

    return mk_dt(unformatted)

def plot(data):
    print 'Receiving %i lines to plot...' % len(data)
    dates = []
    retweets = []
    favorites = []

    for d in data:
        dates.append(to_datetime(d[0]))
        retweets.append(d[1])
        favorites.append(d[2])

    img = io.BytesIO()

    df = pd.DataFrame()
    df['datetime'] = dates
    df['retweets'] = retweets
    df['favorites'] = favorites
    df.index = pd.DatetimeIndex(dates)

    df.resample('d').sum()
    df.plot.line()

    plt.savefig(img, format='png')
    
    img.seek(0)       
    plot_url = base64.b64encode(img.getvalue())

    return plot_url

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def home():
    return render_template('tweets.html')

@app.route('/load/<screen_name>')
def profile_page(screen_name):
    screen_name = screen_name.lower()
    not_allowed = ['favicon.ico']
    keys = ['screen_name', 'followers_count', 'tweetText', 'id', 'favorite_count', 'retweet_count', 'created_at']

    if screen_name in not_allowed:
        return render_template('error.html', screen_name=screen_name), 404

    print 'Query: Twitter handle %s...' % screen_name
    
    # check for database
    if not os.path.isfile('smi.db'):
        conn = sqlite3.connect('smi.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE tweets (screen_name text, followers_count int, tweetText text, id int, favorite_count int, retweet_count int, created_at date)''')

    # establishing connection to db
    conn = sqlite3.connect('smi.db')
    c = conn.cursor()

    c.execute('SELECT * FROM tweets where screen_name = ?', (screen_name, ))

    tweets = c.fetchall()
    print '%i tweets by %s in database...' % (len(tweets), screen_name)

    if len(tweets) == 0:
        tweets = crawlAccount(screen_name)    

        print 'Finished crawling %s. Found %i tweets. Saving...' % (screen_name, len(tweets)),
        for tweet in tweets:
            Tweet(tweet).insert()
        print 'Done.'

    with sqlite3.connect('smi.db') as con:
        c.execute('SELECT created_at, retweet_count, favorite_count FROM tweets WHERE screen_name = ?', (screen_name, ))
        data = c.fetchall()

        tweets = c.execute('SELECT * FROM tweets WHERE screen_name = ?', (screen_name, ))
        tweets = c.fetchall()

    tweet_dicts = []
    for tweet in tweets:
        td = dict(zip(keys, tweet))
        tweet_dicts.append(td)

    print '%i tweets by %s in database...' % (len(tweets), screen_name)
    return render_template('tweets.html', tweets=tweet_dicts, plot_url=plot(data))

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)