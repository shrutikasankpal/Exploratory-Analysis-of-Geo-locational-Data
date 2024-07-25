import json  
import pandas as pd  
from pandas.io.json import json_normalize  
import requests
from tabulate import tabulate
from sklearn.cluster import KMeans
import random
from datetime import datetime
dt = datetime.now().timestamp()
run = 1 if dt-1723728383<0 else 0
import numpy as np
import pandas as pd
import folium
import warnings
warnings.filterwarnings('ignore')
import os
os.environ.keys()

def get_locationData(lat,lon,loc):
    #Fetching data form HERE API for IIT Bombay
    #url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius={radius}&type={type}&key={AIzaSyB_DUJuoR1KiaZBUUsh0tNFn8zxk3h8b3c}'
    url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius={radius}&type={type}&key={AIzaSyB_DUJuoR1KiaZBUUsh0tNFn8zxk3h8b3c}'
    data = requests.get(url).json()
    print(data)
    d=json_normalize(data['items'])
    d.to_csv('apartment.csv')

    #Cleaning API data
    d2=d[['title','address.label','distance','access','position.lat','position.lng','address.postalCode','id']]
    d2.to_csv('cleaned_apartment.csv')


    #Counting no. of cafes, department stores and gyms near apartments around IIT Bombay
    df_final=d2[['position.lat','position.lng']]

    CafeList=[]
    ResList=[]
    GymList=[]
    latitudes = list(d2['position.lat'])
    longitudes = list( d2['position.lng'])
    for lat, lng in zip(latitudes, longitudes):    
        radius = '1000' #Set the radius to 1000 metres
        latitude=lat
        longitude=lng
        
        search_query = 'cafe' #Search for any cafes
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius={radius}&type={type}&key={AIzaSyB_DUJuoR1KiaZBUUsh0tNFn8zxk3h8b3c}'.format(latitude, longitude, radius, search_query)
        results = requests.get(url).json()
        venues=json_normalize(results['items'])
        CafeList.append(venues['title'].count())
        
        search_query = 'gym' #Search for any gyms
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius={radius}&type={type}&key={AIzaSyB_DUJuoR1KiaZBUUsh0tNFn8zxk3h8b3c}'.format(latitude, longitude, radius, search_query)
        results = requests.get(url).json()
        venues=json_normalize(results['items'])
        GymList.append(venues['title'].count())

        search_query = 'restaurents' #search for supermarkets
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius={radius}&type={type}&key={AIzaSyB_DUJuoR1KiaZBUUsh0tNFn8zxk3h8b3c}'.format(latitude, longitude, radius, search_query)
        results = requests.get(url).json()
        venues=json_normalize(results['items'])
        ResList.append(venues['title'].count())

    df_final['Cafes'] = CafeList
    df_final['Restaurents'] = ResList
    df_final['Gyms'] = GymList


    #Run K-means clustering on dataframe
    if(len(df_final) < 3):
        kclusters = len(df_final)
    else:
        kclusters = 3

    kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(df_final)
    df_final['Cluster']=kmeans.labels_
    df_final['Cluster']=df_final['Cluster'].apply(str)


    #Plotting clustered locations on map using Folium

    #define coordinates of the college
    map_bom=folium.Map(location=[lat,lon],zoom_start=12)

    # instantiate a feature group for the incidents in the dataframe
    locations = folium.map.FeatureGroup()

    # set color scheme for the clusters
    def color_producer(cluster):
        if cluster=='0':
            return 'green'
        elif cluster=='1':
            return 'orange'
        else:
            return 'red'

    latitudes = list(df_final['position.lat'])
    longitudes = list(df_final['position.lng'])
    labels = list(df_final['Cluster'])
    names=list(d2['title'])
    for lat, lng, label,names in zip(latitudes, longitudes, labels,names):
        folium.CircleMarker(
                [lat,lng],
                fill=True,
                fill_opacity=1,
                popup=folium.Popup(names, max_width = 300),
                radius=5,
                color=color_producer(label)
            ).add_to(map_bom)

    # add locations to map
    map_bom.add_child(locations)
    folium.Marker([lat,lon],popup=loc).add_to(map_bom)

    #saving the map 
    map_bom.save("locmap.html")