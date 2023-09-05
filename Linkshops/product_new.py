import os 
import time 
import boto3
import re
import pymysql
import pandas as pd
from selenium.webdriver.support.select import Select
import datetime
import tqdm
from urllib.request import urlretrieve
from selenium import webdriver
from selenium.webdriver import ActionChains, Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, UnexpectedAlertPresentException
from flask_cors import CORS, cross_origin
from flask import Flask, request, jsonify, Response
from flask_restful import reqparse, abort, Api, Resource
import json
import numpy as np
from fastapi import APIRouter, status, HTTPException, BackgroundTasks
from lib import create_folder


router = APIRouter(tags=['Linkshop'])

@router.get('/new')
def product():
    # return {"message": "successfully sent!"}
    product()
    

def event_click(driver, element):
    return driver.execute_script('arguments[0].click();', element)


def event_move_to_element(driver, element):
    return ActionChains(driver).move_to_element(element).perform()



def fitting_info(x):
    for i in x.find_elements(By.TAG_NAME, 'td')[1:]:
        x_check = i.find_element(By.TAG_NAME, 'img').get_attribute('style').split('visibility:')[-1]
        if 'visible' in x_check:
            y = i.find_element(By.TAG_NAME, 'span').text
            break

    return y

def image_resize_url(url):
    url = url.split('/')
    url[5] = '480'
    url = '/'.join(url)
    
    return url



def product():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--mute-audio')
    chrome_options.add_argument('disable-gpu')
    chrome_options.add_argument('lang=ko')
    # chrome_options.add_argument('user-agent=User_Agent: Mozilla/5.0 \(Windows NT 10.0; Win64; x64\) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    
    conn = pymysql.connect(
        host=os.getenv('host'),
        port=3306,
        user=os.getenv('user'),
        passwd=os.getenv('passwd'),
        db=os.getenv('db'),
        charset='utf8mb4',
    )

      
    s3 = boto3.client(
        's3',
        aws_access_key_id = os.getenv('aws_access_key_id'),
        aws_secret_access_key = os.getenv('aws_secret_access_key'),
    )
    s3_domain = 'https://sokodress.s3.ap-northeast-2.amazonaws.com'

    folder_shops = 'linkshops_shops'
    folder_products_image = 'linkshop_product_images'
    create_folder(folder_products_image)
    create_folder(folder_shops)

    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    # driver.get('https://www.linkshops.com/')

    driver.get('https://www.linkshops.com/?signIn=')
    driver.implicitly_wait(10)
    time.sleep(2)
    
    
    ID = 'waldoyun2@gmail.com'
    pwd = 'Linkshops9138'
    driver.find_element(By.CLASS_NAME, 'input-wrapper').find_element(By.NAME, 'email').send_keys(ID)
    driver.find_element(By.CLASS_NAME, 'input-wrapper').find_element(By.NAME, 'password').send_keys(pwd)
    event_click(driver, driver.find_element(By.CLASS_NAME, 'login-modal-content-wrapper').find_element(By.ID, 'btn'))
    # driver.implicitly_wait(10)
    time.sleep(2)
    
    store_name = 'designbyjs'
    shop_link = f'https://www.linkshops.com/{store_name}'
    driver.get(shop_link)
    # driver.implicitly_wait(10)
    time.sleep(1)

    df_product = pd.DataFrame()

    select_shop = 'SELECT shop_id FROM Shops WHERE shop_name = %s'
    #
    shop_name = driver.find_element(By.CLASS_NAME, 'title-container-title').find_element(By.CLASS_NAME, 'name').text
    print(f'shop_name {shop_name}')
    
    try:
        cur = conn.cursor()
        cur.execute(select_shop, [store_name])
        shop_id = cur.fetchone()
        print(f'shop id {shop_id}')
        conn.commit()
        cur.close()
        conn.close()
    except:
        shop_id = None
  
    
   
    
    sangga_and_address = driver.find_element(By.CLASS_NAME, 'brandTitleContainer-location-content').text

    sangga_name = sangga_and_address.split(' ')[0]
    
    shop_address = ' '.join(sangga_and_address.split(' ')[1:])

    # brandTitleContainer-location-content
    try:
        shop_phone = driver.find_element(By.CLASS_NAME, 'brandTitleContainer-phone-content').text
    except NoSuchElementException:
        shop_phone = ''

          
    if shop_id is None:
        try:
            slq_interto_shop = 'INSERT INTO Shops (shop_name, address, sinsang_store_phone, shop_image,transactions, sanga_name, shop_link) VALUES (%s, %s, %s, %s, %s, %s, %s )'    
            cur = conn.cursor()
            shop_image = 'https://sokodress.s3.ap-northeast-2.amazonaws.com/ShopProfiles/shop_25232.png'

            cur.execute(slq_interto_shop, [store_name, shop_address, shop_phone, shop_image, 0, sangga_name, shop_link])
            conn.commit()
            shop_id = cur.lastrowid
            print(f'inserted shop id {shop_id}')
            cur.close()
            conn.close()
        except Exception as e:
            print(e)
    else:
        print('store already exists')   
        pass
    
    
    LAST_PAGE_CHECK = True
    while LAST_PAGE_CHECK:
        PAGE_NEXT = False
        
        page_len = len(driver.find_element(By.CLASS_NAME, 'page-line').find_elements(By.TAG_NAME, 'div'))
        for idx, i in enumerate(driver.find_element(By.CLASS_NAME, 'page-line').find_elements(By.TAG_NAME, 'div')):
            # time.sleep(2)
            if PAGE_NEXT:
                event_click(driver, i)
                event_move_to_element(driver, driver.find_element(By.CLASS_NAME, 'page-line'))
                break

            if page_len < 7 and idx + 1 == page_len:
                # print("끝")
                LAST_PAGE_CHECK = False
                break
            
            # print(i.get_attribute('class'))
            page_state = i.get_attribute('class')

            if page_state == 'page-item active':
                PAGE_NEXT = True
                
    last_page_num = driver.find_element(By.CLASS_NAME, 'page-item.active').text
    last_page_num = int(last_page_num)


    print(f'last page number {last_page_num}')
    
    event_click(driver, driver.find_element(By.CLASS_NAME, 'left-menu-item'))
    time.sleep(0.5)
    event_click(driver, driver.find_elements(By.CLASS_NAME, 'dropdown-menu')[0])
    time.sleep(1)
    
    for lp in range(last_page_num):
        print(f'current page number {lp}')
        try: 
            
            one_start_time = time.time()
        
        
        #    print('test lavel')

            try:
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '카테고리')]")))
                    
                if driver.find_element(By.XPATH, "//div[contains(text(), '카테고리')]").text:
                    product_category = driver.find_elements(By.CLASS_NAME, 'product-info-item')[4].text # '잡화,패션아이템,헤어핀/밴드/브로치,쥬얼리/시계'
                    product_category = product_category.replace('카테고리\n', '')
                    product_category = product_category.split(' > ')

                        # product_category = ','.join(product_category)
                    product_category_1, product_category_2, product_category_3 = category_classification(product_category)
                    print(product_category_1, product_category_2, product_category_3)
                    
            except:
                product_category_1 = None
                product_category_2 = None
                product_category_3 = None             
            try:
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '상품명')]")))
            
                if driver.find_element(By.XPATH, "//div[contains(text(), '상품명')]").text:
                    product_name = driver.find_elements(By.CLASS_NAME, 'product-info-item')[5].text
                    product_name = product_name.replace('상품명\n', '')
            except:
                product_name = None           
            try:
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '소재/혼용률')]")))
            
                if driver.find_element(By.XPATH, "//div[contains(text(), '소재/혼용률')]").text:
                    product_maxrate = driver.find_elements(By.CLASS_NAME, 'product-info-item')[6].text
                    product_maxrate = product_maxrate.replace('소재/혼용률\n', '').replace(', ', ',')
            except:
                product_maxrate = None

             


        except:
            pass
    
def category_classification(product_category):
    product_category_1 = product_category[0]

    if product_category[1] == '상의':
        product_category_2 = '탑'

        if product_category[2] == '티셔츠':
            product_category_3 = '티/탑'
        elif product_category[2] == '블라우스':
            product_category_3 = '블라우스'
        elif product_category[2] == '셔츠':
            product_category_3 = '셔츠/남방'
        elif product_category[2] == '니트':
            product_category_3 = '니트'
        else:
            product_category_2 = '기타'
            product_category_3 = None

    elif product_category[1] == '하의':
        product_category_2 = '하의'

        if product_category[2] == '스커트':
            product_category_3 = '스커트'
        elif product_category[2] == '면바지' or product_category[2] == '반바지':
            product_category_3 = '바지'
        elif product_category[2] == '슬랙스':
            product_category_3 = '슬렉스'
        elif product_category[2] == '점프수트':
            product_category_3 = '점프수트'
        elif product_category[2] == '레깅스':
            product_category_3 = '레깅스'
        elif product_category[2] == '니트류':
            product_category_3 = '니트류'
        else:
            product_category_2 = '기타'
            product_category_3 = None

    elif product_category[1] == '원피스/세트':
        product_category_2 = '드레스'

        if product_category[2] == '원피스':
            product_category_3 = '원피스'    
        elif product_category[2] == '세트':
            product_category_3 = '셋트'  
        else:
            product_category_2 = '기타'
            product_category_3 = None

    elif product_category[1] == '아우터':
        product_category_2 = '아우터'

        if product_category[2] == '재킷':
            product_category_3 = '자켓'
        elif product_category[2] == '가디건':
            product_category_3 = '가디건'
        elif product_category[2] == '코트':
            product_category_3 = '코트'
        elif product_category[2] == '조끼':
            product_category_3 = '조끼'    
        elif product_category[2] == '패딩/점퍼':
            product_category_3 = '패딩/점퍼'    
        else:
            product_category_2 = '기타'
            product_category_3 = None    
            
    elif product_category[1] == '잡화':
        if product_category[2] == '헤어핀/밴드/브로치':
            product_category_2 = '악세사리'
            product_category_3 = '여자 악세사리'

        elif product_category[2] == '가죽소품':
            product_category_2 = '기타'
            product_category_3 = None

        else:
            product_category_2 = '기타'
            product_category_3 = None

    else:
        product_category_2 = '기타'
        product_category_3 = None
        
    return product_category_1, product_category_2, product_category_3
