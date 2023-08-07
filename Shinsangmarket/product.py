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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
# from flask_cors import CORS, cross_origin
# from flask import Flask, request, jsonify, Response
# from flask_restful import reqparse, abort, Api, Resource
import json
from fastapi import APIRouter

router = APIRouter( tags=['sinsang'], responses={404: {"description": "Not found"}})

options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.add_argument('--start-maximized')

# app = Flask(__name__)
# cors = CORS(app)
# app.config['CORS_HEADERS'] = 'Content-Type'

def create_folder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            
    except OSError:
        print(f"Error: Creating directory {directory}")
create_folder('./Products')

# @app.route('/call', methods=['GET','POST'])
# @cross_origin()

@router.get('/{store_id}/{days_ago}')
def predict_code(store_id: int, days_ago:int):   
	# store_id = (request.args.get('store_id'))
	# days_ago = int(request.args.get('days_ago'))
    # print(f'{store_id}')

	return (model_predict(store_id, days_ago))

def model_predict(store_id, days_ago):
    
    global driver
    driver = webdriver.Chrome(service=Service(), options=options)
    # driver  = webdriver.Chrome(options=options)
    
    s3 = boto3.client(
        's3',
        aws_access_key_id = 'AKIAXHNKF4YFB6E7I7OI',
        aws_secret_access_key = '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',
    )

    conn = pymysql.connect(
        host='52.79.173.93',
        port=3306,
        user='user',
        passwd='seodh1234',
        db='sokodress',
        charset='utf8'
    )

    cur = conn.cursor()
    sql_shops = "SELECT * FROM Shops"
    cur.execute(sql_shops)
    rows_shops = cur.fetchall()

    # print(type(store_id), type(days_ago))
    for row_shop in rows_shops:
        if row_shop[14] == int(store_id): # sinsang_store_id
            shop_id = row_shop[0]
            print(shop_id)
            
    sql_products = "SELECT * FROM Products"
    cur.execute(sql_products)
    rows_products = cur.fetchall()
    product_id = rows_products[-1][0] + 1

    sql_categoryofproduct = "SELECT * FROM CategoryOfProduct"
    cur.execute(sql_categoryofproduct)
    rows_categoryofproduct = cur.fetchall()
    category_of_product_id = rows_categoryofproduct[-1][0] + 1

    sql_fabricinfos = "SELECT * FROM FabricInfos"
    cur.execute(sql_fabricinfos)
    rows_fabricinfos = cur.fetchall()
    fabric_id = rows_fabricinfos[-1][0] + 1

    sql_productoptions = "SELECT * FROM ProductOptions"
    cur.execute(sql_productoptions)
    rows_productoptions = cur.fetchall()
    product_option_id = rows_productoptions[-1][0] + 1

    sql_washinfos = "SELECT * FROM WashInfos"
    cur.execute(sql_washinfos)
    rows_washinfos = cur.fetchall()
    wash_info_id = rows_washinfos[-1][0] + 1

    sql_productstyles = "SELECT * FROM ProductStyles"
    cur.execute(sql_productstyles)
    rows_productstyles = cur.fetchall()
    product_style_id = rows_productstyles[-1][0] + 1

    sql_styles = "SELECT * FROM Styles"
    cur.execute(sql_styles)
    rows_styles = cur.fetchall()
    style_id_dict = dict((y, x) for x, y in rows_styles)

    sql_productimages = "SELECT * FROM ProductImages"
    cur.execute(sql_productimages)
    rows_productimages = cur.fetchall()
    image_id = rows_productimages[-1][0] + 1

    driver.get("https://sinsangmarket.kr/login")
    time.sleep(1)
    driver.save_screenshot('screenie.png')
    
    # 로그인
    
    #새로운 계정 
    ID = 'bong2692'
    PASSWORD = 'sinsang4811!'
    # ID = 'rayout2022'
    # PASSWORD = 'elesther2022!'
    # driver.find_element(By.XPATH,'//*[@id="app"]/div[1]/div/header/div/div[2]/div[3]').click()
    driver.execute_script('arguments[0].click();', driver.find_element(By.XPATH,'//*[@id="app"]/div[1]/div/header/div/div[2]/div[3]'))
    driver.find_elements(By.CLASS_NAME,'text-input')[0].send_keys(ID)
    driver.find_elements(By.CLASS_NAME,'text-input')[1].send_keys(PASSWORD)
    # driver.find_element(By.CLASS_NAME, 'px-\[6px\].leading-none.mb-\[12px\].font-bold.contained').click()
    # driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'px-\[6px\].leading-none.mb-\[12px\].font-bold.contained'))
    login_button = driver.find_element(By.XPATH, '//*[@id="app"]/div/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/button')
    login_button.click()
    time.sleep(1)

    # 언어 선택(English)
    driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'select-area__arrow'))
    driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'flag-icon.flag-icon--en'))
    time.sleep(1)

    wait = WebDriverWait(driver, 5)
    actions = ActionChains(driver)

    driver.get(f'https://sinsangmarket.kr/store/{store_id}')
    
    # delay time till 3 seconds
    time.sleep(3)
    # time.sleep(1.5)

    now = datetime.datetime.now()
    standard_date_ago = now - datetime.timedelta(days=days_ago)

    total_table_Products = []
    total_table_CategoryOfProduct = []
    total_table_FabricInfos = []
    total_table_ProductOptions = []
    total_table_WashInfos = []
    total_table_ProductStyles = []
    total_table_ProductImages = []

    category1_dict = {
        "Women's Clothing": '여성 의류', "Men's Clothing": '남성 의류', "Children's Clothing": '유아 의류'
    }

    style_dict = {
        # 여성
        'Romantic': '로맨틱', 'Lady-like': '미시', 'Madame': '마담', 'Office look': '오피스', 'Sexy': '섹시', 
        # 남성
        'Dandy': '댄디', 'Suit': '수트', 'Classic': '클래식', 'Hip-hop': '힙합', 'Japanese Style': '니뽄',
        # 유아
        'Lovely': '러블리', 'Nordic': '북유럽', 'Simple': '심플', 'Modern': '모던', 'Cute': '큐티', 'Cozy / Relax': '이지', 'Vintage': '빈티지', 'Trendy': '트렌드', 'Couple': '커플',
        # 공통(최소 2개)
        'Casual': '캐주얼', 'Simple/Basic': '심플/베이직', 'Luxurious': '럭셔리', 'Unique': '유니크', 'Premium brand style': '명품스타일',
        'Urban/Modern': '어반/모던', 'Celebrity': '연예인', 'Chic': '시크'
    }

    category2_dict = {
        'Outer': '아우터', 'T-shirts&Tops': '티&탑', 'Dresses': '원피스', 'Blouses': '블라우스', 'Knitwear': '니트',
        'Jeans': '청바지', 'Pants': '팬츠', 'Skirts': '스커트', 'Sales': '세일상품', 'In Season': '시즌상품',
        'Set Products': '세트 아이템', 'Shirts': '셔츠/남방', 'Plus Size': '빅사이즈', 'Maternity Clothing': '임부복',
        'Suit': '수트', 'T-shirts/Tops': '티/탑', 'Top&Bottom': '상하세트'
    }

    nation_dict = {
        'South Korea': '대한민국',
        'China': '중국',
        'Others': '기타'
    }
    
    fabric_dict = {
        # 두께감
        'Thick': '두꺼움',  'Thin': '얇음',
        # 신축성
        'High': '좋음', 
        # 비침

        # 안감
        'Fleece-lined': '기모안감',
        # 공통
        'Mid': '보통', 'None': '없음', 'Yes': '있음'
    }

    wash_dict = {
        'Wash separately': '단독세탁', 'Dry clean': '드라이클리닝', 'Wool wash': '울세탁',
        'Hand wash': '손세탁', 'Machine wash': '물세탁', 'Do not machine wash': '세탁기 금지',
        'Do not bleach': '표백제 사용 금지', 'Do not iron': '다리미 사용 금지'
        # 물세탁 금지, 세탁기 사용 가능, 기계건조 금지, 비틀기 금지 - 안보임
    }

    def calculate_category_id(prod_name, c_big, c_small):
        # level_3 = ''
        
        # 여성 의류
        if c_big == "Women's Clothing": #'여성 의류'
            # level_1 = '1'
            # TOP 탑 '7'
            if c_small == "T-shirts&Tops": #'티&탑':
                if '니트' in prod_name:
                    level_3 = '9'
                    return level_3
                elif '후드' in prod_name:
                    level_3 = '18'
                    return level_3
                else:
                    level_3 = '8'
                    return level_3

            elif c_small == "Knitwear": #'니트':
                if '가디건' in prod_name:
                    level_3 = '14'
                    return level_3
                elif '조끼' in prod_name:
                    level_3 = '15'
                    return level_3
                else:
                    level_3 = '9'
                    return level_3

            elif c_small == "Blouses": #'블라우스':
                level_3 = '10'
                return level_3

            elif c_small == "Shirts": #'셔츠/남방':
                level_3 = '11'
                return level_3
            
            # OUTER 아우터 '12'
            elif c_small == "Outer": #'아우터':
                if '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name:
                    level_3 = '13'
                    return level_3
                elif '가디건' in prod_name:
                    level_3 = '14'
                    return level_3
                elif '조끼' in prod_name:
                    level_3 = '15'
                    return level_3
                elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name:
                    level_3 = '16'
                    return level_3
                elif '코트' in prod_name:
                    level_3 = '17'
                    return level_3
                elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
                    level_3 = '18'
                    return level_3
                # elif '' in prod_name: # 망토/숄/판쵸 거의 없는 듯
                #     level_3 = ''
                    # return level_3
                else:
                    level_3 = '12'
                    return level_3

            # DRESS 드레스 '20'
            elif c_small == "Dresses": #'원피스':
                if '세트' in prod_name or '셋트' in prod_name:
                    level_3 = '22'
                    return level_3
                elif '니트' in prod_name:
                    level_3 = '23'
                    return level_3
                else:
                    level_3 = '21'
                    return level_3

            elif c_small == "Set Products": #'세트 아이템':
                level_3 = '22'
                return level_3

            # BOTTOM 하의
            elif c_small == "Skirts": #'스커트':
                level_3 = '25'
                return level_3

            elif c_small == "Pants": #'팬츠':
                if '레깅스' in prod_name:
                    level_3 = '30'
                    return level_3
                elif '슬랙스' in prod_name or '슬렉스' in prod_name:
                    level_3 = '26'
                    return level_3
                elif '점프수트' in prod_name or '점프슈트' in prod_name:
                    level_3 = '29'
                    return level_3
                else:
                    level_3 = '27'
                    return level_3

            elif c_small == "Jeans": #'청바지':
                if '점프수트' in prod_name or '점프슈트' in prod_name:
                    level_3 = '29'
                    return level_3
                else:
                    level_3 = '28'
                    return level_3

            # +MORE
            elif c_small == "Plus Size": #'빅사이즈':
                level_3 = '32'
                return level_3

            elif c_small == "Maternity Clothing": #'임부복':
                level_3 = '34'
                return level_3

            if '파자마' in prod_name or '잠옷' in prod_name or '속옷' in prod_name:
                level_3 = '33'
                return level_3

            if '비키니' in prod_name or '수영복' in prod_name or '레쉬가드' in prod_name or '비치웨어' in prod_name \
            or '래시가드' in prod_name or '래쉬가드' in prod_name:
                level_3 = '36'
                return level_3

            if '스포츠' in prod_name or '골프' in prod_name:
                level_3 = '35'
                return level_3

            else:
                level_3 = '98'
                return level_3

        # 남성 의류
        elif c_big == "Men's Clothing": #'남성 의류'
            # level_1 = '2'

            # TOP '37'
            if c_small == "Shirts": #'티&탑':
                level_3 = '38'
                return level_3
            elif c_small == "Knitwear": #'니트':
                level_3 = '39'
                return level_3
            elif c_small == "Shirts": #'셔츠/남방':
                level_3 = '40'
                return level_3

            # BOTTOM '41'
            elif c_small == "Pants": #'팬츠':
                if '니트' in prod_name:
                    level_3 = '44'
                    return level_3
                else:
                    level_3 = '42'
                    return level_3

            elif c_small == "Jeans": #'청바지':
                level_3 = '43'
                return level_3

            # OUTER '45'
            elif c_small == "Outer": #'아우터':
                if '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name:
                    level_3 = '46'
                    return level_3
                elif '가디건' in prod_name:
                    level_3 = '47'
                    return level_3
                elif '조끼' in prod_name:
                    level_3 = '48'
                    return level_3
                elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name:
                    level_3 = '49'
                    return level_3
                elif '코트' in prod_name:
                    level_3 = '50'
                    return level_3
                elif '후드' in prod_name or '집업' in prod_name or '판쵸' in prod_name:
                    level_3 = '51'
                    return level_3
                else:
                    level_3 = '45'
                    return level_3

            # SUIT '52'
            elif c_small == "Suit": #'수트':
                level_3 = '53'
                return level_3

            else:
                level_3 = '98'
                return level_3

        # 유아 의류
        elif c_big == "Children's Clothing": #'유아 의류'
            # level_1 = '3'
            if c_small == "Outer": #'아우터':
                level_3 = '55'
                return level_3
            elif c_small == "Knitwear": #'니트':
                level_3 = '56'
                return level_3
            elif c_small == "T-shirts/Tops": #'티/탑':
                level_3 = '57'
                return level_3
            elif c_small == "Jeans": #'청바지':
                level_3 = '58'
                return level_3
            elif c_small == "Dresses": #'원피스':
                level_3 = '59'
                return level_3
            elif c_small == "Pants": #'팬츠':
                level_3 = '60'
                return level_3
            elif c_small == "Blouses": #'블라우스':
                level_3 = '61'
                return level_3
            elif c_small == "Skirts": #'스커트':
                level_3 = '62'
                return level_3
            elif c_small == "Suit": #'정장세트':
                level_3 = '63'
                return level_3
            elif c_small == "In Season": #'시즌':
                level_3 = '64'
                return level_3
            # elif c_small == '': # Kids Goods
                # level_3 = ''
                # return level_3
            else:
                level_3 = '98'
                return level_3

        else:
            level_3 = '98'
            return level_3

    def calculate_is_unit(contents_text):
        contents_text = contents_text.split('\n')
        contents_text = [x for x in contents_text if x]
        
        for i in contents_text:
            i = i.replace(' ', '')
            # print(i)
            if '첫주문' in i or '첫거래' in i or '첫품목' in i or '첫구매' in i:
                if '낱장거래는하지않아요' in i:
                    is_unit = 'F'
                    # print("[LOG] 걸렸나?")
                    break
                
                else:
                    is_unit = 'T'
                    # print("[LOG] 1")
                    break
                
            else:
                if '낱장' in i:
                    if '불가능' in i:
                        is_unit = 'F'
                        # print("[LOG] 2")
                        break

                    elif '안' in i or '불가' in i:
                        is_unit = 'F'
                        # print("[LOG] 3")
                        break
                        
                    elif '가능' in i:
                        is_unit = 'T'
                        # print("[LOG] 4")
                        break
                    
                    else:
                        is_unit = 'T'
                        # print("[LOG] 5")
                        break
                
                elif '최소' in i and ('2장' in i or '3장' in i or '4장' in i or '5장' in i or '6장' in i):
                    is_unit = 'F'
                    # print("[LOG] 이건 뭐냐")
                    break

                else:
                    # print("[LOG] 아무것도 걸리지 않음")
                    is_unit = 'T'
            
        return is_unit

    category_list = [1, 2, 11] # 여성 의류, 남성 의류, 유아 의류

    for c in category_list:
        element = wait.until(EC.presence_of_element_located((By.XPATH, f'//*[@id="{store_id}"]/div/div[3]/div/div[1]/aside/div[3]/div[2]/ul[{c}]/li')))
        # CLASS_NAME : category-list__name
        category = driver.find_element(By.XPATH, f'//*[@id="{store_id}"]/div/div[3]/div/div[1]/aside/div[3]/div[2]/ul[{c}]/li') 
        goods_category = driver.find_element(By.XPATH, f'//*[@id="{store_id}"]/div/div[3]/div/div[1]/aside/div[3]/div[2]/ul[{c}]/li').text
        # print(f"1. [goods_category] : {goods_category}")
        driver.execute_script('arguments[0].click();', category)
        
        clothes_list = driver.find_element(By.XPATH, f'//*[@id="{store_id}"]/div/div[3]/div/div[1]/aside/div[3]/div[2]/ul[{c}]').\
                            find_element(By.TAG_NAME, 'div').find_elements(By.TAG_NAME, 'li')
        
        for clo in range(1, len(clothes_list)):
            if c == 11:
                if clo >= 11 and clo <= 16 or clo == 18 or clo == 19:
                    continue
            
            element = wait.until(EC.presence_of_element_located((By.XPATH, f'//*[@id="{store_id}"]/div/div[3]/div/div[1]/aside/div[3]/div[2]/ul[{c}]/div/li[{clo+1}]')))
            clothes = driver.find_element(By.XPATH, f'//*[@id="{store_id}"]/div/div[3]/div/div[1]/aside/div[3]/div[2]/ul[{c}]/div/li[{clo+1}]')
            goods_clothes = driver.find_element(By.XPATH, f'//*[@id="{store_id}"]/div/div[3]/div/div[1]/aside/div[3]/div[2]/ul[{c}]/div/li[{clo+1}]').text
            # print(f'2. [goods_clothes] : {goods_clothes}')

            driver.execute_script('arguments[0].click();', clothes)
            
            if clo == 1:
                driver.execute_script('arguments[0].click();', category)      
            
            actions.move_to_element(driver.find_element(By.CLASS_NAME, 'color-title.title')).perform()
            
            # 스타일
            try:
                driver.execute_script('arguments[0].click();', driver.find_element(By.CSS_SELECTOR, 'button.list-more'))
                time.sleep(0.2)
            except Exception as e:
                pass    
                
            # style_list = driver.find_element(By.CSS_SELECTOR, 'ul.style__filter-list').find_elements(By.CSS_SELECTOR, 'span.block.flex.items-center')
            style_list = driver.find_element(By.CLASS_NAME, 'style__filter-list').find_elements(By.TAG_NAME, 'button')

            for sty in range(1, len(style_list)):
                style_element = driver.find_element(By.CLASS_NAME, 'style__filter-list').find_elements(By.TAG_NAME, 'button')[sty]
                style = style_element.text
                #style
                style = style_dict[style]
                # style_id
                style_id = style_id_dict[style]
                
                driver.execute_script('arguments[0].click();', style_element)                                  
                # print(f">>> {style}")
                
                for _ in range(2):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(0.1)
                
                goods_list = driver.find_elements(By.XPATH, '//div[@data-group="goods-list"]')
                driver.execute_script("window.scrollTo(0, 1000)")                     
                
                if len(goods_list) == 0:
                    continue
                
                for goo in range(len(goods_list)):
                    driver.execute_script("window.scrollTo(0, 1000)")                     
                    driver.execute_script('arguments[0].click();', driver.find_elements(By.XPATH, '//div[@data-group="goods-list"]')[goo])
                    
                    # create_at
                    try:
                        element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Updated at')]/following-sibling::div")))
                        create_at = driver.find_element(By.XPATH, "//div[contains(text(), 'Updated at')]/following-sibling::div").text
                    except Exception as e:
                        create_at = ''
                        print("[LOG] 등록일 X!")
                    
                    # 날짜가 days_ago보다 더 크면 break
                    if 'Boosted' in create_at:
                        if 'hours' in create_at or 'minutes' in create_at:
                            pass
                        elif 'year' in create_at:
                            driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'close-button'))
                            break
                        elif 'days' in create_at:
                            if int(re.sub(r'[^0-9]', '', create_at.split('\n')[1])) < days_ago:
                                pass
                            else:
                                driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'close-button'))
                                break
                        else:
                            print(f"[LOG] 등록일: {create_at}")
                    
                    elif datetime.datetime.strptime(create_at.split(' ')[0],'%Y.%m.%d') < standard_date_ago:
                        # driver.find_element(By.CLASS_NAME, 'close-button').click()
                        driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'close-button'))
                        break
                    
                    else:
                        pass
                    
                    # 위의 날짜 계산이 끝나면 입력할 create_at로 변환
                    if create_at != '':
                            create_at = create_at.split(' ')[0].replace('.', '-')
                    
                    # prod_link
                    try:
                        prod_id = driver.find_elements(By.XPATH, '//div[@data-group="goods-list"]')[goo].get_attribute('data-gid')
                        prod_link = f'https://sinsangmarket.kr/goods/{prod_id}'
                    except Exception as e:
                        prod_link = ''
                    
                    # prod_name
                    try:
                        prod_name = driver.find_element(By.XPATH, '//div[@class="goods-detail-right__row"]').find_element(By.CSS_SELECTOR, 'p.title').text
                    except Exception as e:
                        prod_name = ''
                    
                    # real_price, price, team_price
                    try:
                        # goods_price = driver.find_element(By.XPATH, '//*[@id="goods-detail"]').find_element(By.CSS_SELECTOR, 'div.price.flex.items-center').text
                        goods_price = driver.find_element(By.CLASS_NAME, 'price.flex.items-center').find_element(By.CLASS_NAME, 'ml-\[2px\]').text
                        goods_price = re.sub(r'[^0-9]', '', goods_price)
                        real_price = price = team_price = goods_price
                    except Exception as e:
                        goods_price = ''
                    
                    # star
                    try:
                        star = driver.find_element(By.XPATH, '//*[@id="goods-detail"]').find_element(By.CSS_SELECTOR, 'p.zzim-button__count').text
                    except Exception as e:
                        star = '0'
                    
                    # is_sold_out
                    try:
                        add_to_cart_button = driver.find_element(By.CLASS_NAME, 'flex-grow').find_element(By.CLASS_NAME, 'ssm-button').\
                                                    find_element(By.TAG_NAME, 'button').get_attribute('class')
                        if 'disabled' in add_to_cart_button:
                            is_sold_out = '1'
                        else:
                            is_sold_out = '0'
                    except Exception as e:
                        is_sonld_out = '0'
                    
                    # ProductImages
                    try:
                        for i in range(len(driver.find_elements(By.XPATH, '//img[@alt="thumbnail-image"]'))):
                            goods_src = driver.find_elements(By.XPATH, '//img[@alt="thumbnail-image"]')[i].get_attribute('src')
                            urlretrieve(goods_src, f'./Products/{product_id}_{i}.jpg')
                                
                            s3.upload_file(
                                f'./Products/{product_id}_{i}.jpg',
                                'sokodress',
                                f'Products/{product_id}_{i}.jpg',
                                ExtraArgs={'ACL':'public-read'}
                            )
                        
                            image_url = f'https://sokodress.s3.ap-northeast-2.amazonaws.com/Products/{product_id}_{i}.jpg'
                            # https://sokodress.s3.ap-northeast-2.amazonaws.com/ShopProfiles/img_test1.png
                            table_ProductImages = (
                                str(image_id), # autoincrement
                                str(product_id),
                                f'{str(product_id)}_{str(i)}', # image_name(not null), 
                                image_url
                            )
                            
                            total_table_ProductImages.append(table_ProductImages)
                            image_id += 1
                    except Exception as e:
                        print("[LOG] S3 Upload Error")

                    # category1
                    try:
                        category1 = driver.find_elements(By.XPATH, "//div[contains(text(), 'Categories')]/following-sibling::div/div")[0].text
                        
                    except Exception as e:
                        category1 = ''

                    # category2
                    try:
                        category2 = driver.find_elements(By.XPATH, "//div[contains(text(), 'Categories')]/following-sibling::div/div")[1].text
                        
                    except Exception as e:
                        category2 = ''

                    # color
                    try:
                        color = driver.find_element(By.XPATH, "//div[contains(text(), 'Colors')]/following-sibling::div").text
                    except Exception as e:
                        color = ''

                    # size
                    try:
                        size = driver.find_element(By.XPATH, "//div[contains(text(), 'Size')]/following-sibling::div").text
                    except Exception as e:
                        size = ''
                    
                    # maxrate
                    try:
                        maxrate = driver.find_element(By.XPATH, "//div[contains(text(), 'Proposition')]/following-sibling::div").text
                    except Exception as e:
                        maxrate = ''
                    
                    # nation
                    try:
                        nation = driver.find_element(By.XPATH, "//div[contains(text(), 'Origin')]/following-sibling::div").text
                        nation = nation_dict[nation]
                    except Exception as e:
                        nation = ''
                    
                    # is_unit
                    try:
                        contents_text = driver.find_element(By.CLASS_NAME, 'mb-\[80px\]').find_element(By.CLASS_NAME, 'row__content').text
                        if contents_text == 'No details.':
                            is_unit = 'T'
                        else:
                            is_unit = calculate_is_unit(contents_text)
                    except Exception as e:
                        is_unit = 'T'
        
                    # goods_laundry
                    try:
                        laundry_elements = driver.find_elements(By.CSS_SELECTOR, 'div.laundry-item__name')
                        for i in laundry_elements:
                            goods_laundry = i.text
                            goods_laundry = wash_dict[goods_laundry]
                        
                            table_WashInfos = (
                                str(wash_info_id), # autoincrement
                                str(product_id),
                                goods_laundry # category 라고 써져 있는데 세탁 정보
                            )

                            total_table_WashInfos.append(table_WashInfos)
                            wash_info_id += 1
                    except Exception as e:
                        goods_laundry = ''
                    
                    # goods_fabric_thickness
                    try:
                        goods_fabric_thickness = [x for x in driver.find_elements(By.XPATH, "//div[contains(text(), 'Thickness')]/following-sibling::div/div/div") if x.get_attribute('class')=='min-w-[42px] text-gray-100'][0].text
                        goods_fabric_thickness = fabric_dict[goods_fabric_thickness]
                    except Exception as e:
                        goods_fabric_thickness = ''

                    # goods_fabric_seethrough
                    try:
                        goods_fabric_seethrough = [x for x in driver.find_elements(By.XPATH, "//div[contains(text(), 'Transparency')]/following-sibling::div/div/div") if x.get_attribute('class')=='min-w-[42px] text-gray-100'][0].text
                        goods_fabric_seethrough = fabric_dict[goods_fabric_seethrough]
                    except Exception as e:
                        goods_fabric_seethrough = ''
                    
                    # goods_fabric_elasticity
                    try:
                        goods_fabric_elasticity = [x for x in driver.find_elements(By.XPATH, "//div[contains(text(), 'Elasticity')]/following-sibling::div/div/div") if x.get_attribute('class')=='min-w-[42px] text-gray-100'][0].text
                        goods_fabric_elasticity = fabric_dict[goods_fabric_elasticity]
                    except Exception as e:
                        goods_fabric_elasticity = ''
                    
                    # goods_fabric_lining
                    try:
                        goods_fabric_lining = [x for x in driver.find_elements(By.XPATH, "//div[contains(text(), 'Lining')]/following-sibling::div/div/div") if x.get_attribute('class')=='min-w-[42px] text-gray-100'][0].text
                        goods_fabric_lining = fabric_dict[goods_fabric_lining]
                    except Exception as e:
                        goods_fabric_lining = ''
                    
                    # category_id
                    category_id = calculate_category_id(prod_name, category1, category2)
                    
                    category1 = category1_dict[category1]
                    
                    for key, value in category2_dict.items():
                        if c == 10 and category2 == 'Suit':
                            category2 = '정장세트'
                        elif key == category2:
                            category2 = value

                    table_Products = (
                        str(product_id), # autoincrement
                        str(shop_id), # 일단 임의로
                        prod_name,
                        real_price,
                        price,
                        team_price,
                        nation,
                        is_unit,
                        None, # contents,
                        create_at,
                        maxrate,
                        is_sold_out,
                        style,
                        category1,
                        prod_link,
                        category2,
                        star
                    )
                    
                    table_CategoryOfProduct = (
                        str(category_of_product_id), # autoincrement
                        category_id,
                        str(product_id)
                    )
                    
                    table_FabricInfos = (
                        str(fabric_id), # autoincrement
                        str(product_id),
                        '기본핏', # 핏정보(not null)
                        goods_fabric_thickness, # 두께감
                        goods_fabric_elasticity, # 신축성
                        goods_fabric_seethrough, # 비침
                        goods_fabric_lining, # 안감
                        '없음', # 광택('없음'으로)
                        '보통', # 촉감('보통'으로)
                        '없음' # 밴딩('없음'으로)
                    )
                    
                    table_ProductOptions = (
                        str(product_option_id), # autoincrement
                        str(product_id),
                        size, # size
                        color # color
                    )
                    
                    table_ProductStyles = (
                        str(product_style_id), # autoincrement
                        str(product_id),
                        str(style_id)
                    )
                    
                    total_table_Products.append(table_Products)
                    total_table_CategoryOfProduct.append(table_CategoryOfProduct)
                    total_table_FabricInfos.append(table_FabricInfos)
                    total_table_ProductOptions.append(table_ProductOptions)
                    total_table_ProductStyles.append(table_ProductStyles)
                    
                    product_id += 1
                    category_of_product_id += 1
                    fabric_id += 1
                    product_option_id += 1
                    product_style_id += 1

                    element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'close-button')))
                    # driver.find_element(By.CLASS_NAME, 'close-button').click()
                    driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'close-button'))
                    # time.sleep(0.5)
                    
            # print("========")    

    sql_products = """INSERT IGNORE INTO Products (product_id, shop_id, prod_name, real_price, price, team_price, nation, is_unit,
                                                contents, create_at, maxrate, is_sold_out, style, category1, prod_link, category2, star)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    cur.executemany(sql_products, total_table_Products)
    conn.commit()

    sql_categoryofproducts = """INSERT INTO CategoryOfProduct (category_of_product_id, category_id, product_id)
                                                    VALUES (%s, %s, %s)"""
    cur.executemany(sql_categoryofproducts, total_table_CategoryOfProduct)
    conn.commit()

    sql_fabricinfos = """INSERT INTO FabricInfos (fabric_id, product_id, 핏정보, 두께감, 신축성, 비침, 안감, 광택, 촉감, 밴딩)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    cur.executemany(sql_fabricinfos, total_table_FabricInfos)
    conn.commit()

    sql_productoptions = """INSERT INTO ProductOptions (product_option_id, product_id, size, color)
                                                VALUES (%s, %s, %s, %s)"""
    cur.executemany(sql_productoptions, total_table_ProductOptions)
    conn.commit()

    sql_washinfos = """INSERT INTO WashInfos (wash_info_id, product_id, category)
                                    VALUES (%s, %s, %s)"""
    cur.executemany(sql_washinfos, total_table_WashInfos)
    conn.commit()

    sql_productstyles = """INSERT INTO ProductStyles (product_style_id, product_id, style_id)
                                            VALUES (%s, %s, %s)"""
    cur.executemany(sql_productstyles, total_table_ProductStyles)
    conn.commit()

    sql_productimages = """INSERT INTO ProductImages (image_id, product_id, image_name, image_url)
                                            VALUES (%s, %s, %s, %s)"""
    cur.executemany(sql_productimages, total_table_ProductImages)
    conn.commit()

    driver.quit()

    log_message = {'Message':'Success insert db(goods)'}
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
 
 