""""
Scrape feeder load and rating data from corporate Netplan intranet site
"""

from pathlib import Path
import time
import pandas as pd
from typing import Union, Any
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def get_inputs() -> list:

    filename = 'PowerFactory Feeders.xlsx'

    user = Path.home().name
    clientpath = Path('c:/LocalData') / user / Path('RelayCoordinationStudies')

    feeders_pd = pd.read_excel(
        f'{clientpath}/{filename}')
    all_feeders_dict = feeders_pd.to_dict()
    all_feeders_list = [feeder for feeder in all_feeders_dict.values()][0]
    all_feeders = [str(feeder) for feeder in all_feeders_list.values()]

    return all_feeders


def query_all_feeders(all_feeders):

    rating_sd = []
    rating_sn = []
    max_load = []
    driver = chrome_driver()
    for feeder in all_feeders:
        print(f'Analysing feeder {feeder}')
        if feeder != all_feeders[0]:
            rating_sd_value, rating_sn_value, max_value = query_netplan(driver, feeder)
        else:
            rating_sd_value, rating_sn_value, max_value = query_netplan(driver, feeder, first_query=True)
        rating_sd.append(rating_sd_value)
        rating_sn.append(rating_sn_value)
        max_load.append(max_value)

    netplan_dict = {
        'Feeder': all_feeders,
        'Rating SD': rating_sd,
        'Rating SN': rating_sn,
        'Maximum load': max_load
    }
    driver.quit()

    return netplan_dict


def query_netplan(driver, feeder_name, first_query=False) -> tuple[Union[str,None], Union[float,None], Union[float,None]]:
    """

    :param driver:
    :param feeder_name:
    :param first_query:
    :return:
    """

    def failed(driver):
        # Go back to Ratings tab in preparation for next iteration
        rating_button = driver.find_element(By.ID, 'MN006')
        rating_button.click()
        time.sleep(1)
        rating_sd_value = ''
        rating_sn_value = ''
        max_value = ''
        return rating_sd_value, rating_sn_value, max_value

    forecast_years = 5
    poe = 10

    current_date, future_date = get_times(forecast_years)

    try:
        if first_query:
            driver.get("http://sbnswas116.services.local:82/Netplan/(S(x3bat2h3b45o2cqe0ho4qrpb))/Ratings/Rating.aspx")
        search_input = driver.find_element(By.CSS_SELECTOR, "div.dataTables_filter input[type='search']")
        search_input.clear()
        search_input.send_keys(feeder_name)
        search_input.send_keys(Keys.RETURN)
        time.sleep(1)
        try:
            loadflow_rating_cell = driver.find_element(By.XPATH, "//td[text()='LOADFLOW RATING']")
            loadflow_rating_cell.click()
        except:
            project_rating_cell = driver.find_element(By.XPATH, "//td[text()='PROJECT RATING']")
            project_rating_cell.click()
        forecast_button = driver.find_element(By.ID, "MN002")
        forecast_button.click()
        time.sleep(1)

        # Get thermal rating
        table = driver.find_element(By.ID, "ForecastDataTableWithEventsFiltered")

        # Iterate through the rows of the table
        rows = table.find_elements(By.TAG_NAME, "tr")

        # Initialize variable to store the rating SD value
        rating_sd_value = None
        rating_sn_value = None

        for row in rows:
            # Get the cells in the row
            cells = row.find_elements(By.TAG_NAME, "td")

            # Check if the row has the "THERMAL RATING" in the "Event" column (2nd column)
            if len(cells) > 1 and cells[1].text == "THERMAL RATING":
                # Extract the value from the specified rating column
                rating_sd_value = cells[8].text
                rating_sn_value = cells[9].text
                break

        # Set POE
        dropdown_element = driver.find_element(By.ID, "ctl00_Content_Body_filterPOE")
        select = Select(dropdown_element)
        select.select_by_visible_text(f"{poe}% POE")
        time.sleep(1)

        # Set Start and finish dates
        if first_query:
            button = driver.find_element(By.ID, "UserFiltersControl")
            button.click()
            time.sleep(1)
            start_date = driver.find_element(By.NAME, 'ctl00$FLT008')
            start_date.clear()
            start_date.send_keys(current_date)
            end_date = driver.find_element(By.NAME, 'ctl00$FLT009')
            end_date.clear()
            end_date.send_keys(future_date)
            button = driver.find_element(By.ID, "ctl00_btnFilterApply")
            button.click()
            time.sleep(1)

        # Obtain forecast data
        table = driver.find_element(By.ID, 'ForecastDataTable')
        # Locate all rows in the table body
        rows = table.find_elements(By.CSS_SELECTOR, 'tbody tr')

        # Initialize a variable to keep track of the maximum value
        max_value = float('-inf')

        # Column indices for 'Forecast SD', 'Forecast SN', 'Forecast WD', and 'Forecast WN'
        forecast_sd_index = 8
        forecast_sn_index = 9
        forecast_wd_index = 10
        forecast_wn_index = 11

        # Loop through each row to find the maximum value across the specified columns
        for row in rows:

            # Find all cells in the row
            cells = row.find_elements(By.TAG_NAME, 'td')
            if cells[0].text == 'No data available in table':
                rating_sd_value, rating_sn_value, max_value = failed(driver)
                return rating_sd_value, rating_sn_value, max_value

            # Extract and compare values for 'Forecast SD'
            forecast_sd_text = cells[forecast_sd_index].text
            if forecast_sd_text:
                forecast_sd_value = float(forecast_sd_text)
                if forecast_sd_value > max_value:
                    max_value = forecast_sd_value

            # Extract and compare values for 'Forecast SN'
            forecast_sn_text = cells[forecast_sn_index].text
            if forecast_sn_text:
                forecast_sn_value = float(forecast_sn_text)
                if forecast_sn_value > max_value:
                    max_value = forecast_sn_value

            # Extract and compare values for 'Forecast WD'
            forecast_wd_text = cells[forecast_wd_index].text
            if forecast_wd_text:
                forecast_wd_value = float(forecast_wd_text)
                if forecast_wd_value > max_value:
                    max_value = forecast_wd_value

            # Extract and compare values for 'Forecast WN'
            forecast_wn_text = cells[forecast_wn_index].text
            if forecast_wn_text:
                forecast_wn_value = float(forecast_wn_text)
                if forecast_wn_value > max_value:
                    max_value = forecast_wn_value

        # Go back to Ratings tab in preparation for next iteration
        rating_button = driver.find_element(By.ID, 'MN006')
        rating_button.click()
        time.sleep(1)

    except:
        rating_sd_value, rating_sn_value, max_value = failed(driver)
        return rating_sd_value, rating_sn_value, max_value

    return rating_sd_value, rating_sn_value, max_value


def get_times(forecast_years) -> tuple[str, str]:
    """

    :param forecast_years:
    :return:
    """

    current_time = time.localtime()
    current_date = time.strftime('%d/%m/%Y', current_time)

    future_time = time.struct_time((
        current_time.tm_year + forecast_years,  # Add 5 years
        current_time.tm_mon,
        current_time.tm_mday,
        current_time.tm_hour,
        current_time.tm_min,
        current_time.tm_sec,
        current_time.tm_wday,
        current_time.tm_yday,
        current_time.tm_isdst
    ))

    # Format the future date
    future_date = time.strftime('%d/%m/%Y', future_time)

    return current_date, future_date


def chrome_driver():
    """

    :return:
    """

    from pathlib import Path
    import os

    # Initialize the Chrome options
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_version = dv.get_chrome_version()

    clientpath = 'Y:/PROTECTION/STAFF/Dan Park/PowerFactory/Dan script development/protection-coordination/templates_data/chromedriver-win64 1.25/chromedriver.exe'

    service = Service(clientpath)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    if not driver:
        return None

    return driver


def save_file(dictionary):

    import os

    date_string = time.strftime("%Y%m%d-%H%M%S")
    format_dataframe = pd.DataFrame.from_dict(dictionary)
    filename = 'Netplan Extract ' + date_string + ".csv"

    clientpath = 'C:/LocalData/dp072/RelayCoordinationStudies'
    filepath = os.path.join(clientpath, filename)
    print('Writing data to excel file...')
    with open(filepath, mode='w', newline='') as file:
        format_dataframe.to_csv(file, index=False)


    print("Output file saved to " + filepath)

if __name__ == '__main__':
    start = time.time()

    all_feeders = get_inputs()
    dictionary = query_all_feeders(all_feeders)
    save_file(dictionary)

    end = time.time()
    run_time = round(end - start, 6)
    print(f"Script run time: {run_time} seconds")

