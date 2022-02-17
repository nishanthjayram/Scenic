""" Scenario Description:
A pedestrian is on a road or an intersection (including crosswalks),
and the pedestrian's heading angle differs from ego's heading by 70 degrees or more
"""

param map = localPath('../../../tests/formats/opendrive/maps/CARLA/Town10HD')
param carla_map = 'Town10HD'
model scenic.simulators.carla.model

ego = Car on drivableRoad,
    facing Range(-15,15) deg relative to roadDirection,
    with visibleDistance 50,
    with viewAngle 90 deg

ped = Pedestrian on roadsOrIntersections,
    with regionContainedIn roadRegion,
    facing Range(-180,180) deg,
    with requireVisible True

require abs(relative heading of ped from ego) > 90 deg
