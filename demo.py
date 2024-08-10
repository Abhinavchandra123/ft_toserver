from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--remote-debugging-port=9222')

# Initialize the WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Load the page to set up cookies
driver.get("https://rckongen.dk/en/")

# Wait for the page to load properly
time.sleep(5)

# Load and add cookies
with open('cookies.json', 'r') as file:
    cookies = json.load(file)
    for cookie in cookies:
        driver.add_cookie(cookie)

# Refresh the page to apply the cookies
driver.refresh()
time.sleep(5)

# Print page title and source
print(driver.title)
print(driver.page_source)

# Quit the WebDriver
driver.quit()
