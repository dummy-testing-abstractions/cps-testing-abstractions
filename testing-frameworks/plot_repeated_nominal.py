import sys
import os
import numpy as np
from plot.Plot import Storage
import matplotlib.pyplot as plt

# directory of the repeated tests
directory = 'pitl/flightdata/nominal-repeated'
# length of traces
trace_length = 10000
# generate csv files or not
gen_csv = False
csv_name = 'repeated_nominal.csv'

if __name__ == "__main__":
  
  #######################
  ### initializations ###
  #######################

  experiment_names = os.listdir(directory)
  experiment_names.sort()
  num_tests        = len(experiment_names)

  ### init storage classes
  avg_plot = Storage()
  avg_plot.estimated_position_x = np.zeros(trace_length)
  avg_plot.estimated_position_y = np.zeros(trace_length)
  avg_plot.estimated_position_z = np.zeros(trace_length)
  max_plot = Storage()
  max_plot.estimated_position_x = np.zeros(trace_length)
  max_plot.estimated_position_y = np.zeros(trace_length)
  max_plot.estimated_position_z = np.zeros(trace_length)
  min_plot = Storage()
  min_plot.estimated_position_x = 1000*np.ones(trace_length)
  min_plot.estimated_position_y = 1000*np.ones(trace_length)
  min_plot.estimated_position_z = 1000*np.ones(trace_length)

  #######################
  ### data extraction ###
  #######################

  ## open all flight data 
  all_data = [Storage() for i in range(num_tests)]
  for i in range(num_tests):
    file_location = directory + '/' + experiment_names[i]
    all_data[i] = Storage()
    all_data[i].open(file_location, experiment_names[i])

  ## iterate over time to get average min and max
  for t in range(trace_length):
    ## iterate over the different tests
    for data in range(num_tests):
      ## average values
      avg_plot.estimated_position_x[t] = avg_plot.estimated_position_x[t] + \
                                         (all_data[data].estimated_position_x[t]/num_tests)
      avg_plot.estimated_position_y[t] = avg_plot.estimated_position_y[t] + \
                                         (all_data[data].estimated_position_y[t]/num_tests)
      avg_plot.estimated_position_z[t] = avg_plot.estimated_position_z[t] + \
                                         (all_data[data].estimated_position_z[t]/num_tests)
      ## min values
      min_plot.estimated_position_x[t] = min(min_plot.estimated_position_x[t], \
                                             all_data[data].estimated_position_x[t])
      min_plot.estimated_position_y[t] = min(min_plot.estimated_position_y[t], \
                                             all_data[data].estimated_position_y[t])
      min_plot.estimated_position_z[t] = min(min_plot.estimated_position_z[t], \
                                             all_data[data].estimated_position_z[t])
      ## max values
      max_plot.estimated_position_x[t] = max(max_plot.estimated_position_x[t], \
                                             all_data[data].estimated_position_x[t])
      max_plot.estimated_position_y[t] = max(max_plot.estimated_position_y[t], \
                                             all_data[data].estimated_position_y[t])
      max_plot.estimated_position_z[t] = max(max_plot.estimated_position_z[t], \
                                             all_data[data].estimated_position_z[t])

  # get time trace
  avg_plot.time = all_data[0].time[0:trace_length]

  # get setpoints
  avg_plot.setpoint_position_x = all_data[0].data.set_pt[0, 0:trace_length]
  avg_plot.setpoint_position_y = all_data[0].data.set_pt[1, 0:trace_length]
  avg_plot.setpoint_position_z = all_data[0].data.set_pt[2, 0:trace_length]

  #######################
  ### actual plotting ###
  #######################

  # some settingss
  chosen_size = (20, 7)
  chosen_grid_linewidth = 0.3
  chosen_grid_linestyle = '--'
  chosen_grid_color = 'gray'

  fig, axs = plt.subplots(3, 1, figsize=chosen_size)
  plt.subplots_adjust(wspace=0.2, hspace=1)

  axs[0].title.set_text('Estimated Position (x)')
  axs[0].plot(avg_plot.time, avg_plot.setpoint_position_x, 'k')
  axs[0].plot(avg_plot.time, min_plot.estimated_position_x, 'b', linestyle = 'dashed')
  axs[0].plot(avg_plot.time, avg_plot.estimated_position_x, 'b:')
  axs[0].plot(avg_plot.time, max_plot.estimated_position_x, 'b', linestyle = 'dashed')
  axs[0].legend(['setpoint','min', 'avg', 'max'])
  axs[0].grid(color=chosen_grid_color, linestyle=chosen_grid_linestyle, linewidth=chosen_grid_linewidth)

  axs[1].title.set_text('Estimated Position (y)')
  axs[1].plot(avg_plot.time, avg_plot.setpoint_position_y, 'k')
  axs[1].plot(avg_plot.time, min_plot.estimated_position_y, 'g', linestyle = 'dashed')
  axs[1].plot(avg_plot.time, avg_plot.estimated_position_y, 'g:')
  axs[1].plot(avg_plot.time, max_plot.estimated_position_y, 'g', linestyle = 'dashed')
  axs[1].legend(['setpoint','min', 'avg', 'max'])
  axs[1].grid(color=chosen_grid_color, linestyle=chosen_grid_linestyle, linewidth=chosen_grid_linewidth)

  axs[2].title.set_text('Estimated Position (z)')
  axs[2].plot(avg_plot.time, avg_plot.setpoint_position_z, 'k')
  axs[2].plot(avg_plot.time, min_plot.estimated_position_z, 'r', linestyle = 'dashed')
  axs[2].plot(avg_plot.time, avg_plot.estimated_position_z, 'r:')
  axs[2].plot(avg_plot.time, max_plot.estimated_position_z, 'r', linestyle = 'dashed')
  axs[2].legend(['setpoint','min', 'avg', 'max'])
  axs[2].grid(color=chosen_grid_color, linestyle=chosen_grid_linestyle, linewidth=chosen_grid_linewidth)

  plt.show()

  if gen_csv :
    with open(csv_name, 'w') as f:

      # header for file
      f.write('i, time, ' +
              'min_estimated_position_x, min_estimated_position_y, min_estimated_position_z, ' +
              'avg_estimated_position_x, avg_estimated_position_y, avg_estimated_position_z, ' +
              'max_estimated_position_x, max_estimated_position_y, max_estimated_position_z, ' +
              'setpoint_position_x, setpoint_position_y, setpoint_position_z, \n')

      for i in range(trace_length):
        ith_string = str(i) + ", " + \
                     str(avg_plot.time[i]) + ", " + \
                     str(min_plot.estimated_position_x[i]) + ", " + \
                     str(min_plot.estimated_position_y[i]) + ", " + \
                     str(min_plot.estimated_position_z[i]) + ", " + \
                     str(avg_plot.estimated_position_x[i]) + ", " + \
                     str(avg_plot.estimated_position_y[i]) + ", " + \
                     str(avg_plot.estimated_position_z[i]) + ", " + \
                     str(max_plot.estimated_position_x[i]) + ", " + \
                     str(max_plot.estimated_position_y[i]) + ", " + \
                     str(max_plot.estimated_position_z[i]) + ", " + \
                     str(avg_plot.setpoint_position_x[i])  + ", " + \
                     str(avg_plot.setpoint_position_y[i])  + ", " + \
                     str(avg_plot.setpoint_position_z[i])  + "\n"
        f.write(ith_string)