import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
import itertools
import math
import base64
from flask import Flask
import os
#import psycopg2
import datetime
import sqlite3

import re
import nltk
#nltk.download('punkt')
#nltk.download('stopwords')
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from textblob import TextBlob
import config as c

from io import BytesIO

import pandas as pd
import base64
from wordcloud import WordCloud, STOPWORDS
from PIL import Image
import numpy as np


def plot_wordcloud(data):
    mask = np.array(Image.open('twitter_mask.png'))
    wc = WordCloud(width=280, height=280,background_color="white", max_words=2000, mask=mask,font_path='cabin-sketch.bold.ttf',
                contour_width=3, contour_color='steelblue')
    wc.fit_words(data)

    return wc.to_image()


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Real-Time Twitter Analysis'

server = app.server


app.layout = html.Div(children=[
    html.H2('Real-time Twitter Analysis', style={
        'textAlign': 'center'
    }),


    html.Div(id='live-update-graph'),
    html.Div(id='live-update-graph-bottom'),

    # Author's Words
    html.Br(),

    # ABOUT ROW
    html.Div(
        className='row',
        children=[
            html.Div(
                className='three columns',
                children=[
                    html.P(
                    'Data extracted using:'
                    ),
                    html.A(
                        'Twitter API',
                        href='https://developer.twitter.com'
                    )
                ]
            ),
            html.Div(
                className='three columns',
                children=[
                    html.P(
                    'Code avaliable at:'
                    ),
                    html.A(
                        'GitHub',
                        href='https://github.com/raiakash203'
                    )
                ]
            ),
            html.Div(
                className='three columns',
                children=[
                    html.P(
                    'Made with:'
                    ),
                    html.A(
                        'Dash / Plot.ly',
                        href='https://plot.ly/dash/'
                    )
                ]
            ),
            html.Div(
                className='three columns',
                children=[
                    html.P(
                    'Author:'
                    ),
                    html.A(
                        'Akash Rai',
                        href='https://www.linkedin.com/in/akash-rai-59906589/'
                    )
                ]
            )
        ], style={'marginLeft': 70, 'fontSize': 16}
    ),

    dcc.Interval(
        id='interval-component-slow',
        interval=5*10000, # in milliseconds
        n_intervals=0
    )
    ], style={'padding': '20px'})



@app.callback(Output('live-update-graph', 'children'),
              [Input('interval-component-slow', 'n_intervals')])


def update_graph_live(n):

    # Loading data from Heroku PostgreSQL
    conn = sqlite3.connect(c.DATABASE_NAME)
    timenow = (datetime.datetime.utcnow() - datetime.timedelta(hours=0, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
    query = "SELECT id_str, text, created_at, polarity,user_location FROM {} WHERE created_at >= '{}'".format(c.TABLE_NAME, timenow)
    df = pd.read_sql(query, con=conn)

    dailytime = (datetime.datetime.now() - datetime.timedelta(days = 1,hours=0, minutes=0)).strftime('%Y-%m-%d')
    dailytime = dailytime+' 18:30:00'
    query = "SELECT count(*) FROM {} WHERE created_at >= '{}'".format(c.TABLE_NAME,dailytime)
    dailycount = pd.read_sql(query, con=conn)

    query = "SELECT count(*) FROM {}".format(c.TABLE_NAME)
    totaltillnow = pd.read_sql(query, con=conn)

    conn.close()

    # Convert UTC into PDT

    df['polarity'] = df['polarity'].apply(c.polarity_change)
    df['created_at'] = df['created_at'].apply(c.dateconversion)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['created_at'] = df['created_at'].apply(lambda x:x.tz_localize(None))

    # Clean and transform data to enable time series
    result = df.groupby([pd.Grouper(key='created_at', freq='10s'), 'polarity']).count().unstack(fill_value=0).stack().reset_index()
    result = result.rename(columns={"id_str": "Num of '{}' mentions".format(c.TRACK_WORDS_KEY[0]), "created_at":"Time"})
    time_series = result["Time"][result['polarity']==0].reset_index(drop=True)

    min10 = datetime.datetime.now() - datetime.timedelta(hours=0, minutes=10)
    min20 = datetime.datetime.now() - datetime.timedelta(hours=0, minutes=20)

    neu_num = result[result['Time']>min10]["Num of '{}' mentions".format(c.TRACK_WORDS_KEY[0])][result['polarity']==0].sum()
    neg_num = result[result['Time']>min10]["Num of '{}' mentions".format(c.TRACK_WORDS_KEY[0])][result['polarity']==-1].sum()
    pos_num = result[result['Time']>min10]["Num of '{}' mentions".format(c.TRACK_WORDS_KEY[0])][result['polarity']==1].sum()



    daily_impressions= totaltillnow['count(*)'][0]
    daily_tweets_num = dailycount['count(*)'][0]
    # Percentage Number of Tweets changed in Last 10 mins

    count_now = df[df['created_at'] > min10]['id_str'].count()
    count_before = df[ (min20 < df['created_at']) & (df['created_at'] < min10)]['id_str'].count()
    percent = (count_now-count_before)/count_before*100
    # Create the graph
    children = [
                html.Div(
                    className='row',
                    children=[
                        html.Div(
                            children=[
                                html.P('Tweets/10 Mins Changed By',
                                    style={
                                        'fontSize': 17
                                    }
                                ),
                                html.P('{0:.2f}%'.format(percent) if percent <= 0 else '+{0:.2f}%'.format(percent),
                                    style={
                                        'fontSize': 40
                                    }
                                )
                            ],
                            style={
                                'width': '20%',
                                'display': 'inline-block'
                            }

                        ),
                        html.Div(
                            children=[
                                html.P('Total Tweets Till Now',
                                    style={
                                        'fontSize': 17
                                    }
                                ),
                                html.P('{0:.1f}K'.format(daily_impressions/1000) \
                                        if daily_impressions < 1000000 else \
                                            ('{0:.1f}M'.format(daily_impressions/1000000) if daily_impressions < 1000000000 \
                                            else '{0:.1f}B'.format(daily_impressions/1000000000)),
                                    style={
                                        'fontSize': 40
                                    }
                                )
                            ],
                            style={
                                'width': '20%',
                                'display': 'inline-block'
                            }
                        ),
                        html.Div(
                            children=[
                                html.P('Total Tweets Today',
                                    style={
                                        'fontSize': 17
                                    }
                                ),
                                html.P('{0:.1f}K'.format(daily_tweets_num/1000),
                                    style={
                                        'fontSize': 40
                                    }
                                )
                            ],
                            style={
                                'width': '20%',
                                'display': 'inline-block'
                            }
                        ),

                        html.Div(
                            children=[
                                html.P("Currently tracking Keyword related to \"COVID\" .",
                                    style={
                                        'fontSize': 25
                                    }
                                ),
                            ],
                            style={
                                'width': '40%',
                                'display': 'inline-block'
                            }
                        ),

                    ],
                    style={'marginLeft': 70}
                ),

                html.Div([
                    html.Div([
                        dcc.Graph(
                            id='crossfilter-indicator-scatter',
                            figure={
                                'data': [
                                    go.Scatter(
                                        x=time_series,
                                        y=result["Num of '{}' mentions".format(c.TRACK_WORDS_KEY[0])][result['polarity']==0].reset_index(drop=True),
                                        name="Neutrals",
                                        opacity=0.8,
                                        mode='lines',
                                        line=dict(width=0.5, color='rgb(131, 90, 241)'),
                                        stackgroup='one'
                                    ),
                                    go.Scatter(
                                        x=time_series,
                                        y=result["Num of '{}' mentions".format(c.TRACK_WORDS_KEY[0])][result['polarity']==-1].reset_index(drop=True).apply(lambda x: -x),
                                        name="Negatives",
                                        opacity=0.8,
                                        mode='lines',
                                        line=dict(width=0.5, color='rgb(255, 50, 50)'),
                                        stackgroup='two'
                                    ),
                                    go.Scatter(
                                        x=time_series,
                                        y=result["Num of '{}' mentions".format(c.TRACK_WORDS_KEY[0])][result['polarity']==1].reset_index(drop=True),
                                        name="Positives",
                                        opacity=1,
                                        mode='lines',
                                        line=dict(width=0.5, color='rgb(51, 255, 255)'),
                                        stackgroup='three'
                                    )
                                ]
                            }
                        )
                    ], style={'width': '73%', 'display': 'inline-block', 'padding': '0 0 0 20'}),

                    html.Div([
                        dcc.Graph(
                            id='pie-chart',
                            figure={
                                'data': [
                                    go.Pie(
                                        labels=['Positives', 'Negatives', 'Neutrals'],
                                        values=[pos_num, neg_num, neu_num],
                                        name="View Metrics",
                                        marker_colors=['rgba(51, 255, 255, 0.6)','rgba(255, 50, 50, 0.6)','rgba(131, 90, 241, 0.6)'],
                                        textinfo='value',
                                        hole=.65)
                                ],
                                'layout':{
                                    'showlegend':False,
                                    'title':'Tweets In Last 10 Mins',
                                    'annotations':[
                                        dict(
                                            text='{0:.1f}K'.format((pos_num+neg_num+neu_num)/1000),
                                            font=dict(
                                                size=40
                                            ),
                                            showarrow=False
                                        )
                                    ]
                                }

                            }
                        )
                    ], style={'width': '27%', 'display': 'inline-block'})
                ]),
            ]

    return children


@app.callback(Output('live-update-graph-bottom', 'children'),
              [Input('interval-component-slow', 'n_intervals')])
def update_graph_bottom_live(n):

    # Loading data from Heroku PostgreSQL
    conn = sqlite3.connect(c.DATABASE_NAME)
    mycursor = conn.cursor()
    timenow = (datetime.datetime.utcnow() - datetime.timedelta(hours=0, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
    query = "SELECT id_str, text, created_at, polarity,user_location FROM {} WHERE created_at >= '{}'".format(c.TABLE_NAME, timenow)
    df = pd.read_sql(query, con=conn)
    conn.close()



    # Convert UTC into PDT
    df['created_at'] = df['created_at'].apply(c.dateconversion)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['created_at'] = df['created_at'].apply(lambda x:x.tz_localize(None))


    # Clean and transform data to enable word frequency
    content = ' '.join(df["text"])
    content = re.sub(r"http\S+", "", content)
    content = content.replace('RT ', ' ').replace('&amp;', 'and')
    hashtags = c.hastag(content)
    content = re.sub('[^A-Za-z0-9]+', ' ', content)
    content = content.lower()

    # Filter constants for states in US
    #STATES,STATE_DICT,INV_STATE_DICT = c.STATES,c.STATE_DICT,c.INV_STATE_DICT
    STATES,STATE_DICT,INV_STATE_DICT = pickle.load(open('countries.p','rb'))
    # Clean and transform data to enable geo-distribution
    is_in_US=[]
    geo = df[['user_location']]
    df = df.fillna(" ")
    for x in df['user_location']:
        check = False
        for s in STATES:
            if s in x:
                is_in_US.append(STATE_DICT[s] if s in STATE_DICT else s)
                check = True
                break
        if not check:
            is_in_US.append(None)

    geo_dist = pd.DataFrame(is_in_US, columns=['State']).dropna().reset_index()
    geo_dist = geo_dist.groupby('State').count().rename(columns={"index": "Number"}) \
        .sort_values(by=['Number'], ascending=False).reset_index()
    geo_dist["Log Num"] = geo_dist["Number"].apply(lambda x: math.log(x, 2))


    geo_dist['Full State Name'] = geo_dist['State'].apply(lambda x: INV_STATE_DICT[x])
    geo_dist['text'] = geo_dist['Full State Name'] + '<br>' + 'Num: ' + geo_dist['Number'].astype(str)


    tokenized_word = word_tokenize(content)
    stop_words=set(stopwords.words("english"))
    #stop_words=[]
    filtered_sent=[]
    for w in tokenized_word:
        if (w not in stop_words) and (len(w) >= 3):
            filtered_sent.append(w)

    fdist = FreqDist(hashtags)
    fd = pd.DataFrame(fdist.most_common(10), columns = ["Word","Frequency"]).drop([0]).reindex()
    #fd['Polarity'] = fd['Word'].apply(lambda x: TextBlob(x).sentiment.polarity)
    #fd['Marker_Color'] = fd['Polarity'].apply(lambda x: 'rgba(255, 50, 50, 0.6)' if x < -0.1 else \
    #    ('rgba(51, 255, 255, 0.6)' if x > 0.1 else 'rgba(131, 90, 241, 0.6)'))
    #fd['Line_Color'] = fd['Polarity'].apply(lambda x: 'rgba(255, 50, 50, 1)' if x < -0.1 else \
    #    ('rgba(51, 255, 255, 1)' if x > 0.1 else 'rgba(131, 90, 241, 1)'))

    #print(fd['Marker_Color'].loc[::-1])
    #print(fd['Word'].loc[::-1].tolist())
    #print(geo_dist)

    word_cloud_words = c.datakeyValue(filtered_sent)
    img = BytesIO()
    plot_wordcloud(data=word_cloud_words).save(img, format='PNG')


    # Create the graph
    children = [
                html.Div([
                    dcc.Graph(
                        id='x-time-series',
                        figure = {
                            'data':[
                                go.Bar(
                                    x=fd["Frequency"].loc[::-1],
                                    y=fd["Word"].loc[::-1],
                                    name="Freq Dist",
                                    orientation='h',
                                    #marker_color=fd['Marker_Color'].loc[::-1].tolist(),
                                    #marker=dict(
                                    #    line=dict(
                                    #        color=fd['Line_Color'].loc[::-1].tolist(),
                                    #        width=1),
                                    #    ),
                                )
                            ],
                            'layout':{
                                'hovermode':"closest",
                                'title' : 'Top Hashtags in last half hour'
                            }
                        }
                    )
                ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 0 0 20'}),


                html.Div([
                    dcc.Graph(
                        id='y-time-series',
                        figure = {
                            'data':[
                                go.Choropleth(
                                    locations=geo_dist['State'], # Spatial coordinates
                                    z = geo_dist['Log Num'].astype(float), # Data to be color-coded
                                    locationmode = 'ISO-3', # set of locations match entries in `locations`
                                    #colorscale = "Blues",
                                    text=geo_dist['text'], # hover text
                                    geo = 'geo',
                                    colorbar_title = "Num in Log2",
                                    marker_line_color='white',
                                    colorscale = ["rgb(234, 234, 250)", "rgb(19, 19, 83)"],
                                    #autocolorscale=False,
                                    #reversescale=True,
                                )
                            ],
                            'layout': {
                                'title': "Geographic Segmentation over World",
                                'geo':{'scope':'world'}
                            }
                        }

                    )
                ], style={'display': 'inline-block', 'width': '51%'}),
                html.Div(
                 children=[
                            html.P("WordCloud of top words in Tweet ",style={"text-align":"center","font-family": '"Open Sans", verdana, arial, sans-serif','font-size': '17px','fill': 'rgb(68, 68, 68)','opacity': '1','font-weight': 'normal','white-space': 'pre'}),
                            html.Img(src='data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode()),style={'height': '350px','display': 'block','margin-left': 'auto','margin-right': 'auto'})
                        ]
            )
        ]
    return children


if __name__ == '__main__':
    app.run_server(debug=True)
