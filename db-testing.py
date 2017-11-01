import sqlite3

conn = sqlite3.connect('smi.db')
c = conn.cursor()

target = raw_input('Access data for what account?\n> ')

tweets = c.execute('select * from tweets where screen_name = ?', (target, )).fetchall()

print 'Found %i tweets from %s.' % (len(tweets), target)

for tweet in tweets:
	print tweet