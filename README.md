# Indian Road Routing and Pincode Mapping using LatLongs:

Hakcernoon Article: https://hackernoon.com/building-a-pincode-mapper-and-routing-engine-with-postgis-and-pgrouting-79bba806a842

- Extrapolating the Pincode given the Latitude and Longitude 
- Figuring out the path by road between two LatLongs 

A Postal Index Number or PIN or PIN code is a code in the post office numbering or post code system used by India Post, the Indian postal administration. The code is six digits long

We have developed a Simple Flask Application that can retrieve the path by road between two given Latlongs and also retrieve the Pincode of a location given it's Latitude and Longitude 

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.


### Prerequisites

The below mentioned packages have been used to succesfully implement this project 

```
pip install flask
pip install Shapely
pip install geopandas
pip install scipy
```

## Running the project

Clone the repository into your local system

```
git clone https://github.com/Sangarshanan/Pincode-Mapping.git
```

and run app.py 

```
python app.py
```
The flask application now runs in your localhost:5000

## How it works ?

For calculating the path between two given latlong we make use of the Open Street Data available online and Postgres extensions such as Postgis and  PGrouting 

**PGrouting:** pgRouting extends the PostGIS / PostgreSQL geospatial database to provide geospatial routing functionality.

- We can visualize the road dataset as a graph model (Combination of Nodes and Edges)
- To do this we can use **osm2pgrouting** to get tables corresponding to the nodes and edges 
- These tables can be loaded into the Postgres database  
- For the given source and destination latlong find the nearest Node in the given dataset. This gives us two nodes  

```python
s_query = "SELECT source FROM ways WHERE source_osm in (SELECT osm_id FROM ways_vertices_pgr ORDER BY the_geom <-> ST_GeometryFromText('{}',4326) LIMIT 1) LIMIT 1".format(s_geom)
source = doQuery( myConnection, s_query )
t_query =  "SELECT target FROM ways WHERE target_osm in (SELECT osm_id FROM ways_vertices_pgr ORDER BY the_geom <-> ST_GeometryFromText('{}',4326) LIMIT 1) LIMIT 1 ".format(t_geom)
target = doQuery( myConnection, t_query )
```

- Use those nodes to determine the Path between them using any path finding algorithm (Dijkstra's algorithm)

```python

dist_query = "SELECT * INTO DD FROM pgr_dijkstra('SELECT gid AS id, source, target, length AS cost FROM ways',{}, {},directed := false)".format(source[0][0], target[0][0])
doQueryv2( myConnection, dist_query )
```
- Adding weight to the edges of the graph can help us calculate the ETA and the distance between the points

As we are considering routing citywise we cannot route for inter-city travel but the sharding approach and partitioning  the databse for major cities can help with load balancing 


For the pincode mapping we are using a combination of two different algorithms 

+ The First algorithm used to shapfiles of cities by dividing them into polygons where each polygon represents a pincode 
+ The Second algorithm uses Kdtrees to map a given latlong to the nearest latlong with a known pincode 

The Combination of both approaches gives us high accuracy for cities and passable accuracy other regions 

The Python function that makes it possible 

```python
def getpincode(lat , long):
    lat = float(lat)
    long = float(long)
    p = Point(long,lat)
    for i in range(0,len(data)):
        if p.within(data['geometry'][i]) is True:
            pin = int(data['pin_code'][i])
        else:
            pin = 0
    if pin !=0:
        return pin
    else:
        latlongs = np.array([lat,long])
        result = tree.query(latlongs)
        pin = int(data1.iloc[[result[1]]]['postalcode'])       
    return pin

```


## Acknowledgments

This work was presented as an internship bootcamp project at Grofers <a href="https://grofers.com">
 
**Presentation:** https://bit.ly/2MrgK18

## Team 

- [Aditya Pankaj Shaha](https://github.com/AdityaShaha)
- [Anushtha Kalia](https://github.com/anushthakalia)
- [Kariya Keyur Rajeshbhai](https://github.com/keyur007)
- [Sangarshanan](https://github.com/Sangarshanan)


## License

Check out the GNU General Public License v3.0 [LICENSE](LICENSE) file for details

## Useful Links 

- https://pgrouting.org/
- https://eng.uber.com/engineering-an-efficient-route/ 
- http://map.project-osrm.org/
- https://download.bbbike.org/
- http://kazuar.github.io/visualize-trip-with-flask-and-mapbox/
      

**Full Disclosure** The Name for the project was inspired from the Tv show [Person of Interest](https://www.imdb.com/title/tt1839578/)
