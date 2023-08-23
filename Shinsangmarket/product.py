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
from lib import downloadImage, upload_image, create_folder, style_dict, category1_dict, category2_dict, fabric_dict, nation_dict, wash_dict, calculate_category_id, calculate_is_unit, check_duplicate_product, papago_translate
import random


class Accounts(BaseModel):
    id: Union[str, None] = 'bong2692'
    password: Union[str, None] = 'sinsang4811!'
    max_count: Union[int, None] = 50
    selected_categories: Union[List[int], None] = None

class RequestBody(BaseModel):
    store_id: Union[int, None] = 25232
    days_ago: Union[int, None] = 3
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
    
    weekdays = 5


    if datetime.datetime.today().weekday() < weekdays:
             # production database
        conn = pymysql.connect(
                host='moyvle.cz561frejrez.us-west-1.rds.amazonaws.com',
                port=3306,
                user='user',
                passwd='seodh1234',
                db='sokodress',
                charset='utf8'
                )

        cur = conn.cursor()
        sql_scraping = """INSERT INTO Scraping (shop_id) VALUES (%s) """
        cur.execute(sql_scraping, (body.store_id))
        # Retrieve the last inserted row's ID
        cur.execute("SELECT LAST_INSERT_ID()")
        inference_id =  cur.fetchone()[0]
        conn.commit()
        store_id = body.store_id
        days_ago = body.days_ago
        accounts = body.accounts
        print(f'max count {body.accounts}')
        def initiate_task(body):
            for account in accounts:
                if account.max_count == 0:
                    continue
                model_predict(store_id, days_ago, account.id, account.password, account.max_count, inference_id, account.selected_categories)
                 # time.sleep(60 * 60)
                time.sleep(4)     
        background_tasks.add_task(initiate_task, body)
        return {'inference_id': inference_id}          
    else:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You can do scraping only on weekdays')


def model_predict(store_id, days_ago, id, password, MAX_COUNT, inference_id, categories):

    # driver  = webdriver.Chrome(options=options)
    s3 = boto3.client(
        's3',
        aws_access_key_id='AKIAXHNKF4YFB6E7I7OI',
        aws_secret_access_key='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',
    )

#    prev database
    # conn = pymysql.connect(
    #     host='52.79.173.93',
    #     port=3306,
    #     user='user',
    #     passwd='seodh1234',
    #     db='sokodress',
    #     charset='utf8'
    # )


# production database
    conn = pymysql.connect(
            host='moyvle.cz561frejrez.us-west-1.rds.amazonaws.com',
            port=3306,
            user='user',
            passwd='seodh1234',
            db='sokodress',
            charset='utf8'
            )

    cur = conn.cursor()
    sql_shops = "SELECT * FROM Shops"
    # cur.execute(sql_shops)
    # rows_shops = cur.fetchall()
    sql_shops = """SELECT * FROM Shops WHERE shop_id ='%s' """
    cur.execute(sql_shops, store_id)
    row_shop = cur.fetchone()
    print(row_shop)
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
    print(rows_products)
    product_id = rows_products[-1][0] + 1 if len(list(rows_products)) > 0 else 1

    sql_categoryofproduct = "SELECT * FROM CategoryOfProduct"
    cur.execute(sql_categoryofproduct)
    rows_categoryofproduct = cur.fetchall()
    category_of_product_id = rows_categoryofproduct[-1][0] + 1 if len(list(rows_categoryofproduct)) > 0 else 1

    sql_fabricinfos = "SELECT * FROM FabricInfos"
    cur.execute(sql_fabricinfos)
    rows_fabricinfos = cur.fetchall()
    fabric_id = rows_fabricinfos[-1][0] + 1 if len(list(rows_fabricinfos)) > 0 else 1

    sql_productoptions = "SELECT * FROM ProductOptions"
    cur.execute(sql_productoptions)
    rows_productoptions = cur.fetchall()
    product_option_id = rows_productoptions[-1][0] + 1 if len(list(rows_productoptions)) > 0 else 1

    sql_washinfos = "SELECT * FROM WashInfos"
    cur.execute(sql_washinfos)
    rows_washinfos = cur.fetchall()
    wash_info_id = rows_washinfos[-1][0] + 1 if len(list(rows_washinfos)) > 0 else 1

    sql_productstyles = "SELECT * FROM ProductStyles"
    cur.execute(sql_productstyles)
    rows_productstyles = cur.fetchall()
    product_style_id = rows_productstyles[-1][0] + 1 if len(list(rows_productstyles)) > 0 else 1

    sql_styles = "SELECT * FROM Styles"
    cur.execute(sql_styles)
    rows_styles = cur.fetchall()
    style_id_dict = dict((y, x) for x, y in rows_styles)

    sql_productimages = "SELECT * FROM ProductImages"
    cur.execute(sql_productimages)
    rows_productimages = cur.fetchall()
    image_id = rows_productimages[-1][0] + 1 if len(list(rows_productimages)) > 0 else 1

    global driver
    driver = webdriver.Chrome(service=Service(), options=options)

    driver.get("https://sinsangmarket.kr/login")
    time.sleep(1)
    driver.save_screenshot('screenie.png')

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

    # delay time till 3 seconds
    # time.sleep(3)
    time.sleep(1.5)
    # MAX_COUNT = 2
    now = datetime.datetime.now()
    standard_date_ago = now - datetime.timedelta(days=days_ago)

    total_table_Products = []
    total_table_CategoryOfProduct = []
    total_table_FabricInfos = []
    total_table_ProductOptions = []
    total_table_WashInfos = []
    total_table_ProductStyles = []
    total_table_ProductImages = []


    # category_list = [1, 2, 11]  # 여성 의류, 남성 의류, 유아 의류
    start_time = time.time()
    max_runtime = 3
    scraped_item = 0
    stop_looping = False
    print(f'stop looping outside {stop_looping}')
    for c in categories:

        print(f'stop looping inside {stop_looping}')
        if stop_looping:
            break
        print(f'item count -->> {scraped_item}')
        if c == 15: 
            continue
        time.sleep(1.5)
        
        driver.execute_script('arguments[0].click();', driver.find_element(By.XPATH, f'//*[@id="{store_id}"]/div/div[2]/div[2]/div/aside/div[3]/ul/li[{c}]/div/button'))

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
                if sty == 1:
                    continue
                # if sty == len(style_list):
                #     continue
                # //*[@id="25232"]/div/div[2]/div[2]/div/aside/div[4]/ul/li[2]/div/button/div/span
                style_element = driver.find_element(
                    By.XPATH, f'//*[@id="{store_id}"]/div/div[2]/div[2]/div/aside/div[4]/ul/li[{sty}]/div/button/div/span')
                # style_element = driver.find_element(By.CLASS_NAME, 'style__filter-list').find_elements(By.TAG_NAME, 'button')[sty]
                style = style_element.text

                # style
                style = style_dict[list(style_dict.keys())[-1]] if style is None or style == '' else style_dict[style]
                # style_id
                style_id = style_id_dict[style]

                driver.execute_script('arguments[0].click();', style_element)
                time.sleep(0.5)
                for _ in range(2):
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(0.1)
                total_product_count = 0
                
                try:
                    total_product_count = driver.find_element(By.XPATH, f'//*[@id="{store_id}"]/div/div[2]/div[2]/div/aside/div[1]/p/span').text.strip()
                    print("Element exists:", total_product_count)
                    
                except NoSuchElementException:
                    total_product_count = 0
                    print("Element does not exist")
                    continue
                
                goods_list = driver.find_elements(By.XPATH, '//div[@data-group="goods-list"]')
                # print(f'goods list ->>> {goods_list}')
                driver.execute_script("window.scrollTo(0, 1000)")
                time.sleep(2)
                print(f'total product out {total_product_count}')
                if int(total_product_count) == 0:
                    continue

                # if len(goods_list) == 0:
                #     continue

                #TODO
                # total_product_count = driver.find_element(By.XPATH, f'//*[@id="{store_id}"]/div/div[2]/div[2]/div/aside/div[1]/p/span').text
                # for goo in range(1 , len(goods_list)):
                time.sleep(1)
                # print(f'total product count {total_product_count}')

                print(f'scraped_item count ==> {scraped_item}')
                # if int(total_product_count) == 0:
                #     continue
                
                previous_height = driver.execute_script('return document.body.scrollHeight')

                for goo in range(0, int(total_product_count)):
                    
                    # driver.execute_script('window.s   crollTo(0, document.body.scrollHeight)')
                    print(f'in progress item {goo}')
                    time.sleep(2)
                    new_height = driver.execute_script('return document.body.scrollHeight')
                        
                                        
                    driver.execute_script("window.scrollTo(0, 1000)")
                    driver.execute_script('arguments[0].click();', driver.find_elements(
                        By.XPATH, '//div[@data-group="goods-list"]')[goo])
                    time.sleep(0.5)
                    
                    try:
                        #goods-detail > div > div.content__section > div.goods-detail-right > div:nth-child(1) > p
                        prod_name = driver.find_element(By.CSS_SELECTOR, '#goods-detail > div > div.content__section > div.goods-detail-right > div:nth-child(1) > p').text
                        print(f'inner prod name ->>> {prod_name}')
                        prod_name_en = papago_translate(prod_name)
                        time.sleep(2)
                    except Exception as e:
                        prod_name_en = ''
                        print(f'error {e}')
                        continue
                        # prod_name = ''
                    print(f'product number {scraped_item}')
                    print(f'is prod exist {check_duplicate_product(prod_name, rows_products)}')
                    if check_duplicate_product(prod_name, rows_products) is True:
                        time.sleep(1.2)
                        driver.execute_script('arguments[0].click();', driver.find_element(
                            By.CLASS_NAME, 'close-button'))
                        continue
                    else:
                        pass
                    # create_at
                    try:
                        element = wait.until(EC.presence_of_element_located(
                            (By.XPATH, "//div[contains(text(), 'Updated at')]/following-sibling::div")))
                        create_at = driver.find_element(
                            By.XPATH, "//div[contains(text(), 'Updated at')]/following-sibling::div").text
                        print(f'create at ->>> {create_at}')
                    except Exception as e:
                        create_at = ''
                        # print("[LOG] 등록일 X!")
                    print(f'standard date ago --->>>>{standard_date_ago}')



                        #TODO  scrapp all products 
                        
                    # # 날짜가 days_ago보다 더 크면 break
                    # if 'Boosted' in create_at:
                    #     if 'hours' in create_at or 'minutes' in create_at:
                    #         pass
                    #     elif 'year' in create_at:
                    #         driver.execute_script('arguments[0].click();', driver.find_element(
                    #             By.CLASS_NAME, 'close-button'))
                    #         break
                    #     elif 'days' in create_at:
                    #         if int(re.sub(r'[^0-9]', '', create_at.split('\n')[1])) < days_ago:
                    #             pass
                    #         else:
                    #             driver.execute_script('arguments[0].click();', driver.find_element(
                    #                 By.CLASS_NAME, 'close-button'))
                    #             break
                    #     else:
                    #         print(f"[LOG] 등록일: {create_at}")

                    # elif datetime.datetime.strptime(create_at.split(' ')[0], '%Y.%m.%d') < standard_date_ago:
                    #     # driver.find_element(By.CLASS_NAME, 'close-button').click()
                    #     driver.execute_script('arguments[0].click();', driver.find_element(
                    #         By.CLASS_NAME, 'close-button'))
                    #     continue

                    # else:
                    #     pass

                    # 위의 날짜 계산이 끝나면 입력할 create_at로 변환
                    if create_at != '':
                        create_at = create_at.split(' ')[0].replace('.', '-')

                    # prod_link
                    try:
                        prod_id = driver.find_elements(
                            By.XPATH, '//div[@data-group="goods-list"]')[goo].get_attribute('data-gid')
                        prod_link = f'https://sinsangmarket.kr/goods/{prod_id}'
                        # print(f'prod link ->>> {prod_link}')
                    except Exception as e:
                        prod_link = ''

                    # prod_name

                    # real_price, price, team_price
                    try:
                        # goods_price = driver.find_element(By.XPATH, '//*[@id="goods-detail"]').find_element(By.CSS_SELECTOR, 'div.price.flex.items-center').text
                        goods_price = driver.find_element(
                            By.CLASS_NAME, 'price.flex.items-center').find_element(By.CLASS_NAME, 'ml-\[2px\]').text
                        goods_price = re.sub(r'[^0-9]', '', goods_price)
                        real_price = price = team_price = goods_price
                        # print(
                        #     f'goods price : {goods_price} real price : {real_price}')
                    except Exception as e:
                        goods_price = ''

                    # star
                    try:
                        star = driver.find_element(By.XPATH, '//*[@id="goods-detail"]').find_element(
                            By.CSS_SELECTOR, 'p.zzim-button__count').text
                        # print(f'start ->>> {star}')
                    except Exception as e:
                        star = '0'

                    # is_sold_out
                    try:
                        add_to_cart_button = driver.find_element(By.CLASS_NAME, 'flex-grow').find_element(By.CLASS_NAME, 'ssm-button').\
                            find_element(
                                By.TAG_NAME, 'button').get_attribute('class')
                        # print(f'add to cart button ->>> {add_to_cart_button}')
                        if 'disabled' in add_to_cart_button:
                            is_sold_out = '1'
                        else:
                            is_sold_out = '0'
                    except Exception as e:
                        is_sonld_out = '0'

                    # ProductImages
                    images_list = driver.find_elements(
                        By.XPATH, '//img[@alt="thumbnail-image"]')
                    # images_list = driver.find_element(By.XPATH, f'//*[@id="goods-detail"]/div/div[2]/div[1]/div[1]/div/div[1]/div[3]/div')
                    # //*[@id="goods-detail"]/div/div[2]/div[1]/div[1]/div/div[1]/div[3]/div/div
                    try:
                        for i in range(1,len(images_list), 1):
                            time.sleep(2)
                            print(f'image loop ->> {i}')

                            # goods_src = driver.find_elements(
                            #     By.XPATH, '//img[@alt="thumbnail-image"]')[i].get_attribute('src')
                            # print(f'goods src {goods_src}')
                            
                            driver.execute_script('arguments[0].click();', driver.find_element(By.XPATH, f'//*[@id="goods-detail"]/div/div[2]/div[1]/div[1]/div/div[1]/div[3]/div/div[{i}]/div'))
                            time.sleep(1)
                            goods_src = driver.find_element(By.XPATH, f'//*[@id="goods-detail"]/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div[1]/div/div[{i}]/div/img').get_attribute('src')
                            print(f'image src =>>> {goods_src}')
                            image_path = f'./Products/{product_id}_{i}.jpg'
                            downloadImage(goods_src, image_path)

                            image_url = upload_image(s3,product_id,i)
                            
                            table_ProductImages = (
                                # str(image_id),  # autoincrement
                                str(product_id),
                                # image_name(not null),
                                f'{str(product_id)}_{str(i)}',
                                image_url
                            )
                            print(f'table images ->>> {table_ProductImages}')
                            total_table_ProductImages.append(
                                table_ProductImages)
                            os.remove(image_path)
                            image_id += 1
                    except Exception as e:
                        print("[LOG] S3 Upload Error {e}")

                    # category1
                    try:
                        category1 = driver.find_elements(
                            By.XPATH, "//div[contains(text(), 'Categories')]/following-sibling::div/div")[0].text

                        # print(f'category 1 ->>> {category1}')

                    except Exception as e:
                        category1 = ''

                    # category2
                    try:
                        category2 = driver.find_elements(
                            By.XPATH, "//div[contains(text(), 'Categories')]/following-sibling::div/div")[1].text
                        # print(f'category 2 ->>> {category2}')

                    except Exception as e:
                        category2 = ''

                    # color
                    try:
                        color = driver.find_element(
                            By.XPATH, "//div[contains(text(), 'Colors')]/following-sibling::div").text
                        # print(f'color ->>> {color}')

                    except Exception as e:
                        color = ''

                    # size
                    try:
                        size = driver.find_element(
                            By.XPATH, "//div[contains(text(), 'Size')]/following-sibling::div").text

                        print(f"size ==> {size}")
                    except Exception as e:
                        size = ''

                    # maxrate
                    try:
                        maxrate = driver.find_element(
                            By.XPATH, "//div[contains(text(), 'Proposition')]/following-sibling::div").text
                        # print(f'maxrate ->>> {maxrate}')

                    except Exception as e:
                        maxrate = ''

                    # nation
                    try:
                        nation = driver.find_element(
                            By.XPATH, "//div[contains(text(), 'Origin')]/following-sibling::div").text
                        nation = nation_dict[nation]
                        # print(f'nation ->>> {nation}')
                    except Exception as e:
                        nation = ''

                    # is_unit
                    try:
                        contents_text = driver.find_element(
                            By.CLASS_NAME, 'mb-\[80px\]').find_element(By.CLASS_NAME, 'row__content').text
                        print(f'contents text ->>> {contents_text}')
                        if contents_text == 'No details.':
                            is_unit = 'T'
                        else:
                            is_unit = calculate_is_unit(contents_text)
                    except Exception as e:
                        is_unit = 'T'

                    # goods_laundry
                    try:
                        laundry_elements = driver.find_elements(
                            By.CSS_SELECTOR, 'div.laundry-item__name')
                        # print(f'laundry elements ->>> {laundry_elements}')
                        for i in laundry_elements:
                            goods_laundry = i.text
                            goods_laundry = wash_dict[goods_laundry]

                            table_WashInfos = (
                                # str(wash_info_id),  # autoincrement
                                str(product_id),
                                goods_laundry  # category 라고 써져 있는데 세탁 정보
                            )

                            total_table_WashInfos.append(table_WashInfos)
                            # wash_info_id += 1
                    except Exception as e:
                        goods_laundry = ''

                    # goods_fabric_thickness
                    try:
                        goods_fabric_thickness = [x for x in driver.find_elements(
                            By.XPATH, "//div[contains(text(), 'Thickness')]/following-sibling::div/div/div") if x.get_attribute('class') == 'min-w-[42px] text-gray-100'][0].text
                        goods_fabric_thickness = fabric_dict[goods_fabric_thickness]
                    except Exception as e:
                        goods_fabric_thickness = ''

                    # goods_fabric_seethrough
                    try:
                        goods_fabric_seethrough = [x for x in driver.find_elements(
                            By.XPATH, "//div[contains(text(), 'Transparency')]/following-sibling::div/div/div") if x.get_attribute('class') == 'min-w-[42px] text-gray-100'][0].text
                        goods_fabric_seethrough = fabric_dict[goods_fabric_seethrough]
                    except Exception as e:
                        goods_fabric_seethrough = ''

                    # goods_fabric_elasticity
                    try:
                        goods_fabric_elasticity = [x for x in driver.find_elements(
                            By.XPATH, "//div[contains(text(), 'Elasticity')]/following-sibling::div/div/div") if x.get_attribute('class') == 'min-w-[42px] text-gray-100'][0].text
                        goods_fabric_elasticity = fabric_dict[goods_fabric_elasticity]
                    except Exception as e:
                        goods_fabric_elasticity = ''

                    # goods_fabric_lining
                    try:
                        goods_fabric_lining = [x for x in driver.find_elements(
                            By.XPATH, "//div[contains(text(), 'Lining')]/following-sibling::div/div/div") if x.get_attribute('class') == 'min-w-[42px] text-gray-100'][0].text
                        print(
                            f'goods fabric_linking ->>> {goods_fabric_lining}')
                        goods_fabric_lining = fabric_dict[goods_fabric_lining]
                    except Exception as e:
                        goods_fabric_lining = ''

                    # category_id
                    category_id = calculate_category_id(
                        prod_name, category1, category2)
                    # print(f'category id  --->>>> {category_id}')
                    category1 = category1_dict[category1]
                    print(f'category 1 -->>> {category1}')
                    for key, value in category2_dict.items():
                        if c == 10 and category2 == 'Suit':
                            category2 = '정장세트'
                        elif key == category2:
                            category2 = value
                    # print(f'category 2 ->>> {category2}')
                    table_Products = (
                        str(product_id),  # autoincrement
                        str(store_id),  # 일단 임의로
                        prod_name,
                        prod_name_en,
                        real_price,
                        price,
                        team_price,
                        nation,
                        is_unit,
                        None,  # contents,
                        create_at,
                        maxrate,
                        is_sold_out,
                        style,
                        category1,
                        prod_link,
                        category2,
                        star
                    )

                    print(f'category products ->>> {table_Products}')

                    table_CategoryOfProduct = (
                        # str(category_of_product_id), # autoincrement
                        category_id,
                        str(product_id)
                    )

                    table_FabricInfos = (
                        # str(fabric_id),  # autoincrement
                        str(product_id),
                        '기본핏',  # 핏정보(not null)
                        goods_fabric_thickness,  # 두께감
                        goods_fabric_elasticity,  # 신축성
                        goods_fabric_seethrough,  # 비침
                        goods_fabric_lining,  # 안감
                        '없음',  # 광택('없음'으로)
                        '보통',  # 촉감('보통'으로)
                        '없음'  # 밴딩('없음'으로)
                    )

                    table_ProductOptions = (
                        # str(product_option_id),  # autoincrement
                        str(product_id),
                        size,  # size
                        color  # color
                    )

                    table_ProductStyles = (
                        # str(product_style_id),  # autoincrement
                        str(product_id),
                        str(style_id)
                    )

                    total_table_Products.append(table_Products)
                    total_table_CategoryOfProduct.append(
                        table_CategoryOfProduct)
                    total_table_FabricInfos.append(table_FabricInfos)
                    total_table_ProductOptions.append(table_ProductOptions)
                    total_table_ProductStyles.append(table_ProductStyles)

                    element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'close-button')))
                    # driver.find_element(By.CLASS_NAME, 'close-button').click()
                    driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'close-button'))
                    # save single row
                    try:
                        
                        sql_products = """INSERT IGNORE INTO Products (product_id, shop_id, prod_name,prod_name_en, real_price, price, team_price, nation, is_unit,
                                                    contents, create_at, maxrate, is_sold_out, style, category1, prod_link, category2, star)
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                        cur.execute(sql_products, table_Products)
                        conn.commit()

                        sql_categoryofproducts = """INSERT INTO CategoryOfProduct (category_id, product_id)
                                                                        VALUES (%s, %s)"""
                        # cur.executemany(sql_categoryofproducts, total_table_CategoryOfProduct)
                        cur.execute(sql_categoryofproducts, table_CategoryOfProduct)
                        conn.commit()

                        sql_fabricinfos = """INSERT INTO FabricInfos (product_id, 핏정보, 두께감, 신축성, 비침, 안감, 광택, 촉감, 밴딩)
                                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                        # cur.executemany(sql_fabricinfos, total_table_FabricInfos)
                        cur.execute(sql_fabricinfos, table_FabricInfos)
                        conn.commit()

                        sql_productoptions = """INSERT INTO ProductOptions (product_id, size, color)
                                                                    VALUES ( %s, %s, %s)"""
                        # cur.executemany(sql_productoptions, total_table_ProductOptions)
                        print(f'table product options :::: {table_ProductOptions}') 
                        cur.execute(sql_productoptions, table_ProductOptions)
                        conn.commit()

                        sql_washinfos = """INSERT INTO WashInfos (product_id, category)
                                                        VALUES ( %s, %s)"""
                        cur.executemany(sql_washinfos, total_table_WashInfos)
                        conn.commit()

                        sql_productstyles = """INSERT INTO ProductStyles (product_id, style_id)
                                                                VALUES (%s, %s)"""

                        # cur.executemany(sql_productstyles, total_table_ProductStyles)
                        cur.execute(sql_productstyles, table_ProductStyles)
                        conn.commit()

                        sql_productimages = """INSERT INTO ProductImages (product_id, image_name, image_url)
                                                                VALUES ( %s, %s, %s)"""
                        cur.executemany(sql_productimages, total_table_ProductImages)
                        conn.commit()
                        product_id += 1
                        category_of_product_id += 1
                        fabric_id += 1
                        product_option_id += 1
                        product_style_id += 1
                        scraped_item += 1
                    except Exception as e:
                        print(e)                        
                    
                    print(f'product count {scraped_item}')
                    
                    if scraped_item >= MAX_COUNT:
                        stop_looping = True
                        time.sleep(1)
                        sql_scraping_update = 'UPDATE Scraping SET scraped_product_count = %s WHERE scraping_id = %s'
                        cur.execute(sql_scraping_update, (scraped_item, inference_id))
                        conn.commit()
                    
                        try:
                            driver.execute_script('arguments[0].click();', driver.find_element(
                                By.CLASS_NAME, 'close-button'))
                        except Exception as e:
                            print(e)
                        break
                    # continue

                
            # print("========")

    # print(f'product: {table_Products}')
    # print(f'images: {table_ProductImages}')z
    # print(f'category: {table_CategoryOfProduct}')
    # print(f'option: {table_ProductOptions}')
    # return
    # sql_products = """INSERT IGNORE INTO Products (product_id, shop_id, prod_name, real_price, price, team_price, nation, is_unit,
    #                                             contents, create_at, maxrate, is_sold_out, style, category1, prod_link, category2, star)
    #                                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    # cur.executemany(sql_products, total_table_Products)
    # conn.commit()

    # sql_categoryofproducts = """INSERT INTO CategoryOfProduct (category_of_product_id, category_id, product_id)
    #                                                 VALUES (%s, %s, %s)"""
    # cur.executemany(sql_categoryofproducts, total_table_CategoryOfProduct)
    # conn.commit()

    # sql_fabricinfos = """INSERT INTO FabricInfos (fabric_id, product_id, 핏정보, 두께감, 신축성, 비침, 안감, 광택, 촉감, 밴딩)
    #                                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    # cur.executemany(sql_fabricinfos, total_table_FabricInfos)
    # conn.commit()

    # sql_productoptions = """INSERT INTO ProductOptions (product_option_id, product_id, size, color)
    #                                             VALUES (%s, %s, %s, %s)"""
    # cur.executemany(sql_productoptions, total_table_ProductOptions)
    # conn.commit()

    # sql_washinfos = """INSERT INTO WashInfos (wash_info_id, product_id, category)
    #                                 VALUES (%s, %s, %s)"""
    # cur.executemany(sql_washinfos, total_table_WashInfos)
    # conn.commit()

    # sql_productstyles = """INSERT INTO ProductStyles (product_style_id, product_id, style_id)
    #                                         VALUES (%s, %s, %s)"""
    # cur.executemany(sql_productstyles, total_table_ProductStyles)
    # conn.commit()

    # sql_productimages = """INSERT INTO ProductImages (image_id, product_id, image_name, image_url)
    #                                         VALUES (%s, %s, %s, %s)"""
    # cur.executemany(sql_productimages, total_table_ProductImages)
    # conn.commit()

    # driver.quit()

    log_message = {'Message': 'Success inserted to db(goods)'}
    return log_message
    # resp = Response(json.dumps(log_message, ensure_ascii=False).encode('utf8'), status=200, mimetype='application/json')

    # return resp

# @app.errorhandler(Exception)


# @cross_origin(origin="*", headers=['Content-Type', 'Authorization'])
# def exception_handler(error):
#     driver.quit()
#     print(error)
#     log_message = {'Message':'Fail insert db(goods)'}
#     return log_message

# if __name__ == '__main__':
# 	app.run(host='0.0.0.0', debug=True, port=5002)


@router.get('/')
def test():
    downloadImage(f'https://image-v4.sinsang.market/?f=https://image-cache.sinsang.market/images/25232/92046071/167922118000577415_547936075.png&w=375&h=500', './Products/test3.png')
    # try:

    # url = 'https://image-v4.sinsang.market/?f=https://image-cache.sinsang.market/images/25232/92085305/167655035100655297_1462791657.jpg&w=1500&h=2000'
    # # url = 'https://www.searchenginejournal.com/wp-content/uploads/2022/06/image-search-1600-x-840-px-62c6dc4ff1eee-sej-1280x720.png'

    # headers = {
    #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'  # A common user agent
    #         }

    # response = requests.get(url=url, headers=headers)
    # if response.status_code == 200:
    #     with open('./Products/test2.png', 'wb') as f:
    #         f.write(response.content)
    #     print("Image downloaded successfully.")
    # else:
    #     print("Failed to download image. Status code:", response.status_code)

    #     # urlretrieve(url, './Products/test.png')

    #     # image_response = requests.get(url, stream=True)
    #     # with open('./Products/test.jpg', 'wb') as out_file:
    #     #     shutil.copyfileobj(image_response.raw, out_file)
    #     # del image_response
    #     # print(image_response.status_code)
    #     # if image_response.status_code == 200:
    #     #     with  open('./Products/test2.jpg', 'wb') as out_file:
    #     #         out_file.write(image_response.content)
    #     #     return HTTPException(
    #     #      status_code=status.HTTP_200_OK
    #     #     )

    # except Exception as err:
    #     print(f'Error {err}')
    #     return HTTPException(
    #     status_code=status.HTTP_400_BAD_REQUEST,
    #     detail=f'{err}')
    
    
@router.get('/progress/{reference_id}')
def progress(reference_id:int):
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

