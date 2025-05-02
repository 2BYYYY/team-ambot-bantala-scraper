from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Set up Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (Windows-specific)
chrome_options.add_argument("--no-sandbox")  # Recommended for Linux

# Set up WebDriver with service
service = Service("/usr/local/bin/chromedriver")  # Path where Docker installed it
driver = webdriver.Chrome(service=service, options=chrome_options)

PHIVOLCS_URL = "https://wovodat.phivolcs.dost.gov.ph/bulletin/list-of-bulletin?vdId=565&type=bulletin&sdate=2021-01-01&edate=&page=1"
driver.get(PHIVOLCS_URL)

# Initializing variables
TYPE_VOLCANO = "NO DATA"
BULLETIN_DATE = "NO DATA"
ALERT_LEVEL = "NO DATA"
ERUPTION = "NO DATA"
ACTIVITY = "NO DATA"
SEISMICITY = "NO DATA"
SULFUR_DIOXIDE_FLUX = "NO DATA"
PLUME = "NO DATA"
GROUND_DEFORMATION = "NO DATA"

# Get Volcano Type
try:
    VOLCANO = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, f"/html/body/div[2]/div[3]/div/div/div[2]/form/div/div[3]/div[4]/table/tbody/tr[1]/td[1]"))
    )
    TYPE_VOLCANO = VOLCANO.text
except Exception as e:
    print(f"Error getting Volcano: {e}")

# Get Bulletin Date
try:
    DATE = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, f"/html/body/div[2]/div[3]/div/div/div[2]/form/div/div[3]/div[4]/table/tbody/tr[1]/td[3]"))
    )
    BULLETIN_DATE = DATE.text
except Exception as e:
    print(f"Error getting Bulletin Date: {e}")

# Get First Row and Click
try:
    FIRST_ROW = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[3]/div/div/div[2]/form/div/div[3]/div[4]/table/tbody/tr[1]/td[4]"))
    )
    FIRST_ROW.click()
except Exception as e:
    print(f"Error clicking first row: {e}")

# Switch to New Window
window_handles = driver.window_handles
driver.switch_to.window(window_handles[1])

# Get Parameters
try:
    PARAMS = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.XPATH, "/html/body/div/div/div[3]/div[2]/div[3]/div/table/tbody/tr"))
    )
except Exception as e:
    print(f"Error getting parameters: {e}")

# Get Alert Level
try:
    div_element = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div[3]/div[2]/div[1]/div[1]/div[2]/table/tbody/tr/td[2]/div"))
    )
    ALERT_LEVEL = div_element.text
except Exception as e:
    print(f"Error getting alert level: {e}")

# Loop through Parameters
for index_params in range(1, len(PARAMS) + 1):
    try:
        TYPE_PARAMS = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, f"/html/body/div/div/div[3]/div[2]/div[3]/div/table/tbody/tr[{index_params}]/td[1]"))
        )
        CLEAN = str(TYPE_PARAMS.text.strip().lower())
        TYPE_PARAMS_CLEAN = " ".join(CLEAN.split())

        DESCRIPTION_PARAMS = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, f"/html/body/div/div/div[3]/div[2]/div[3]/div/table/tbody/tr[{index_params}]/td[2]/p"))
        )

        if TYPE_PARAMS_CLEAN == "eruption":
            ERUPTION = DESCRIPTION_PARAMS.text
        elif TYPE_PARAMS_CLEAN == "activity":
            ACTIVITY = DESCRIPTION_PARAMS.text
        elif TYPE_PARAMS_CLEAN == "seismicity":
            SEISMICITY = DESCRIPTION_PARAMS.text
        elif TYPE_PARAMS_CLEAN == "sulfur dioxide flux":
            SULFUR_DIOXIDE_FLUX = DESCRIPTION_PARAMS.text
        elif TYPE_PARAMS_CLEAN == "plume":
            PLUME = DESCRIPTION_PARAMS.text
        elif TYPE_PARAMS_CLEAN == "ground deformation":
            GROUND_DEFORMATION = DESCRIPTION_PARAMS.text
    except Exception as e:
        print(f"Error processing parameter {index_params}: {e}")

print(TYPE_VOLCANO, BULLETIN_DATE, ALERT_LEVEL, ERUPTION, ACTIVITY, SEISMICITY, SULFUR_DIOXIDE_FLUX, PLUME, GROUND_DEFORMATION)
print("Data Extracted")

# Close the browser
driver.close()
driver.switch_to.window(window_handles[0])
driver.quit()
