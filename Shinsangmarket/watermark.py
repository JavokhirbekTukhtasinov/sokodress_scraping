from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, UnexpectedAlertPresentException
from selenium import webdriver
import pandas as pd
import os
from os import listdir
import time
from pynput.keyboard import Controller, Key
# from lib import create_folder, downloadImage
options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.add_argument('--start-maximized')




def downloadImage(url:str, path:str): 
    try:
        # url = 'https://image-v4.sinsang.market/?f=https://image-cache.sinsang.market/images/25232/92085305/167655035100655297_1462791657.jpg&w=1500&h=2000'
        # url = 'https://www.searchenginejournal.com/wp-content/uploads/2022/06/image-search-1600-x-840-px-62c6dc4ff1eee-sej-1280x720.png'

        headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'  # A common user agent
                }
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            with open(f'{path}', 'wb') as f:
                f.write(response.content)
            print("Image downloaded successfully.")
        else:
            print("Failed to download image. Status code:", response.status_code)

        # urlretrieve(url, './Products/test.png')

        # image_response = requests.get(url, stream=True)
        # with open('./Products/test.jpg', 'wb') as out_file:
        #     shutil.copyfileobj(image_response.raw, out_file)
        # del image_response
        # print(image_response.status_code)
        # if image_response.status_code == 200: 
        #     with  open('./Products/test2.jpg', 'wb') as out_file:
        #         out_file.write(image_response.content)
        #     return HTTPException( 
        #      status_code=status.HTTP_200_OK
        #     )

    except Exception as err: 
        print(f'Error {err}')


def create_folder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)

    except OSError:
        print(f"Error: Creating directory {directory}")
     
def watermark(images):
   print('test')
   
   
def images():
   
   global driver
   driver = webdriver.Chrome(service=Service(), options=options)
   folder_path = f'{os.getcwd()}/../Products'

   image_list = listdir(folder_path)[:2]
   create_folder('./Watermark')
   for image in image_list:
      driver.get('https://www.watermarkremover.io/upload')
      driver.find_element(By.ID, 'uploadImage').send_keys(f'/Users/jackson/Desktop/elether/sokodress_scraping/Products/{image}')
      time.sleep(20)

      # image_src = driver.find_element(By.CLASS_NAME, 'ImageMagnifier__StyledPixelBinImage-sc-kcdk33-3 kBnRAJ').get_attribute('src')
      # print(f'Image src : {image_src}')
      # image_path = './Watermark/' + image
      # downloadImage(image_src, image_path)
      
      
   time.sleep(1999)
   
   folder_path = f'{os.getcwd()}/../../productImages'
   image_list = listdir(folder_path)[:10]


   for image in image_list: 
      print(image)
      
      # urlretrieve(f'https://sokodress.s3.ap-northeast-2.amazonaws.com/Products/{image}', f'./Products/{image}')

images()