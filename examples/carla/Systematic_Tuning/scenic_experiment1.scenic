""" Scenario Description:
A pedestrian is on a road or an intersection (including crosswalks),
and the pedestrian's heading angle differs from ego's heading by 70 degrees or more
"""

param map = localPath('../../../tests/formats/opendrive/maps/CARLA/Town10HD')
param carla_map = 'Town10HD'
model scenic.simulators.carla.model

# # Define weather attributes as params
# param weather = {
#     'cloudiness': 
#     'precipitation': 
#     'precipitation_deposits: 
#     'wind_intensity': 
#     'sun_azimuth_angle': 
#     'sun_altitude_angle': 
#     'fog_density': 
#     'fog_distance': 
#     'wetness': 
#     'fog_falloff: 
#     'scattering_intensity': 
#     'mie_scattering_scale': 
#     'rayleigh_scattering_scale': 0.0331
# }

# Define RGB camera attributes as params
param bloom_intensity = 800
param fov = 800
param fstop = 800
param image_size_x = 800
param image_size_y = 800
param iso = 800
param gamma = 800
param lens_flare_intensity = 800
param sensor_tick = 800
param shutter_speed = 800
param lens_circle_falloff = 800
param lens_circle_multiplier = 800
param lens_k = 800
param lens_kcube = 800
param lens_x_size = 800
param lens_y_size = 800
param min_fstop = 800
param blade_count = 800
param exposure_mode = 800
param exposure_compensation = 800
param exposure_min_bright = 800
param exposure_max_bright = 800
param exposure_speed_up = 800
param exposure_speed_down = 800
param calibration_constant = 800
param focal_distance = 800
param blur_amount = 800
param blur_radius = 800
param motion_blur_intensity = 400
param motion_blur_max_distortion = 1.0
param motion_blur_min_object_screen_size = 800
param slope = 800
param toe = 800
param shoulder = 800
param black_clip = 800
param white_clip = 800
param temp = 800
param tint = 800
param chromatic_aberration_intensity = 800
param chromatic_aberration_offset = 800

ego = Car on drivableRoad,
    facing Range(-15,15) deg relative to roadDirection,
    with visibleDistance 50,
    with viewAngle 135 deg
ped = Pedestrian on roadsOrIntersections,
    with regionContainedIn roadRegion,
    facing Range(-180,180) deg,
    with requireVisible True

require abs(relative heading of ped from ego) > 70 deg
