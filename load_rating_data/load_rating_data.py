"""
Scrape feeder load and rating data from corporate Netplan intranet site
"""
import time
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from input_files.input_file import instructions, grad_param


def query_netplan() -> tuple[str|None, float|None]:
    """

    :param netplan_inputs:
    :return:
    """

    # Input parameters
    feeder_name = instructions[0]
    forecast_years = grad_param['Load forecast years']
    thermal_rating = grad_param['Feeder rating period']
    poe = grad_param['Load forecast years POE']
    if thermal_rating == "SD":
        col = 8
    else:
        col = 9     # thermal_rating == "SN"


    current_date, future_date = get_times(forecast_years)

    driver = chrome_driver()
    if not driver:
        return None, None

    try:
        driver.get("http://sbnswas116.services.local:82/Netplan/(S(hahm3g14nkffltlrf13j5c2p))/Ratings/Rating.aspx")
        search_input = driver.find_element(By.CSS_SELECTOR, "div.dataTables_filter input[type='search']")
        search_input.send_keys(feeder_name)
        search_input.send_keys(Keys.RETURN)
        time.sleep(1)
        loadflow_rating_cell = driver.find_element(By.XPATH, "//td[text()='LOADFLOW RATING']")
        loadflow_rating_cell.click()
        forecast_button = driver.find_element(By.ID, "MN002")
        forecast_button.click()
        time.sleep(1)

        # Get thermal rating
        table = driver.find_element(By.ID, "ForecastDataTableWithEventsFiltered")

        # Iterate through the rows of the table
        rows = table.find_elements(By.TAG_NAME, "tr")

        # Initialize variable to store the rating SD value
        rating_sd_value = None

        for row in rows:
            # Get the cells in the row
            cells = row.find_elements(By.TAG_NAME, "td")

            # Check if the row has the "THERMAL RATING" in the "Event" column (2nd column)
            if len(cells) > 1 and cells[1].text == "THERMAL RATING":
                # Extract the value from the specified rating column
                rating_sd_value = cells[col].text
                break

        # Set POE
        dropdown_element = driver.find_element(By.ID, "ctl00_Content_Body_filterPOE")
        select = Select(dropdown_element)
        select.select_by_visible_text(f"{poe}% POE")

        # Set Start and finish dates
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

    except:
        rating_sd_value = None
        max_value = None

    driver.quit()

    return rating_sd_value, max_value


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


def chrome_driver() -> object:
    """

    :return:
    """

    # Initialize the Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_version = get_chrome_version()
    if chrome_version == '125.0.6422.113':
        chrome_driver_path = \
         'Y:/PROTECTION/STAFF/Dan Park/PowerFactory/Dan script development/protection-coordination/templates_data/chromedriver-win64 1.25/chromedriver.exe'
        service = Service(chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        driver = None

    return driver


def get_chrome_version():

    import winreg as reg

    try:
        reg_path = r"SOFTWARE\Google\Chrome\BLBeacon"
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, reg_path)
        version, _ = reg.QueryValueEx(key, "version")
        return version
    except Exception as e:
        return None

