import pandas as pd

"""
The PowerFactory Ergon library lists fuse sizes and melting curves, but doesn't link this to transformer size.
Transfer the information from "TSD0013i - RMU fuse selection guide" and "TSD0019i HV and LV fuse selection guide" to
CSV files.
Creeate a lookup function that matches the fuse size from Powerfactory with the transformer size as per the csv file.
Create a context manager using the with statement
"""

path_ = ('E:\Python\_python_work\protection_coordination\inputs')

Data = pd.read_excel(f'{path_}/EQL fuse data.xlsx', sheet_name='Data')
Data_2 = Data.interpolate()


def fuse_melting_time(fuse_name, fault_current):
    """
    Interpolates the fuse melting time for a given fuse and fault current.

    Parameters:
        fuse_name (str): Name of the fuse.
        fault_current (float): Fault current for which to interpolate the melting time.

    Returns:
        float: Interpolated fuse melting time.
    """
    # Extract the column index of the fuse
    fuse_index = Data_2.columns.get_loc(fuse_name)

    # Sort the DataFrame by the fault current column
    df_sorted = Data_2.sort_values(by=Data_2.columns[0])

    # Interpolate the melting time for the given fault current
    melting_time = df_sorted.iloc[:, [0, fuse_index]].interpolate(method='linear'). \
        loc[df_sorted.iloc[:, 0].searchsorted(fault_current)].iloc[1]

    return melting_time





