"""
Converts the NuScenesMap data class to the SCENIC Network class.

Relevant documentation:
	* https://github.com/nutonomy/nuscenes-devkit/blob/master/python-sdk/nuscenes/map_expansion/map_api.py
	* https://github.com/nutonomy/nuscenes-devkit/blob/master/python-sdk/tutorials/map_expansion_tutorial.ipynb

Relevant authors:
	* Francis Indaheng (@findaheng)
	* Jay Shenoy (@JayShenoy)
"""

import scenic.formats.nuscenes.utils as utils
import shapely
from collections import defaultdict
from nuscenes.map_expansion.map_api import NuScenesMap
from scenic.core.regions import PolylineRegion
from scenic.domains.driving import roads
from shapely.geometry import LineString, MultiLineString
from shapely.ops import unary_union

class NuScenesMapData:
	"""Data representation for nuScenes map data."""

	def __init__(self, dataroot, map_name, tolerance=0.05):
		self.map_name = map_name
		self.nusc_map = NuScenesMap(dataroot=dataroot, map_name=map_name)
		self.tolerance = tolerance
		# Road segments that are too small to work with
		self.invalid_road_segment_tokens = {
			'boston-seaport': ['ff6335c7-bc4a-415a-961b-c832309c7ddb']
		}
		
	def toScenicNetwork(self):
		# Find all road blocks within each road segment
		road_segment_blocks = defaultdict(list) # Indexed by road segment token

		for road_block in self.nusc_map.road_block:
			road_segment_blocks[road_block['road_segment_token']].append(road_block)

		# Find all lanes within each road block
		road_block_lanes = defaultdict(list) # Indexed by road block token

		for lane in self.nusc_map.lane:
			lane_poly = self.nusc_map.extract_polygon(lane['polygon_token'])
			point_in_lane = lane_poly.representative_point()
			road_block_token = self.nusc_map.record_on_point(point_in_lane.x, point_in_lane.y, 'road_block')

			road_block_lanes[road_block_token].append(lane)

		road_polys = [self.nusc_map.extract_polygon(rec['polygon_token']).buffer(self.tolerance) for rec in self.nusc_map.road_segment]
		road_shapely = unary_union(road_polys)

		# Retrieve the curb, which is the boundary of the road polygon
		curb_lines = []
		for road_poly in road_shapely:
			oriented_poly = shapely.geometry.polygon.orient(road_poly) # Orient the vertices CCW
			curb_vertices = list(oriented_poly.exterior.coords)
			curb_lines.append(LineString(curb_vertices))

		curb = MultiLineString(curb_lines)
		curb_region = PolylineRegion(polyline=curb)

		# Find all pedestrian crossings within each road segment
		road_segment_crossings = defaultdict(list) # Indexed by road segment token

		# Construct all lanes
		road_block_lanes_scenic = defaultdict(dict) # Indexed by road block token, then lane token
		road_block_lane_secs_scenic = defaultdict(dict) # Same indexing as above

		lanes_scenic = []
		lane_secs_scenic = []
		lane_groups_scenic = []

		# NOT part of an intersection
		roads_ordinary_scenic = []

		# Part of an intersection
		connecting_roads_scenic = []

		road_sections_scenic = []

		# All elements
		network_elements = {}

		for road_segment_token, road_block_list in list(road_segment_blocks.items()):
			if self.map_name in self.invalid_road_segment_tokens \
				 and road_segment_token in self.invalid_road_segment_tokens[self.map_name]:
				continue
				
			lanes_for_road_segment = []
			lane_groups_for_road_segment = []
			lane_secs_for_road_segment = [] # List of lists of lane sections

			for road_block in road_block_list:
				road_block_token = road_block['token']
				lane_list = road_block_lanes[road_block_token]
				
				if lane_list == []:
					continue

				# Track lane dividers
				lane_with_left_divider = {}
				lane_with_right_divider = {}

				for l in lane_list:
					poly, lane_centerline, lane_left_edge, lane_right_edge = utils.get_polygonal_features(self.nusc_map, l)
					
					lane_uid = l['token']
					lane_sec_uid = '{}_sec'.format(l['token'])
					
					lane = roads.Lane(
						polygon=poly,
						centerline=lane_centerline,
						leftEdge=lane_left_edge,
						rightEdge=lane_right_edge,
						group=None,
						road=None,
						sections=None,
						uid=lane_uid
					)

					# Each lane consists of one lane section for nuScenes maps
					lane_sec = roads.LaneSection(
						lane=lane,
						group=None,
						road=None,
						polygon=poly,
						leftEdge=lane_left_edge,
						rightEdge=lane_right_edge,
						centerline=lane_centerline,
						uid=lane_sec_uid,
						openDriveID=0
					)

					lane.sections = (lane_sec,)

					road_block_lanes_scenic[road_block_token][l['token']] = lane
					road_block_lane_secs_scenic[road_block_token][l['token']] = lane_sec
					
					if len(l['left_lane_divider_segments']) > 0:
						left_divider = [x['node_token'] for x in l['left_lane_divider_segments']]
						left_divider = tuple(sorted(left_divider))
						lane_with_left_divider[left_divider] = l
					
					if len(l['right_lane_divider_segments']) > 0:
						right_divider = [x['node_token'] for x in l['right_lane_divider_segments']]
						right_divider = tuple(sorted(right_divider))
						lane_with_right_divider[right_divider] = l
				
				# Determine rightmost lane
				rightmost_lane = lane_list[0]
				
				adjacent_right_divider = [x['node_token'] for x in rightmost_lane['right_lane_divider_segments']]
				adjacent_right_divider = tuple(sorted(adjacent_right_divider))
				
				# while there exists a lane to the right of rightmost_lane
				while adjacent_right_divider in lane_with_left_divider.keys():
					rightmost_lane = lane_with_left_divider[adjacent_right_divider]
					adjacent_right_divider = [x['node_token'] for x in rightmost_lane['right_lane_divider_segments']]
					adjacent_right_divider = tuple(sorted(adjacent_right_divider))
				
				# Figure out order of lanes within road block
				curr_lane = rightmost_lane

				lane_order = [curr_lane['token']]
				
				adjacent_left_divider = [x['node_token'] for x in curr_lane['left_lane_divider_segments']]
				adjacent_left_divider = tuple(sorted(adjacent_left_divider))

				# while there exists a lane to the left of curr_lane
				while adjacent_left_divider in lane_with_right_divider.keys():
					curr_lane = lane_with_right_divider[adjacent_left_divider]
					lane_order.append(curr_lane['token'])
					adjacent_left_divider = [x['node_token'] for x in curr_lane['left_lane_divider_segments']]
					adjacent_left_divider = tuple(sorted(adjacent_left_divider))

				# Order lane sections accordingly
				for lane_token_left, lane_token_right in zip(lane_order[1:], lane_order[:-1]):
					left_lane_sec = road_block_lane_secs_scenic[road_block_token][lane_token_left]
					right_lane_sec = road_block_lane_secs_scenic[road_block_token][lane_token_right]

					left_lane_sec._laneToRight = right_lane_sec
					right_lane_sec._laneToLeft = left_lane_sec

				# Order Scenic lanes & lane sections
				lane_order_scenic = []
				lane_secs_order_scenic = []

				for lane_token in lane_order:
					lane_scenic = road_block_lanes_scenic[road_block_token][lane_token]
					lane_order_scenic.append(lane_scenic)
					lane_secs_order_scenic.append(road_block_lane_secs_scenic[road_block_token][lane_token])
					
				lane_group_poly, lane_group_centerline, lane_group_left_edge, lane_group_right_edge = utils.get_polygonal_features(self.nusc_map, road_block)
				
				lane_group_uid = road_block['token']
				
				lane_group = roads.LaneGroup(
					road=None,
					lanes=tuple(lane_order_scenic),
					polygon=lane_group_poly,
					centerline=lane_group_centerline,
					leftEdge=lane_group_left_edge,
					rightEdge=lane_group_right_edge,
					curb=None,
					uid=lane_group_uid
				)
				
				for lane, lane_sec in zip(lane_order_scenic, lane_secs_order_scenic):
					lane.group = lane_group
					lane_sec.group = lane_group

				lanes_for_road_segment.append(lane_order_scenic)
				lane_groups_for_road_segment.append(lane_group)
				lane_secs_for_road_segment.append(lane_secs_order_scenic)

				lanes_scenic.extend(lane_order_scenic)
				lane_secs_scenic.extend(lane_secs_order_scenic)
				lane_groups_scenic.append(lane_group)

			# Construct road section
			if lane_secs_for_road_segment == []:
				continue
				
			forward_lane_secs = lane_secs_for_road_segment[0]

			if len(lane_secs_for_road_segment) > 1:
				backward_lane_secs = lane_secs_for_road_segment[1]
			else:
				backward_lane_secs = []
			
			# Reverse backward lane sections to preserve RTL ordering
			road_section_lane_secs = forward_lane_secs + backward_lane_secs[::-1]
			
			road_seg = self.nusc_map.get('road_segment', road_segment_token)
			road_sec_poly, road_sec_centerline, road_sec_left_edge, road_sec_right_edge = utils.get_polygonal_features(self.nusc_map, road_seg)

			road_sec_uid = '{}_sec'.format(road_segment_token)
			
			road_section = roads.RoadSection(
				road=None,
				lanes=tuple(road_section_lane_secs),
				forwardLanes=tuple(forward_lane_secs),
				backwardLanes=tuple(backward_lane_secs),
				polygon=road_sec_poly,
				centerline=road_sec_centerline,
				leftEdge=road_sec_left_edge,
				rightEdge=road_sec_right_edge,
				lanesByOpenDriveID=None,
				uid=road_sec_uid
			)

			# Construct road
			forward_lanes = lanes_for_road_segment[0]

			if len(lanes_for_road_segment) > 1:
				backward_lanes = lanes_for_road_segment[1]
			else:
				backward_lanes = []

			# Reverse backward lanes to preserve RTL ordering
			road_lanes = forward_lanes + backward_lanes[::-1]

			forward_lane_group = lane_groups_for_road_segment[0]

			if len(lane_groups_for_road_segment) > 1:
				backward_lane_group = lane_groups_for_road_segment[1]
				backward_lane_group._opposite = forward_lane_group
			else:
				backward_lane_group = None
			
			forward_lane_group._opposite = backward_lane_group

			road = roads.Road(
				uid=road_segment_token,
				lanes=tuple(road_lanes),
				forwardLanes=forward_lane_group,
				backwardLanes=backward_lane_group,
				laneGroups=None,
				sections=(road_section,),
				polygon=road_sec_poly,
				centerline=road_sec_centerline,
				leftEdge=road_sec_left_edge,
				rightEdge=road_sec_right_edge,
				signals=()
			)
			
			for lane_list, lane_sec_list in zip(lanes_for_road_segment, lane_secs_for_road_segment):
				for lane, lane_sec in zip(lane_list, lane_sec_list):
					lane.road = road
					lane_sec.road = road
			
			road_section.road = road

			roads_ordinary_scenic.append(road)
			road_sections_scenic.append(road_section)

		intersection_roads = [r for r in self.nusc_map.road_segment if r['is_intersection']]

		intersections_scenic = []
			
		for r in intersection_roads:
			road_poly, road_centerline, road_leftEdge, road_rightEdge = utils.get_polygonal_features(self.nusc_map, r)
			
			road_uid = r['token']
			inter_uid = '{}_inter'.format(road_uid)
			
			road = roads.Road(
				uid=road_uid,
				lanes=None,
				forwardLanes=None,
				backwardLanes=None,
				laneGroups=None,
				sections=(),
				polygon=road_poly,
				centerline=road_centerline,
				leftEdge=road_leftEdge,
				rightEdge=road_rightEdge,
				signals=()
			)
			
			inter = roads.Intersection(
				uid=inter_uid,
				roads=(road),
				incomingLanes=(),
				outgoingLanes=(),
				maneuvers=(),
				crossings=(),
				polygon=road_poly,
				signals=()
			)
			
			connecting_roads_scenic.append(road)
			intersections_scenic.append(inter)
			
		utils.add_to_network_elements(network_elements, roads_ordinary_scenic)
		utils.add_to_network_elements(network_elements, connecting_roads_scenic)
		utils.add_to_network_elements(network_elements, intersections_scenic)
		utils.add_to_network_elements(network_elements, road_sections_scenic)
		utils.add_to_network_elements(network_elements, lanes_scenic)
		utils.add_to_network_elements(network_elements, lane_secs_scenic)
		utils.add_to_network_elements(network_elements, lane_groups_scenic)

		scenicNetwork = roads.Network(
			elements=network_elements,
			lanes=tuple(lanes_scenic),
			laneGroups=tuple(lane_groups_scenic),
			roads=tuple(roads_ordinary_scenic),
			connectingRoads=tuple(connecting_roads_scenic),
			intersections=tuple(intersections_scenic),
			sidewalks=(),
			crossings=(),
			shoulders=(),
			curbRegion=curb_region,
			tolerance=self.tolerance
		)

		for elem in scenicNetwork.elements.values():
			elem.network = scenicNetwork

		return scenicNetwork
