# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# ■■■■■■■■ ddmmarket data crawling & DB insert ■■■■■■■■
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

import math
import os
import time
import re
import pickle
import boto3
import pymysql
from glob import glob
import pandas as pd
from datetime import datetime
# from tqdm.notebook import tqdm
from tqdm import tqdm
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
import json
import numpy as np
from fastapi import APIRouter
from fastapi import HTTPException, status
from lib import create_folder, downloadImage, upload_image, check_duplicate_shop, check_duplicate_product, papago_translate, check_product_register_date, parse_relative_time
import urllib.request
from dotenv import load_dotenv
load_dotenv()


router = APIRouter(tags=['DDMmarket'])



def parse_datetime(datetime_str):
    datetime_patern = r'\d{4}\-\d{2}\-\d{2}'
    matches = re.findall(datetime_patern, datetime_str)
    if matches:
        datetime_str = matches[0]

        parsed_datetime = datetime.strptime(datetime_str, '%Y-%m-%d')

        return parsed_datetime.strftime('%Y-%m-%d %H:%M:%S')

    else:
        return ''

def shops_hold_category(x):  # 여성
    if x == 'DB2G150042' or x == 'CB1GA30C35' or \
       x == 'D1D1000460' or x == 'C5LA525237' or \
       x == 'NZ12230029':  # 그루, 한나네, 낫씽베러, 폴링제이, 보니타
        x = '21'  # Dress(원피스)
    elif x == 'DWP2320474':  # 라인
        x == '8'  # Tee/Top
    elif x == 'D2G1700317':  # 비키
        x == '26'  # Slacks
    elif x == 'C3NA180483':  # 더이태리
        x == '27'  # Pants
    elif x == 'Q215300310' or x == 'DB2N301265' or x == 'D3E2100443':  # 바닐라제이, 피노키오, 데님부티크
        x == '28'  # Jean
    elif x == 'D1J1800328':  # 보따리
        x == '9'
    elif x == 'DB2D300037':  # 페이퍼
        x = '25'  # Skirts
    elif x == 'C2KA350516':  # 제이엠
        x = '18'  # Hood/Zip-uip/Safari
    elif x == 'NZB1207434':  # 시엘(뉴존)
        x = '34'  # Maternity(임부복)
    else:
        x = False

    return x


def calculate_nation(nation:str) -> str:
    if '한국' in nation:
        return '대한민국'
    elif '중국' in nation: 
        return '중국'
    else: 
        return '기타'


def click_element(element):
    try:
        driver.execute_script("arguments[0].click();", element)
    except Exception as e:
        print(e)


@router.post('/product')
def product():
    job()


def job(store_id='CB1NA24367'):
    
    max_day_ago = 30 * 6 
    
    create_folder('./Products')
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
    sql_products = "SELECT * FROM Products"
    cur.execute(sql_products)
    rows_products = cur.fetchall()
    # last_prod_create_at = rows_products[-1][9]  # last updated product time
    product_id = rows_products[-1][0] + \
        1 if len(list(rows_products)) > 0 else 1

    print(f'product id --->>>> {product_id}')
    sql_shops = "SELECT * FROM Shops"
    cur.execute(sql_shops)
    rows_shops = cur.fetchall()

    # chrome option
    global driver

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--mute-audio')
    chrome_options.add_argument('disable-gpu')
    chrome_options.add_argument('lang=ko')
    chrome_options.add_argument(
        'user-agent=User_Agent: Mozilla/5.0 \(Windows NT 10.0; Win64; x64\) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"])

    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    # 로그인

    driver.get('https://www.ddmmarket.co.kr')
    driver.implicitly_wait(10)
    # time.sleep(2)

    id = 'sokodress'
    password = 'ddmmarket9138'

    driver.execute_script('arguments[0].click();', driver.find_element(
        By.XPATH, '//*[@id="app"]/div[2]/div[6]/div/div/header/div[1]/div/button[3]/span'))
    time.sleep(2)
    driver.find_element(By.ID, 'input-22').send_keys(id)
    time.sleep(1)
    driver.find_element(By.ID, 'input-25').send_keys(password)
    time.sleep(0.5)
    driver.execute_script('arguments[0].click();', driver.find_element(
        By.XPATH, '//*[@id="app"]/div[4]/div/div/div[2]/form/button'))
    time.sleep(2)

    # 크롤링 사이트 목록
    basic_domain = f'https://www.ddmmarket.co.kr/shop/RegularProducts'
    driver.get(basic_domain)
    driver.implicitly_wait(2)

    shops = driver.find_element(By.XPATH, '//*[@id="app"]/div[1]/main/div/div/div/div[3]/div/div[2]/div[1]/div[2]/div').find_elements(
        By.XPATH, '//span[contains(@class,"px-2 v-chip v-chip--clickable v-chip--label v-chip--no-color v-chip--outlined theme--light v-size--default")]')
    total_product_count = 0
    total_table_ProductImages = []
    
    scraped_item = 0
    for shop in shops:
        shop_name = shop.text.strip()
        shop_address = '서울시 강남구 삼성동 153-12'
        shop_phone = '010-1234-5678'
        shop_link = 'https://www.ddmmarket.co.kr/shop/RegularProducts'
        sanga_name = '디오트'

        if check_duplicate_shop(shop_name, rows_shops) is None:
            try:
                shop_create_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                slq_interto_shop = """INSERT INTO Shops (shop_name, address, sinsang_store_phone, shop_image,transactions, sanga_name, shop_link, main_items, create_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                # cursor = conn.cursor()
                shop_image = 'https://sokodress.s3.ap-northeast-2.amazonaws.com/ShopProfiles/shop_25232.png'
                shop_insert_data = (shop_name, shop_address, shop_phone, shop_image,
                                    0, sanga_name, shop_link, '주력 아이템', shop_create_at)
                print(shop_insert_data)
                cur.execute(slq_interto_shop, shop_insert_data)
                # conn.commit()
                shop_id = cur.lastrowid

                print(f'inserted shop id {shop_id}')
            # cursor.close()
            # conn.close()

            except Exception as e:
                print(f'shop inserting error {e}')
        else:
            print('store already exists')
            shop_id = check_duplicate_shop(shop_name, rows_shops)
            pass

            print(f'shop id {shop_id}')

        click_element(shop)
        time.sleep(1)
       
        try:
            total_product_count = driver.find_element(
                By.XPATH, '//*[@id="app"]/div[1]/main/div/div/div/div[5]').text
            match = re.search(r'\d+', total_product_count)
            total_product_count = int(match.group())
        except:
            pass

        # temp
        # total_product_count = 2
        if total_product_count == 0:
            continue
        
        category_id = 98
        # while True and product_number <= total_product_count:
        for product_number in range(1, int(total_product_count + 1),1):

            if product_number == 0:
                continue
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

          
            print(f'product number {product_number}')
            original_create_at = None
            try:
                element = WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, f'//*[@id="app"]/div[1]/main/div/div/div/div[6]/div[1]/div[{product_number}]/div/div[2]/div/div[5]')))
                original_create_at = driver.find_element(By.XPATH, f'//*[@id="app"]/div[1]/main/div/div/div/div[6]/div[1]/div[{product_number}]/div/div[2]/div/div[5]').text.strip()
                
            except Exception as e:
                print(f'original create at error {e}')
                original_create_at = None
                continue
            
            print(f'original create at ========>>>> {original_create_at}')
            
            try:
                if original_create_at is None or check_product_register_date(original_create_at, max_day_ago) is False:
                    print(f"product uploaded {max_day_ago} days ago")
                
                else: 
                    original_create_at = parse_datetime(original_create_at)
                    pass
            except Exception as e:
                print(f'original create at error {e}')
                continue
            
            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script(
                "return document.body.scrollHeight")
            
              # product which is clicked
            active_prod = driver.find_element(By.XPATH, f'//*[@id="app"]/div[1]/main/div/div/div/div[6]/div[1]/div[{product_number}]/div')
            print(f'product loop ->> {product_number}')
            click_element(active_prod)
            time.sleep(1)
            
            try:
                prod_name = driver.find_element(
                    By.XPATH, '//*[@id="scroll-target"]/div[1]/div[1]/div[2]/div[1]/div/div[1]').text.split(' ')[1].strip()
            except:
                prod_name = ''
                continue
            if prod_name is None:
                close_btn = driver.find_element(By.XPATH, '//*[@id="app"]/div[4]/div/div/div[1]/header/div/button')
                click_element(close_btn)
                continue

            if check_duplicate_product(prod_name, rows_products) is True:
                close_btn = driver.find_element(By.XPATH, '//*[@id="app"]/div[4]/div/div/div[1]/header/div/button')
                click_element(close_btn)
                continue
            else:
                print('not duplicate')
                pass
            
            if prod_name is not None:
                category_id = calculate_category(shop_name, prod_name)
                print(f'category id {category_id}')
                # connect this to papago
                try:
                    prod_name_en = papago_translate(prod_name)
                except Exception as e:
                    print(f'papago error {e}')
                    prod_name_en = prod_name
                    
            # try:
            #     sanga = driver.find_element(
            #         By.XPATH, '//*[@id="scroll-target"]/div[1]/div[1]/div[2]/div[1]/div/div[2]').text
            # except:
            #     sanga = ''

            # try:
            #     address = driver.find_element(
            #         By.XPATH, '//*[@id="scroll-target"]/div[1]/div[1]/div[2]/div[1]/div/div[3]').text.split(':')[1]
            # except:
            #     address = ''

            try:
                shop_phone = driver.find_element(
                    By.XPATH, '//*[@id="scroll-target"]/div[1]/div[1]/div[2]/div[1]/div/div[4]').text.split(':')[1]
            except:
                shop_phone = ''

            bottom_card = driver.find_element(By.TAG_NAME, 'table').find_element(
                By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
            try:
                price = driver.find_element(
                    By.XPATH, '//*[@id="scroll-target"]/div[1]/div[1]/div[2]/div[2]/div[2]/div').text.replace(',','')
            except:
                price = ''

            try:
                nation = driver.find_element(
                    By.XPATH, '//*[@id="scroll-target"]/div[1]/div[1]/div[2]/div[4]/div[2]/div').text
                nation = calculate_nation(nation)
            except:
                nation = ''

            try:
                style = driver.find_element(
                    By.XPATH, '//*[@id="scroll-target"]/div[1]/div[1]/div[2]/div[5]/div[2]/div').text
            except:
                style = ''
                
            try:
                contents = driver.find_element(
                    By.XPATH, '//*[@id="scroll-target"]/div[1]/div[1]/div[2]/div[8]/div[2]/div/span').text
            except:
                contents = ''


            try:
                goods_fabric_seethrough = driver.find_element(
                    By.XPATH, '//*[@id="scroll-target"]/div[1]/div[1]/div[2]/div[9]/div[2]/div[1]').text.split(':')[1].strip()
                goods_fabric_elasticity = driver.find_element(
                    By.XPATH, '//*[@id="scroll-target"]/div[1]/div[1]/div[2]/div[9]/div[2]/div[2]').text.split(':')[1].strip()
                goods_fabric_lining = driver.find_element(
                    By.XPATH, '//*[@id="scroll-target"]/div[1]/div[1]/div[2]/div[9]/div[2]/div[3]').text.split(':')[1].strip()
                피팅감 = driver.find_element(
                    By.XPATH, '//*[@id="scroll-target"]/div[1]/div[1]/div[2]/div[9]/div[2]/div[4]').text.split(':')[1].strip()
            except:
                비침 = ''
                신축성 = ''
                안감 = ''
                피팅감 = ''
                goods_fabric_lining = ''
                goods_fabric_elasticity = ''
                goods_fabric_seethrough = ''
                
            image_group = []
            
            try:
                image_group = driver.find_element(By.XPATH, '//*[@id="scroll-target"]/div[1]/div[1]/div[1]/div/div[2]/div/div[2]/div').find_elements(
                    By.XPATH, '//div[contains(@class, "ma-1 v-card v-card--link v-sheet theme--light rounded-0 grey lighten-1")]')
                time.sleep(1)
            
            except:
                image_group = []
                pass
            if len(image_group) == 0:
                close_btn = driver.find_element(By.XPATH, '//*[@id="app"]/div[4]/div/div/div[1]/header/div/button')
                click_element(close_btn)
                continue
            
            for i in range(1, len(image_group),1):
                if i == 0:
                    continue
                
                time.sleep(0.5)
                bg_url = driver.find_element(
                    By.XPATH, f'//*[@id="scroll-target"]/div[1]/div[1]/div[1]/div/div[2]/div/div[2]/div/div[{i}]/div/div[2]').value_of_css_property('background-image')
                
                goods_src = bg_url.lstrip('url("').rstrip('")')
                image_path = f'./Products/{product_id}_{i}.jpeg'                
                try:
                    urllib.request.urlretrieve(goods_src, image_path)
                    # print(f'image downloaded ->>> {image_path}')
                except Exception as e:
                    print(f'image download error {e}')

                time.sleep(1)
                image_url = upload_image(s3, product_id, i)
                
                table_ProductImages = (
                    # str(image_id),  # autoincrement
                    str(product_id),
                    # 'ddmkarket product image',
                    f'{str(product_id)}_{str(i)}',
                    image_url
                )

                total_table_ProductImages.append(
                    table_ProductImages)

                os.remove(image_path)
                # image_id += 1


            # print(f'prod_images : {prod_images}')

            # style="background-image: url(&quot;https://gimg.ddmadmin.co.kr/2022/10/26/__20221026143432140_5.jpg&quot;); background-position: center center;"

            # print(
            #     f'상품명 : {prod_name} 주소 : {address} 전화번호 : {shop_phone} 가격 : {price} 비침 :  {비침} , 신축성: {신축성}, 안감 : {안감}, 피팅감 : {피팅감}')

            color = ''
            size = ''
            # color and size
            for i in range(len(bottom_card)):
                time.sleep(0.3)
                if i == 0:
                    continue
                try:
                    size_color = bottom_card[i].find_elements(
                        By.TAG_NAME, 'td')[0].text
                    inner_color = size_color.split(
                        '/')[0].split(':')[1].strip()
                    inner_size = size_color.split('/')[1].split(':')[1].strip()

                    if inner_color not in color:
                        if color != '':
                            color = color + ', ' + inner_color
                        else:
                            color = inner_color
                    if inner_size not in size:
                        if size != '':
                            size = size + ', ' + inner_size
                        else:
                            size = inner_size

                except Exception as e:
                    print(e)
                    pass

            # print(color)
            # print(size)
            created_at = datetime.now()
            created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
            
            table_Products = (
                str(product_id),
                str(shop_id),
                prod_name,
                prod_name_en,
                price, #real price,
                price, #sale price
                price, #team price
                nation,
                'F', # is unit
                contents,
                created_at,
                None,
                False,
                style,
                '여성 의류',
                shop_link,
                '하의', #TODO: temporary value
                '5'
            )
            
            table_FabricInfos = (
                # str(fabric_id),  # autoincrement
                str(product_id),
                '기본핏',  # 핏정보(not null)
                '보통',  # 두께감
                goods_fabric_elasticity,  # 신축성
                goods_fabric_seethrough,  # 비침
                goods_fabric_lining,  # 안감
                '없음',  # 광택('없음'으로)
                '보통',  # 촉감('보통'으로)
                '없음'  # 밴딩('없음'으로)
        )

            print(f'table_FabricInfos : {table_FabricInfos}')
            table_ProductOptions = (
                # str(product_option_id),  # autoincrement
                str(product_id),
                size,  # size
                color,  # color
                original_create_at,
        )

            table_ProductStyles = (
                # str(product_style_id),  # autoincrement
                str(product_id),
                str(1), #TODO: temporary value
            )
            
            table_CategoryOfProduct = (
                # str(category_of_product_id), # autoincrement
                    str(category_id),
                    str(product_id)
                )
            try:        

                sql_products = """INSERT IGNORE INTO Products (product_id, shop_id, prod_name, prod_name_en, real_price, price, team_price, nation, is_unit,
                                    contents, create_at, maxrate, is_sold_out, style, category1, prod_link, category2, star)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
  
                cur.execute(sql_products, table_Products)
                conn.commit()

                # after inserting new row to product define category of products
               
                sql_categoryofproducts = """INSERT IGNORE INTO CategoryOfProduct (category_id, product_id) VALUES (%s, %s)"""
                cur.execute(sql_categoryofproducts, table_CategoryOfProduct)
                conn.commit()
                print(f'category products {table_CategoryOfProduct}')
                
                sql_fabricinfos = """INSERT INTO FabricInfos (product_id, 핏정보, 두께감, 신축성, 비침, 안감, 광택, 촉감, 밴딩) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

                cur.execute(sql_fabricinfos, table_FabricInfos)
                conn.commit()

                sql_productoptions = """INSERT INTO ProductOptions (product_id, size, color, original_create_at)
                                                                    VALUES ( %s, %s, %s, %s)"""

                cur.execute(sql_productoptions, table_ProductOptions)
                print(f'table product options :::: {table_ProductOptions}')
                conn.commit()

                # sql_washinfos = """INSERT INTO WashInfos (product_id, category)
                #                                         VALUES ( %s, %s)"""
                # cur.executemany(sql_washinfos, total_table_WashInfos)
                # conn.commit()

                sql_productstyles = """INSERT INTO ProductStyles (product_id, style_id) VALUES (%s, %s)"""
                cur.execute(sql_productstyles, table_ProductStyles)
                conn.commit()

                sql_productimages = """INSERT INTO ProductImages (product_id, image_name, image_url) VALUES ( %s, %s, %s)"""
                cur.executemany(sql_productimages, total_table_ProductImages)
                
                conn.commit()

                product_id += 1
                scraped_item += 1
                total_table_ProductImages = []

                close_btn = driver.find_element(By.XPATH, '//*[@id="app"]/div[4]/div/div/div[1]/header/div/button')
                click_element(close_btn)

            except Exception as e:
                conn.rollback()
                product_id += 1
                print(f'something went wrong:::: {e}')
                close_btn = driver.find_element(By.XPATH, '//*[@id="app"]/div[4]/div/div/div[1]/header/div/button')
                click_element(close_btn)
    pass



# @router.get('/product')
# def test():
#     conn = pymysql.connect(
#           host=os.getenv('host'),
#         port=int(str(os.getenv('port'))),
#         user=os.getenv('user'),
#         passwd=os.getenv('passwd'),
#         db=os.getenv('db'),
#         charset='utf8'
#     )
#     cur = conn.cursor()
#     sql = """SELECT * FROM Products"""
#     cur.execute(sql)
#     products = cur.fetchall()
#     conn.commit()
#     return len(products)



def calculate_category(shop_name:str, prod_name:str) -> int:
    category_id = 98
    
    if   '유성' in shop_name:
        if '가디건' or 'CD' in prod_name or 'Y' in prod_name or 'VY' in prod_name or '볼레로' in prod_name:
            category_id = 14
        elif '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name or 'JK' in prod_name or 'Jk' in prod_name:
            category_id = 13
        elif 'PT' in prod_name or 'pt' in prod_name:
            category_id = 27
        elif '베스트' in prod_name or '조끼' in prod_name:
            category_id = 15
        elif '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '코트' or 'CT' or "ct" or 'Coat' in prod_name:
            category_id = 17
        elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
            category_id = 18
        elif '치마' in prod_name or 'SK' in prod_name or 'SKT' in prod_name or '스커트' in prod_name:
            category_id = 25
        elif '바지' in prod_name or '반바지' in prod_name or '팬츠' in prod_name or '부츠컷' in prod_name or '치마PT' in prod_name or '조거' in prod_name or '컷' in prod_name: 
            category_id = 27
        elif 'SL' in prod_name or 'PA' in prod_name or 'PT' in prod_name or '슬렉스' in prod_name or '슬랙스' in prod_name: 
            category_id = 26
        elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name or '구스' in prod_name:
            category_id = 16
        elif 'OPS' in prod_name or '원피스' in prod_name or '드래스' in prod_name or '드레스' in prod_name:
            category_id = 21
        elif '티' in prod_name or 'U년' in prod_name or '카라' in prod_name or '탑' in prod_name or 'P(PolarT)' in prod_name or 'P' in prod_name or '티셔츠' in prod_name or 'T' in prod_name or 'V' in prod_name or 'Y' in prod_name or 'P' in prod_name or 'RT' in prod_name or 'R' in prod_name or 'VT' in prod_name or '나시' in prod_name or '니트' in prod_name or '민소매' in prod_name or '반팔' in prod_name or '단가라' in prod_name or '카라' in prod_name or '폴라' in prod_name:
            category_id = 8
        elif '볼레로' in prod_name: 
            category_id = 14
        elif '체크' in prod_name:
            category_id = 11
        else:
            category_id = 26

    if   '와글' in shop_name:
        if 'BL' in prod_name or 'bl' in prod_name or 'blouse' in prod_name or '블라우스' in prod_name:
            category_id = 10
        elif '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name or 'JK' in prod_name or 'Jk' in prod_name:
            category_id = 13
        elif '가디건' or 'CD' in prod_name:
            category_id = 14
            
        elif '조끼' in prod_name:
            category_id = 15
            
        elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name:
            category_id = 16
            
        elif '코트' or 'CT' or "ct" in prod_name:
            category_id = 17
            
        elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
            category_id = 18

         # DRESS 드레스 '20'
        elif '세트' in prod_name or '셋트' in prod_name:
            category_id = 22

        elif '니트' in prod_name:
            category_id = 23

        else:
            category_id = 32

    if   '더블유디(WD)' in shop_name:
        category_id = 27 #pants
    
    if   '루키' in shop_name:
        if '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name or 'JK' in prod_name or 'Jk' in prod_name:
            category_id = 13
        elif 'PT' in prod_name or 'pt' in prod_name:
            category_id = 27
        elif '베스트' in prod_name:
            category_id = 15
        elif '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '코트' or 'CT' or "ct" or 'Coat' in prod_name:
            category_id = 17
        elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
            category_id = 18
        elif '치마' in prod_name or 'SK' in prod_name or 'SKT' in prod_name or '스커트' in prod_name:
            category_id = 25
        elif '바지' in prod_name or '반바지' in prod_name or '팬츠' in prod_name or '부츠컷' in prod_name or '치마PT' in prod_name or '조거' in prod_name or '컷' in prod_name: 
            category_id = 27
        elif 'SL' in prod_name or 'PA' in prod_name or 'PT' in prod_name or '슬렉스' in prod_name or '슬랙스' in prod_name: 
            category_id = 26
        elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name:
            category_id = 16
        elif 'OPS' in prod_name or '원피스' in prod_name or '드래스' in prod_name or '드레스' in prod_name:
            category_id = 21
            
    if   '게이트' in shop_name:
        if '치마' in prod_name or 'SK' in prod_name or 'SKT' in prod_name or '스커트' in prod_name:
            category_id = 25
        elif 'BL' in prod_name or 'bl' in prod_name or 'blouse' in prod_name or '블라우스' in prod_name:
            category_id = 10
        elif 'SL' in prod_name or 'PA' in prod_name or 'PT' in prod_name or '슬렉스' in prod_name or '슬랙스' in prod_name: 
            category_id = 26
        elif '티' in prod_name or '탑' in prod_name or '티셔츠' in prod_name or 'T' in prod_name or 'V' in prod_name or 'Y' in prod_name or 'P' in prod_name or 'RT' in prod_name or 'R' in prod_name or 'VT' in prod_name or '나시' in prod_name or '니트' in prod_name or '민소매' in prod_name or '반팔' in prod_name or '단가라' in prod_name or '카라' in prod_name or '폴라' in prod_name:
            category_id = 8
        elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name:
            category_id = 16
        elif 'OPS' in prod_name or '원피스' in prod_name or '드래스' in prod_name or '드레스' in prod_name:
            category_id = 21
            
    if  '스킨' in shop_name:
        category_id = 27
        return category_id
    if  '문(mun)' in shop_name:
        if '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name or 'JK' in prod_name or 'Jk' in prod_name:
            category_id = 13
        elif 'PT' in prod_name or 'pt' in prod_name:
            category_id = 27
        elif '베스트' in prod_name:
            category_id = 15
        elif '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '코트' or 'CT' or "ct" or 'Coat' in prod_name:
            category_id = 17
        elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
            category_id = 18
        elif '치마' in prod_name or 'SK' in prod_name or 'SKT' in prod_name or '스커트' in prod_name:
            category_id = 25
        elif '바지' in prod_name or '반바지' in prod_name or '팬츠' in prod_name or '부츠컷' in prod_name or '치마PT' in prod_name or '조거' in prod_name or '컷' in prod_name: 
            category_id = 27
        elif 'SL' in prod_name or 'PA' in prod_name or 'PT' in prod_name or '슬렉스' in prod_name or '슬랙스' in prod_name: 
            category_id = 26
        elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name:
            category_id = 16
        elif 'OPS' in prod_name or '원피스' in prod_name or '드래스' in prod_name or '드레스' in prod_name:
            category_id = 21
        elif '티' in prod_name or '탑' in prod_name or '티셔츠' in prod_name or 'T' in prod_name or 'V' in prod_name or 'Y' in prod_name or 'P' in prod_name or 'RT' in prod_name or 'R' in prod_name or 'VT' in prod_name or '나시' in prod_name or '니트' in prod_name or '민소매' in prod_name or '반팔' in prod_name or '단가라' in prod_name or '카라' in prod_name or '폴라' in prod_name:
            category_id = 8
            
    if  '톤앤톤' in shop_name:
        if '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name or 'JK' in prod_name or 'Jk' in prod_name:
            category_id = 13
        elif 'PT' in prod_name or 'pt' in prod_name:
            category_id = 27
        elif '베스트' in prod_name:
            category_id = 15
        elif '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '코트' or 'CT' or "ct" or 'Coat' in prod_name:
            category_id = 17
        elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
            category_id = 18
        elif '치마' in prod_name or 'SK' in prod_name or 'SKT' in prod_name or '스커트' in prod_name:
            category_id = 25
        elif '바지' in prod_name or '반바지' in prod_name or '팬츠' in prod_name or '부츠컷' in prod_name or '치마PT' in prod_name or '조거' in prod_name or '컷' in prod_name: 
            category_id = 27
        elif 'SL' in prod_name or 'PA' in prod_name or 'PT' in prod_name or '슬렉스' in prod_name or '슬랙스' in prod_name: 
            category_id = 26
        elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name:
            category_id = 16
        elif 'OPS' in prod_name or '원피스' in prod_name or '드래스' in prod_name or '드레스' in prod_name:
            category_id = 21
        elif '티' in prod_name or '탑' in prod_name or '티셔츠' in prod_name or 'T' in prod_name or 'V' in prod_name or 'Y' in prod_name or 'P' in prod_name or 'RT' in prod_name or 'R' in prod_name or 'VT' in prod_name or '나시' in prod_name or '니트' in prod_name or '민소매' in prod_name or '반팔' in prod_name or '단가라' in prod_name or '카라' in prod_name or '폴라' in prod_name:
            category_id = 8
            
    if  '미모' in shop_name:
        if '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name or 'JK' in prod_name or 'Jk' in prod_name:
            category_id = 13
        elif 'PT' in prod_name or 'pt' in prod_name:
            category_id = 27
        elif '베스트' in prod_name:
            category_id = 15
        elif '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '코트' or 'CT' or "ct" or 'Coat' in prod_name:
            category_id = 17
        elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
            category_id = 18
        elif '치마' in prod_name or 'SK' in prod_name or 'SKT' in prod_name or '스커트' in prod_name:
            category_id = 25
        elif '바지' in prod_name or '반바지' in prod_name or '팬츠' in prod_name or '부츠컷' in prod_name or '치마PT' in prod_name or '조거' in prod_name or '컷' in prod_name: 
            category_id = 27
        elif 'SL' in prod_name or 'PA' in prod_name or 'PT' in prod_name or '슬렉스' in prod_name or '슬랙스' in prod_name: 
            category_id = 26
        elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name:
            category_id = 16
        elif 'OPS' in prod_name or '원피스' in prod_name or '드래스' in prod_name or '드레스' in prod_name:
            category_id = 21
        elif '티' in prod_name or '탑' in prod_name or '티셔츠' in prod_name or 'T' in prod_name or 'V' in prod_name or 'Y' in prod_name or 'P' in prod_name or 'RT' in prod_name or 'R' in prod_name or 'VT' in prod_name or '나시' in prod_name or '니트' in prod_name or '민소매' in prod_name or '반팔' in prod_name or '단가라' in prod_name or '카라' in prod_name or '폴라' in prod_name:
            category_id = 8
            
    if   '주라엘' in shop_name:
        if '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name or 'JK' in prod_name or 'Jk' in prod_name:
            category_id = 13
        elif 'PT' in prod_name or 'pt' in prod_name:
            category_id = 27
        elif '베스트' in prod_name:
            category_id = 15
        elif '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '코트' or 'CT' or "ct" or 'Coat' in prod_name:
            category_id = 17
        elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
            category_id = 18
        elif '치마' in prod_name or 'SK' in prod_name or 'SKT' in prod_name or '스커트' in prod_name:
            category_id = 25
        elif '바지' in prod_name or '반바지' in prod_name or '팬츠' in prod_name or '부츠컷' in prod_name or '치마PT' in prod_name or '조거' in prod_name or '컷' in prod_name: 
            category_id = 27
        elif 'SL' in prod_name or 'PA' in prod_name or 'PT' in prod_name or '슬렉스' in prod_name or '슬랙스' in prod_name: 
            category_id = 26
        elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name:
            category_id = 16
        elif 'OPS' in prod_name or '원피스' in prod_name or '드래스' in prod_name or '드레스' in prod_name:
            category_id = 21
        elif '티' in prod_name or '탑' in prod_name or '티셔츠' in prod_name or 'T' in prod_name or 'V' in prod_name or 'Y' in prod_name or 'P' in prod_name or 'RT' in prod_name or 'R' in prod_name or 'VT' in prod_name or '나시' in prod_name or '니트' in prod_name or '민소매' in prod_name or '반팔' in prod_name or '단가라' in prod_name or '카라' in prod_name or '폴라' in prod_name:
            category_id = 8
        elif '볼레로' in prod_name: 
            category_id = 14
    if   '롤리팝' in shop_name:
        if '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name or 'JK' in prod_name or 'Jk' in prod_name:
            category_id = 13
        elif 'PT' in prod_name or 'pt' in prod_name:
            category_id = 27
        elif '베스트' in prod_name:
            category_id = 15
        elif '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '코트' or 'CT' or "ct" or 'Coat' in prod_name:
            category_id = 17
        elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
            category_id = 18
        elif '치마' in prod_name or 'SK' in prod_name or 'SKT' in prod_name or '스커트' in prod_name:
            category_id = 25
        elif '바지' in prod_name or '반바지' in prod_name or '팬츠' in prod_name or '부츠컷' in prod_name or '치마PT' in prod_name or '조거' in prod_name or '컷' in prod_name: 
            category_id = 27
        elif 'SL' in prod_name or 'PA' in prod_name or 'PT' in prod_name or '슬렉스' in prod_name or '슬랙스' in prod_name: 
            category_id = 26
        elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name or '구스' in prod_name:
            category_id = 16
        elif 'OPS' in prod_name or '원피스' in prod_name or '드래스' in prod_name or '드레스' in prod_name:
            category_id = 21
        elif '티' in prod_name or '탑' in prod_name or 'P(PolarT)' in prod_name or 'P' in prod_name or '티셔츠' in prod_name or 'T' in prod_name or 'V' in prod_name or 'Y' in prod_name or 'P' in prod_name or 'RT' in prod_name or 'R' in prod_name or 'VT' in prod_name or '나시' in prod_name or '니트' in prod_name or '민소매' in prod_name or '반팔' in prod_name or '단가라' in prod_name or '카라' in prod_name or '폴라' in prod_name:
            category_id = 8
        elif '볼레로' in prod_name: 
            category_id = 14
    if   '하마' in shop_name:
        if '아이스' in prod_name: 
            category_id = 28
        else :
            category_id = 27
            
    if    '피노키오' in shop_name:
        category_id = 28
    
    if   '커피샤워' in shop_name:
        if '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name or 'JK' in prod_name or 'Jk' in prod_name:
            category_id = 13
        elif 'PT' in prod_name or 'pt' in prod_name:
            category_id = 27
        elif '베스트' in prod_name:
            category_id = 15
        elif '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '코트' or 'CT' or "ct" or 'Coat' in prod_name:
            category_id = 17
        elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
            category_id = 18
        elif '치마' in prod_name or 'SK' in prod_name or 'SKT' in prod_name or '스커트' in prod_name:
            category_id = 25
        elif '바지' in prod_name or '반바지' in prod_name or '팬츠' in prod_name or '부츠컷' in prod_name or '치마PT' in prod_name or '조거' in prod_name or '컷' in prod_name: 
            category_id = 27
        elif 'SL' in prod_name or 'PA' in prod_name or 'PT' in prod_name or '슬렉스' in prod_name or '슬랙스' in prod_name: 
            category_id = 26
        elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name or '구스' in prod_name:
            category_id = 16
        elif 'OPS' in prod_name or '원피스' in prod_name or '드래스' in prod_name or '드레스' in prod_name:
            category_id = 21
        elif '티' in prod_name or '탑' in prod_name or 'P(PolarT)' in prod_name or 'P' in prod_name or '티셔츠' in prod_name or 'T' in prod_name or 'V' in prod_name or 'Y' in prod_name or 'P' in prod_name or 'RT' in prod_name or 'R' in prod_name or 'VT' in prod_name or '나시' in prod_name or '니트' in prod_name or '민소매' in prod_name or '반팔' in prod_name or '단가라' in prod_name or '카라' in prod_name or '폴라' in prod_name:
            category_id = 8
        elif '볼레로' in prod_name: 
            category_id = 14
        elif '체크' in prod_name:
            category_id = 11
            
    if  '가나다' in shop_name:
        if '가디건' or 'CD' in prod_name or 'Y' in prod_name or 'VY' in prod_name or '볼레로' in prod_name:
            category_id = 14
        elif '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name or 'JK' in prod_name or 'Jk' in prod_name:
            category_id = 13
        elif 'PT' in prod_name or 'pt' in prod_name:
            category_id = 27
        elif '베스트' in prod_name or '조끼' in prod_name:
            category_id = 15
        elif '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '코트' or 'CT' or "ct" or 'Coat' in prod_name:
            category_id = 17
        elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
            category_id = 18
        elif '치마' in prod_name or 'SK' in prod_name or 'SKT' in prod_name or '스커트' in prod_name:
            category_id = 25
        elif '바지' in prod_name or '반바지' in prod_name or '팬츠' in prod_name or '부츠컷' in prod_name or '치마PT' in prod_name or '조거' in prod_name or '컷' in prod_name: 
            category_id = 27
        elif 'SL' in prod_name or 'PA' in prod_name or 'PT' in prod_name or '슬렉스' in prod_name or '슬랙스' in prod_name: 
            category_id = 26
        elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name or '구스' in prod_name:
            category_id = 16
        elif 'OPS' in prod_name or '원피스' in prod_name or '드래스' in prod_name or '드레스' in prod_name:
            category_id = 21
        elif '티' in prod_name or 'U년' in prod_name or '카라' in prod_name or '탑' in prod_name or 'P(PolarT)' in prod_name or 'P' in prod_name or '티셔츠' in prod_name or 'T' in prod_name or 'V' in prod_name or 'Y' in prod_name or 'P' in prod_name or 'RT' in prod_name or 'R' in prod_name or 'VT' in prod_name or '나시' in prod_name or '니트' in prod_name or '민소매' in prod_name or '반팔' in prod_name or '단가라' in prod_name or '카라' in prod_name or '폴라' in prod_name:
            category_id = 8
        elif '볼레로' in prod_name: 
            category_id = 14
        elif '체크' in prod_name:
            category_id = 11

    if   '이프하우스' in shop_name:
        if '티' in prod_name or 'RNT' in prod_name or 'NT' in prod_name or 'Neck Tee' in prod_name or 'U년' in prod_name or '카라' in prod_name or '탑' in prod_name or 'P(PolarT)' in prod_name or 'P' in prod_name or '티셔츠' in prod_name or 'T' in prod_name or 'V' in prod_name or 'Y' in prod_name or 'P' in prod_name or 'RT' in prod_name or 'R' in prod_name or 'VT' in prod_name or '나시' in prod_name or '니트' in prod_name or '민소매' in prod_name or '반팔' in prod_name or '단가라' in prod_name or '카라' in prod_name or '폴라' in prod_name:
            category_id = 8
        elif 'SL' in prod_name or 'PA' in prod_name or 'PT' in prod_name or '슬렉스' in prod_name or '슬랙스' in prod_name: 
            category_id = 26
        elif '가디건' or 'CD' in prod_name or 'Y' in prod_name or 'VY' in prod_name or '볼레로' in prod_name:
            category_id = 14
        elif '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name or 'JK' in prod_name or 'Jk' in prod_name:
            category_id = 13
        elif 'PT' in prod_name or 'pt' in prod_name:
            category_id = 27
        elif '베스트' in prod_name or '조끼' in prod_name:
            category_id = 15
        elif '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '코트' or 'CT' or "ct" or 'Coat' in prod_name:
            category_id = 17
        elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
            category_id = 18
        elif '치마' in prod_name or 'SK' in prod_name or 'SKT' in prod_name or '스커트' in prod_name:
            category_id = 25
        elif '바지' in prod_name or '반바지' in prod_name or '팬츠' in prod_name or '부츠컷' in prod_name or '치마PT' in prod_name or '조거' in prod_name or '컷' in prod_name: 
            category_id = 27
        elif 'SL' in prod_name or 'PA' in prod_name or 'PT' in prod_name or '슬렉스' in prod_name or '슬랙스' in prod_name: 
            category_id = 26
        elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name or '구스' in prod_name:
            category_id = 16
        elif 'OPS' in prod_name or '원피스' in prod_name or '드래스' in prod_name or '드레스' in prod_name:
            category_id = 21
        elif '티' in prod_name or 'U년' in prod_name or '카라' in prod_name or '탑' in prod_name or 'P(PolarT)' in prod_name or 'P' in prod_name or '티셔츠' in prod_name or 'T' in prod_name or 'V' in prod_name or 'Y' in prod_name or 'P' in prod_name or 'RT' in prod_name or 'R' in prod_name or 'VT' in prod_name or '나시' in prod_name or '니트' in prod_name or '민소매' in prod_name or '반팔' in prod_name or '단가라' in prod_name or '카라' in prod_name or '폴라' in prod_name:
            category_id = 8
        elif '볼레로' in prod_name: 
            category_id = 14
        elif '체크' in prod_name:
            category_id = 11
    if   '시엘' in shop_name:
        if '홈웨어' in prod_name:
            category_id = 33
        elif '수유SET' in prod_name: 
            category_id = 34
        elif '가디건' or 'CD' in prod_name or 'Y' in prod_name or 'VY' in prod_name or '볼레로' in prod_name:
            category_id = 14
        elif '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name or 'JK' in prod_name or 'Jk' in prod_name:
            category_id = 13
        elif 'PT' in prod_name or 'pt' in prod_name:
            category_id = 27
        elif '베스트' in prod_name or '조끼' in prod_name:
            category_id = 15
        elif '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '코트' or 'CT' or "ct" or 'Coat' in prod_name:
            category_id = 17
        elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
            category_id = 18
        elif '치마' in prod_name or 'SK' in prod_name or 'SKT' in prod_name or '스커트' in prod_name:
            category_id = 25
        elif '바지' in prod_name or '반바지' in prod_name or '팬츠' in prod_name or '부츠컷' in prod_name or '치마PT' in prod_name or '조거' in prod_name or '컷' in prod_name: 
            category_id = 27
        elif 'SL' in prod_name or 'PA' in prod_name or 'PT' in prod_name or '슬렉스' in prod_name or '슬랙스' in prod_name: 
            category_id = 26
        elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name or '구스' in prod_name:
            category_id = 16
        elif 'OPS' in prod_name or '원피스' in prod_name or '드래스' in prod_name or '드레스' in prod_name:
            category_id = 21
        elif '티' in prod_name or 'U년' in prod_name or '카라' in prod_name or '탑' in prod_name or 'P(PolarT)' in prod_name or 'P' in prod_name or '티셔츠' in prod_name or 'T' in prod_name or 'V' in prod_name or 'Y' in prod_name or 'P' in prod_name or 'RT' in prod_name or 'R' in prod_name or 'VT' in prod_name or '나시' in prod_name or '니트' in prod_name or '민소매' in prod_name or '반팔' in prod_name or '단가라' in prod_name or '카라' in prod_name or '폴라' in prod_name:
            category_id = 8
        elif '볼레로' in prod_name: 
            category_id = 14
        elif '체크' in prod_name:
            category_id = 11
    if   '르방' in shop_name:
        if 'MTM' in prod_name: 
            category_id = 63 
        elif '가디건' or 'CD' in prod_name or 'Y' in prod_name or 'VY' in prod_name or '볼레로' in prod_name:
            category_id = 14
        elif '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name or 'JK' in prod_name or 'Jk' in prod_name:
            category_id = 13
        elif 'PT' in prod_name or 'pt' in prod_name:
            category_id = 27
        elif '베스트' in prod_name or '조끼' in prod_name:
            category_id = 15
        elif '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '코트' or 'CT' or "ct" or 'Coat' in prod_name:
            category_id = 17
        elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
            category_id = 18
        elif '치마' in prod_name or 'SK' in prod_name or 'SKT' in prod_name or '스커트' in prod_name:
            category_id = 25
        elif '바지' in prod_name or '반바지' in prod_name or '팬츠' in prod_name or '부츠컷' in prod_name or '치마PT' in prod_name or '조거' in prod_name or '컷' in prod_name: 
            category_id = 27
        elif 'SL' in prod_name or 'PA' in prod_name or 'PT' in prod_name or '슬렉스' in prod_name or '슬랙스' in prod_name: 
            category_id = 26
        elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name or '구스' in prod_name:
            category_id = 16
        elif 'OPS' in prod_name or '원피스' in prod_name or '드래스' in prod_name or '드레스' in prod_name:
            category_id = 21
        elif '티' in prod_name or 'U년' in prod_name or '카라' in prod_name or '탑' in prod_name or 'P(PolarT)' in prod_name or 'P' in prod_name or '티셔츠' in prod_name or 'T' in prod_name or 'V' in prod_name or 'Y' in prod_name or 'P' in prod_name or 'RT' in prod_name or 'R' in prod_name or 'VT' in prod_name or '나시' in prod_name or '니트' in prod_name or '민소매' in prod_name or '반팔' in prod_name or '단가라' in prod_name or '카라' in prod_name or '폴라' in prod_name:
            category_id = 8
        elif '볼레로' in prod_name: 
            category_id = 14
        elif '체크' in prod_name:
            category_id = 11
    if  '페니블루' in shop_name or  '페니블루 (페니)' in shop_name:
        if '가디건' or 'CD' in prod_name or 'Y' in prod_name or 'VY' in prod_name or '볼레로' in prod_name:
            category_id = 14
        elif '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name or 'JK' in prod_name or 'Jk' in prod_name:
            category_id = 13
        elif 'PT' in prod_name or 'pt' in prod_name:
            category_id = 27
        elif '베스트' in prod_name or '조끼' in prod_name:
            category_id = 15
        elif '가디건' or 'CD' in prod_name:
            category_id = 14
        elif '코트' or 'CT' or "ct" or 'Coat' in prod_name:
            category_id = 17
        elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
            category_id = 18
        elif '치마' in prod_name or 'SK' in prod_name or 'SKT' in prod_name or '스커트' in prod_name:
            category_id = 25
        elif '바지' in prod_name or '반바지' in prod_name or '팬츠' in prod_name or '부츠컷' in prod_name or '치마PT' in prod_name or '조거' in prod_name or '컷' in prod_name: 
            category_id = 27
        elif 'SL' in prod_name or 'PA' in prod_name or 'PT' in prod_name or '슬렉스' in prod_name or '슬랙스' in prod_name: 
            category_id = 26
        elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name or '구스' in prod_name:
            category_id = 16
        elif 'OPS' in prod_name or '원피스' in prod_name or '드래스' in prod_name or '드레스' in prod_name:
            category_id = 21
        elif '티' in prod_name or 'KT' in prod_name or 'TS' in prod_name or 'U년' in prod_name or '카라' in prod_name or '탑' in prod_name or 'P(PolarT)' in prod_name or 'P' in prod_name or '티셔츠' in prod_name or 'T' in prod_name or 'V' in prod_name or 'Y' in prod_name or 'P' in prod_name or 'RT' in prod_name or 'R' in prod_name or 'VT' in prod_name or '나시' in prod_name or '니트' in prod_name or '민소매' in prod_name or '반팔' in prod_name or '단가라' in prod_name or '카라' in prod_name or '폴라' in prod_name:
            category_id = 8
        elif '볼레로' in prod_name: 
            category_id = 14
        elif '체크' in prod_name:
            category_id = 11
    return category_id