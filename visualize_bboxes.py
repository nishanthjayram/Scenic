from scenic.simulators.carla.recording import *

DATA_DIR = '/home/carla_challenge/Desktop/SystematicTuning/scenic/examples/carla/Systematic_Tuning/output/rgb/scenic_experiment1'
SENSOR_CONFIG_FILE = '/home/carla_challenge/Desktop/SystematicTuning/scenic/examples/carla/Systematic_Tuning/sensor_config_rgb.json'

sensor_config = SensorConfig(SENSOR_CONFIG_FILE)

data = DataAPI(DATA_DIR, sensor_config)

sims = data.get_simulations()
sims = list(sims.values())
# print(sims)
# sim = sims[0]

for i, sim in enumerate(sims):
	frame = sim[0]
	draw_bbox_3d(frame['bboxes']['pedestrian'], sensor_config.get('cam'), frame['cam']['rgb'], f'output/rgb/frame{i}.jpg')
