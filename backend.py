from pickletools import long1
from flask import Flask, redirect, url_for, render_template, request, make_response

import shutil
import os
import random

import json

from geopy.geocoders import GoogleV3
import geopy.distance
import googlemaps

import folium
import pandas as pd

from datetime import datetime


app = Flask(__name__)

API = ''
geolocator = GoogleV3(api_key=API)

from math import radians, cos, sin, asin, sqrt

def distance(lat1, lat2, lon1, lon2):
    
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
      
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
 
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371
      
    # calculate the result
    return(c * r * 1.609344)

@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":

        # get current time
        current_time = "" + datetime.now().strftime("%H:%M")


        # generate map
        user = request.form["nm"]
        print(user)
        #geolocation = [geolocator.geocode(user).latitude,geolocator.geocode(user).longitude]
        long = geolocator.geocode(user).longitude
        lat = geolocator.geocode(user).latitude

        m = folium.Map(location=[lat,long], zoom_start=20, tiles='OpenStreetMap')
        # add searched marker
        folium.Marker(location=[lat,long],popup="You are here!",icon=folium.Icon(color="red", icon="user", prefix='fa'),).add_to(m)

        day = "mon"
        start_park_time = current_time
        end_park_time = "17:30"

        time1 = int(start_park_time[:2]) * 60 + int(start_park_time[3:])
        time2 = int(end_park_time[:2]) * 60 + int(end_park_time[3:])
        time = time2 - time1

        #bay_location = pd.read_json(r"C:\Users\mghosh22\Desktop\project2\parking-aggregator\on_street_parking.json")

        def sort_location(origin_lat, origin_lon, sorted_on='distance', radius=1):

            sorted_list= [] 
            # opens json file
            with open(r'C:\Users\mghosh22\Desktop\project2\parking-aggregator\off_street_data.json') as data_file:
                data = json.load(data_file)
            for park in data["parkings"]:
                point_distance = distance(origin_lat, park['geocode']['latitude'], origin_lon , park['geocode']['longitude'])
                if point_distance<radius:
                    final=[park['location'],point_distance, park['geocode']['latitude'], 
                    park['geocode']['longitude'], park["fee"], park["nearby"][:3], park["labels"]]
                    sorted_list.append([point_distance, park['fee'], final])
            # finds sorter key
            if sorted_on == 'price':
                sorter= lambda x:[x[1], x[0]]
            else:
                sorter= lambda x:[x[0]]
            data_file.close()

            with open(r'C:\Users\mghosh22\Desktop\project2\parking-aggregator\on_street_parking.json') as data_file:
                data = json.load(data_file)
            for key, value in data["status"].items():
                if(value == "Present"):
                    continue
                destination_lat=data['lat'][str(key)]
                destination_lon=data['lon'][str(key)]
                point_distance= distance(origin_lat, float(destination_lat), origin_lon , float(destination_lon))
                if point_distance < radius:
                    final=[data["address"][key], point_distance, float(destination_lat), float(destination_lon), data["mon"][str(key)][0][3]]
                    sorted_list.append([point_distance, data["mon"][str(key)][0][3], final])
            if sorted_on == 'price':
                sorter= lambda x:[x[1],x[0]]
            else:
                sorter= lambda x:[x[0]]

            sorted_list=sorted(sorted_list, key=sorter)[:5]
            final_list=[]
            for i in sorted_list:
                final_list.append(i[2])
            return final_list
    
        final_list = sort_location(lat, long, 'distance', 5)
        def userMarker():
            for item in final_list:
                latitude = item[2]
                longitude = item[3]
                #on street
                if len(item) == 5:
                    txt = "$" + str(item[4]) + "\n"
                    txt += "\n" + str(item[0])
                    #txt += "\n" + "$" + str(item[4])
                    folium.Marker(location=[latitude,longitude],popup=txt,icon=folium.Icon(color="green", icon="road", prefix='fa'),).add_to(m)
                else:
                    txt = "$" + str(item[4]) + "\n"
                    txt += "\n" + str(item[0]) + "\n"
                    txt += "Featured nearby places: " + ", ".join(item[5])
                    folium.Marker(location=[latitude,longitude],popup=txt,icon=folium.Icon(color="blue", icon="arrow-down", prefix='fa'),).add_to(m)

            
                print(item[3])
            #print(final_list)
            m.save('map.html')

        userMarker()

        #add all nearby markers here

        # m.save("map.html")

        shutil.move("map.html", "templates/map.html")


        return render_template("base.html")
        #return redirect(url_for("parkspots", usr=source_code))
    else:
        return render_template("index.html")

#https://stackoverflow.com/questions/37379374/insert-the-folium-maps-into-the-jinja-template
@app.route('/map')
def map():
    r = int(random.triangular(0,100))
    t = "templates/map_{i}.html"
    for i in range(0,100):
        f = t.format(i=i)
        if os.path.exists(f):
            os.remove(f)
    f = t.format(i=r)
    shutil.copy("templates/map.html", f)

    r = make_response(render_template(os.path.split(f)[1]))
    r.cache_control.max_age = 0
    r.cache_control.no_cache = True
    r.cache_control.no_store = True
    r.cache_control.must_revalidate = True
    r.cache_control.proxy_revalidate = True
    return r

    # return render_template("map.html")

# @app.route("/parkingspots")
# def parkspots(usr):
#     return render_template("parkspots.html", content=usr)


if __name__ == "__main__":
    app.run(debug=True)
