import csv
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

class ThaveMobileScraper:
    def __init__(self):
        options = Options()
        # ****************** Use this for server hosting ***********************
        options.add_argument("--headless") 
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # **********************************************************************
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
        # self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920, 1080)
        
        # self.driver.get("https://holte-modelhobby.dk/")
        # time.sleep(3)
        # self.save_cookies("holte-modelhobby_cookies.json") #use when needed to refresh cookies or when cookies file missing
        # self.load_cookies("holte-modelhobby_cookies.json")
        # self.driver.refresh()

    def save_cookies(self, path):
        with open(path, 'w') as file:
            json.dump(self.driver.get_cookies(), file)

    def load_cookies(self, path):
        with open(path, 'r') as file:
            cookies = json.load(file)
            for cookie in cookies:
                self.driver.add_cookie(cookie)
        
    def extract_collection_links(self, output_file, url):
        all_products = []
        self.driver.get(url)
        time.sleep(2)  # Adjust sleep time as needed

        while True:
            wait = WebDriverWait(self.driver, 10)
            product_items = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.grid__item")))

            for item in product_items:
                try:
                    title_element = item.find_element(By.CSS_SELECTOR, "h3.card__heading a")
                    product_title = title_element.text
                    product_link = title_element.get_attribute("href")
                    print(product_link)
                    all_products.append([product_link])
                except Exception as e:
                    print(f"Error extracting product details: {e}")

            try:
                # Locate the "Next" button using aria-label
                next_button = self.driver.find_element(By.CSS_SELECTOR, "a[aria-label='Next page']")
                self.driver.execute_script("arguments[0].click();", next_button)
                time.sleep(2)  # Adjust sleep time as needed
            except Exception as e:
                print(f"Pagination ended or error occurred: {e}")
                # If the "Next" button is not found, break the loop
                break

        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Link"])
            writer.writerows(all_products)
    
    def get_product_links(self, collection_file, output_file):
        pass
    
    def extract_product_details(self, product_urls_file, output_file):
        def extract_details(product_url):
            json_url = product_url + ".json"
            response = requests.get(json_url)
            if response.status_code == 200:
                product_data = response.json()['product']
                variants = product_data['variants']

                details = []
                title = product_data.get('title', 'N/A')
                brand = product_data.get('vendor', 'N/A')
                for variant in variants:
                    sku = variant.get('sku', 'N/A')
                    price = variant.get('price', 'N/A')
                    price_currency = variant.get('price_currency', 'N/A')
                    full_price = f"{price} {price_currency}" if price != 'N/A' and price_currency != 'N/A' else 'N/A'
                    options = []
                    try:
                        for i in range(1, 11):  # Assuming there might be up to 10 options
                            option = variant.get(f'option{i}')
                            if option:
                                options.append(option)
                    except Exception as e:
                        print(f"Error extracting options: {e}")

                    details.append({
                        'Title': title,
                        'Brand': brand,
                        'SKU': sku,
                        'Price': full_price,
                        'Options': ', '.join(options) if options else 'N/A',
                        'URL': product_url
                    })
                return details
            else:
                print(f"Failed to fetch data from {json_url}")
                return [{
                    'Title': 'N/A',
                    'Brand': 'N/A',
                    'SKU': 'N/A',
                    'Price': 'N/A',
                    'Options': 'N/A',
                    'URL': product_url
                }]

        with open(product_urls_file, "r") as file:
            reader = csv.DictReader(file)
            product_urls = [row['Link'] for row in reader]

        with open(output_file, "w", newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Title', 'Brand', 'SKU', 'Price', 'Options', 'URL']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for url in product_urls:
                product_details_list = extract_details(url)
                for product_details in product_details_list:
                    writer.writerow(product_details)

    def close_driver(self):
        self.driver.quit()

if __name__ == "__main__":
    scraper = ThaveMobileScraper()
    
    url = "https://www.8thavemobile.sg/collections/all"
    output_file = '8thavemobile_product_links.csv'
    product_details = "8thavemobile_product_details.csv"
    
    print("Choose an option:")
    print("1. Extract collection links")
    print("2. Extract product details from product links")
    option = input("Enter the option number (1, 2, or 3): ")

    if option == "1":
        scraper.extract_collection_links(output_file, url)
    elif option == "2":
        scraper.extract_product_details(output_file, product_details)
    else:
        print("Invalid option. Please run the script again and choose a valid option.")

    scraper.close_driver()
