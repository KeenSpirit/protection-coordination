from pathlib import Path
import time
import powerfactory as pf
import pandas as pd


def main(app):
    """

    :return:
    """

    user = app.GetCurrentUser()
    database = user.fold_id
    app.PrintPlain('Obtaining master folders...')
    seq_models = database.GetContents("Publisher\\MasterProjects\\SEQ Models")[0]
    projects_folder = seq_models.GetContents("*.IntPrj")


    all_feeders = []
    for project in projects_folder:
        app.PrintPlain(f'retrieving feeders for project {project}...')
        feeders_folder = project.GetContents(r"Network Model\Network Data\Feeders")[0]
        feeders = feeders_folder.GetContents("*.ElmFeeder")
        project_feeders = [feeder.loc_name for feeder in feeders]
        all_feeders.extend(project_feeders)

    feeders_dict = {'Feeder': all_feeders}

    return feeders_dict


def save_file(app, dictionary):

    import os

    date_string = time.strftime("%Y%m%d")
    format_dataframe = pd.DataFrame.from_dict(dictionary)
    filename = 'PowerFactory Feeders ' + date_string + ".xlsx"
    user = Path.home().name
    basepath = Path('//client/c$/LocalData') / user

    if basepath.exists():
        clientpath = basepath / Path('RelayCoordinationStudies')
    else:
        clientpath = Path('c:/LocalData') / user / Path('RelayCoordinationStudies')
    filepath = os.path.join(clientpath, filename)

    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # General Information sheet
        format_dataframe.to_excel(writer, sheet_name='PowerFactory Feeders', index=False)

    app.PrintPlain("Output file saved to " + filepath)


if __name__ == '__main__':
    start = time.time()

    app = pf.GetApplication()
    app.SetEnableUserBreak(1)
    app.ClearOutputWindow()

    dictionary = main(app)
    save_file(app, dictionary)

    end = time.time()
    run_time = round(end - start, 6)
    print(f"Script run time: {run_time} seconds")