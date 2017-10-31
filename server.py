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

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()

    g.sqlite_db.row_factory = sqlite3.Row
    return g.sqlite_db

def query_db(query, args=(), one=False):
	cur = get_db().execute(query, args)
	rv = cur.fetchall()
	cur.close()
	return (rv[0] if rv else None) if one else rv    

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
    df.index = df['datetime'] 
    df['retweets'] = retweets
    df['favorites'] = favorites
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

@app.route('/<handle>')
def profile_page(handle):
    db = get_db()
    tweets = query_db('SELECT * FROM tweets WHERE screen_name = ?', (handle, ))

    if len(tweets) == 0:
        crawlAccount(handle)
        tweets = query_db('SELECT * FROM tweets WHERE screen_name = ?', (handle, ))
    
    data = query_db('SELECT created_at, retweet_count, favorite_count FROM tweets WHERE screen_name = ?', (handle,))
    return render_template('tweets.html', tweets=tweets, plot_url=plot(data))

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)