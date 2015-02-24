__author__ = 'sensun'

import networkx as nx
from django.contrib.gis.geos import Polygon, LineString, GeometryCollection, Point

def transform_convex_hull(convexHullAsGeom, convexHullAsGraph, hole, edge):
    verticesInHole = []
    commonEdgeGeom = convexHullAsGeom[0].intersection(hole)
    for vertex in edge:
        # test in which hole the vertex is
        # the vertex could be interior to the hole or on the boundary
        pnt = Point(*vertex)
        if hole.contains(pnt) or hole[0].contains(pnt):
            if commonEdgeGeom.disjoint(pnt):
                verticesInHole.append(vertex)

    # no endpoints in this hole, return
    if len(verticesInHole) == 0:
        return convexHullAsGraph

    cec = commonEdgeGeom.coords
    assert commonEdgeGeom.geom_type == 'LineString'

    if convexHullAsGraph.has_edge(*cec):
        convexHullAsGraph.remove_edge(*cec)

    if len(verticesInHole) == 1:
        vertex = verticesInHole[0]
        anotherVertex = edge[0] if vertex == edge[1] else edge[1]

        if cec[0] not in convexHullAsGraph.nodes():
            assert cec[1] in convexHullAsGraph.nodes()
            convexHullAsGraph.add_edge(anotherVertex, cec[0])
            if convexHullAsGraph.has_edge(anotherVertex, cec[1]):
                convexHullAsGraph.remove_edge(anotherVertex, cec[1])

        if cec[1] not in convexHullAsGraph.nodes():
            assert cec[0] in convexHullAsGraph.nodes()
            convexHullAsGraph.add_edge(anotherVertex, cec[1])
            if convexHullAsGraph.has_edge(anotherVertex, cec[0]):
                convexHullAsGraph.remove_edge(anotherVertex, cec[0])
        if vertex not in cec:
            graph1 = GraphGenerator(vertex, cec[0], hole.coords).get_graph()
            convexHullAsGraph.add_edges_from(graph1.edges())
            graph2 = GraphGenerator(vertex, cec[1], hole.coords).get_graph()
            convexHullAsGraph.add_edges_from(graph2.edges())

    # special case that two endpoints are located in the same hole
    elif len(verticesInHole) == 2:
        graph1 = GraphGenerator(edge[0], edge[1], hole.coords).get_graph()
        convexHullAsGraph = nx.Graph()
        convexHullAsGraph.add_edges_from(graph1.edges())

    return convexHullAsGraph


def make_graph_from_convex_hull(ch):
    """
    Description:
        Transforms a convex hull geometry to an undirected networkx graph

    Parameters:
        ch: Polygon
            -- geometry of the convex hull
    """
    graph = nx.Graph()
    coords = ch.coords[0]
    edge_list = [(coords[i], coords[i+1]) for i in range(len(coords)-1)]
    graph.add_edges_from(edge_list)
    return graph


def init_memo(polygon):
    memo = {}
    for ls in polygon:
        edges = [(ls[i], ls[i+1]) for i in range(len(ls)-1)]
        edges2 = [(ls[i+1], ls[i]) for i in range(len(ls)-1)]
        edges.extend(edges2)
        for e in edges:
            memo[e] = None
    return memo


class PassableArea:

    def __init__(self, polygon):
        outerBound = Polygon((tuple(polygon[0])))
        # test if the outer boundary is convex
        convexHull = outerBound.convex_hull
        self._boundary = convexHull
        self._original_boundary = outerBound
        self._obstacles = []
        self._numAuxObstacles = 0
        if not convexHull.equals(outerBound):
            holes = convexHull.difference(outerBound)
            if holes.geom_type == "Polygon":
                self._obstacles.append(holes)
            elif holes.geom_type == "MultiPolygon":
                for hole in holes:
                    self._obstacles.append(hole)
            self._numAuxObstacles = len(self._obstacles)
            #print "Number of auxiliary obstacles:", self._numAuxObstacles
        # original obstacles
        if len(polygon) > 1:
            for i in range(1, len(polygon)):
                self._obstacles.append(Polygon((tuple(polygon[i]))))

    def get_obstacles(self):
        return self._obstacles

    def get_num_aux_obstacles(self):
        return self._numAuxObstacles

    def get_boundary(self):
        return self._boundary

    def get_original_boundary(self):
        return self._original_boundary


class GraphGenerator:

    def __init__(self, start, end, polygon):
        self._start = start
        self._end = end
        self._passableArea = PassableArea(polygon)
        self._graph = nx.Graph()
        self._graph.add_edge(start, end)
        self._detectedObstacle = []
        self._memo = init_memo(polygon)
        self._crossing = True
        self._polygon = polygon

    def _find_impeding_obstacles(self, edgeGeom):
        """Return the indices of impeding obstacles"""
        crossingObstacles = []
        pa = self._passableArea
        obstacles = pa.get_obstacles()
        numAux = pa.get_num_aux_obstacles()
        #print numAux
        originalBoundary = pa.get_original_boundary()
        for i in xrange(len(obstacles)):
            obstacleGeom = obstacles[i]
            if obstacleGeom.crosses(edgeGeom):
                crossingObstacles.append(i)
                continue
            # do extra check for auxiliary obstacles
            if i < numAux and edgeGeom.within(obstacleGeom[0]):
                if not edgeGeom.within(originalBoundary[0]):
                    crossingObstacles.append(i)
        return crossingObstacles

    def _vertices_are_on_convex_hull(self, edgeGeom, convexHullGeom):

        for pnt in edgeGeom:
            if not Point(*pnt).within(convexHullGeom[0]):
                return False
        return True

    def _transform_concave_obstacle(self, edge, obstacle):
        """
        Description:
            Extends the convex hull of an obstacle so that it concludes the
            vertices of the edge
        Parameters:
            edge: LineString
            obstacle: Polygon
        Return:
            networkx graph
        """
        obstacleAndEdge = GeometryCollection(edge, obstacle)
        # outer convex hull is the convex hull of both the edge and the obstacle
        outerConvexHullAsGeom = obstacleAndEdge.convex_hull  # Polygon

        # differ1 is the difference of outer convex hull and the obstacle
        differ1 = outerConvexHullAsGeom.difference(obstacle)

        # a workaround to include all the vertices
        convexHullRing = outerConvexHullAsGeom[0].union(outerConvexHullAsGeom[0].intersection(differ1))
        nodesForGraph = convexHullRing.coords  # MultiLineString

        convexHullAsGraph = nx.Graph()
        edge_list = []
        for segment in nodesForGraph:
            edge_list.extend([(segment[i], segment[i+1]) for i in range(len(segment)-1)])

        convexHullAsGraph.add_edges_from(edge_list)

        innerConvexHullAsGeom = obstacle.convex_hull
        differ2 = innerConvexHullAsGeom.difference(obstacle)
        if differ2.geom_type == "Polygon":
            convexHullAsGraph = transform_convex_hull(innerConvexHullAsGeom, convexHullAsGraph, differ2, edge)
        else:
            for hole in differ2:
                convexHullAsGraph = transform_convex_hull(innerConvexHullAsGeom, convexHullAsGraph, hole, edge)
        return convexHullAsGraph

    def _exclude_extra_half(self, edge, convexHullAsGraph):

        cycles = nx.cycle_basis(convexHullAsGraph)
        #exclude self loops
        cyclesWithoutSelfLoops = [c for c in cycles if len(c) > 1]
        assert len(cyclesWithoutSelfLoops) == 1
        cycle = cyclesWithoutSelfLoops[0]
        idx1 = cycle.index(edge[0])
        idx2 = cycle.index(edge[1])
        cycleDoubled = cycle + cycle
        startIdx = min(idx1, idx2)
        midIdx = max(idx1, idx2)
        endIdx = startIdx + len(cycle)
        path1 = cycleDoubled[startIdx:midIdx + 1]
        path2 = cycleDoubled[midIdx:endIdx + 1]

        #convert path to tuple
        pathAsList1 = [(path1[i], path1[i+1]) for i in range(len(path1) - 1)]
        pathAsList2 = [(path2[i], path2[i+1]) for i in range(len(path2) - 1)]

        #decide which path to exclude
        if any(self._is_not_original(e) for e in pathAsList1):
            convexHullAsGraph.remove_edges_from(pathAsList1)
        if any(self._is_not_original(e) for e in pathAsList2):
        #else:
            convexHullAsGraph.remove_edges_from(pathAsList2)
        return convexHullAsGraph

    def _is_within_polygon(self, edge):
        geom = LineString(*edge)
        originalBoundary = self._passableArea.get_original_boundary()
        if geom.within(originalBoundary) or geom.within(originalBoundary[0]):
            return True
        return False

    def _is_not_original(self, edge):
        geom = LineString(*edge)
        boundary = self._passableArea.get_boundary()
        originalBoundary = self._passableArea.get_original_boundary()
        #print originalBoundary.coords
        #print geom[0]
        con1 = geom[0] in boundary[0].coords
        con2 = geom[1] in boundary[0].coords
        con3 = geom.within(originalBoundary[0])
        if con1 and con2 and not con3:
            edgeGraph = nx.Graph()
            edgeGraph.add_edge(*edge)
            return True
        return False

    def _add_convex_hull_to_graph(self, edgeGeom, idx, subGraph):
        obstacleGeom = self._passableArea.get_obstacles()[idx]
        edgeAndObstacle = GeometryCollection(edgeGeom, obstacleGeom)
        convexHullAsGeom = edgeAndObstacle.convex_hull
        if not self._vertices_are_on_convex_hull(edgeGeom, convexHullAsGeom):
            convexHullAsGraph = self._transform_concave_obstacle(edgeGeom, obstacleGeom)
        else:
            convexHullAsGraph = make_graph_from_convex_hull(convexHullAsGeom)
        # if the obstacle is an auxiliary one, half of the convex hull should be
        # deleted
        if idx < self._passableArea.get_num_aux_obstacles() \
                and len(nx.cycle_basis(convexHullAsGraph)) > 0:
            convexHullAsGraph = self._exclude_extra_half(edgeGeom, convexHullAsGraph)
        subGraph.add_edges_from(convexHullAsGraph.edges())
        return subGraph

    def _check_and_adjust_edge(self, edge):

        if edge in self._memo.keys():
            return self._memo[edge]
        else:
            edgeGeom = LineString(edge)
            impedingObstacles = self._find_impeding_obstacles(edgeGeom)
            if len(impedingObstacles) == 0:
                self._memo[edge] = None
                self._memo[(edge[1], edge[0])] = None
                return
            subGraph = nx.Graph()
            for idx in impedingObstacles:
                subGraph = self._add_convex_hull_to_graph(edgeGeom, idx, subGraph)
            #print subGraph.number_of_edges()
            self._memo[edge] = subGraph
            self._memo[(edge[1], edge[0])] = subGraph
            return subGraph

    def _adjust_graph(self):
        self._crossing = False
        currentEdges = self._graph.edges()[:]
        for edge in currentEdges:
            result = self._check_and_adjust_edge(edge)
            #sprint result.number_of_edges()
            if result is not None:
                #print result.number_of_edges()
                self._crossing = True
                self._graph.add_edges_from(result.edges())
                self._graph.remove_edge(*edge)

    def get_graph(self):
        while self._crossing:
            self._adjust_graph()
        return self._graph