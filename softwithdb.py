import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, JSON, TIMESTAMP
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from datetime import datetime
import random
import string
from datetime import datetime, timezone

Base = declarative_base()

class DevelopersMain(Base):
    __tablename__ = 'developersMain'
    id = Column(Integer, primary_key=True, autoincrement=True)
    uniqueID = Column(String(7), unique=True, nullable=False)
    companyName = Column(String(255))
    companyArea = Column(String(255))
    companyNumberAgents = Column(Integer)
    companyLicense = Column(String(48))
    companyLanguages = Column(String(255))
    companyDescription = Column(Text)
    companyServices = Column(JSON)
    companyOffices = Column(JSON)
    logo_filename = Column(String(255))
    banner_filename = Column(String(255))
    filePath = Column(String(500))
    scrapeVoid = Column(Boolean, default=False)
    scrapeLast_ts = Column(TIMESTAMP, default=datetime.utcnow)
    deleted_ts = Column(TIMESTAMP)
    updated_ts = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_ts = Column(TIMESTAMP, default=datetime.utcnow)

class DevelopersFiles(Base):
    __tablename__ = 'developersFiles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    developerID = Column(Integer, nullable=False)
    fileName = Column(String(255), unique=True, nullable=False)
    fileNameOri = Column(String(255))
    filePath = Column(String(500))
    fileType = Column(String(24))
    fileSize = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    video_duration = Column(Integer)
    video_link_type = Column(String(48))
    video_link_code = Column(String(255))
    category = Column(String(255))
    headline = Column(String(255))
    tagline = Column(String(255))
    tags = Column(String(255))
    deleted_ts = Column(TIMESTAMP)
    updated_ts = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_ts = Column(TIMESTAMP, default=datetime.utcnow)

class ReellyScraper:
    def __init__(self, email, password, db_url, start_company_id, end_company_id):
        self.email = email
        self.password = password
        self.start_company_id = start_company_id
        self.end_company_id = end_company_id
        options = Options()
        # options.add_argument('--headless')
        # options.add_argument('--no-sandbox')
        # options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.base_url = "https://soft.reelly.io"
        
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
    def generate_unique_id(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
    
    def login(self):
        login_url = f"{self.base_url}/sign-in"
        self.driver.get(login_url)
        time.sleep(3.5)
        
        email_input = self.driver.find_element(By.ID, 'email-2')
        email_input.send_keys(self.email)
        
        password_input = self.driver.find_element(By.ID, 'field')
        password_input.send_keys(self.password)
        
        continue_button = self.driver.find_element(By.XPATH, "//a[@wized='loginButton']")
        continue_button.click()
        
        time.sleep(5)
        
    def scrape_company_details(self, company_id):
        self.unique_id = self.generate_unique_id()
        self.data = {}
        
        company_url = f"{self.base_url}/market-company?company={company_id}"
        self.driver.get(company_url)
        time.sleep(3)
        
        try:
            self.data['companyName'] = self.driver.find_element(By.CLASS_NAME, 'name-agency').text
            self.data['companyArea'] = self.driver.find_element(By.CLASS_NAME, 'location-text').text
            self.data['companyNumberAgents'] = int(self.driver.find_element(By.XPATH, "//div[contains(@class, 'company-tag')]//div[contains(@class, 'text-block-33')]").text)
            self.data['companyLanguages'] = self.driver.find_element(By.CLASS_NAME, 'languages-number-txt').text
            self.data['companyLicense'] = self.driver.find_element(By.XPATH, "//div[contains(@class, 'license-block market')]//div[contains(@class, 'license-txt')][2]").text
            self.data['companyDescription'] = self.driver.find_element(By.CLASS_NAME, "offers-description-text").text
            
            services = self.driver.find_elements(By.CLASS_NAME, 'service-card')
            service_details = []
            for service in services:
                icon_url = service.find_element(By.CLASS_NAME, 'service-icon').get_attribute('src')
                service_text = service.find_element(By.CLASS_NAME, 'service-text').text
                service_details.append({'service_text': service_text, 'icon_url': icon_url})
            self.data['companyServices'] = service_details
            
            background_image_element = self.driver.find_element(By.CLASS_NAME, 'agency-background-photo')
            background_image_style = background_image_element.get_attribute('style')
            self.data['background_image_url'] = background_image_style.split('url("')[1].split('")')[0]
            
            logo_image_element = self.driver.find_element(By.CLASS_NAME, 'logo-agency-block')
            logo_image_style = logo_image_element.get_attribute('style')
            self.data['logo_image_url'] = logo_image_style.split('url("')[1].split('")')[0]
            
            video_iframe = self.driver.find_element(By.XPATH, "//div[@wized='marketCompanyVideoHTML']//iframe")
            self.data['video_url'] = video_iframe.get_attribute('src')
            
            photo_elements = self.driver.find_elements(By.XPATH, "//img[@wized='marketCompanyPhotos']")
            photo_urls = set() 
            for photo in photo_elements:
                photo_url = photo.get_attribute('src')
                photo_urls.add(photo_url)
            self.data['photo_urls'] = list(photo_urls)
            
        except Exception as e:
            print(f"Failed to scrape details for company ID {company_id}: {str(e)}")
            return
        
        self.save_to_db()
        
    def save_to_db(self):
        session = self.Session()
        company = DevelopersMain(
            uniqueID=self.unique_id,
            companyName=self.data.get('companyName'),
            companyArea=self.data.get('companyArea'),
            companyNumberAgents=self.data.get('companyNumberAgents'),
            companyLicense=self.data.get('companyLicense'),
            companyLanguages=self.data.get('companyLanguages'),
            companyDescription=self.data.get('companyDescription'),
            companyServices=self.data.get('companyServices'),
            logo_filename='logo_image.jpg',
            banner_filename='background_image.jpg',
            filePath=self.unique_id,
            created_ts=datetime.now(timezone.utc),
            updated_ts=datetime.now(timezone.utc)
        )
        session.add(company)
        session.commit()
        
        self.save_files_to_db(session, company.id)
        
        session.close()
        print("Data saved to database")
        
    def save_files_to_db(self, session, developer_id):
        folder_name = os.path.join('data', self.unique_id)
        os.makedirs(folder_name, exist_ok=True)
        
        self.download_image(self.data.get('logo_image_url'), folder_name, 'logo_image.jpg')
        self.download_image(self.data.get('background_image_url'), folder_name, 'background_image.jpg')
        
        photo_folder = os.path.join(folder_name, 'photos')
        os.makedirs(photo_folder, exist_ok=True)
        for index, photo_url in enumerate(self.data.get('photo_urls', [])):
            filename = f'photo_{index + 1}.jpg'
            self.download_image(photo_url, photo_folder, filename)
            file = DevelopersFiles(
                developerID=developer_id,
                fileName=self.generate_unique_filename(),
                fileNameOri=filename,
                filePath=os.path.join(photo_folder, filename),
                fileType='image/jpeg',
                fileSize=os.path.getsize(os.path.join(photo_folder, filename)),
                category='Company photo and video',
                created_ts=datetime.now(timezone.utc)
            )
            session.add(file)
        
        session.commit()
        
    def download_image(self, url, folder_name, filename):
        if not url:
            return
        response = requests.get(url)
        if response.status_code == 200:
            with open(os.path.join(folder_name, filename), 'wb') as file:
                file.write(response.content)
        else:
            print(f"Failed to download image from {url}")
            
    def generate_unique_filename(self, length=12):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    def close(self):
        self.driver.quit()
    
    def run(self):
        self.login()
        for company_id in range(self.start_company_id, self.end_company_id + 1):
            self.scrape_company_details(company_id)
        self.close()

# Usage
dbHost = 'localhost'
dbUser = 'root'
dbPassword = ''
dbName = ''
db_url = f'mysql+pymysql://{dbUser}:{dbPassword}@{dbHost}/{dbName}'
loginName = ''
loginPassword = ''
start_company_id = 1
end_company_id = 3
scraper = ReellyScraper(loginName,loginPassword, db_url, start_company_id, end_company_id)
scraper.run()
