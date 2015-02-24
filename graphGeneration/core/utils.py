import time
from functools import wraps
import networkx as nx
from math import radians, cos, sin, asin, sqrt
from django.contrib.gis.geos import LineString

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # 6367 km is the radius of the Earth
    km = 6367 * c
    return km

def convert_field_format(fieldAsArray):
    """
    Description:
        converts the polygon given as nested arrays
        to nested tuples.
    Parameters:
        fieldAsArray: [ [ [x, y], ... ], ... ]
    Return:
        ( ( (x, y), ... ), ... )
    """
    return tuple( tuple( tuple(vertex) for vertex in ring) for ring in fieldAsArray )


def timer (fn):
    """
    Measure the running time of a function and add it 
    to the return values
    """
    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        print("@timefn: " + fn.func_name + " took " + str(t2 - t1) + " seconds")
        return result, str(t2 - t1)
    return measure_time


def add_weight_to_graph(graph, distFunc = haversine):
    """
    Description:
        add the distance between adjacent nodes as the weight attribute
        of each edge.
    Parameters:
        graph: networkx graph
        distFunc: the function that should be used to calculate the distance
                  haversine formula by default
    Return:
        networkx graph
    """
    weightedGraph = nx.Graph()
    for edge in graph.edges():
        start, end = edge
        distance = distFunc(start[0], start[1], end[0], end[1])
        weightedGraph.add_edge(start, end, weight=distance)
    return weightedGraph

def shortest_path(graph, start, end):
    return nx.dijkstra_path(graph, start, end)

def shortest_path_length(graph, start, end):
    return nx.dijkstra_path_length(graph, start, end)

def nx_path_to_geojson(path):
    geom = LineString(tuple(path))
    return geom.json



"""unit tests"""
if __name__ == "__main__":
    print convertFieldFormat([ [ [1,2], [3,4], [5,6] ], [ [1,2], [3,4], [5,6] ] ])

    @timer
    def some_func (s):
        return s

    result, time = some_func('hello, timer!')
    print result, time
