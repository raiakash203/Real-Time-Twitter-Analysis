
import pandas as pd
import pickle

locationdata = pd.read_csv('worldcities.csv')
locationdata = locationdata[['city_ascii','country','iso2','iso3']]
STATES = locationdata['city_ascii'].tolist()
iso3_l = locationdata['iso3'].tolist()
STATE_DICT={}
for k,v in zip(STATES,iso3_l):
    STATE_DICT[k]=v
country = locationdata['country'].tolist()
for k,v in zip(country,iso3_l):
    STATE_DICT[k]=v
INV_STATE_DICT = {}
for k,v in zip(iso3_l,country):
    INV_STATE_DICT[k]=v
data = [STATES,STATE_DICT,INV_STATE_DICT]
pickle.dump(data, open( "countries.p", "wb" ) )
