from datetime import datetime, timezone
from dateutil import tz
import datetime
import pickle
from nltk.probability import FreqDist
import re


DATABASE_NAME = 'Twitterdata.db'
TABLE_NAME = "Tweets"
STATES,STATE_DICT,INV_STATE_DICT = pickle.load(open('countries.p','rb'))
TRACK_WORDS_KEY=["COVID19"]

def datakeyValue(words):
    fdist = FreqDist(words)
    d_k_v = {a: x for a, x in fdist.most_common(2000)}
    return d_k_v

def hastag(text):
    return re.findall(r'\B#\w*[a-zA-Z]+\w*', text)

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
