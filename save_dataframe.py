from pathlib import Path
import pandas as pd


def is_file_in_use(file_path):
    """Checks to see if the file entered is in use
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError

    try:
        path.rename(path)
    except PermissionError:
        return True
    else:
        return False


def save_dataframe(dataframe_1, dataframe_2, filename):
    """ saves the dataframe in the user directory using the provided
    file name. If the user is connected through citrix, the file should
    be saved local users PowerFactoryResults folder
    """
    user = Path.home().name
    basepath = Path('//client/c$/Users') / user

    if basepath.exists():
        clientpath = basepath / Path('PowerFactoryResults')
    else:
        clientpath = Path('c:/Users') / user / Path('PowerFactoryResults')

    clientpath.mkdir(exist_ok=True)
    filepath = clientpath / Path(filename + '.xlsx')

    if filepath.exists() and is_file_in_use(filepath):
        file_suffix = 0
        while filepath.exists() and is_file_in_use(filepath):
            filepath = clientpath / Path(filename + '_' + str(file_suffix).zfill(3) + '.xlsx')
            file_suffix += 1

    with pd.ExcelWriter(filepath) as writer:
        dataframe_1.to_excel(writer, sheet_name='Results')
        dataframe_2.to_excel(writer, sheet_name='Setting Report', index=False)
        #dataframe.to_excel(writer, sheet_name='Results', index=False)