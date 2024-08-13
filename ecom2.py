import csv
import json
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

class MorfarsScraper:
    def __init__(self):
        options = Options()
        # ****************** Use this for server hosting ***********************
        options.add_argument("--headless") 
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # **********************************************************************
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
    
    def extract_product_links(self, url, output_file):
        def extract_links_from_page(url):
            self.driver.get(url)
            time.sleep(5)
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, '.product-card__figure a')
            product_links = [element.get_attribute('href') for element in product_elements if element.get_attribute('href')]

            with open(output_file, "a", newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=['Product Link'])
                if csvfile.tell() == 0: 
                    writer.writeheader()
                for link in product_links:
                    writer.writerow({'Product Link': link})

            return product_links

        def get_next_page_url():
            try:
                next_button = self.driver.find_element(By.CSS_SELECTOR, '.pagination__item[rel="next"]')
                if "pagination__item--disabled" in next_button.get_attribute("class"):
                    return None
                return next_button.get_attribute('href')
            except:
                return None
            # try:
            #     next_button = self.driver.find_element(By.CSS_SELECTOR, '#pagination .next-page')
            #     return next_button.get_attribute('href')
            # except:
            #     return None

        def extract_all_product_links(start_url):
            all_links = []
            self.driver.get(start_url)
            while True:
                product_links = extract_links_from_page(self.driver.current_url)
                all_links.extend(product_links)
                next_page_url = get_next_page_url()
                if next_page_url:
                    self.driver.get(next_page_url)
                    time.sleep(5)
                else:
                    break
            return all_links

        extract_all_product_links(url)
        
        
    def extract_product_details(self, product_urls_file, output_file):
        def extract_details(product_url):
            json_url = product_url + ".json"
            response = requests.get(json_url)
            if response.status_code == 200:
                product_data = response.json()['product']
                variants = product_data['variants']

                details = []
                for variant in variants:
                    title = product_data.get('title', 'N/A')
                    brand = product_data.get('vendor', 'N/A')
                    sku = variant.get('sku', 'N/A')
                    available = 'In Stock' if variant.get('inventory_management', 'shopify') == 'shopify' else 'Out of Stock'
                    price = variant.get('price', 'N/A')
                    quantity = variant.get('inventory_quantity', 'N/A')
                    print(quantity,type(quantity))
                    if quantity == 'N/A':
                        self.driver.get(url)
                        
                        try:
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '.product-info__inventory .text-with-icon'))
                            )
                            stock_status_element = self.driver.find_element(By.CSS_SELECTOR, '.product-info__inventory .text-with-icon')
                            stock_status = stock_status_element.text if stock_status_element else 'N/A'
                        except:
                            try:
                                sold_out_badge = self.driver.find_element(By.CSS_SELECTOR, '.badge--sold-out')
                                if sold_out_badge.is_displayed():
                                    stock_status = sold_out_badge.text
                                else:
                                    stock_status = 'N/A'
                            except:
                                stock_status = 'N/A'
                        print(stock_status)
                        if stock_status =='UDSOLGT':
                            available ='Out of Stock'
                        elif stock_status =='Udsolgt':
                            available ='Out of Stock'
                        else :
                            available ='In Stock'
                    if quantity <=0 :
                        self.driver.get(url)
                        try:
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '.product-info__inventory .text-with-icon'))
                            )
                            stock_status_element = self.driver.find_element(By.CSS_SELECTOR, '.product-info__inventory .text-with-icon')
                            stock_status = stock_status_element.text if stock_status_element else 'N/A'
                        except:
                            try:
                                sold_out_badge = self.driver.find_element(By.CSS_SELECTOR, '.badge--sold-out')
                                if sold_out_badge.is_displayed():
                                    stock_status = sold_out_badge.text
                                else:
                                    stock_status = 'N/A'
                            except:
                                stock_status = 'N/A'
                        print(stock_status)
                        if stock_status =='UDSOLGT':
                            available ='Out of Stock'
                        elif stock_status =='Udsolgt':
                            available ='Out of Stock'
                        else :
                            available ='In Stock'
                    details.append({
                        'Title': title,
                        'Brand':brand,
                        'SKU': sku,
                        'Price': f'{price} kr' if price != 'N/A' else 'N/A',
                        'Stock Status': available,
                        'Quantity': quantity,
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
                    'Stock Status': 'N/A',
                    'Quantity': 'N/A',
                    'URL': product_url
                }]

        with open(product_urls_file, "r") as file:
            reader = csv.DictReader(file)
            product_urls = [row['Product Link'] for row in reader]

        with open(output_file, "w", newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Title', 'Brand', 'SKU', 'Price', 'Stock Status', 'Quantity', 'URL']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for url in product_urls:
                product_details_list = extract_details(url)
                for product_details in product_details_list:
                    writer.writerow(product_details)


    def close_driver(self):
        self.driver.quit()

if __name__ == "__main__":
    scraper = MorfarsScraper()
    
    url = 'https://morfars.dk/collections/all'
    product_urls = "morfars_product_urls.csv"
    product_details = "morfars_product_details.csv"
    
    print("Choose an option:")
    print("1. Extract product links from collection links")
    print("2. Extract product details from product links")
    option = input("Enter the option number (1, 2): ")

    if option == "1":
        scraper.extract_product_links(url, product_urls)
    elif option == "2":
        scraper.extract_product_details(product_urls, product_details)
    else:
        print("Invalid option. Please run the script again and choose a valid option.")

    scraper.close_driver()
