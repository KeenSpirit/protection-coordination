import pandas as pd
import os
from pathlib import Path


def input():

    home_path = str(Path.home())
    path_ = '\\\\client\\' + home_path[0] + '$' + home_path[2:]

    data = pd.read_excel(f'{path_}/relay_grading_input_file.xlsx', sheet_name='Inputs')
    data = data.loc[:, ~data.columns.str.contains('Unnamed|^$')]
    data_1 = data.iloc[:,1:]

    data_2 = data_1.to_dict('list')
    return data_2


