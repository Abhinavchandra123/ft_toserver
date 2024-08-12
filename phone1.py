import csv
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

class HoltEModelHobbyScraper:
    def __init__(self):
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
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
        time.sleep(2)  

        wait = WebDriverWait(self.driver, 10)
        product_items = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.jet-woo-products__item.jet-woo-builder-product")))

        for item in product_items:
            title_element = item.find_element(By.CSS_SELECTOR, "h5.jet-woo-product-title a")
            product_title = title_element.text
            product_link = title_element.get_attribute("href")
            
            if product_title and product_link:
                all_products.append([product_title, product_link])

        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Title", "Link"])
            writer.writerows(all_products)
    
    def get_product_links(self, collection_file, output_file):
        pass
    
    def scroll_and_click(self, element):
        element.click()
        time.sleep(2)  # Wait for the click action to take effect

    def extract_product_details(self, product_urls_file, output_file):
        product_details = []
        with open(product_urls_file, 'r') as file:
            reader = csv.reader(file)
            next(reader)  
            urls = [row[1] for row in reader]

        for url in urls:
            self.driver.get(url)
            time.sleep(4) 

            wait = WebDriverWait(self.driver, 10)
            try:
                title_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product_title.entry-title.elementor-heading-title")))
                product_title = title_element.text
            except Exception as e:
                product_title = "N/A"
                print(f"Failed to extract title: {e}")

            try:
                storage_variations = self.driver.find_elements(By.CSS_SELECTOR, "ul[aria-label='Storage Size'] li")
                color_variations = self.driver.find_elements(By.CSS_SELECTOR, "ul[aria-label='Color'] li")

                try:
                    activation_variations = self.driver.find_elements(By.CSS_SELECTOR, "ul[aria-label='Activation'] li")
                    print(f"Found {len(activation_variations)} activation variations")
                except Exception as e:
                    activation_variations = []  # Set to empty list if not found
                    print(f"Activation variants not found: {e}")
                
                try:
                    connectivity_variations = self.driver.find_elements(By.CSS_SELECTOR, "ul[aria-label='Connectivity'] li")
                    print(f"Found {len(connectivity_variations)} connectivity variations")
                except Exception as e:
                    connectivity_variations = []  # Set to empty list if not found
                    print(f"Connectivity variants not found: {e}")

                print(f"Found {len(storage_variations)} storage variations")
                print(f"Found {len(color_variations)} color variations")

                if not activation_variations:
                    if not connectivity_variations:
                        # No activation or connectivity variants, process other variations
                        for storage in storage_variations:
                            while True:
                                self.scroll_and_click(storage)
                                try:
                                    elements = self.driver.find_elements(By.CSS_SELECTOR, "th.label span.woo-selected-variation-item-name")
                                    if any(storage.get_attribute('data-title') in element.text for element in elements):
                                        print(f"Clicked storage: {storage.get_attribute('data-title')}")
                                        break
                                except:
                                    pass
                            
                            for color in color_variations:
                                self.scroll_and_click(color)
                                print(f"Clicked color: {color.get_attribute('data-title')}")

                                try:
                                    price_element = self.driver.find_element(By.CSS_SELECTOR, "p.price span.woocommerce-Price-amount")
                                    price = price_element.text.replace('\n', '').strip()
                                    print(f"Extracted price: {price}")
                                except Exception as e:
                                    price = "N/A"
                                    print(f"Failed to extract price: {e}")
                                
                                try:
                                    stock_element = self.driver.find_element(By.CSS_SELECTOR, "div.woocommerce-variation-availability p.stock")
                                    if "out of stock" in stock_element.text.lower():
                                        stock_status = "Out of Stock"
                                    else:
                                        stock_status = "In Stock"
                                except Exception as e:
                                    stock_status = "In Stock"
                                    print(f"Failed to extract stock status: {e}")

                                storage_name = storage.get_attribute("data-title")
                                color_name = color.get_attribute("data-title")
                                variation_info = f"{storage_name},{color_name}"
                                print(f"Variation info: {variation_info}")
                                product_details.append([product_title, stock_status, variation_info, price, url])
                    else:
                        for connectivity in connectivity_variations:
                            while True:
                                self.scroll_and_click(connectivity)
                                try:
                                    elements = self.driver.find_elements(By.CSS_SELECTOR, "th.label span.woo-selected-variation-item-name")
                                    if any(connectivity.get_attribute('data-title') in element.text for element in elements):
                                        print(f"Clicked connectivity: {connectivity.get_attribute('data-title')}")
                                        break
                                except:
                                    pass
                            for storage in storage_variations:
                                self.scroll_and_click(storage)
                                print(f"Clicked storage: {storage.get_attribute('data-title')}")
                                
                                for color in color_variations:
                                    self.scroll_and_click(color)
                                    print(f"Clicked color: {color.get_attribute('data-title')}")

                                    try:
                                        price_element = self.driver.find_element(By.CSS_SELECTOR, "p.price span.woocommerce-Price-amount")
                                        price = price_element.text.replace('\n', '').strip()
                                        print(f"Extracted price: {price}")
                                    except Exception as e:
                                        price = "N/A"
                                        print(f"Failed to extract price: {e}")
                                    
                                    try:
                                        stock_element = self.driver.find_element(By.CSS_SELECTOR, "div.woocommerce-variation-availability p.stock")
                                        if "out of stock" in stock_element.text.lower():
                                            stock_status = "Out of Stock"
                                        else:
                                            stock_status = "In Stock"
                                    except Exception as e:
                                        stock_status = "In Stock"
                                        print(f"Failed to extract stock status: {e}")

                                    storage_name = storage.get_attribute("data-title")
                                    color_name = color.get_attribute("data-title")
                                    connectivity_name = connectivity.get_attribute('data-title')
                                    variation_info = f"{connectivity_name},{storage_name},{color_name}"
                                    print(f"Variation info: {variation_info}")
                                    product_details.append([product_title, stock_status, variation_info, price, url])

                else:
                    # Process cases with activation variants
                    for activation in activation_variations:
                        while True:
                            self.scroll_and_click(activation)
                            try:
                                elements = self.driver.find_elements(By.CSS_SELECTOR, "th.label span.woo-selected-variation-item-name")
                                if any("Activated" in element.text or "Not Activated" in element.text for element in elements):
                                    break
                            except:
                                pass

                        for storage in storage_variations:
                            self.scroll_and_click(storage)
                            print(f"Clicked storage: {storage.get_attribute('data-title')}")

                            for color in color_variations:
                                self.scroll_and_click(color)
                                print(f"Clicked color: {color.get_attribute('data-title')}")
                                
                                try:
                                    price_element = self.driver.find_element(By.CSS_SELECTOR, "p.price span.woocommerce-Price-amount")
                                    price = price_element.text.replace('\n', '').strip()
                                    print(f"Extracted price: {price}")
                                except Exception as e:
                                    price = "N/A"
                                    print(f"Failed to extract price: {e}")

                                try:
                                    stock_element = self.driver.find_element(By.CSS_SELECTOR, "div.woocommerce-variation-availability p.stock")
                                    if "out of stock" in stock_element.text.lower():
                                        stock_status = "Out of Stock"
                                    else:
                                        stock_status = "In Stock"
                                except Exception as e:
                                    stock_status = "In Stock"
                                    print(f"Failed to extract stock status: {e}")

                                activation_name = activation.get_attribute("data-title")
                                storage_name = storage.get_attribute("data-title")
                                color_name = color.get_attribute("data-title")
                                variation_info = f"{activation_name},{storage_name},{color_name}"
                                print(f"Variation info: {variation_info}")
                                product_details.append([product_title, stock_status, variation_info, price, url])

            except Exception as e:
                print(f"Error during scraping variations: {e}")
                
        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Title", "Stock status", "Variations", "Price", "URL"])
            writer.writerows(product_details)

    def close_driver(self):
        self.driver.quit()

if __name__ == "__main__":
    scraper = HoltEModelHobbyScraper()
    
    url = "https://www.mistermobile.com.sg/new-phone-mobile-shop-singapore/"
    output_file = 'holte-modelhobby_collections.csv'
    product_details = "holte-modelhobby_details.csv"
    
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
