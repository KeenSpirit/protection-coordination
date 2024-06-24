from pathlib import Path
import pandas as pd


# TODO: Below are temporary data storeage paths to be used during testing. These are to be updated to Q drive when
#  deployed.

def grade_sheet_fuse_data():
    """
    This function is used for the grading sheet excel file
    :return:
    """

    user = Path.home().name
    basepath = Path('//client/c$/LocalData') / user

    if basepath.exists():
        clientpath = basepath / Path('RelayCoordinationStudies')
    else:
        clientpath = Path('c:/LocalData') / user / Path('RelayCoordinationStudies')

    data = pd.read_excel(f'{clientpath}/EGX fuse data.xlsx', sheet_name='Data')
    data = data.interpolate()
    return data


def fuse_data():
    """
    This function is used for the line fuse study imputs
    :return:

    """
    user = Path.home().name
    basepath = Path('//client/c$/LocalData') / user

    if basepath.exists():
        clientpath = basepath / Path('RelayCoordinationStudies')
    else:
        clientpath = Path('c:/LocalData') / user / Path('RelayCoordinationStudies')

    with open(f'{clientpath}/EQL Fuse Data.csv', 'r') as file:
        df = pd.read_csv(file)
    return df


def netplan_extract():
    """

    :return:
    """
    user = Path.home().name
    basepath = Path('//client/c$/LocalData') / user

    if basepath.exists():
        clientpath = basepath / Path('RelayCoordinationStudies')
    else:
        clientpath = Path('c:/LocalData') / user / Path('RelayCoordinationStudies')

    with open(f'{clientpath}/Netplan Extract.csv', 'r') as file:
        df = pd.read_csv(file)
    return df


fuse_data_1 = grade_sheet_fuse_data()
fuse_data_2 = fuse_data()

