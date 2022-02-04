from scenic.simulators.carla.recording import *

DATA_DIR = '/home/carla_challenge/Desktop/SystematicTuning/scenic/examples/carla/Systematic_Tuning/output/scenic_experiment2'
SENSOR_CONFIG_FILE = '/home/carla_challenge/Desktop/SystematicTuning/scenic/examples/carla/Systematic_Tuning/sensor_config.json'

sensor_config = SensorConfig(SENSOR_CONFIG_FILE)

data = DataAPI(DATA_DIR, sensor_config)

sims = data.get_simulations()
sims = list(sims.values())
sim = sims[0]

frame = sim[0]
draw_bbox_3d(frame['bboxes']['pedestrian'], sensor_config.get('cam'), frame['cam']['rgb'], 'frame.jpg')
