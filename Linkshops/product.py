import math
import os
import time
import re
import pickle
import boto3

from glob import glob
import pandas as pd
import datetime
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
import pymysql
from dotenv import load_dotenv
from lib import downloadImage, upload_image, check_duplicate_product, check_duplicate_shop, papago_translate
import schedule
from fastapi import HTTPException, status, BackgroundTasks, APIRouter
load_dotenv()
router = APIRouter(tags=['Linkshop'])


@router.post('/product')
async def product():
    """
    Purpose: 
    """
    job('designbyjs', max_day_ago = 30 * 6)
    return {"message": "successfully sent!"}
    # job()
    


def create_folder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print(f'[ERROR] 폴더 생성 실패 : {directory}')


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




def calculate_nation(nation:str) -> str:
    if '한국' in nation or 'Korea' in nation or 'korea' in nation or '대한민국' in nation:
        return '대한민국'
    elif '중국' in nation or 'Chine' in nation or 'chine' in nation: 
        return '중국'
    else: 
        return '기타'



def check_product_register_date(text_date:str, days_ago) -> bool:

    if text_date is None:
        return False
    
    try:
        
        date_obj = datetime.datetime.strptime(text_date.strip(), "%Y-%m-%d")

    # Calculate the current date
        current_date = datetime.datetime.now()

    # Calculate the difference between the two dates
        date_difference = current_date - date_obj

    # Calculate a timedelta for two months (approximately 60 days)
        two_months = datetime.timedelta(days=days_ago)
    # Compare the date difference with two months
        if date_difference < two_months:
            result = True
        else:
            result = False
        return result
    except Exception as e:
        print(f'parsing date error {e}')
        return False
    
def parse_datetime(datetime_str):
    datetime_patern = r'\d{4}\-\d{2}\-\d{2}'
    matches = re.findall(datetime_patern, datetime_str)
    print(f'matches {matches}')
    if matches:
        datetime_str = matches[0]

        parsed_datetime = datetime.datetime.strptime(datetime_str, '%Y-%m-%d')

        return parsed_datetime.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return ''



def calculate_category_id(category1, category2, category3):
    # 여성 = 1
    category_id = 98
    if category1 == '여성':
        #  '탐' = 7
        if  '탐' in category2 or  '티' in category2 or '상의' in category2:
            if  '셔츠' in category2 or '티셔츠' in category2 or  '남방' in category2:
               category_id = 11
               return category_id
            if  '블라우스' in category2 or 'BLOUSE' in category2:
               category_id = 10
               return category_id
            if  '니트' in category2 or 'Knit' in category2 or  'knit' in category2:
               category_id = 9
               return category_id
        # outer = 20
        if   '아우터' in category2 or  "OUTER" in category2:
            if   '원피스/세트' in category3 or  '원피스' in category3:
               category_id = 21
               return category_id
            if  '조끼' in category3 or '조기' in category3:
               category_id = 15
               return category_id
            if   '가디건' in category3 or 'Cardigan' in category3:
               category_id = 14
               return category_id
            if   '재킷' in category3 or '자켓' in category3 or   'jacket' in category3:
               category_id = 13
               return category_id
            if   '패딩/점퍼' in category3 or  '패딩' in category3 or   '점퍼' in category3:
               category_id = 16
               return category_id
            if   '코트' in category3 or   'coat' in category3 or   'Coat' in category3:
               category_id = 17
               return category_id
           
        if   '하의' in category2 or   'BOTTOM' in category2 or   'bottom' in category2:
            if   '스커트' in category3:
                category_id = 25
                return category_id
            if   '바지' in category3:
                category_id = 27
            if   '청비지' in category3 or  'Jean' in category3:
                category_id = 28
            if   '점프수트' in category3:
                category_id = 29
                return category_id
            if   '레깅스' in category3: 
                category_id = 30
                return category_id
        elif  '빅사이즈' in category3:
            category_id = 32
            return category_id
        elif  '비치웨어' in category1:
            category_id = 33
            return category_id
           
    elif '남성' in category1:
        if  '상의' in category2 or  'Top' in category2:
            if  '셔츠' in category3 or  '티셔츠' in category3 or  '남방' in category3:
                category_id = 40
                return category_id
            if  '블라우스' in category3 or  'BLOUSE' in category3:
                category_id = 19
                return category_id
            if  '니트' in category3 or  'Knit' in category3 or  'knit' in category3:
                category_id = 39
                return category_id
        elif  '하의' in category2:
            if  '바지' in category3:
                category_id = 42
                return category_id
            if  '청바지' in category3:
                category_id = 43
                return category_id
            if  '니트류' in category3:
                category_id = 44
                return category_id
        elif  '아우터' in category2:
            if   '재킷' in category3:
                category_id = 46
                return category_id
            if  '가디건' in category3:
                category_id = 47
                return category_id
            if  '코트' in category3:
                category_id = 50
                return category_id
            if  '조끼' in category3:
                category_id = 48
                return category_id
            if  '패딩/점퍼' in category3 or  '패딩' in category3:
                category_id = 49
                return category_id

            # 정장
        if  '정장' in category2:
            category_id = 52
            return category_id
    if   '유아동' in category1:
        if  '상의' in category2:
            if '셔츠' in category3 or '티셔츠' in category3 or '남방' in category3:
                category_id = 54
                return category_id
            if '블라우스' in category3 or 'BLOUSE' in category3 or '블라우스/ in category3셔츠':
                category_id = 61
                return category_id
            if '니트' in category3 or 'Knit' in category3 or 'knit' in category3:
                category_id = 56
                return category_id
        if  '하의' in category2:
            if '스커트' in category3:
                category_id = 62
                return category_id
            if '바지' in category3:
                category_id = 60
                return category_id
            
            if '니트류' in category3:
                category_id = 56
                return category_id
            
        if  '원피스/세트' in category2:
            if '원피스' in category3:
                category_id = 59
                return category_id
        if  '잡화' in category2:
            if '아동소품' in category3:
                category_id = 65
                return category_id
    if   '잡화' in category1:
        if  '가방' in category2:
            if '숄더백' in category3:
                category_id = 68
                return  category_id
            if '토트백' in category3:
                category_id = 67
                return category_id
            if '크로스백' in category3:
                category_id = 69
                return category_id
            if '클러치/지갑' in category3:
                category_id = 70
                return category_id
            if '백팩/힙색' in category3:
                category_id = 71
                return category_id
            if '기타' in category3:
                category_id = 72
                return category_id
            
    # TODO : shoes and accessories 
    return category_id


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



def job(store_name, max_day_ago = 30 * 2):


    # chrome option - 토르 테스트 중
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument("--proxy-server=socks5://127.0.0.1:9150")
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
    
    
    sql_products = "SELECT * FROM Products"

    cursor = conn.cursor()
    cursor.execute(sql_products)
    rows_products = cursor.fetchall()
    # last_prod_create_at = rows_products[-1][9]  # last updated product time
    print(rows_products)
    product_id = rows_products[-1][0] + 1 if len(list(rows_products)) > 0 else 1 
    
    sql_shops = "SELECT * FROM Shops"
    cursor.execute(sql_shops)
    rows_shops = cursor.fetchall()
    # shop_id = rows_shops[-1][0] + 1 if len(list(rows_shops)) > 0 else 1
    
    
    sql_styles = "SELECT * FROM Styles"
    cursor.execute(sql_styles)
    rows_styles = cursor.fetchall()
    style_id_dict = dict((y, x) for x, y in rows_styles)

    sql_productimages = "SELECT * FROM ProductImages"
    cursor.execute(sql_productimages)
    rows_productimages = cursor.fetchall()
    image_id = rows_productimages[-1][0] + 1 if len(list(rows_productimages)) > 0 else 1


    s3 = boto3.client(
        's3',
        aws_access_key_id = os.getenv('aws_access_key_id'),
        aws_secret_access_key = os.getenv('aws_secret_access_key'),
    )
    s3_domain = 'https://sokodress.s3.ap-northeast-2.amazonaws.com'

    folder_shops = 'linkshops_shops'
    folder_products_image = 'Products'
    create_folder(folder_products_image)
    create_folder(folder_shops)

    driver = webdriver.Chrome(service=Service(), options=chrome_options)
    # driver.get('https://www.linkshops.com/')


    # 회원 정보 입력 창 접속
    driver.get('https://www.linkshops.com/?signIn=')
    driver.implicitly_wait(10)
    time.sleep(2)
    
    # 로그인
    ID = 'waldoyun2@gmail.com'
    pwd = 'Linkshops9138!'
    driver.find_element(By.CLASS_NAME, 'input-wrapper').find_element(By.NAME, 'email').send_keys(ID)
    driver.find_element(By.CLASS_NAME, 'input-wrapper').find_element(By.NAME, 'password').send_keys(pwd)
    event_click(driver, driver.find_element(By.CLASS_NAME, 'login-modal-content-wrapper').find_element(By.ID, 'btn'))
    time.sleep(2)

    total_table_ProductImages = []

    # 매장(티엔씨) 접속
    if store_name is None:
        store_name = 'designbyjs'
        
    shop_link = f'https://www.linkshops.com/{store_name}'
    driver.get(shop_link)
    # driver.implicitly_wait(10)
    time.sleep(1)
    # 한국어 선택
    event_click(driver, driver.find_element(By.CLASS_NAME, 'left-menu-item'))
    time.sleep(0.5)
    event_click(driver, driver.find_elements(By.CLASS_NAME, 'dropdown-menu')[0])
    time.sleep(1)
    df_product = pd.DataFrame()

    #
    shop_name = driver.find_element(By.CLASS_NAME, 'title-container-title').find_element(By.CLASS_NAME, 'name').text
    print(f'shop_name {shop_name}')

    # try:
    #     select_shop = f'SELECT shop_id FROM Shops WHERE shop_name = {store_name}'
    #     cursor = conn.cursor()
    #     cursor.execute(select_shop, [store_name])
    #     shop_id = cursor.fetchone()
    #     print(f'shop id {shop_id}')
    #     conn.commit()
    #     # cursor.close()
    #     # conn.close()
    # except:
    #     shop_id = None
  
    # if shop_id is None:
    #     return
       
    sangga_and_address = driver.find_element(By.CLASS_NAME, 'brandTitleContainer-location-content').text

    sangga_name = sangga_and_address.split(' ')[0]
    
    shop_address = ' '.join(sangga_and_address.split(' ')[1:])

    # brandTitleContainer-location-content
    
    try:
        shop_phone = driver.find_element(By.CLASS_NAME, 'brandTitleContainer-phone-content').text
    except NoSuchElementException:
        shop_phone = ''

          

          
    if  check_duplicate_shop(store_name, rows_shops) is None:
        try:
            shop_create_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            slq_interto_shop = """INSERT INTO Shops (shop_name, address, sinsang_store_phone, shop_image,transactions, sanga_name, shop_link, main_items, create_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor = conn.cursor()
            shop_image = 'https://sokodress.s3.ap-northeast-2.amazonaws.com/ShopProfiles/shop_25232.png'
            shop_insert_data = (store_name, shop_address, shop_phone, shop_image, 0, sangga_name, shop_link, '주력 아이템', shop_create_at)
            print(shop_insert_data)
            cursor.execute(slq_interto_shop, shop_insert_data)
            conn.commit()
            shop_id = cursor.lastrowid

            print(f'inserted shop id {shop_id}')
            # cursor.close()
            # conn.close()
            
        except Exception as e:
            print(f'shop inserting error {e}')
    else:
        print('store already exists')   
        shop_id = check_duplicate_shop(store_name, rows_shops)
        pass     

        print(f'shop id {shop_id}')

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
    # driver.get(shop_link)
    # driver.implicitly_wait(10)
    # time.sleep(2)

    scrapped_product_count = 0

    start_time = time.time()

    for lp in range(last_page_num):
        print(f'last page number {last_page_num}')
        try:
            one_start_time = time.time()
            
            ONE_PAGE_FLAG = True

            driver.get(f'{shop_link}?pageNum={lp+1}')
            driver.implicitly_wait(10)
            time.sleep(2)

            FIRST_PRODUCT_SWITCH = True
            
            while ONE_PAGE_FLAG:
                print('one page flag')
                if FIRST_PRODUCT_SWITCH:
                    
                    print('first product switch')
                    
                    # 첫상품 클릭
                    
                    event_click(driver, driver.find_element(By.CLASS_NAME, 'center-container').\
                                               find_elements(By.CLASS_NAME, 'flex-container')[0].\
                                               find_element(By.CLASS_NAME, 'inner-wrap'))
                    FIRST_PRODUCT_SWITCH = False

                
                
                # 상품 정보
                original_create_at = None #상품 등록 날짜
                try:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '상품 번호')]")))
                    
                    if driver.find_element(By.XPATH, "//div[contains(text(), '상품 번호')]").text:
                        product_unique_id_and_create_at = driver.find_elements(By.CLASS_NAME, 'product-info-item')[3].text
                        
                        # original_create_at = product_unique_id_and_create_at.split('      ')[1].replace('업데이트(', '').replace(')', '')


                    date_pattern = r'\(\d{4}-\d{2}-\d{2}\)'
                    match = re.search(date_pattern, product_unique_id_and_create_at)

                    if match:
                        original_create_at = match.group(0)[1:-1]  # Remove the parentheses
                    else:
                        print("Date not found in the text.")
                except:
                    original_create_at = None
                    time.sleep(2)
                    
                    # 상품 다음 > 클릭
                    try:
                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-product-next')))

                        if driver.find_element(By.CLASS_NAME, 'modal-product-next-button.next').find_element(By.CLASS_NAME, 'icon-product-next'):
                            # time.sleep(5)
                            event_click(driver, driver.find_element(By.CLASS_NAME, 'modal-product-next-button.next').\
                                            find_element(By.CLASS_NAME, 'icon-product-next'))
                            print(f'shop id {shop_id}')
                            print("다음 상품 >")

                    except NoSuchElementException:
                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-product-modal-close')))

                        print("스킵 후 끝")
                        event_click(driver, driver.find_element(By.CLASS_NAME, 'icon-product-modal-close'))
                        ONE_PAGE_FLAG = False
                        
                    finally:
                        time.sleep(1)
                        # continue
                    
                print(f'original create at {original_create_at}')
                
                try: 
                    if original_create_at is None or check_product_register_date(original_create_at, max_day_ago) is False:
                        time.sleep(1)
                        if driver.find_element(By.CLASS_NAME, 'modal-product-next-button.next').find_element(By.CLASS_NAME, 'icon-product-next'):
                            event_click(driver, driver.find_element(By.CLASS_NAME, 'modal-product-next-button.next').\
                                            find_element(By.CLASS_NAME, 'icon-product-next'))
                            
                        print("다음 상품 >>>>>>>")
                        continue
                except Exception as e:
                    print(e)
                    if driver.find_element(By.CLASS_NAME, 'modal-product-next-button.next').find_element(By.CLASS_NAME, 'icon-product-next'):
                            event_click(driver, driver.find_element(By.CLASS_NAME, 'modal-product-next-button.next').\
                                            find_element(By.CLASS_NAME, 'icon-product-next'))

                # else: 
                
                try:
                    original_create_at = parse_datetime(original_create_at)
                    pass  
                except Exception as e:
                    original_create_at = None
                    if driver.find_element(By.CLASS_NAME, 'modal-product-next-button.next').find_element(By.CLASS_NAME, 'icon-product-next'):
                            event_click(driver, driver.find_element(By.CLASS_NAME, 'modal-product-next-button.next').\
                                            find_element(By.CLASS_NAME, 'icon-product-next'))
                
                print(f'original create at {original_create_at}')
                
                try:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '카테고리')]")))
                    
                    if driver.find_element(By.XPATH, "//div[contains(text(), '카테고리')]").text:
                        product_category = driver.find_elements(By.CLASS_NAME, 'product-info-item')[4].text # '잡화,패션아이템,헤어핀/밴드/브로치,쥬얼리/시계'
                        product_category = product_category.replace('카테고리\n', '')
                        product_category = product_category.split(' > ')
                        
                        print(f"product_category {product_category}")

                        # product_category = ','.join(product_category)
                        category_id = calculate_category_id(product_category[0], product_category[1],  product_category[2])
                        product_category_1, product_category_2, product_category_3 = category_classification(product_category)
                except:
                    product_category_1 = None
                    product_category_2 = None
                    product_category_3 = None

                try:
                    element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '상품명')]")))
                    
                    if driver.find_element(By.XPATH, "//div[contains(text(), '상품명')]").text:
                        product_name = driver.find_elements(By.CLASS_NAME, 'product-info-item')[5].text
                        product_name = product_name.replace('상품명\n', '')
                except:
                    product_name = None
                    
                try:
                    nation = driver.find_element(
                    By.XPATH, "//*[@id='product-modal-container']/div[2]/div[1]/div[2]/div[1]/div/div[8]/div[2]").text
                    print(f'nation ->>> {nation}')
                    
                except Exception as e:
                    print(f'nation error {e}')
                    nation = ''

                    
                if check_duplicate_product(product_name, rows_products) is True:
                        time.sleep(1.2)
                        print('check duplicate')
                        event_click(driver, driver.find_element(By.CLASS_NAME, 'modal-product-next-button.next').\
                                            find_element(By.CLASS_NAME, 'icon-product-next'))
                        print("다음 상품 >")
                        continue
                    
                else:
                    print('not duplicate')
                    pass

                try:
                    element = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '소재/혼용률')]")))
                    
                    if driver.find_element(By.XPATH, "//div[contains(text(), '소재/혼용률')]").text:
                        product_maxrate = driver.find_elements(By.CLASS_NAME, 'product-info-item')[6].text
                        product_maxrate = product_maxrate.replace('소재/혼용률\n', '').replace(', ', ',')
                except:
                    product_maxrate = None

                # 세탁방법이 있는게 있고 없는게 있어서 달라짐
                try:
                    element = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '세탁방법')]")))
                    
                    if driver.find_element(By.XPATH, "//div[contains(text(), '세탁방법')]").text:
                        product_fabric = driver.find_elements(By.CLASS_NAME, 'product-info-item')[7].text
                        product_fabric = product_fabric.replace('세탁방법\n', '').replace(' / ', ',')
                        
                    element = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '원산지')]")))

                    if driver.find_element(By.XPATH, "//div[contains(text(), '원산지')]").text:
                        product_made = driver.find_elements(By.CLASS_NAME, 'product-info-item')[8].text

                    element = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '낱장여부')]")))
                    
                    if driver.find_element(By.XPATH, "//div[contains(text(), '낱장여부')]").text:
                        product_is_unit = driver.find_elements(By.CLASS_NAME, 'product-info-item')[9].text 
                    
                    element = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '도매판매가')]")))

                    if driver.find_element(By.XPATH, "//div[contains(text(), '도매판매가')]").text:
                        product_price = driver.find_elements(By.CLASS_NAME, 'product-info-item')[10].text

                except:
                    product_fabric = None
                    
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '원산지')]")))
                    product_made = driver.find_elements(By.CLASS_NAME, 'product-info-item')[7].text
                    
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '낱장여부')]")))
                    product_is_unit = driver.find_elements(By.CLASS_NAME, 'product-info-item')[8].text 
                    
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '도매판매가')]")))
                    product_price = driver.find_elements(By.CLASS_NAME, 'product-info-item')[9].text

                finally:
                    product_made = product_made.replace('원산지\n', '')
                    product_is_unit = product_is_unit.replace('낱장여부\n', '')
                    product_price = int(re.sub(r'[^0-9]', '', product_price))
                
                try:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'product-option-select')))
                    color_and_size = driver.find_element(By.CLASS_NAME, 'product-option-select').text

                    product_color = color_and_size.split('\n사이즈\n')[0]
                    product_color = product_color.replace('색상\n', '').replace('\n', ',')
                    
                    product_size = color_and_size.split('\n사이즈\n')[1]
                    product_size = product_size.replace('\n', ',')
                except:
                    product_color = None
                    product_size = None
                try:
                    if driver.find_element(By.CLASS_NAME, 'product-detail-info-title').text == '피팅 정보':
                        fit_list = []
                        for i in driver.find_element(By.CLASS_NAME, 'product-info-table').find_elements(By.TAG_NAME, 'tr'):
                            fit_list.append(fitting_info(i))

                        product_fitting = fit_list[0]
                        product_thickness = fit_list[1]
                        product_elasticity = fit_list[2]
                        product_seethrough = fit_list[3]
                        product_lining = fit_list[4]
                        product_gloss = fit_list[5]
                        product_touch = fit_list[6]
                        product_banding = fit_list[7]
                
                except:
                    product_fitting = None
                    product_thickness = '보통'
                    product_elasticity = '보통'
                    product_seethrough = '약간'
                    product_lining = '기모안감'
                    product_gloss = None
                    product_touch = None
                    product_banding = None
                
                try:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'slick-slide')))

                    slick_hidden = driver.find_element(By.CLASS_NAME, 'slick-initialized.slick-slider.productProductModalThumbnailSlider').\
                                        find_element(By.CLASS_NAME, 'slick-track').\
                                        find_elements(By.CLASS_NAME, 'slick-slide')

                    for idx, i in enumerate(slick_hidden):
                        img_ele = i.find_element(By.CLASS_NAME, 'img').get_attribute('style')
                        img_ele = img_ele.split('url("')[1].split('");')[0]
                        img_ele = image_resize_url(img_ele)
                        image_path = f'./Products/{product_id}_{image_id}.jpeg'
                        
                        urlretrieve(f'https:{img_ele}', image_path)
                        # downloadImage(img_ele, image_path)
                        image_url = upload_image(s3,product_id,image_id)

                        table_product_images = (
                            str(product_id),
                            f'{str(product_id)}_{str(image_id)}',
                            image_url
                        )
                        
                        total_table_ProductImages.append(table_product_images)
                        os.remove(image_path)
                        image_id += 1

                    
                except Exception as e:
                    print(f'product image error {e}')
                    continue
                    
                try:
                    prod_name_en = papago_translate(product_name)
                except Exception as e: 
                    prod_name_en = product_name
                                   

                table_ProductOptions = (
                        # str(product_option_id),  # autoincrement
                        str(product_id),
                        product_size,  # size
                        product_color,  # color
                        original_create_at,
                    )
                
                print(f'nation before ======>>>> {nation}')

                nation = calculate_nation(nation)

                print(f'nation after ======>>>> {nation}')
                
                table_Products = (
                        str(product_id),  # autoincrement
                        str(shop_id),  
                        product_name,
                        prod_name_en, # 일단 임의로
                        str(product_price),# 일단 임의로
                        str(product_price),# 일단 임의로
                        str(product_price),# 일단 임의로
                        nation, #nation
                        "T",
                        # None,  # contents,
                        product_maxrate,
                        # False,
                        "캐주얼", #style
                        product_category_1,
                        product_category_2,
                        shop_link,
                        str(5), # #star
                    )
                

                table_CategoryOfProduct = (
                        # str(category_of_product_id), # autoincrement
                        category_id,
                        str(product_id)
                    )
                

                table_FabricInfos = (
                        # str(fabric_id),  # autoincrement
                        str(product_id),
                        '기본핏',  # 핏정보(not null)
                        product_thickness,  # 두께감    
                        product_elasticity,  # 신축성
                        product_seethrough,  # 비침
                        product_lining,  # 안감
                        '없음',  # 광택('없음'으로)
                        '보통',  # 촉감('보통'으로)
                        '없음'  # 밴딩('없음'으로)
                )
                
                table_WashInfos = (
                                # str(wash_info_id),  # autoincrement
                                str(product_id),
                                product_fabric  # category 라고 써져 있는데 세탁 정보
                            )

                table_ProductStyles = (
                        # str(product_style_id),  # autoincrement
                        str(product_id),
                        str(1) #style_id
                )
                print(f'table_ProductStyles {table_ProductStyles}')
                time.sleep(1)
        
                try:
                    
                    print('inserting start...')
                    
                    sql_products = """INSERT IGNORE INTO Products (
                                product_id,
                                shop_id,
                                prod_name,
                                prod_name_en,
                                team_price,
                                real_price,
                                price,
                                nation,
                                is_unit,
                                maxrate,
                                style,
                                category1,
                                category2,
                                prod_link,
                                star)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

                    cursor.execute(sql_products, table_Products)
                    
                    conn.commit()
                
                    sql_productimages = """INSERT INTO ProductImages (
                                                        product_id,
                                                        image_name,
                                                        image_url)
                                                        VALUES ( %s, %s, %s)"""
                    cursor.executemany(sql_productimages, total_table_ProductImages)
                    conn.commit()
                    
                    total_table_ProductImages = []
                    
                    sql_categoryofproducts = """INSERT INTO CategoryOfProduct (
                                            category_id,
                                            product_id)
                                            VALUES (%s, %s)"""
                    
                    cursor.execute(sql_categoryofproducts, table_CategoryOfProduct)
                    conn.commit()
                    sql_fabricinfos = """INSERT INTO FabricInfos (
                                                product_id,
                                                핏정보,
                                                두께감,
                                                신축성,
                                                비침,
                                                안감,
                                                광택,
                                                촉감,
                                                밴딩)
                                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

                    cursor.execute(sql_fabricinfos, table_FabricInfos)
                    conn.commit()


                    sql_productoptions = """INSERT INTO ProductOptions (
                                                                product_id,
                                                                size,
                                                                color,
                                                                original_create_at )
                                                                VALUES ( %s, %s, %s, %s)"""
                                                                 
                    cursor.execute(sql_productoptions, table_ProductOptions)
                    conn.commit()
                    
                    
                    sql_washinfos = """INSERT INTO WashInfos (
                                                        product_id, 
                                                        category)
                                                        VALUES ( %s, %s)"""
                                                    
                    cursor.execute(sql_washinfos, table_WashInfos)
                    conn.commit()

                    sql_productstyles = """INSERT INTO ProductStyles (product_id, style_id)
                                                            VALUES (%s, %s)"""
                    # cur.executemany(sql_productstyles, total_table_ProductStyles)
                    cursor.execute(sql_productstyles, table_ProductStyles)
                    conn.commit()
                   
                    product_id += 1
                    # cursor.close()
                    # conn.close()
                    
                except pymysql.Error as e:
                    
                    print(f'something went wrong {e}')  
                # 상품 다음 > 클릭
                try:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-product-next')))

                    if driver.find_element(By.CLASS_NAME, 'modal-product-next-button.next').find_element(By.CLASS_NAME, 'icon-product-next'):
                        # time.sleep(5)
                        event_click(driver, driver.find_element(By.CLASS_NAME, 'modal-product-next-button.next').\
                                                   find_element(By.CLASS_NAME, 'icon-product-next'))
                        print("다음 상품 >")
                        
                        scrapped_product_count += 1

                except NoSuchElementException:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-product-modal-close')))
                    
                    print("한 페이지 크롤링 끝")
                    event_click(driver, driver.find_element(By.CLASS_NAME, 'icon-product-modal-close'))
                    ONE_PAGE_FLAG = False

                finally:
                    time.sleep(5)
                    
                    # <div class="img" style="background-image: url(&quot;//thumbs.cdn.linkshops.com/thumbs/20211102/480/6fef7cb0-3bb8-11ec-a643-1552bbc0ef37.jpg&quot;); background-size: contain; background-repeat: no-repeat; background-color: black; background-position: center center;"></div>

            # one_result_time = str(datetime.timedelta(seconds=time.time()-one_start_time)).split('.')[0]
            # print(f"한 페이지 도는 시간: {one_result_time}")
                    

        except Exception as e:
            print(f"하다 끊겨서 저장 {e}")
            # now_time = datetime.datetime.today().strftime('%Y%m%d_%H%M')
            # df_product.to_csv(f'./{folder_shops}/{shop_name}.csv', index=False)
            # df_product.to_csv(f'./{folder_shops}/{shop_name}_fail.csv', index=False)
            

            # df_product.to_csv(f'./{folder_shops}/{shop_name}.csv', index=False)        

    print("크롤링 완료")
    # df_product['product_all_cnt'] = product_all_cnt
    # df_product.to_csv(f'{folder_shops}/{shop_name}.csv', index=False)
    result_time = str(datetime.timedelta(seconds=time.time()-start_time)).split('.')[0]
    print(f"runtime: {result_time}")
    cursor.close()
    conn.close()
    driver.close()


@router.post('/test')
def mupliple_prods_excecute():
    conn = pymysql.connect(
        host=os.getenv('host'),
        port=3306,
        user=os.getenv('user'),
        passwd=os.getenv('passwd'),
        db=os.getenv('db'),
        charset='utf8mb4',
    )

    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM ScrapingShops WHERE type = 'linkshop' ")
        shops = cur.fetchall()
        cur.execute("SELECT * FROM ScrapingAccounts WHERE type = 'linkshop' ")
        accounts = cur.fetchall()

        # return shops[-1][-1]
        for shop in shops: 
            
            shop_id = shop[3]
            days_ago = shop[-1]
            print(days_ago)
            print(shop_id)
            job(shop_id)
            
            time.sleep(1000 * 5)
            
    except pymysql.Error as e:
        cur.close()
        conn.close()
        return f'something went wrong {e}'
        