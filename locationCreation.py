
import pandas as pd
import pickle

locationdata = pd.read_csv('worldcities.csv')
locationdata = locationdata[['city_ascii','country','iso2','iso3']]
Location = locationdata['city_ascii'].tolist()
country = locationdata['country'].tolist()
Location.extend(list(set(country)))
countrycode = locationdata['iso3'].tolist()
countrycode.extend(list(set(countrycode)))
location_dict = {}
for key,val in zip(Location,countrycode):
    location_dict[key]=val

STATES = Location
STATE_DICT = location_dict
INV_STATE_DICT={}
for value,key in zip(locationdata['country'],locationdata['iso3']):
    INV_STATE_DICT[key]=value

data = [STATES,STATE_DICT,INV_STATE_DICT]
pickle.dump(data, open( "countries.p", "wb" ) )
