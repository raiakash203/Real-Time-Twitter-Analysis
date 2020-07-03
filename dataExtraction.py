import re
import tweepy
import sqlite3
import pandas as pd
from textblob import TextBlob
import sqlite3
from datetime import datetime, timezone
from dateutil import tz
import pandas as pd
import time
import math
import datetime
import re


TRACK_WORDS=["Corona Virus","Corona","COVID19","Covid-19"]
DATABASE_NAME = 'Twitterdata.db'
TABLE_NAME = "Tweets"
TABLE_ATTRIBUTES = "id_str VARCHAR(255), created_at DATETIME, text VARCHAR(255), \
            polarity INT, subjectivity INT, user_created_at VARCHAR(255), user_location VARCHAR(255), \
            user_description VARCHAR(255), user_followers_count INT, longitude DOUBLE, latitude DOUBLE, \
            retweet_count INT, favorite_count INT"

conn = sqlite3.connect(DATABASE_NAME)
mycursor = conn.cursor()
mycursor.execute("CREATE TABLE IF NOT EXISTS {} ({})".format(TABLE_NAME,TABLE_ATTRIBUTES))
conn.commit()
mycursor.close()


def clean_tweet(self, tweet):
    '''
    Use sumple regex statemnents to clean tweet text by removing links and special characters
    '''
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t]) \
                                |(\w+:\/\/\S+)", " ", tweet).split())
def deEmojify(text):
    '''
    Strip all non-ASCII characters to remove emoji characters
    '''
    if text:
        return text.encode('ascii', 'ignore').decode('ascii')
    else:
        return None

def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

def aslocaltimestr(utc_dt):
    return utc_to_local(utc_dt).strftime('%Y-%m-%d %H:%M:%S')

def polarity_change(polarity):
    if polarity<0:
        polarity = -1
    elif polarity>0:
        polarity = 1
    else:
        polarity = 0
    return polarity

def dateconversion(text):
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    utc = datetime.datetime.strptime(text, '%Y-%m-%d %H:%M:%S')
    utc = utc.replace(tzinfo=from_zone)
    central = utc.astimezone(to_zone)
    return central

class MyStreamListener(tweepy.StreamListener):
    '''
    Tweets are known as “status updates”. So the Status class in tweepy has properties describing the tweet.
    https://developer.twitter.com/en/docs/tweets/data-dictionary/overview/tweet-object.html
    '''

    def on_status(self, status):
        '''
        Extract info from tweets
        '''
        if status.retweeted:
            # Avoid retweeted info, and only original tweets will be received
            return True
        # Extract attributes from each tweet
        id_str = status.id_str
        #created_at = aslocaltimestr(status.created_at)
        created_at = status.created_at
        print(type(status.created_at))
        text = status.text
        if hasattr(status, 'extended_tweet'):
            text = status.extended_tweet['full_text']
        if hasattr(status, 'retweeted_status') and hasattr(status.retweeted_status, 'extended_tweet'):
            text = status.retweeted_status.extended_tweet['full_text']

        text = deEmojify(text)    # Pre-processing the text
        #print(text)
        sentiment = TextBlob(text).sentiment
        polarity = sentiment.polarity
        subjectivity = sentiment.subjectivity

        user_created_at = status.user.created_at
        user_location = deEmojify(status.user.location)
        user_description = deEmojify(status.user.description)
        user_followers_count =status.user.followers_count
        longitude = None
        latitude = None
        if status.coordinates:
            longitude = status.coordinates['coordinates'][0]
            latitude = status.coordinates['coordinates'][1]

        retweet_count = status.retweet_count
        favorite_count = status.favorite_count

        print(text)
        print("Long: {}, Lati: {}".format(longitude, latitude))

        # Store all data in MySQL
        if conn:
            mycursor = conn.cursor()
            sql = "INSERT INTO {} (id_str, created_at, text, polarity, subjectivity, user_created_at, user_location, user_description, user_followers_count, longitude, latitude, retweet_count, favorite_count) VALUES (?, ?, ?, ?, ?,?, ?, ?, ?, ?, ?, ?, ?)".format(TABLE_NAME)
            val = (id_str, created_at, text, polarity, subjectivity, user_created_at, user_location, \
                user_description, user_followers_count, longitude, latitude, retweet_count, favorite_count)
            mycursor.execute(sql, val)
            conn.commit()
            mycursor.close()

    def on_error(self, status_code):
        '''
        Since Twitter API has rate limits, stop srcraping data as it exceed to the thresold.
        '''
        if status_code == 420:
            # return False to disconnect the stream
            return False


consumer_key = ""
consumer_secret = ""
access_key = ""
access_secret = ""

#auth  = tweepy.OAuthHandler(consumer_key, consumer_secret)
#auth.set_access_token(access_key, access_secret)
#api = tweepy.API(auth)

while True:
    try:
        auth  = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_key, access_secret)
        api = tweepy.API(auth)
        myStreamListener = MyStreamListener()
        myStream = tweepy.Stream(auth = api.auth, listener = myStreamListener,tweet_mode='extended')
        myStream.filter(languages=["en"],track=TRACK_WORDS)
    except:
        continue
