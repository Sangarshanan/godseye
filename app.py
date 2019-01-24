from flask import Flask, render_template, request, url_for, redirect, render_template_string
from shapely.geometry import Point
import geopandas as gpd
import pandas as pd
from pandas import DataFrame, merge
import folium
import numpy as np
from scipy import spatial
import psycopg2
from folium.features import DivIcon
import json


def ReadConfig():
    """
        Reads the configuration variables like hostname, username, password and databasename from config.json file

        returns A json object of config variables
    """
    with open('config.json') as f:
        data = json.load(f)

    return data


app = Flask(__name__)

def doQueryv1(conn, query):
    cur = conn.cursor()
    cur.execute(query)
    if cur.rowcount > 0:
        return cur.fetchall()
    cur.close()


def doQueryv2(conn, query):
    cur = conn.cursor()
    cur.execute(query)
    cur.close()

# Set "homepage" to index.html
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/route')
def index_r():
    return render_template('index_route.html')

@app.route('/route2')
def index_rd():
    return render_template('index_route_delhi.html')


def error_temp(lat_s, long_s, lat_t, long_t, message):
    """
    Returns a blank map when the lat and long not in database.
    """
    start_coords = (float(lat_s), float(long_s))
    folium_map = folium.Map(location=start_coords, zoom_start=14)
    folium.Marker([float(lat_s), float(long_s)], popup='<i>Start</i>').add_to(folium_map)
    folium.Marker([float(lat_t), float(long_t)], popup='<b>End</b>').add_to(folium_map)
    folium.map.Marker([float(lat_s), float(long_s)],\
     icon=DivIcon(icon_size=(120,22),icon_anchor=(0,0),html='<div style="font-size: 24pt">{}</div>'.format(message),)
    ).add_to(folium_map)
    return folium_map.get_root().render()
    # folium_map.save('templates/map1.html')

def read_latlong():

    long_s = request.form['long_s']
    lat_s = request.form['lat_s']
    long_t = request.form['long_t']
    lat_t = request.form['lat_t']

    return float(lat_s), float(long_s), float(lat_t), float(long_t)

def nearest_st(s_geom, t_geom, myConnection):
    s_query = "SELECT source FROM ways WHERE (x1,y1) in \
    (SELECT lon, lat FROM ways_vertices_pgr ORDER BY the_geom <-> ST_GeometryFromText('{}',4326) LIMIT 1) LIMIT 1".format(
        s_geom)
    source = doQueryv1(myConnection, s_query)
    t_query = "SELECT target FROM ways WHERE (x1,y1) in \
    (SELECT lon, lat FROM ways_vertices_pgr ORDER BY the_geom <-> ST_GeometryFromText('{}',4326) LIMIT 1) LIMIT 1".format(
        t_geom)
    target = doQueryv1(myConnection, t_query)

    return source, target

def nearest_st_delhi(s_geom, t_geom, myConnection):
    s_query = "SELECT source FROM ways_delhi WHERE (x1,y1) in \
    (SELECT lon, lat FROM ways_vertices_pgr_delhi ORDER BY the_geom <-> ST_GeometryFromText('{}',4326) LIMIT 1) LIMIT 1".format(
        s_geom)
    source = doQueryv1(myConnection, s_query)
    t_query = "SELECT target FROM ways_delhi WHERE (x1,y1) in \
    (SELECT lon, lat FROM ways_vertices_pgr_delhi ORDER BY the_geom <-> ST_GeometryFromText('{}',4326) LIMIT 1) LIMIT 1".format(
        t_geom)
    target = doQueryv1(myConnection, t_query)

    return source, target

def check_beng(lat, long):
    if (lat>12.782) and (lat<13.135) and (long>77.386) and (long<77.854):
        return True
    else:
        return False

def check_delhi(lat, long):
    if (lat>28.289) and (lat<28.926) and (long>76.878) and (long<77.813):
        return True
    else:
        return False


@app.route('/search', methods=['POST'])
def pin():
    lat1 = request.form['lat']
    long1 = request.form['long']

    b = gpd.read_file('data/blore.geojson')
    c = gpd.read_file('data/chennai.geojson')
    m = gpd.read_file('data/mumbai.geojson')
    a = gpd.read_file('data/ahmedabad.geojson')
    h = gpd.read_file('data/hyderabad.geojson')
    k = gpd.read_file('data/kolkatta.geojson')
    df1 = pd.read_csv('data/allind.csv')

    c['pin_code'] = c['pin']



    data = pd.concat([b, c, m, a, h, k], ignore_index=True, sort=False)

    long = float(long1)
    lat = float(lat1)



    p = Point(long, lat)
    pin = 0
    if lat < 8.4 or lat > 37.6 or long < 68.7 or long > 97.25:
        return render_template('success.html', pin="Sorrry! OUT OF BOUNDS.", lat2=lat, long2=long)

    for i in range(0, len(data)):

        if p.within(data['geometry'][i]) is True:
            pin = int(data['pin_code'][i])

    if pin != 0:
        return render_template('success.html', pin=pin, lat2=lat, long2=long)
    else:
        data1 = df1[['postalcode', 'placename', 'latitude', 'longitude ']]
        latlongs = data1.iloc[:, 2:]
        d = np.array(latlongs)
        tree = spatial.KDTree(d)
        latlongs = np.array([lat, long])
        result = tree.query(latlongs)
        pin = int(data1.iloc[[result[1]]]['postalcode'])

        return render_template('success.html', pin=pin, lat2=lat, long2=long)


@app.route('/search2', methods=['POST'])
def routing():
    '''
    Finds the distance for two Latitude and Longitude in Bangalore
    '''
    data = ReadConfig()
    myConnection = None
    myConnection = psycopg2.connect \
        (host=data["hostname"], user=data["username"], password=data["password"], dbname=data["database"])
    # Reads lat and long

    lat_s, long_s, lat_t, long_t = read_latlong()

    if (not check_beng(lat_s, long_s)) or ( not check_beng(lat_t, long_t)):
        return render_template_string(error_temp(lat_s, long_s, lat_t, long_t, 'Not Inside Bengaluru!'))

    s_geom = 'POINT({} {})'.format(long_s, lat_s)
    t_geom = 'POINT({} {})'.format(long_t, lat_t)

    doQueryv1(myConnection, "DROP TABLE IF EXISTS DD")

    source, target = nearest_st(s_geom, t_geom, myConnection)

    if (source== None) or (target == None):
        return render_template_string(error_temp(lat_s, long_s, lat_t, long_t, 'Could not find source or target'))

    # extracting Djikstra's path
    dist_query = "SELECT * INTO DD FROM pgr_dijkstra('SELECT gid AS id, source, target, length AS cost FROM ways',{}, {},directed := false)".format(
        source[0][0], target[0][0])
    doQueryv2(myConnection, dist_query)

    # extracting distance
    length_query = "SELECT SUM(length_m) FROM ways WHERE gid IN (SELECT edge FROM DD)"
    distance = doQueryv1(myConnection, length_query)

    if distance==None:
        return render_template_string(error_temp(lat_s, long_s, lat_t, long_t, 'Could not find a path'))

    pt_query = "SELECT node FROM DD;"
    dd = doQueryv1(myConnection, pt_query)

    pt_query = "SELECT ST_AsText(the_geom),id FROM ways_vertices_pgr WHERE id IN (SELECT node FROM DD)"
    points = doQueryv1(myConnection, pt_query)

    path = DataFrame(dd)
    point = DataFrame(points)

    point.columns = ['geom', 'node']
    path.columns = ['node']

    points = list(merge(path, point, how='left', on='node')['geom'])
    location = []
    for i in range(len(points)):
        temp = list(map(float, points[i].split('(')[1].split(')')[0].split(' ')))
        location.append(tuple(temp[::-1]))

    folium_map = folium.Map(location=(float(lat_s), float(long_s)), zoom_start=14)
    folium.Marker([float(lat_s), float(long_s)], popup='<i>Start</i>').add_to(folium_map)
    folium.Marker([float(lat_t), float(long_t)], popup='<b>End</b>').add_to(folium_map)
    folium.PolyLine(location).add_to(folium_map)
    folium.map.Marker([float(lat_s), float(long_s)],\
    icon=DivIcon(icon_size=(120,22),icon_anchor=(0,0),html='<div style="font-size: 24pt">{0:.2f} Km</div>'.format(distance[0][0]/1000))
    ).add_to(folium_map)
    html_string = folium_map.get_root().render()
    # folium_map.save('templates/map1.html')
    return render_template_string(html_string)

# return render_template('map.html', lat_s=lat_s, long_s=long_s, lat_t=lat_t, long_t=long_t, location = json.dumps(location))
@app.route('/search3', methods=['POST'])
def routing_d():

    '''
    Finds the distance for two Latitude and Longitude in Delhi
    '''
    data = ReadConfig()
    myConnection = None
    myConnection = psycopg2.connect \
        (host=data["hostname"], user=data["username"], password=data["password"], dbname=data["database"])
    # Reads lat and long

    lat_s, long_s, lat_t, long_t = read_latlong()

    if (not check_delhi(lat_s, long_s)) or ( not check_delhi(lat_t, long_t)):
        return render_template_string(error_temp(lat_s, long_s, lat_t, long_t, 'Not Inside Delhi!'))

    s_geom = 'POINT({} {})'.format(long_s, lat_s)
    t_geom = 'POINT({} {})'.format(long_t, lat_t)

    doQueryv1(myConnection, "DROP TABLE IF EXISTS DD")

    source, target = nearest_st_delhi(s_geom, t_geom, myConnection)

    if (source== None) or (target == None):
        return render_template_string(error_temp(lat_s, long_s, lat_t, long_t, 'Could not find source or target'))

    # extracting Djikstra's path
    dist_query = "SELECT * INTO DD FROM pgr_dijkstra('SELECT gid AS id, source, target, length AS cost FROM ways_delhi',{}, {},directed := false)".format(
        source[0][0], target[0][0])
    doQueryv2(myConnection, dist_query)

    # extracting distance
    length_query = "SELECT SUM(length_m) FROM ways_delhi WHERE gid IN (SELECT edge FROM DD)"
    distance = doQueryv1(myConnection, length_query)

    if distance==None:
        return render_template_string(error_temp(lat_s, long_s, lat_t, long_t, 'Could not find a path'))

    pt_query = "SELECT node FROM DD;"
    dd = doQueryv1(myConnection, pt_query)

    pt_query = "SELECT ST_AsText(the_geom),id FROM ways_vertices_pgr_delhi WHERE id IN (SELECT node FROM DD)"
    points = doQueryv1(myConnection, pt_query)

    path = DataFrame(dd)
    point = DataFrame(points)

    point.columns = ['geom', 'node']
    path.columns = ['node']

    points = list(merge(path, point, how='left', on='node')['geom'])
    location = []
    for i in range(len(points)):
        temp = list(map(float, points[i].split('(')[1].split(')')[0].split(' ')))
        location.append(tuple(temp[::-1]))

    folium_map = folium.Map(location=(float(lat_s), float(long_s)), zoom_start=14)
    folium.Marker([float(lat_s), float(long_s)], popup='<i>Start</i>').add_to(folium_map)
    folium.Marker([float(lat_t), float(long_t)], popup='<b>End</b>').add_to(folium_map)
    folium.PolyLine(location).add_to(folium_map)
    folium.map.Marker([float(lat_s), float(long_s)],\
    icon=DivIcon(icon_size=(120,22),icon_anchor=(0,0),html='<div style="font-size: 24pt">{0:.2f} Km</div>'.format(distance[0][0]/1000))
    ).add_to(folium_map)
    html_string = folium_map.get_root().render()
    # folium_map.save('templates/map1.html')
    return render_template_string(html_string)



if __name__ == '__main__':
    app.debug = True
    app.run()
