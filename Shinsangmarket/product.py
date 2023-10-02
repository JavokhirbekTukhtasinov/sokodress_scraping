import math
import os
import time
import datetime
import re
import pickle
import boto3
import pymysql
from glob import glob
import pandas as pd
from tqdm.notebook import tqdm
from urllib.request import urlretrieve
from selenium import webdriver
from selenium.webdriver import ActionChains, Chrome
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import json
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Union, List, Set, Any
from fastapi import HTTPException, status, BackgroundTasks
from lib import downloadImage, upload_image, create_folder, style_dict, category1_dict, category2_dict, fabric_dict, nation_dict, wash_dict, calculate_category_id, calculate_is_unit, check_duplicate_product, papago_translate, scrap_prodcut_only, check_duplicate_shop
import random
from dotenv import load_dotenv
load_dotenv()

class Accounts(BaseModel):
    id: Union[str, None] = 'bong2692'
    password: Union[str, None] = 'sinsang4811!'
    max_count: Union[int, None] = 50
    selected_categories: Union[List[int], None] = None


class RequestBody(BaseModel):
    store_id: Union[int, None] = 25232
    days_ago: Union[int, None] = 60
    # id: Union[str, None] = 'bong2692'
    # password: Union[str, None] = 'sinsang4811!'
    accounts: Union[List[Accounts], None] = None

    # url: Union[str, None] = 'https://sinsangmarket.kr/store/25232?sort=DATE&isPublic=true&cgIdx=1&ciIdx=1&cdIdx=0'


router = APIRouter(tags=['Sinsang'], responses={
                   404: {"description": "Not found"}})


options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.add_argument('--start-maximized')


@router.post('/product')
def predict_code(background_tasks: BackgroundTasks, body: RequestBody):
    create_folder('./Products')
    # change weekdays to 5 in order to defer scraping on weekends
    weekdays = 7

    if datetime.datetime.today().weekday() < weekdays:
        # production database
        conn = pymysql.connect(
        host=os.getenv('host'),
        port=int(str(os.getenv('port'))),
        user=os.getenv('user'),
        passwd=os.getenv('passwd'),
        db=os.getenv('db'),
        charset='utf8'
    )


        cur = conn.cursor()
        # sql_scraping = """INSERT INTO Scraping (shop_id) VALUES (%s) """
        # cur.execute(sql_scraping, (body.store_id))
        # Retrieve the last inserted row's ID
        # cur.execute("SELECT LAST_INSERT_ID()")
        # inference_id = cur.fetchone()[0]
        conn.commit()
        store_id = body.store_id
        days_ago = body.days_ago
        accounts = body.accounts
        
        def initiate_task(body):
            for account in accounts:
                if account.max_count == 0:
                    continue
                # model_predict(store_id, days_ago, account.id, account.password,
                #               account.max_count, inference_id,account.selected_categories)
                model_predict(store_id, days_ago, account.id, account.password,
                              account.max_count,account.selected_categories)
                # time.sleep(60 * 60)
                time.sleep(4)
                
        background_tasks.add_task(initiate_task, body)
        return {'inference_id'}
    else:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You can do scraping only on weekdays')


def model_predict(store_id, days_ago, id, password, MAX_COUNT,categories):
        
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('aws_access_key_id'),
        aws_secret_access_key=os.getenv('aws_secret_access_key')
    )

    # DB connect
    conn = pymysql.connect(
        host=os.getenv('host'),
        port=int(str(os.getenv('port'))),
        user=os.getenv('user'),
        passwd=os.getenv('passwd'),
        db=os.getenv('db'),
        charset='utf8'
    )


    cur = conn.cursor()
    sql_shops = "SELECT * FROM Shops"
    # cur.execute(sql_shops)
    # rows_shops = cur.fetchall()
    sql_shops = """SELECT * FROM Shops WHERE shop_id ='%s' """
    cur.execute(sql_shops, store_id)
    row_shop = cur.fetchone()

    if row_shop is None:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Shop with id {store_id} does not exist in our db',
        )

    # print(rows_shops)
    # return
    # print(type(store_id), type(days_ago))
    # for row_shop in rows_shops:
    #     if row_shop[14] == int(store_id): # sinsang_store_id
    #         shop_id = row_shop[0]
    #         print(shop_id)

    print(f'shop id --->>>> {store_id}')
    sql_products = "SELECT * FROM Products"
    cur.execute(sql_products)
    rows_products = cur.fetchall()
    # last_prod_create_at = rows_products[-1][9]  # last updated product time
    product_id = rows_products[-1][0] + \
        1 if len(list(rows_products)) > 0 else 1

    sql_categoryofproduct = "SELECT * FROM CategoryOfProduct"
    cur.execute(sql_categoryofproduct)
    rows_categoryofproduct = cur.fetchall()
    category_of_product_id = rows_categoryofproduct[-1][0] + 1 if len(
        list(rows_categoryofproduct)) > 0 else 1

    sql_fabricinfos = "SELECT * FROM FabricInfos"
    cur.execute(sql_fabricinfos)
    rows_fabricinfos = cur.fetchall()
    fabric_id = rows_fabricinfos[-1][0] + \
        1 if len(list(rows_fabricinfos)) > 0 else 1

    sql_productoptions = "SELECT * FROM ProductOptions"
    cur.execute(sql_productoptions)
    rows_productoptions = cur.fetchall()
    product_option_id = rows_productoptions[-1][0] + \
        1 if len(list(rows_productoptions)) > 0 else 1

    sql_washinfos = "SELECT * FROM WashInfos"
    cur.execute(sql_washinfos)
    rows_washinfos = cur.fetchall()
    wash_info_id = rows_washinfos[-1][0] + \
        1 if len(list(rows_washinfos)) > 0 else 1

    sql_productstyles = "SELECT * FROM ProductStyles"
    cur.execute(sql_productstyles)
    rows_productstyles = cur.fetchall()
    product_style_id = rows_productstyles[-1][0] + \
        1 if len(list(rows_productstyles)) > 0 else 1

    sql_styles = "SELECT * FROM Styles"
    cur.execute(sql_styles)
    rows_styles = cur.fetchall()
    style_id_dict = dict((y, x) for x, y in rows_styles)

    sql_productimages = "SELECT * FROM ProductImages"
    cur.execute(sql_productimages)
    rows_productimages = cur.fetchall()
    image_id = rows_productimages[-1][0] + \
        1 if len(list(rows_productimages)) > 0 else 1

    global driver
    driver = webdriver.Chrome(service=Service(), options=options)

    driver.get("https://sinsangmarket.kr/login")
    time.sleep(1)
    driver.save_screenshot('screenie.png')

    sql_shops = "SELECT * FROM Shops"
    cur.execute(sql_shops)
    rows_shops = cur.fetchall()
    
    
    # 로그인
    # 새로운 계정
    # ID = 'bong2692'
    # PASSWORD = 'sinsang4811!'
    # ID = 'rayout2022'
    # PASSWORD = 'elesther2022!'
    # driver.find_element(By.XPATH,'//*[@id="app"]/div[1]/div/header/div/div[2]/div[3]').click()
    driver.execute_script('arguments[0].click();', driver.find_element(
        By.XPATH, '//*[@id="app"]/div[1]/div/header/div/div[2]/div[3]'))
    driver.find_elements(By.CLASS_NAME, 'text-input')[0].send_keys(id)
    driver.find_elements(By.CLASS_NAME, 'text-input')[1].send_keys(password)
    # driver.find_element(By.CLASS_NAME, 'px-\[6px\].leading-none.mb-\[12px\].font-bold.contained').click()
    # driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'px-\[6px\].leading-none.mb-\[12px\].font-bold.contained'))
    login_button = driver.find_element(
        By.XPATH, '//*[@id="app"]/div/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/button')
    login_button.click()
    time.sleep(1)
    # 언어 선택(English)
    driver.execute_script('arguments[0].click();', driver.find_element(
        By.CLASS_NAME, 'select-area__arrow'))
    driver.execute_script('arguments[0].click();', driver.find_element(
        By.CLASS_NAME, 'flag-icon.flag-icon--en'))
    time.sleep(1)

    wait = WebDriverWait(driver, 5)
    actions = ActionChains(driver)

    # driver.get(f'https://sinsangmarket.kr/store/{store_id}')
    driver.get(f'https://sinsangmarket.kr/store/{store_id}')

    
    # check shop exist in database else create new one 
    
    time.sleep(2)
    shop_name = driver.find_element(By.XPATH , f'//*[@id="{store_id}"]/div/div[1]/div/div/div[2]/div[1]/div[1]/span').text.strip()
    try:
        shop_address = driver.find_element(By.XPATH , f'//*[@id="{store_id}"]/div/div[1]/div/div/div[2]/div[1]/div[2]/div[2]/div[2]').text.strip()
    except Exception as e:
        print(f'address error {e}')
        shop_address = ''
        pass
        
    try:
        shop_phone  = driver.find_element(By.XPATH , f'//*[@id="{store_id}"]/div/div[1]/div/div/div[2]/div[1]/div[2]/div[1]/div[2]').text.strip()
    except Exception as e:
        print(f'phone error {e}')
        shop_phone = ''
        pass
        
    shop_link = f'https://sinsangmarket.kr/store/{store_id}'
        
    if check_duplicate_shop(shop_name, rows_shops) is None:
        try:
            shop_create_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            slq_interto_shop = """INSERT INTO Shops (shop_name, address, sinsang_store_phone, shop_image,transactions,  shop_link, main_items, create_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                # cursor = conn.cursor()
            shop_image = '${s3_image_url}/ShopProfiles/shop_25232.png'
            shop_insert_data = (shop_name, shop_address, shop_phone, shop_image,
                                    0,  shop_link, '주력 아이템', shop_create_at)
            print(shop_insert_data)
            cur.execute(slq_interto_shop, shop_insert_data)

            shop_id = cur.lastrowid

            print(f'inserted shop id {shop_id}')

        except Exception as e:
                print(f'shop inserting error {e}')
    else:
            print('store already exists')
            shop_id = check_duplicate_shop(shop_name, rows_shops)
            pass

            print(f'shop id {shop_id}')
    
    
    
    
    
    
    
    
    
    
    
    # delay time till 3 seconds
    # time.sleep(3)
    time.sleep(1.5)
    # MAX_COUNT = 2
    now = datetime.datetime.now()
    standard_date_ago = now - datetime.timedelta(days=days_ago)

    # category_list = [1, 2, 11]  # 여성 의류, 남성 의류, 유아 의류

    scraped_item = 0
    stop_looping = False
    
    print(f'stop looping outside {stop_looping}')
    for c in categories:
        if c == 0:
            continue
        print(f'stop looping inside {stop_looping}')
        if stop_looping:
            break
        print(f'item count -->> {scraped_item}')
        if c == 15:
            continue
        time.sleep(1.5)
        # //*[@id="25232"]/div/div[2]/div[2]/div/aside/div[3]/ul/li[2]/div/button/div/span
        driver.execute_script('arguments[0].click();', driver.find_element(
            By.XPATH, f'//*[@id="{store_id}"]/div/div[2]/div[2]/div/aside/div[3]/ul/li[{c}]/div/button/div/span'))

        time.sleep(1)

        # select category list
        category_parent = driver.find_element(
            By.XPATH, f'//*[@id="{store_id}"]/div/div[2]/div[2]/div/aside/div[3]/ul/li[{c}]/ul')
        clothes_list = category_parent.find_elements(By.TAG_NAME, 'div')
        for clo in range(1, len(clothes_list), 1):
            print(f'category 2 id {clo}')
            if stop_looping:
                break
            if clo == 1 or clo == 15:
                continue
            if c == 11:
                if clo >= 11 and clo <= 16 or clo == 18 or clo == 19:
                    continue
            if c == 2:
                if clo == 1:
                    continue
                elif clo == 10:
                    break

            try:
                clothes = driver.find_element(
                    By.XPATH, f'//*[@id="{store_id}"]/div/div[2]/div[2]/div/aside/div[3]/ul/li[{c}]/ul/div[{clo}]/button/div/span')
            except Exception as e:
                print(e)
                break
            # goods_clothes = driver.find_element(
            #     By.XPATH, f'//*[@id="{store_id}"]/div/div[2]/div[2]/div/aside/div[3]/ul/li[{c}]/ul/div[{clo}]/button/div/span').text

            time.sleep(2)
            driver.execute_script('arguments[0].click();', clothes)

            # 스타일
            try:
                driver.execute_script('arguments[0].click();', driver.find_element(
                    By.XPATH, f'//*[@id="{store_id}"]/div/div[2]/div[2]/div/aside/div[4]/button/div'))
                time.sleep(2)
            except Exception as e:
                print(f'error {e}')
                pass

            try:
                style_list = driver.find_element(
                    By.XPATH, f'//*[@id="{store_id}"]/div/div[2]/div[2]/div/aside/div[4]/ul').find_elements(By.TAG_NAME, 'li')
            except Exception as e:
                print(f'error {e}')
                continue
            
            print(f'style list {len(style_list)}')
            
            for sty in range(1, len(style_list)):
                print(f'style id =>>> {sty}')
                if stop_looping:
                    break
                if sty == 1 or sty == 0:
                    continue

                style_element = driver.find_element(
                    By.XPATH, f'//*[@id="{store_id}"]/div/div[2]/div[2]/div/aside/div[4]/ul/li[{sty}]/div/button/div/span')

                style = style_element.text

                # style
                style = style_dict[list(
                    style_dict.keys())[-1]] if style is None or style == '' else style_dict[style]
                # style_id
                style_id = style_id_dict[style]

                driver.execute_script('arguments[0].click();', style_element)

                # for _ in range(2):
                #     driver.execute_script(
                #         "window.scrollTo(0, document.body.scrollHeight);")
                total_product_count = 0
                time.sleep(1)
                
                try:
                    total_product_count = driver.find_element(
                        By.XPATH, f'//*[@id="{store_id}"]/div/div[2]/div[2]/div/aside/div[1]/p/span').text.strip()
                    print("Element exists:", total_product_count)
                    
                except NoSuchElementException:
                    total_product_count = 0
                    print("Element does not exist")
                    continue

                time.sleep(1)

                if total_product_count.isdigit():
                    total_product_count = int(total_product_count)
                else:
                    print(f'total product error=>>> {total_product_count}')
                    total_product_count = 0
                    continue

                if total_product_count == 0 or total_product_count is None:
                    continue
                
                # if len(goods_list) == 0:
                #     continue

                time.sleep(1)

                print(f'scraped_item count ==> {scraped_item}')

                try:
                    scrap_prodcut_only(driver, total_product_count, rows_products, standard_date_ago, wait, s3, store_id,
                                       style, c, style_id, cur, conn, MAX_COUNT,  scraped_item, image_id, product_id, days_ago, shop_id)
                except Exception as e:
                    print(f'error product scraping {e}')
                    continue

    log_message = {'Message': 'Success inserted to db(goods)'}
    return log_message


# @router.get('/')
# def test():
#     downloadImage(f'https://image-v4.sinsang.market/?f=https://image-cache.sinsang.market/images/25232/92046071/167922118000577415_547936075.png&w=375&h=500', './Products/test3.png')
#     # try:

#     # url = 'https://image-v4.sinsang.market/?f=https://image-cache.sinsang.market/images/25232/92085305/167655035100655297_1462791657.jpg&w=1500&h=2000'
#     # # url = 'https://www.searchenginejournal.com/wp-content/uploads/2022/06/image-search-1600-x-840-px-62c6dc4ff1eee-sej-1280x720.png'

#     # headers = {
#     #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'  # A common user agent
#     #         }

#     # response = requests.get(url=url, headers=headers)
#     # if response.status_code == 200:
#     #     with open('./Products/test2.png', 'wb') as f:
#     #         f.write(response.content)
#     #     print("Image downloaded successfully.")
#     # else:
#     #     print("Failed to download image. Status code:", response.status_code)

#     #     # urlretrieve(url, './Products/test.png')
#     #     # image_response = requests.get(url, stream=True)
#     #     # with open('./Products/test.jpg', 'wb') as out_file:
#     #     #     shutil.copyfileobj(image_response.raw, out_file)
#     #     # del image_response
#     #     # print(image_response.status_code)
#     #     # if image_response.status_code == 200:
#     #     #     with  open('./Products/test2.jpg', 'wb') as out_file:
#     #     #         out_file.write(image_response.content)
#     #     #     return HTTPException(
#     #     #      status_code=status.HTTP_200_OK
#     #     #     )

#     # except Exception as err:
#     #     print(f'Error {err}')
#     #     return HTTPException(
#     #     status_code=status.HTTP_400_BAD_REQUEST,
#     #     detail=f'{err}')


@router.get('/progress/{reference_id}')
def progress(reference_id: int):
    try:

        conn = pymysql.connect(
            host='moyvle.cz561frejrez.us-west-1.rds.amazonaws.com',
            port=3306,
            user='user',
            passwd='seodh1234',
            db='sokodress',
            charset='utf8'
        )
        cur = conn.cursor()

        sql_progress = 'SELECT scraped_product_count FROM Scraping WHERE scraping_id = %s'
        cur.execute(sql_progress, (reference_id))
        product_count = cur.fetchone()

        return {'product_count': product_count}
    except Exception as err:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'{err}')
    finally:
        cur.close()
        conn.close()

@router.get('/products/all')
def get_products():
    print(f'test')
    try:
        conn = pymysql.connect(
            host='moyvle.cz561frejrez.us-west-1.rds.amazonaws.com',
            port=3306,
            user='user',
            passwd='seodh1234',
            db='sokodress',
            charset='utf8'
        )
        cur = conn.cursor()
        sql = 'SELECT * FROM Products'
        cur.execute(sql)
        products = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return products
    except Exception as err:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'{err}')
    finally:
        cur.close()
        conn.close()
