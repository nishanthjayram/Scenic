import numpy as np
from scenic.core.regions import PolylineRegion
from shapely.geometry import Point, Polygon

def add_to_network_elements(network_elements, elem_list):
  """Compiles all network elements."""
  for elem in elem_list:
    network_elements[elem.uid] = elem

def get_polygonal_features(map_api, nusc_obj):
  """Gets polygon, centerline, left edge, and right edge from nuScenes object."""
  lane_node_tokens = nusc_obj['exterior_node_tokens']
  node_pts = [map_api.get('node', tok) for tok in lane_node_tokens]
  node_pts = [(pt['x'], pt['y']) for pt in node_pts]
  poly = Polygon(node_pts)
  
  if 'from_edge_line_token' in nusc_obj and 'to_edge_line_token' in nusc_obj:
    # Construct centerline of lane using midpoints of to/from edges
    from_edge = map_api.get('line', nusc_obj['from_edge_line_token'])
    to_edge = map_api.get('line', nusc_obj['to_edge_line_token'])

    from_nodes = [map_api.get('node', t) for t in from_edge['node_tokens']]
    from_nodes = [np.array([n['x'], n['y']]) for n in from_nodes]
    to_nodes = [map_api.get('node', t) for t in to_edge['node_tokens']]
    to_nodes = [np.array([n['x'], n['y']]) for n in to_nodes]

    # Compute traffic flow vector using midpoints of edges
    from_mid = (from_nodes[0] + from_nodes[1]) / 2
    to_mid = (to_nodes[0] + to_nodes[1]) / 2

    # Construct left and right edges
    from_edge_start_idx = lane_node_tokens.index(from_edge['node_tokens'][0])
    from_edge_end_idx = lane_node_tokens.index(from_edge['node_tokens'][-1])

    to_edge_start_idx = lane_node_tokens.index(to_edge['node_tokens'][0])
    to_edge_end_idx = lane_node_tokens.index(to_edge['node_tokens'][-1])

    # Ensure indices are in ascending order
    highest_idx = len(lane_node_tokens) - 1
    if from_edge_start_idx == 0 and from_edge_end_idx == highest_idx:
      # Special wraparound case
      from_edge_start_idx, from_edge_end_idx = from_edge_end_idx, from_edge_start_idx
    elif set([from_edge_start_idx, from_edge_end_idx]) != {0, highest_idx}:
      from_edge_start_idx, from_edge_end_idx = sorted([from_edge_start_idx, from_edge_end_idx])

    if to_edge_start_idx == 0 and to_edge_end_idx == highest_idx:
      # Special wraparound case
      to_edge_start_idx, to_edge_end_idx = to_edge_end_idx, to_edge_start_idx
    elif set([to_edge_start_idx, to_edge_end_idx]) != {0, highest_idx}:
      to_edge_start_idx, to_edge_end_idx = sorted([to_edge_start_idx, to_edge_end_idx])

    left_edge_start_idx = from_edge_end_idx
    left_edge_end_idx = (to_edge_start_idx + 1) % len(lane_node_tokens)

    right_edge_start_idx = to_edge_end_idx
    right_edge_end_idx = (from_edge_start_idx + 1) % len(lane_node_tokens)

    # Construct left edge
    left_edge_nodes = []
    curr_idx = left_edge_start_idx
    while curr_idx != left_edge_end_idx:
      n = map_api.get('node', lane_node_tokens[curr_idx])
      left_edge_nodes.append((n['x'], n['y']))

      curr_idx += 1
      # Wraparound
      curr_idx %= len(lane_node_tokens)

    # Construct right edge
    right_edge_nodes = []
    curr_idx = right_edge_start_idx
    while curr_idx != right_edge_end_idx:
      n = map_api.get('node', lane_node_tokens[curr_idx])
      right_edge_nodes.append((n['x'], n['y']))

      curr_idx += 1
      # Wraparound
      curr_idx %= len(lane_node_tokens)

    # Reverse order (to fix direction)
    right_edge_nodes.reverse()

    # lane_centerline = PolylineRegion(points=(from_mid, to_mid))
    lane_centerline = PolylineRegion(left_edge_nodes)
    lane_left_edge = PolylineRegion(left_edge_nodes)
    lane_right_edge = PolylineRegion(right_edge_nodes)
  else:
    # Hack: compute random line segment within polygon
    rand_pt = poly.representative_point()
    rand_pt2 = Point(rand_pt.x + 0.5, rand_pt.y + 0.5)
    rand_pts = (rand_pt, rand_pt2)
    lane_centerline = PolylineRegion(rand_pts)
    lane_left_edge = PolylineRegion(rand_pts)
    lane_right_edge = PolylineRegion(rand_pts)
  
  poly = poly.buffer(0)
  
  return poly, lane_centerline, lane_left_edge, lane_right_edge
