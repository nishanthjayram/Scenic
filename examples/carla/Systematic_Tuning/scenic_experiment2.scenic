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
param bloom_intensity = Range(0, 1)
# param fov = 800
param fstop = Range(1, 22)
# param image_size_x = 800
# param image_size_y = 800
param iso = Uniform(200, 400, 800, 1600)
param gamma = Range(1.8, 2.2)
# param lens_flare_intensity = 800
# param sensor_tick = 800
param shutter_speed = Range(100, 300)
param lens_circle_falloff = Range(0, 10)
param lens_circle_multiplier = Range(0, 10)
# param lens_k = 800
# param lens_kcube = 800
# param lens_x_size = Range(0, 1)
# param lens_y_size = Range(0, 1)
# param min_fstop = 800
# param blade_count = 800
# param exposure_mode = 800
# param exposure_compensation = 800
# param exposure_min_bright = 800
# param exposure_max_bright = 800
# param exposure_speed_up = 800
# param exposure_speed_down = 800
# param calibration_constant = 800
# param focal_distance = 800
# param blur_amount = 800
# param blur_radius = 800
param motion_blur_intensity = Range(0, 1)
# param motion_blur_max_distortion = 1.0
# param motion_blur_min_object_screen_size = 800
param slope = Range(0, 1)
param toe = Range(0, 1)
param shoulder = Range(0, 1)
param black_clip = Range(0, 1)
param white_clip = Range(0, 1)
param temp = Range(6000, 7000)
# param tint = 800
# param chromatic_aberration_intensity = 800
# param chromatic_aberration_offset = 800

ego = Car at network.roads[15].centerline[0],
    # facing Range(-15,15) deg relative to roadDirection,
    facing 15 deg relative to roadDirection,
    with visibleDistance 50,
    with blueprint 'vehicle.tesla.model3',
    with viewAngle 135 deg
ped = Pedestrian ahead of ego by 20,
    with regionContainedIn roadRegion,
    # facing Range(-180,180) deg,
    facing 90 deg,
    with blueprint 'walker.pedestrian.0001',
    with requireVisible True

print(ego.position.x)

require abs(relative heading of ped from ego) > 70 deg
