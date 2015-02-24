import json

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt

from core.convex_oo import PassableArea, GraphGenerator
import core.utils as ut

@csrf_exempt
def index(request):
	if request.method == 'POST':
		try:
			json_data = json.loads(request.body)
			points = json_data['endPoints']
			start = tuple(points[0][u'geometry'][u'coordinates'])
			end = tuple(points[1][u'geometry'][u'coordinates'])
			polygon = ut.convert_field_format(json_data[u'polygonGeom'][u'geometry'][u'coordinates']) 
			graph = GraphGenerator(start, end, polygon).get_graph()
			weightedGraph = ut.add_weight_to_graph(graph)
			path = ut.shortest_path(graph, start, end)
			pathAsGeoJSON = ut.nx_path_to_geojson(path)
			responseJSON = {
				'status': 'OK',
				'path': pathAsGeoJSON
			}
			return HttpResponse(json.dumps(responseJSON), content_type='application/json')
		except Exception as e:
			responseJSON = {
				'status': 'ERROR',
				'message': e
			}
			print e
			return HttpResponse(json.dumps(responseJSON), content_type='application/json')
	return HttpResponse("Please post your data to the same url.")


def drawPolygon(request):
	return render_to_response('index.html')
