import json
import os
import time
import subprocess
from dotmap import DotMap

from verifai.falsifier import generic_falsifier
from verifai.features.features import *
from verifai.monitor import specification_monitor
from verifai.samplers.feature_sampler import *


class systematic_tuning_monitor(specification_monitor):
  def __init__(self, config_path, data_path, model_path, output_path, carla_path,
               scenic_program, nuscenes_mAP=0, debug=False):
    self.scenario_path  = config_path + '/scenario_config.json'
    self.sensor_path    = config_path + '/sensor_config.json'
    self.data_path      = data_path
    self.model_path     = model_path
    self.output_path    = output_path + '/carla'
    self.carla_path     = carla_path
    self.scenic_program = scenic_program
    self.nuscenes_mAP   = nuscenes_mAP
    self.debug          = debug

  def specification(traj):
    curr_dir = os.path.abspath(os.getcwd())

    # Set sensor configurations in data generation pipeline
    sensor_params = [{
      'name': 'cam',
      'type': 'rgb',
      'transform': [0, 0, 2.4],
      'settings': {
        'image_size_x': 1600,
        'image_size_y': 900,
        'fov': 90,
        'iso': traj.scene.params['iso'],
        'motion_blur_intensity': traj.scene.params['motion_blur_intensity'],
        'bloom_intensity': traj.scene.params['bloom_intensity'],
        'slope': traj.scene.params['slope'],
        'toe': traj.scene.params['toe'],
        'shoulder': traj.scene.params['shoulder'],
        'white_clip': traj.scene.params['white_clip'],
        'black_clip': traj.scene.params['black_clip'],
        'lens_circle_falloff': traj.scene.params['lens_circle_falloff'],
        'lens_circle_multiplier': traj.scene.params['lens_circle_multiplier'],
        'fstop': traj.scene.params['fstop'],
        'gamma': traj.scene.params['gamma'],
        'shutter_speed': traj.scene.params['shutter_speed'],
        'temp': traj.scene.params['temp'],
      }
    }]
    if self.debug:
      print(f'Sampled sensor configurations are: {sensor_params}')
      print(f'Writing these sensor configurations to {self.sensor_path}...')
    with open(self.sensor_path, 'w') as f:
      json.dump(sensor_params, f)

    # Run data generation pipeline
    if self.debug:
      print(f'Changing directories to {self.data_path}...')
    os.chdir(self.data_path)
    if self.debug:
      print('Running data generation pipeline...')
    subprocess.run(['python', '-m', 'scenic.simulators.carla.recording', '--scenarios', self.scenario_path, '--sensors', self.sensor_path])
    if self.debug:
      print(f'Changing directories to {curr_dir}...')
    os.chdir(curr_dir)

    # Run perception model on generated CARLA images
    if self.debug:
      print(f'Changing directories to {self.model_path}...')
    os.chdir(self.model_path)
    if self.debug:
      print('Running perception model on generated images...')
    subprocess.run(['./calculate_map.py', '--data', self.carla_path, '--scenario', self.scenic_program, '-o', self.output_path])
    with open(f'{self.output_path}/carla/{self.scenic_program}/mAP_calc.json', 'r') as f:
      metrics = json.load(f)
      carla_mAP = metrics['mAP']
    if self.debug:
      print(f'Changing directories to {curr_dir}...')
    os.chdir(curr_dir)

    rho = abs(self.nuscenes_mAP - carla_mAP)
    if self.debug:
      print(f'''Monitor Results:\n
                \tQueried mAP: {self.nuscenes_mAP}\n
                \tSimulation mAP: {carla_mAP}\n
                \tRHO: {rho}''')
    return rho


if __name__ == '__main__':
  # Set user parameters
  sampler_type  = 'halton'
  num_iters     = 10
  num_images    = 50
  scenic_path   = '/home/carla_challenge/Desktop/SystematicTuning/scenic/examples/carla/Systematic_Tuning/scenic_experiment1.scenic'
  nuscenes_path = 'path/to/nuscenes/images' # TODO
  model_path    = '/home/carla_challenge/Desktop/abhi/notebooks'
  config_path   = '/home/carla_challenge/Desktop/SystematicTuning/scenic/examples/carla/Systematic_Tuning'
  data_path     = '/home/carla_challenge/Desktop/SystematicTuning/scenic'
  carla_path    = '/home/carla_challenge/Desktop/SystematicTuning/scenic/examples/carla/Systematic_Tuning/output/verifai'
  output_path   = '/home/carla_challenge/Desktop/abhi/notebooks'
  debug         = False

  # Extract Scenic program name from Scenic path
  scenic_program = scenic_path.split('/')[-1].split['.'][0]

  # Run perception model on queried nuScenes images
  if self.debug:
    print(f'Changing directories to {self.model_path}...')
  os.chdir(self.model_path)
  if self.debug:
    print('Running perception model on nuscenes images...')
  subprocess.run(['./calculate_map.py', '--data', nuscenes_path, '--scenario', 0, '-o', output_path + '/nuscenes'])
  with open(f'{self.output_path}/nuscenes/{self.scenic_program}/mAP_calc.json', 'r') as f:
    metrics = json.load(f)
    nuscenes_mAP = metrics['mAP']
  if self.debug:
    print(f'Changing directories to {curr_dir}...')
  os.chdir(curr_dir)

  # Set scenario configuration in data generation pipeline
  scenario_config = {
    'output_dir': config_path + '/output',
    'simulations_per_scenario': num_images,
    'time_per_simulation': 1,
    'scripts': [ scenic_path ]
  }
  if debug:
    print(f'Scenario configurations are: {scenario_config}')
    print(f'Writing these scenario configurations to {config_path}/scenario_config.json...')
  with open(f'{config_path}/scenario_config.json', 'w') as f:
    json.dump(scenario_config, f)

  # Set up VerifAI falsifier
  sensor_params = Struct({
    'iso': Categorical(200, 400, 800, 1600),
    'motion_blur_intensity'  : Box([   0,    1]),
    'bloom_intensity'        : Box([   0,    1]),
    'slope'                  : Box([   0,    1]),
    'toe'                    : Box([   0,    1]),
    'shoulder'               : Box([   0,    1]),
    'white_clip'             : Box([   0,    1]),
    'black_clip'             : Box([   0,    1]),
    'lens_circle_falloff'    : Box([   0,   10]),
    'lens_circle_multiplier' : Box([   0,   10]),
    'fstop'                  : Box([   1,   22]),
    'gamma'                  : Box([ 1.8,  2.2]),
    'shutter_speed'          : Box([ 100,  300]),
    'temp'                   : Box([6000, 7000])
  })
  sample_space = {'sensor_params': sensor_params}
  if sampler_type == 'halton':
    sampler = FeatureSampler.haltonSamplerFor(sample_space)
  elif sampler_type =='ce':
    sampler = FeatureSampler.crossEntropySamplerFor(sample_space)
  else:
    raise ValueError(f"Sampler type '{sampler_type}' not supported")
  falsifier_params = DotMap(
    n_iters=num_iters,
    save_error_table=True,
    save_safe_table=True,
    max_time=None,
  )
  server_options = DotMap(verbosity=0)
  monitor = systematic_tuning_monitor(config_path, data_path, model_path, output_path,carla_path,
                                      scenic_program, nuscenes_mAP, debug=debug)
  falsifier = generic_falsifier(sampler=sampler, falsifier_params=falsifier_params,
                                server_options=server_options, monitor=monitor)
  
  # Run VerfiAI falsifier
  t0 = time.time()
  falsifier.run_falsifier()
  t = time.time() - t0
  if self.debug:
    print(f'''Falsifier Results:\n
              \tGenerated {len(falsifier.samples)} samples in {t} seconds\n
              \tNumber of counterexamples: {len(falsifier.error_table.table)}\n
              \tConfidence interval: {falsifier.get_confidence_interval()}''')
  
  # Write VerifAI output
  tables = []
  if falsifier_params.save_error_table:
    tables.append(falsifier.error_table.table)
    tables.append(falsifier.safe_table.table)
  root, _ = os.path.splitext(scenic_path)
  for i, df in enumerate(tables):
    outfile = root.split('/')[-1]
    if is_parallel:
      outfile += '_parallel'
    if sampler_type:
      outfile += f'_{sampler_type}'
    if i == 0:
      outfile += '_error'
    else:
      outfile += '_safe'
    outfile += '.csv'
    outpath = os.path.join(output_path, outfile)
    print(f'SAVING OUTPUT TO {outpath}')
    df.to_csv(outpath)
