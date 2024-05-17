import matplotlib.pylab as plt
import pandas as pd

import random
import trip_time as tt
from setting_generators import hiset_generators as hg
from inputs import input_file

dictionary = {'Criteria:': ['Downstream device overcurrent minimum grading:', 'Downstream max fuse 2 phase minimum grading:', 'Trip time at inrush current:', 'Primary overcurrent reach factor:', 'Back-up overcurrent reach factor:', 'Overcurrent pick up exceeds load factor (x1.1)?', 'Overcurrent pick up exceeds rating factor (x1.1)?', 'Overcurrent fault slowest trip time:']}, {'X2206291': ['No downstream devices', 0.622, 0.584, 5.33, 'No downstream devices', 'Yes', 'Rating factor unknown', 0.823]}, {'X7134-C': ['No downstream devices', 0.105, 0.441, 10.39, 'No downstream devices', 'Yes', 'Rating factor unknown', 0.175]}, {'X656-F': [0.484, 0.656, 0.591, 4.04, 3.49, 'Yes', 'Rating factor unknown', 0.89]}, {'PPE13A': [0.336, 0.12, 0.15, 2.83, 1.82, 'Yes', 'Yes', 1.198]}, {'Criteria:': ['Downstream device overcurrent minimum grading:', 'Downstream max fuse 2 phase minimum grading:', 'Trip time at inrush current:', 'Primary overcurrent reach factor:', 'Back-up overcurrent reach factor:', 'Overcurrent pick up exceeds load factor (x1.1)?', 'Overcurrent pick up exceeds rating factor (x1.1)?', 'Overcurrent fault slowest trip time:']}, {'X2206291': ['No downstream devices', 0.622, 0.584, 5.33, 'No downstream devices', 'Yes', 'Rating factor unknown', 0.823]}, {'X7134-C': ['No downstream devices', 0.105, 0.441, 10.39, 'No downstream devices', 'Yes', 'Rating factor unknown', 0.175]}, {'X656-F': [0.484, 0.656, 0.591, 4.04, 3.49, 'Yes', 'Rating factor unknown', 0.89]}, {'PPE13A': [0.336, 0.12, 0.15, 2.83, 1.82, 'Yes', 'Yes', 1.198]}

setting_report = pd.DataFrame.from_dict(dictionary)
print(setting_report)


relays = input_file.inputs()
relay_0 = relays[0]
relay_1 = relays[1]
relay_2 = relays[2]
relay_3 = relays[3]

"""print(relay_0.name)
print(relay_1.name)
print(relay_2.name)
print(relay_3.name)"""



"""fault_levels = [a for a in range(100, 5000, 10)]
trip_time = tt.ef_trip_time(relay_1, 491)
print(f"{relay_1.name}, {trip_time}")

for x in fault_levels:
    trip_time = tt.ef_trip_time(relay_1, x)
    print(f"{x}, {trip_time}")

ef_hiset_scenarios = hg.ef_hiset_mintime(relay_2)
print(ef_hiset_scenarios)"""







