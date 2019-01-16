from flask import Flask, render_template, request
from shapely.geometry import Point
import geopandas as gpd
import pandas as pd
import numpy as np
from scipy import spatial
import psycopg2


app = Flask(__name__)


# Set "homepage" to index.html
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def pin():
    try:
        lat1 = request.form['lat']
        long1 = request.form['long']

        b = gpd.read_file('data/blore.geojson')
        c = gpd.read_file('data/chennai.geojson')
        m = gpd.read_file('data/mumbai.geojson')
        a = gpd.read_file('data/ahmedabad.geojson')
        h = gpd.read_file('data/hyderabad.geojson')
        k = gpd.read_file('data/kolkatta.geojson')
        df1 = pd.read_csv('data/allind.csv')
       

        data = pd.concat([b, c, m, a, h, k], ignore_index=True, sort=False)
        long = float(long1)
        lat = float(lat1)

        p = Point(long, lat)
        pin = 0
        if (lat < 8.4 or lat > 37.6 or long < 68.7 or long > 97.25):
            return (render_template('success.html', pin = "Sorrry! OUT OF BOUNDS.", lat2=lat, long2=long))

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

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


if __name__ == '__main__':
    app.debug = True
    app.run()
