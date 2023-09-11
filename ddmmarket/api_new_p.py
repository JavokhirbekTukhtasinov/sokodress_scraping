# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# ■■■■■■■■■■■■■■■ ddmmarket data crawling ■■■■■■■■■■■■■■■
# ■■■■■■■■■■■■■ http://www.ddmmarket.co.kr/ ■■■■■■■■■■■■■
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

# ■■■■■■■■■■■■■■■■ Library ■■■■■■■■■■■■■■■■
import math
import os
import time
import re
import pickle
import boto3
import pymysql
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
# from flask_cors import CORS, cross_origin
# from flask import Flask, request, jsonify, Response
# from flask_restful import reqparse, abort, Api, Resource
import json
import numpy as np
import schedule



# ■■■■■■■■■■■■■■■■ define external function ■■■■■■■■■■■■■■■■
# 폴더 생성
def create_folder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print(f'[ERROR] 폴더 생성 실패 : {directory}')

# FabricInfos 테이블 - 핏정보, 신축성, 비침, 안감

def fabric_info(x):
    if '■' not in x:
        x = None
    else:
        for idx, d in enumerate(x):
            if d == '■':
                x = x[idx+1]
                break
    return x


# CategoryOfProduct - category_id 정의
def product_category_classification(product):
    # WOMEN 7 ~ 36, level 2: 7, 12, 20, 24, 31

    # 괄호 데이터 처리(수집한 데이터 내에서)
    # bracket_word = re.sub('\([^)]*\)', '', product)
    bracket_word = re.compile('\(([^)]+)').findall(product)
    bracket_word = ''.join(bracket_word)
    
    if ('레깅스' in bracket_word):
        x = '하의'
        y = '레깅스'
        
    elif ('긴소매' in bracket_word):
        x = '탑'
        y = '티/탑'
        
    else:    
        product = re.sub('\([^)]*\)', '', product) # (내용) 제거
        product = product.upper() # 대문자화
        product = product.strip() # 양끝 공백 제거

        # ■■■■■■■■■■■■■■■■ 먼저 필터링할 것 ■■■■■■■■■■■■■■■■
        if ('세트' in product) or ('셋트' in product) or ('SET' in product) or \
            ('셋업' in product):
            x = '드레스'
            y = '셋트' # SET
            
        elif ('잠옷' in product) or (product.endswith('파자마')) or (product.endswith('파자마셋')):
            x = '더보기' # '33'
            y = '파자마/이너웨어' # Pajama/Innerwear

        elif (product.endswith('원피스')) or (product.endswith('원피스2')) or (product.endswith('OPS')) or \
            (product.endswith('OPS2')) or (product.endswith('드레스')):
            x = '드레스'
            y = '원피스' # Dress

        # ■■■■■■■■■■■■■■■■ 상의 ■■■■■■■■■■■■■■■■
        elif (product.endswith('자켓')) or (product.endswith('쟈켓')) or (product.endswith('JK')) or \
        (product.endswith('자켓110')):
            x = '아우터'
            y = '자켓' # Jacket

        elif (product.endswith('조끼')) or ('VEST' in product) or ('VT' in product):
            x = '아우터'
            y = '조끼' # Vest 15

        elif ('셔츠' in product) or ('남방' in product) or ('NB' in product) or \
            (product.endswith('ST')) or (product.endswith('SH')):
            x = '탑'
            y = '셔츠/남방' # Shirts 11

        elif (product.endswith('티')) or (product.endswith('나시')) or (product.endswith('반팔')) or \
            (product.endswith('반팔T')) or ('MTM' in product) or ('MTOM' in product) or \
            (product.endswith('맨투맨')) or (product.endswith('티셔츠')):
            x = '탑'
            y = '티/탑' # Tee/Top 8

        elif (product.endswith('가디건')) or (product.endswith('가디간')) or (product.endswith('CD')):
            x = '아우터'
            y = '가디건' # Cardigan 14

        elif ('JP' in product) or ('점퍼' in product) or (product.endswith('J.P')) or \
            (product.endswith('패딩')) or (product.endswith('PD')):
            x = '아우터'
            y = '패딩/점퍼' # Padding/Jumper 16
            
        elif ('점프' in product): # 블루리본 18JSS-36A 같은 것 때문에 일단 JS 미포함
            x = '하의'
            y = '점프수트' # JumpSuit 29

        elif (product.endswith('BL')) or (product.endswith('블라우스')):
            x = '탑'
            y = '블라우스' # Blouse 10

        # ■■■■■■■■■■■■■■■■ 하의(대부분) ■■■■■■■■■■■■■■■■
        elif ('치마' in product) or ('스커트' in product) or ('SK' in product) or ('SKT' in product):
            x = '하의'
            y = '스커트' # Skirts 25

        elif ('슬랙스' in product) or ('슬렉스' in product) or ('SL' in product):
            x = '하의'
            y = '슬렉스' # Slacks 26
        
        elif ('레깅스' in product):
            x = '하의'
            y = '레깅스' # 30
            
        elif (product.endswith('청바지')) or (product.endswith('데님')) or (product.endswith('청PT')):
            x = '하의'
            y = '청바지' # Jean 28
            
        elif (product.endswith('바지')) or (product.endswith('PT')) or (product.endswith('팬츠')) or \
            (product.endswith('PA')) or (product.endswith('PANTS')):
            x = '하의'
            y = '바지' # Pants 27

        elif (product.endswith('코트')) or (product.endswith('COAT')) or (product.endswith('CT')):
            x = '아우터'
            y = '코트' # Coat 17

        elif ('후드' in product) or ('후디' in product) or (product.endswith('HD')) or (product.endswith('사파리')):
            x = '아우터'
            y = '후드/집업/사파리' # Hood/Zip-up/Safari 18

        elif ('판쵸' in product) or (product.endswith('숄')): # '숄' 기준 잡기 어려움
            x = '아우터'
            y = '망토/숄/판쵸' # Cloak/Shawl/Poncho 19
            
        elif (product.endswith('T')) or (product.endswith('V')) or (product.endswith('Y')): # 수정 필요
            x = '탑'
            y = '티/탑' # '8'
            
        elif (product.endswith('니트')):
            x = '탑'
            y = '니트'

        else:
            x = '기타' # 미분류된 것
            y = None

    return x, y

# 매장 고정 기입 카테고리
def shops_hold_category(x): # 여성
    if (x == 'DB2G150042') or (x == 'CB1GA30C35') or (x == 'D1D1000460') or (x == 'C5LA525237') or (x == 'NZ12230029'): # 그루, 한나네, 낫씽베러, 폴링제이, 보니타
        x = '드레스'
        y = '원피스' # '21' # Dress(원피스)
    elif (x == 'DWP2320474'): # 라인
        x = '탑'
        y = '티/탑' # '8' # Tee/Top
    elif (x == 'D2G1700317'): # 비키
        x = '하의'
        y = '슬렉스' # '26' # Slacks
    elif (x == 'C3NA180483'): # 더이태리
        x = '하의'
        y = '바지' # '27' # Pants
    elif (x == 'Q215300310') or (x == 'DB2N301265') or (x == 'D3E2100443'): # 바닐라제이, 피노키오, 데님부티크
        x = '하의'
        y = '청바지' # '28' # Jean
    elif (x == 'D1J1800328'): # 보따리
        x = '탑'
        y = '니트' # '9'
    elif (x == 'DB2D300037'): # 페이퍼
        x = '하의'
        y = '스커트' # '25' # Skirts
    elif (x == 'C2KA350516'): # 제이엠
        x = '아우터'
        y = '후드/집업/사파리' # '18' # Hood/Zip-uip/Safari
    elif (x == 'NZB1207434'): # 시엘(뉴존)
        x = '더보기'
        y = '임부복' # '34' # Maternity(임부복)
    else:
        x = False
        y = False
    
    return x, y

# 데이터 db 네이밍 형식에 맞게 수정
def df_db_convert_name(df):
    # df.loc[df['product_fitting']=='베이직', 'product_fitting'] = '기본핏'
    # df.loc[df['product_seethrough']=='약간비침', 'product_seethrough'] = '약간'
    # df.loc[df['product_seethrough']=='비침', 'product_seethrough'] = '있음'
    df = df.replace('', None)
    df = df.where((pd.notnull(df)), None)

    return df


def job():
    # ■■■■■■■■■■■■■■■■ AWS(EC2, S3) connecting ■■■■■■■■■■■■■■■■
    # AWS S3 login
    s3 = boto3.client(
        's3',
        aws_access_key_id = 'AKIAXHNKF4YFB6E7I7OI',
        aws_secret_access_key = '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',
    )

    s3_domain = 'https://sokodress.s3.ap-northeast-2.amazonaws.com'

    # AWS EC2 login
    conn = pymysql.connect(
        host='52.79.173.93',
        port=3306,
        user='user',
        passwd='seodh1234',
        db='sokodress',
        charset='utf8'
    )

    cur = conn.cursor()


    # ■■■■■■■■■■■■■■■■ Selenium ■■■■■■■■■■■■■■■■
    # selenium.common.exceptions.WebDriverException: Message: unknown error: net::ERR_SOCKS_CONNECTION_FAILED
    # 위 에러??
    # PROXY = '172.31.41.146:5001'
    # webdriver.DesiredCapabilities.CHROME['proxy'] = {
    #     "httpProxy": PROXY,
    #     "ftpProxy": PROXY,
    #     "sslProxy": PROXY,
    #     "proxyType": "MANUAL",
    # }

    # webdriver.DesiredCapabilities.CHROME['acceptSslCerts'] = True


    # chrome option
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--proxy-server=socks5://127.0.0.1:9150")
    chrome_options.add_argument('--mute-audio')
    chrome_options.add_argument('disable-gpu')
    chrome_options.add_argument('lang=ko')
    # chrome_options.add_argument('user-agent=User_Agent: Mozilla/5.0 \(Windows NT 10.0; Win64; x64\) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])



    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    # 로그인
    driver.get('https://www.ddmmarket.co.kr/Login')
    driver.implicitly_wait(10)
    time.sleep(2) # 2
    DDMMARKET_ID = 'sokodress'
    DDMMARKET_PASSWORD = 'ddmmarket9138'
    driver.find_element(By.ID, 'login_frame1').find_element(By.ID, 'user_id').send_keys(DDMMARKET_ID)
    driver.find_element(By.ID, 'login_frame1').find_element(By.ID, 'user_pwd').send_keys(DDMMARKET_PASSWORD)
    driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'login_btn'))
    driver.implicitly_wait(10)
    time.sleep(2) # 2

    # crawling shop list
    basic_domain = 'http://www.ddmmarket.co.kr/Prod?m=S&c='

    # shops_link_list = [
    #     'T111400510', # 가나다
    #     'DB2G150042', # 그루
    #     'D1D1000460', # 낫씽베러
    #     'C3NA180483', # 더이태리
    #     'D3E2100443', # 데님부티크
    #     'DWP2320474', # 라인
    #     'NZB1109525', # 르방
    #     'T441700118', # 멋쟁이
    #     'CB1NA24367', # 미코앤코
    #     'Q215300310', # 바닐라제이
    #     'NZ12230029', # 보니타
    #     'D1J1800328', # 보따리
    #     'D2G1700317', # 비키
    #     'NZB1207434', # 시엘
    #     'APM2120427', # 이프하우스
    #     'D111000174', # 인레이먼트
    #     'C4C4090361', # 제이슈트어트(드레스코드)
    #     'C2KA350516', # 제이엠
    #     'C3RA450034', # 지영
    #     'C1DA120467', # 커피샤워
    #     'U153000240', # 팰리스
    #     'D4H1000435', # 퍼플
    #     'JP21400015', # 페니블루
    #     'DB2D300037', # 페이퍼
    #     'C5LA525237', # 폴링제이
    #     'C2NA110492', # 프로
    #     'DB2N301265', # 피노키오
    #     'CB1GA30C35', # 한나네
    #     'D3I1300101', # 해커
    #     'C2KA540430' # 호박씨
    # ]

    shops_link_list = [
        'DB2N301265', # 피노키오
        'CB1GA30C35', # 한나네

        'T111400510', # 가나다
        'NZB1109525', # 르방
        'T441700118', # 멋쟁이
        'CB1NA24367', # 미코앤코
        'APM2120427', # 이프하우스
        'D111000174', # 인레이먼트
        'C4C4090361', # 제이슈트어트(드레스코드)
        'C3RA450034', # 지영
        'C1DA120467', # 커피샤워 

        'U153000240', # 팰리스
        'D4H1000435', # 퍼플
        'JP21400015', # 페니블루
        'C2NA110492', # 프로
        'D3I1300101', # 해커
        'C2KA540430', # 호박씨

        'DB2G150042', # 그루
        'D1D1000460', # 낫씽베러
        'C3NA180483', # 더이태리
        'D3E2100443', # 데님부티크
        'DWP2320474', # 라인
        'Q215300310', # 바닐라제이

        'NZ12230029', # 보니타
        'D1J1800328', # 보따리
        'D2G1700317', # 비키
        'NZB1207434', # 시엘
        'C2KA350516', # 제이엠
        'DB2D300037', # 페이퍼
        'C5LA525237', # 폴링제이   
    ]

    folder_products_image = 'products_image1'
    folder_shops = 'shops1'
    folder_backup = 'backup'

    create_folder(folder_products_image)
    create_folder(folder_shops)
    create_folder(folder_backup)
    create_folder(f"{folder_backup}/{folder_shops}")

    # now_date = datetime.datetime.today().strftime("%Y%m%d_%H%M")

    print("■■■■■■■■■■■■■■■■ START ■■■■■■■■■■■■■■■■")
    start_time = time.time()

    # 링크별 크롤링
    # for c_link in tqdm(shops_link_list, desc='[Crawling tqdm] 매장별 링크', position=0, leave=True):
    for c_link in shops_link_list:
        try:      
            if shops_hold_category(c_link)[0]:
                SHOPS_HOLD_SWITCH = True
            else:
                SHOPS_HOLD_SWITCH = False

            driver.get(f"{basic_domain}{c_link}")
            driver.implicitly_wait(10)
            time.sleep(5)
            
            df_product = pd.DataFrame()

            # try:
            #     element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'totalItem2')))
            #     product_all_case = int(driver.find_element(By.ID, 'totalItem2').text)
            #     driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'all_check').find_element(By.TAG_NAME, 'label'))
            #     time.sleep(10)# 5
            # except:
            #     print("[인식 불가] 모든 상품 수")
            
            try:
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'totalItem2')))
                product_cate_case = int(driver.find_element(By.ID, 'totalItem2').text)
                driver.get(f"{basic_domain}{c_link}")
                driver.implicitly_wait(10)
                time.sleep(10) # 5
                print(f"카테고리 상품 수: {product_cate_case}")
            except:
                print("[인식 불가] 카테고리 상품 수")

            driver.get(f"{basic_domain}{c_link}")
            driver.implicitly_wait(10)
            time.sleep(10) # 5
            
            category_len = 10
            
            PRODUCT_SWITCH_1 = False

            # 카테고리 체크박스 반복
            for cate_len_idx in range(category_len):
                if cate_len_idx != 0:
                    driver.get(f"{basic_domain}{c_link}")
                    driver.implicitly_wait(10)
                    time.sleep(10)
                
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'label')))
                driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'info_check').\
                                    find_elements(By.TAG_NAME, 'li')[cate_len_idx].find_element(By.TAG_NAME, 'label'))
                time.sleep(10)

                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'span')))
                product_checkbox_category = driver.find_element(By.CLASS_NAME, 'info_check').find_elements(By.TAG_NAME, 'li')[cate_len_idx].\
                                    find_element(By.TAG_NAME, 'label').find_element(By.TAG_NAME, 'span').text
                
                # [다음페이지 계속] 클릭
                try:
                    while True:
                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'next_page')))
                        driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'next_page'))
                        time.sleep(10) # 5
                        if 'none' in driver.find_element(By.CLASS_NAME, 'next_page').get_attribute('style'):
                            break
                except:
                    print("[ERROR] [다음페이지 계속] 클릭 오류")

                try:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'open_pro.ellipsis')))
                    product_len = len(driver.find_element(By.ID, 'mygoodslist').find_elements(By.CLASS_NAME, 'open_pro.ellipsis'))
                except:
                    # print(f"카테고리 체크박스 다음 클릭")
                    continue
                
                # 상품 검색 반복
                # for product_len_idx in tqdm(range(product_len), desc='[Crawling tqdm] 카테고리별 상품들', position=1, leave=False):
                for product_len_idx in range(product_len):
                    try:
                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'open_pro.ellipsis')))
                        driver.execute_script('arguments[0].click();', driver.find_element(By.ID, 'mygoodslist').\
                                            find_elements(By.CLASS_NAME, 'open_pro.ellipsis')[product_len_idx])    
                        time.sleep(10)

                        if PRODUCT_SWITCH_1:
                            pass

                        else:
                            try:
                                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'pro_name')))
                                shop_info = driver.find_element(By.ID, 'pro_name').text
                                sangga_name, shop_name, shop_address, shop_phone = None, None, None, None
                                
                                sangga_name = shop_info.split('\n')[1].split('/')[0].strip()
                                shop_name = shop_info.split('\n')[1].split('/')[1].strip()
                                shop_address = shop_info.split('\n')[2].replace('주소:', '').strip()
                                shop_phone = shop_info.split('\n')[3].strip()
                                # print(shop_name)
                                
                                if sangga_name and shop_name and shop_address and shop_phone:
                                    PRODUCT_SWITCH_1 = True
                                    print("shop 정보 수집 확인")

                            except:
                                pass

                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'pro_name')))
                        product_info = driver.find_element(By.ID, 'pro_name').text        
                        product_unique_id = str(re.sub(r'[^0-9]', '', (product_info.split('\n')[0].split(']')[0] + ']').strip()))

                        sql_products = "SELECT * FROM Products"
                        cur.execute(sql_products)
                        rows_products = cur.fetchall()
                        
                        DUPLICATE_PRODUCT_SWITCH = False
                        # 이미 DB에 있는 상품은 스킵
                        for rp in rows_products:
                            if product_unique_id == rp:
                                DUPLICATE_PRODUCT_SWITCH = True
                                break
                        if DUPLICATE_PRODUCT_SWITCH:
                            continue

                        product_name = product_info.split('\n')[0].split(']')[1].strip()
                        # print(f"product_name: {product_name}")

                        # 상품 정보가 중복되서 나올 경우(정상은 li 10개)
                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'li')))
                        if len(driver.find_element(By.ID, 'pro_info').find_elements(By.TAG_NAME, 'li')) != 10:
                            continue

                        time.sleep(5)
                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'li')))
                        product_price = driver.find_element(By.ID, 'pro_info').find_elements(By.TAG_NAME, 'li')[0].text
                        product_price = int(re.sub(r'[^0-9]', '', product_price).strip())

                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'li')))
                        product_made = driver.find_element(By.ID, 'pro_info').find_elements(By.TAG_NAME, 'li')[2].text
                        if '한국' in product_made:
                            product_made = '대한민국'
                        elif '중국' in product_made:
                            product_made = '중국'
                        elif '원산지' in product_made:
                            product_made = None
                        else:
                            pass

                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'li')))
                        product_style = driver.find_element(By.ID, 'pro_info').find_elements(By.TAG_NAME, 'li')[3].text
                        product_style = product_style.replace('스타일\n', '').strip()
                        
                        if '스타일' in product_style:
                            product_style = None

                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'li')))
                        product_size = driver.find_element(By.ID, 'pro_info').find_elements(By.TAG_NAME, 'li')[4].text
                        product_size = product_size.replace('상세사이즈\n', '').strip()

                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'li')))
                        product_maxrate = driver.find_element(By.ID, 'pro_info').find_elements(By.TAG_NAME, 'li')[6].text
                        product_maxrate = product_maxrate.replace('혼용율\n', '').strip()

                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'li')))
                        detail_info = driver.find_element(By.ID, 'pro_info').find_elements(By.TAG_NAME, 'li')[7].text
                        detail_info = detail_info.split('\n')

                        # 비침, 신축성, 안감, 피팅감
                        product_seethrough = fabric_info(detail_info[1].split())
                        # if '약간비침' in product_seethrough:
                        #     product_seethrough = '약간'
                        # elif '비침' in product_seethrough:
                        #     product_seethrough = '있음'

                        product_elasticity = fabric_info(detail_info[2].split())
                        product_lining = fabric_info(detail_info[3].split())
                        product_fitting = fabric_info(detail_info[4].split())
                        # if '베이직' in product_fitting:
                        #     product_fitting = '기본핏'

                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'csTxtCode')))
                        product_color = [elem.get_attribute('value').replace(', FREE', '').strip() for elem in driver.find_elements(By.ID, 'csTxtCode')[1:]]
                        product_color = ','.join(product_color)

                        product_image_url = []
                        cnt = 0

                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'div')))
                        thumbnail_ele = driver.find_element(By.ID, 'gd_listimg').find_elements(By.TAG_NAME, 'div')            

                        for th_ele in thumbnail_ele:  

                            print(f'product ele {th_ele}')             

                            if th_ele.get_attribute('style') == 'text-align: center; padding-top: 55px;':
                                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'img')))
                                product_src = th_ele.find_element(By.TAG_NAME, 'img').get_attribute('src')
                                urlretrieve(product_src, f'./{folder_products_image}/{product_unique_id}_{cnt}.jpg')
                                s3.upload_file(
                                    f'./{folder_products_image}/{product_unique_id}_{cnt}.jpg', # 로컬
                                    'sokodress', # AWS S3
                                    f'{folder_products_image}/{product_unique_id}_{cnt}.jpg', # AWS S3 파일 저장 주소
                                    ExtraArgs={'ACL':'public-read'}
                                )

                                # e.g. https://sokodress.s3.ap-northeast-2.amazonaws.com/Test/sample1.jpg
                                product_image_url.append(f'{s3_domain}/{folder_products_image}/{product_unique_id}_{cnt}.jpg') # ./ 루트로 쓰면 절대 안됨
                                cnt += 1
                        product_image_url = ','.join(product_image_url)

                        if SHOPS_HOLD_SWITCH:
                            product_category_2 = shops_hold_category(c_link)[0]
                            product_category_3 = shops_hold_category(c_link)[1]

                        else:
                            product_category_2 = product_category_classification(product_name)[0]
                            product_category_3 = product_category_classification(product_name)[1]

                        df_product_one = pd.DataFrame({
                            'shop_name': [shop_name],
                            'sizang_name': ['동대문'],
                            'sangga_name':  [sangga_name],
                            'shop_address': [shop_address],
                            'shop_phone': [shop_phone],
                            'product_cate_case': [product_cate_case],
                            'product_unique_id': [product_unique_id],
                            'product_name': [product_name],
                            'product_checkbox_category': [product_checkbox_category],
                            'product_category_1': ['여성 의류'],
                            'product_category_2': [product_category_2],
                            'product_category_3': [product_category_3],
                            'product_price': [product_price],
                            'product_made': [product_made],
                            'product_image_url': [product_image_url],
                            'product_style': [product_style],
                            'product_size': [product_size],
                            'product_maxrate': [product_maxrate],
                            'product_seethrough': [product_seethrough],
                            'product_elasticity': [product_elasticity],
                            'product_lining': [product_lining],
                            'product_fitting': [product_fitting],
                            'product_color': [product_color],
                            'product_link': [f"{basic_domain}{c_link}"]
                        })

                        df_product = pd.concat([df_product, df_product_one], ignore_index=True)
                        
                    except:
                        print(f"[EXCEPT] shop_name: {shop_name}, product_name: {product_name}")
                        print(f"[EXCEPT] product_len_idx: {product_len_idx}")

                    finally:
                        try:
                            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'close')))
                            driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'close'))
                            time.sleep(10) # 5
                        except UnexpectedAlertPresentException:
                            print("[ERROR] 엉뚱한 font 에러.. 재현도 잘 안되고 이유도 알 수 없다.")
                            pass
                driver.get(f"{basic_domain}{c_link}")
                driver.implicitly_wait(10)
                time.sleep(10) # 5
            
            df_product = df_db_convert_name(df_product)
            df_product.to_csv(f'./{folder_shops}/{shop_name}.csv', index=False)
            now_time = datetime.datetime.today().strftime('%Y%m%d_%H%M')
            df_product.to_csv(f'./{folder_backup}/{folder_shops}/{shop_name}_{now_time}.csv', index=False)

            s3.upload_file(
                f'./{folder_shops}/{shop_name}.csv', # 로컬
                'sokodress',
                f'{folder_shops}/{shop_name}.csv',
                ExtraArgs={'ACL':'public-read'}
            )

            for f in glob("./products_image1/*.jpg"):
                try:
                    os.remove(f)
                except OSError as e:
                    print("f[ERROR] {f} {e.strerror}")

        except:
            continue


    driver.quit()

    end_time = time.time()
    result_time = datetime.timedelta(seconds=end_time-start_time)
    result_time = str(result_time).split(".")[0]
    print("■■■■■■■■■■■■■■■■ END ■■■■■■■■■■■■■■■■")
    print(f"code running time: {result_time}")


schedule.every(3).days.at("15:00").do(job)

# schedule.every().day.at("08:37").do(job) # day 날마다

# schedule.every(42).hours.at("08:00").do(job)
# schedule.every(42).hours.do(job) # day 날마다
# schedule.every(2).days.at("08:36").do(job)


while True:
    schedule.run_pending()
    time.sleep(10) # 3

job()