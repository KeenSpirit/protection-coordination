import pandas as pd


def grade_sheet_fuse_data():
    """
    This function is used for the grading sheet excel file
    :return:
    """
    path_ = 'Y:/PROTECTION/STAFF/Dan Park/PowerFactory/Dan script development/protection-coordination/templates_data'

    data = pd.read_excel(f'{path_}/EGX fuse data.xlsx', sheet_name='Data')
    data = data.interpolate()
    return data


def fuse_data():
    """
    This function is used for the line fuse study imputs
    :return:
    """

    path_ = 'Y:/PROTECTION/STAFF/Dan Park/PowerFactory/Dan script development/protection-coordination/templates_data'

    with open(f'{path_}/EQL Fuse Data.csv', 'r') as file:
        df = pd.read_csv(file)
    return df


fuse_data_1 = grade_sheet_fuse_data()
fuse_data_2 = fuse_data()
