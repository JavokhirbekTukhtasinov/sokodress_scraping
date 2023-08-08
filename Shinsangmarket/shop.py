from fastapi import APIRouter
from pydantic import BaseModel
router = APIRouter()
import math
import os
import time
import datetime
import re
import pickle
import boto3
from glob import glob
import pandas as pd
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ActionChains, Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import pymysql
from fastapi import HTTPException, status
from urllib.request import urlretrieve
import shutil
from datetime import datetime
# class ShopRequestBody(BaseModel):
#     shop_id: 

@router.post('/{shop_id}/{id}/{password}')
def shop(shop_id: int, id: str, password: str):
    """
    Scraping shop 
    """

    return  scrap_shop(shop_id, id = 'bong2692', password = 'sinsang4811!')
# end def


def scrap_shop(shop_id:int, id, password):
    
    # db 
    
    conn = pymysql.connect(
        host='52.79.173.93',
        port=3306,
        user='user',
        passwd='seodh1234',
        db='sokodress',
        charset='utf8'
    )
    
    # aws s3 storage
    
    s3 = boto3.client(
        's3',
        aws_access_key_id = 'AKIAXHNKF4YFB6E7I7OI',
        aws_secret_access_key = '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',
    )
    
    cur = conn.cursor()
    print(f'shop id {shop_id}')
    sql_shops = """SELECT * FROM Shops WHERE shop_id ='%s' """
    cur.execute(sql_shops, shop_id)
    row_shop = cur.fetchone()

    if row_shop is not None:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Shop is already exist in our db',
        )
    
    # 로그인
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    # options.add_argument('headless')

    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver = webdriver.Chrome(service=Service(), options=options)

    driver.maximize_window()
    driver.get("https://sinsangmarket.kr/login")

    driver.find_element(By.XPATH,'//*[@id="app"]/div[1]/div/header/div/div[2]/div[3]').click()
    # id rayout2022
    # password elesther2022!
    driver.find_elements(By.CLASS_NAME,'text-input')[0].send_keys(id)
    driver.find_elements(By.CLASS_NAME,'text-input')[1].send_keys(password)
    driver.find_element(By.XPATH,'//*[@id="app"]/div[1]/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/button').click()
    time.sleep(1.0)

    # driver.get('https://sinsangmarket.kr/search')
    def scroll_down_end():
         SCROLL_PAUSE_SEC = 1
         driver.execute_script("window.scrollTo(0, 0)")

         last_height = driver.execute_script("return document.body.scrollHeight")         
     
         while True:
            # 끝까지 스크롤 다운
             driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") 
             time.sleep(SCROLL_PAUSE_SEC)

             driver.execute_script("window.scrollTo(0, document.body.scrollHeight-50);")  
             time.sleep(SCROLL_PAUSE_SEC)    

            # 스크롤 다운 후 스크롤 높이 다시 가져옴
             new_height = driver.execute_script("return document.body.scrollHeight")

             if new_height == last_height:
                break
                last_height = new_height

    driver.execute_script("window.scrollTo(0, 0)")
    driver.get(f'https://sinsangmarket.kr/store/{shop_id}')

    create_folder('./Shops')
    time.sleep(0.2)
    shop_src = driver.find_element(By.XPATH, f'//img[@alt="store-image"]').get_attribute('src')
    # urlretrieve(shop_src, f'../Shops/{shop_id}.jpg')
    print(shop_src)
    download_image(shop_src, './Shops/{shop_id}.jpg')
    
    
    shop_name = driver.find_element(By.XPATH, f'//*[@id="{shop_id}"]/div/div[1]/div/div/div[2]/div[1]/div[1]/span').text

    shop_address = driver.find_element(By.XPATH, f'//*[@id="{shop_id}"]/div/div[1]/div/div/div[2]/div[1]/div[2]/div[2]/div[2]').text
    shop_phone = ''
    try: 
        shop_phone = driver.find_element(By.XPATH, f'//*[@id="{shop_id}"]/div/div[1]/div/div/div[2]/div[1]/div[2]/div[1]/div[2]').text
    except Exception as e: 
        print(f'shop phone error {e}')

    time.sleep(2)
    
    shop_table = (
        shop_id,
        shop_name,
        shop_src,
        shop_phone,
        shop_address,
        'Approved',
        0,
        '' # main items
    )
    
    print(f'{shop_table}')
    sql_insert_shop = """INSERT INTO Shops (shop_id, shop_name, shop_image, sinsang_store_phone, address, status, transactions,  main_items)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

    try: 
        cur.execute(sql_insert_shop, shop_table)
        conn.commit()
        return HTTPException(
        status_code=status.HTTP_201_CREATED,
        detail=f'Shop with id {shop_id} is successfully saved'
        )
    except Exception as err: 
        print(f'Error {err}')
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'{err}'
        )

    conn.commit()
    cur.close()
    conn.close()
    
    time.sleep(500)
    def scroll_down_lock(whileSeconds):
        start = datetime.datetime.now()
        end = start + datetime.timedelta(seconds=whileSeconds)
        while True:
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            time.sleep(1)
            if datetime.datetime.now() > end:
                break
    
    
    
    
def create_folder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            
    except OSError:
        print("Error: Creating directory " + directory)
           
    
def download_image(url, path):
    try: 
        # image_response = requests.get(url, stream=True)
        # with open(path, 'wb') as out_file:
        #     shutil.copyfileobj(image_response.raw, out_file)
        # del image_response
        urlretrieve(url, path)
    except Exception as e: 
        print(f'something went wrong with saving shop image : {e}')
    # r = requests.get(url, stream=True)
    # if r.status_code == 200:
    #     with open(path, 'wb') as f:
    #         for chunk in r:
    #             f.write(chunk)

