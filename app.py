from flask import Flask, render_template, request
from shapely.geometry import Point
import geopandas as gpd
import pandas as pd
import numpy as np
from scipy import spatial


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

        blore = gpd.read_file('blore.geojson')
        chenn = gpd.read_file('chennai.geojson')
        mumba = gpd.read_file('mumbai.geojson')
        ahmed = gpd.read_file('ahmedabad.geojson')
        hyder = gpd.read_file('hyderabad.geojson')
        kolka = gpd.read_file('kolkatta.geojson')
        df1 = pd.read_csv('allind.csv')
        blore['centroid_column'] = blore.centroid
        b = blore.set_geometry('centroid_column')

        chenn['centroid_column'] = chenn.centroid
        c = chenn.set_geometry('centroid_column')

        mumba['centroid_column'] = mumba.centroid
        m = mumba.set_geometry('centroid_column')

        ahmed['centroid_column'] = ahmed.centroid
        a = ahmed.set_geometry('centroid_column')

        hyder['centroid_column'] = hyder.centroid
        h = hyder.set_geometry('centroid_column')

        kolka['centroid_column'] = kolka.centroid
        k = kolka.set_geometry('centroid_column')

        data = pd.concat([b, c, m, a, h, k], ignore_index=True, sort=False)
        long = float(long1)
        lat = float(lat1)

        p = Point(long, lat)
        pin = 0
        for i in range(0, len(data)):

            if p.within(data['geometry'][i]) is True:

                pin = int(data['pin_code'][i])

        if pin != 0:
            return render_template('success.html', pin=pin)
        else:
            data1 = df1[['postalcode', 'placename', 'latitude', 'longitude ']]
            latlongs = data1.iloc[:, 2:]
            d = np.array(latlongs)
            tree = spatial.KDTree(d)
            latlongs = np.array([lat, long])
            result = tree.query(latlongs)
            pin = int(data1.iloc[[result[1]]]['postalcode'])

            return render_template('success.html', pin=pin)

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


if __name__ == '__main__':
    app.debug = True
    app.run()
