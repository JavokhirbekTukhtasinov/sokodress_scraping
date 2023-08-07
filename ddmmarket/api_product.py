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
from flask_cors import CORS, cross_origin
from flask import Flask, request, jsonify, Response
from flask_restful import reqparse, abort, Api, Resource
import json
import numpy as np


# 전체 흐름
# 1. API call
# 2. crawling & to_csv
# 3. read_csv → DB insert
# 4. 코드 스케줄링(3번 테스트 진행 중)

# numpy → json encoding
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)
        
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

    # 이건 괄호 데이터 임의 처리(수집한 데이터 내에서)
    # bracket_word = re.sub('\([^)]*\)', '', product)
    bracket_word = re.compile('\(([^)]+)').findall(product)
    bracket_word = ''.join(bracket_word)
    
    if '레깅스' in bracket_word:
        x = '30'
        
    elif '긴소매' in bracket_word:
        x = '8'
        
    else:    
        product = re.sub('\([^)]*\)', '', product) # (내용) 제거
        product = product.upper() # 대문자화
        product = product.strip() # 양끝 공백 제거

        if ('세트' in product) or ('셋트' in product) or \
           ('SET' in product) or ('셋업' in product):
            x = '22' # SET
            
        elif ('잠옷' in product) or (product.endswith('파자마')) or (product.endswith('파자마셋')):
            x = '33' # Pajama/Innerwear

        elif (product.endswith('원피스')) or (product.endswith('원피스2')) or \
             (product.endswith('OPS')) or (product.endswith('OPS2')):
            x = '21' # Dress

        # ■■■■■■■■■■■■■■■■ 상의 ■■■■■■■■■■■■■■■■
        elif (product.endswith('자켓')) or (product.endswith('쟈켓')) or (product.endswith('JK')) or \
             (product.endswith('자켓110')):
            x = '13' # Jacket

        elif (product.endswith('조끼')) or ('VEST' in product) or ('VT' in product):
            x = '15' # Vest

        elif ('셔츠' in product) or ('남방' in product) or ('NB' in product): # ST 처리 필요
            x = '11' # Shirts

        # elif (product.endswith('티')) or (product.endswith('나시')) or \
        #      (product.endswith('반팔')) or (product.endswith('반팔T')):
        #     x = '8' # Tee/Top

        elif (product.endswith('티')) or (product.endswith('나시')) or \
             (product.endswith('반팔')) or (product.endswith('반팔T')):
            x = '8' # Tee/Top

        elif (product.endswith('가디건')) or (product.endswith('가디간')) or (product.endswith('CD')):
            x = '14' # Cardigan

        elif ('JP' in product) or ('점퍼' in product) or (product.endswith('J.P')) or \
             (product.endswith('패딩')) or (product.endswith('PD')):
            x = '16' # Padding/Jumper
            
        elif ('점프' in product): # 블루리본 18JSS-36A 같은 것 때문에 일단 JS 미포함
            x = '29' # JumpSuit

        elif (product.endswith('BL')) or (product.endswith('블라우스')):
            x = '10' # Blouse

        # ■■■■■■■■■■■■■■■■ 하의 ■■■■■■■■■■■■■■■■
        elif ('치마' in product) or ('스커트' in product) or \
             ('SK' in product) or ('SKT' in product):
            x = '25' # Skirts

        elif ('슬랙스' in product) or ('슬렉스' in product) or ('SL' in product):
            x = '26' # Slacks
        
        elif ('레깅스' in product):
            x = '30'
            
        elif (product.endswith('청바지')) or (product.endswith('데님')): # 수정 필요
            x = '28' # Jean
            
        elif (product.endswith('바지')) or (product.endswith('PT')) or (product.endswith('팬츠')):
            x = '27' # Pants

        elif (product.endswith('코트')) or (product.endswith('COAT')) or (product.endswith('CT')):
            x = '17' # Coat

        elif ('후드' in product) or ('후디' in product) or (product.endswith('사파리')):
            x = '18' # Hood/Zip-up/Safari

        elif ('판쵸' in product) or (product.endswith('숄')): # '숄' 기준 잡기 어려움
            x = '19' # Cloak/Shawl/Poncho
            
        elif (product.endswith('T')) or (product.endswith('V')) or (product.endswith('Y')): # 수정 필요
            x = '8'
            
        elif ('니트' in product):
            x = '9'

        else:
            x = '98' # 미분류
    
    return x

# Products - category1
def category1_dict(c1):
    c1_dict = {
        'WOMEN': '여성 의류'
    }

    return c1_dict[c1]

# Products - category2
def category2_dict(c2):
    c2_dict = {
        'OUTER': '아우터', 'TOP & TEE': '티&탑', 'DRESS & SET': '원피스',
        'BOTTOM': '팬츠', 'BLOUSE': '블라우스', 'UNDERWEAR': '속옷',
        'ACCESSORIES': '액세서리', 'SALE': '세일상품', 'SHOES & BAG': '신발&가방',
        '기타': '기타'
    }

    return c2_dict[c2]

# 매장 고정 기입 카테고리
def shops_hold_category(x): # 여성
    if x == 'DB2G150042' or x == 'CB1GA30C35' or \
       x == 'D1D1000460' or x == 'C5LA525237' or \
       x == 'NZ12230029': # 그루, 한나네, 낫씽베러, 폴링제이, 보니타
        x = '21' # Dress(원피스)
    elif x == 'DWP2320474': # 라인
        x == '8' # Tee/Top
    elif x == 'D2G1700317': # 비키
        x == '26' # Slacks
    elif  x == 'C3NA180483': # 더이태리
        x == '27' # Pants
    elif x == 'Q215300310' or x == 'DB2N301265' or x == 'D3E2100443': # 바닐라제이, 피노키오, 데님부티크
        x == '28' # Jean
    elif x == 'D1J1800328': # 보따리
        x == '9'
    elif x == 'DB2D300037': # 페이퍼
        x = '25' # Skirts
    elif x == 'C2KA350516': # 제이엠
        x = '18' # Hood/Zip-uip/Safari
    elif x == 'NZB1207434': # 시엘(뉴존)
        x = '34' # Maternity(임부복)
    else:
        x = False
    
    return x

# 데이터 db 네이밍 형식에 맞게 수정
def df_db_convert_name(df):
    df.loc[df['product_fitting']=='베이직', 'product_fitting'] = '기본핏'
    df.loc[df['product_seethrough']=='약간비침', 'product_seethrough'] = '약간'
    df.loc[df['product_seethrough']=='비침', 'product_seethrough'] = '있음'
    df = df.replace('미표기', None)
    df = df.where((pd.notnull(df)), None)

    return df

driver = None
white_list = ['125.141.73.82', '124.56.158.191']

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# IP check(white list)
@app.before_request
def limit_remote_addr():
    if request.remote_addr in white_list:
        pass
    else:
        abort(403)

# call(http://ip:port/call?store_id=매장고유링크값)
# e.g. http://34.200.179.185:5002/call?store_id=CB1NA24367
@app.route('/call', methods=['GET','POST'])
@cross_origin()
def predict_code():   
	store_id = (request.args.get('store_id'))

	return (model_predict(store_id))

def model_predict(store_id):
    print("■■■■■■■■■■■■■■■■ START ■■■■■■■■■■■■■■■■")
    print(f"[CALL] store_id : {store_id}")
    print(f"[CALL] IP : {request.remote_addr}")

    # 폴더 생성
    create_folder('./Test')
    create_folder('./shop')
    create_folder('./shop_total')
    create_folder('./backup')
    create_folder('./backup/shop')
    create_folder('./backup/shop_total')
    create_folder('./json_shop')
   
    # AWS S3 server connect
    s3 = boto3.client(
        's3',
        aws_access_key_id = 'AKIAXHNKF4YFB6E7I7OI',
        aws_secret_access_key = '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',
    )

    # DB connect
    conn = pymysql.connect(
        host='52.79.173.93',
        port=3306,
        user='user',
        passwd='seodh1234',
        db='sokodress',
        charset='utf8'
    )

    cur = conn.cursor()

    if shops_hold_category(store_id):
        product_category_id = shops_hold_category(store_id)
    else:
        product_category_id = None

    # chrome option
    global driver

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--mute-audio')
    chrome_options.add_argument('disable-gpu')
    chrome_options.add_argument('lang=ko')
    chrome_options.add_argument('user-agent=User_Agent: Mozilla/5.0 \(Windows NT 10.0; Win64; x64\) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # 로그인
    driver.get('https://www.ddmmarket.co.kr/Login')
    driver.implicitly_wait(10)
    time.sleep(2)
    driver.find_element(By.ID, 'login_frame1').find_element(By.ID, 'user_id').send_keys('sokodress')
    driver.find_element(By.ID, 'login_frame1').find_element(By.ID, 'user_pwd').send_keys('ddmmarket9138')
    driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'login_btn'))
    driver.implicitly_wait(10)
    time.sleep(2)

    # 크롤링 사이트 목록
    basic_domain = f'http://www.ddmmarket.co.kr/Prod?m=S&c='
    crawling_link_list = [
        f'{basic_domain}{store_id}'
    ]

    target_folder = 'Test'
    s3_domain = 'https://sokodress.s3.ap-northeast-2.amazonaws.com'
    now_date = datetime.today().strftime('%Y%m%d_%H%M')
    df_shop = pd.DataFrame()

    # 매장 링크별 크롤링
    for c_link in tqdm(crawling_link_list, desc='[Crawling tqdm] 매장별 링크', position=0, leave=True):
        driver.get(c_link)
        driver.implicitly_wait(10)
        time.sleep(5)
        
        df_product = pd.DataFrame()

        # 시작
        try:
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'totalItem2')))
            product_all_case = int(driver.find_element(By.ID, 'totalItem2').text)
            driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'all_check').find_element(By.TAG_NAME, 'label'))
            time.sleep(5)
        except:
            print("모든 상품 수 미인식")

        try:
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'totalItem2')))
            product_cate_case = int(driver.find_element(By.ID, 'totalItem2').text)
            driver.get(c_link)
            driver.implicitly_wait(10)
            time.sleep(5)
            print(f"전체 상품: {product_all_case}, 카테고리 상품: {product_cate_case}, 전체 상품 - 카테고리 상품: {product_all_case - product_cate_case}")
        except:
            print("카테고리 상품 수 미인식")

        driver.get(c_link)
        driver.implicitly_wait(10)
        time.sleep(5)
        # 끝
            
        # element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'info_check')))
        # category_len = len(driver.find_element(By.CLASS_NAME, 'info_check').find_elements(By.TAG_NAME, 'li'))
        category_len = 10
        
        PRODUCT_SWITCH_1 = False

        # 카테고리 체크박스 반복
        for cate_len_idx in range(category_len):
            if cate_len_idx != 0:
                driver.get(c_link)
                driver.implicitly_wait(10)
                time.sleep(5)
            
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'label')))
            driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'info_check').\
                                find_elements(By.TAG_NAME, 'li')[cate_len_idx].find_element(By.TAG_NAME, 'label'))
            time.sleep(10)

            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'span')))
            product_category = driver.find_element(By.CLASS_NAME, 'info_check').find_elements(By.TAG_NAME, 'li')[cate_len_idx].\
                                find_element(By.TAG_NAME, 'label').find_element(By.TAG_NAME, 'span').text
            
            # [다음페이지 계속] 클릭
            try:
                while True:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'next_page')))
                    driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'next_page'))
                    time.sleep(5)
                    if 'none' in driver.find_element(By.CLASS_NAME, 'next_page').get_attribute('style'):
                        break
            except:
                print("[ERROR] [다음페이지 계속] 클릭 오류")

            try:
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'open_pro.ellipsis')))
                product_len = len(driver.find_element(By.ID, 'mygoodslist').find_elements(By.CLASS_NAME, 'open_pro.ellipsis'))
            except:
                print(f"아마 상품 없는 곳")
                continue

            #     if category_len == cate_len_idx:
            #         continue
            #     else:
            #         driver.get(c_link)
            #         driver.implicitly_wait(10)
            #         time.sleep(5)
            #         continue
            
            # if product_len == 0:
            #     if category_len == cate_len_idx:
            #         continue
            #     else:
            #         driver.get(c_link)
            #         driver.implicitly_wait(10)
            #         time.sleep(5)
            #         continue
            
            # 상품 검색 반복
            for product_len_idx in tqdm(range(product_len), desc='[Crawling tqdm] 카테고리별 상품들', position=1, leave=False):
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

                    # 상품 정보가 중복되서 나올 경우(정상은 li 10개)
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'li')))
                    if len(driver.find_element(By.ID, 'pro_info').find_elements(By.TAG_NAME, 'li')) != 10:
                        continue

                    # time.sleep(5)
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
                    product_elasticity = fabric_info(detail_info[2].split())
                    product_lining = fabric_info(detail_info[3].split())
                    product_fitting = fabric_info(detail_info[4].split())

                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'csTxtCode')))
                    product_color = [elem.get_attribute('value').replace(', FREE', '').strip() for elem in driver.find_elements(By.ID, 'csTxtCode')[1:]]
                    product_color = ','.join(product_color)

                    product_image_url = []
                    cnt = 0

                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'div')))
                    thumbnail_ele = driver.find_element(By.ID, 'gd_listimg').find_elements(By.TAG_NAME, 'div')            

                    for th_ele in thumbnail_ele:                
                        if th_ele.get_attribute('style') == 'text-align: center; padding-top: 55px;':
                            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'img')))
                            product_src = th_ele.find_element(By.TAG_NAME, 'img').get_attribute('src')
                            urlretrieve(product_src, f'./{target_folder}/{product_unique_id}_{cnt}.jpg')

                            s3.upload_file(
                                f'./{target_folder}/{product_unique_id}_{cnt}.jpg', # 로컬
                                'sokodress', # AWS S3
                                f'{target_folder}/{product_unique_id}_{cnt}.jpg', # AWS S3 파일 저장 주소
                                ExtraArgs={'ACL':'public-read'}
                            )

                            # e.g. https://sokodress.s3.ap-northeast-2.amazonaws.com/Test/sample1.jpg
                            product_image_url.append(f'{s3_domain}/{target_folder}/{product_unique_id}_{cnt}.jpg') # ./ 루트로 쓰면 절대 안됨
                            cnt += 1
                    product_image_url = ','.join(product_image_url)

                    df_product_one = pd.DataFrame({
                        'shop_image_url': [None],
                        'shop_address': [shop_address],
                        'shop_name': [shop_name],
                        'sizang_name': ['동대문'],
                        'sangga_name': [sangga_name],
                        'product_all_case': [product_all_case],
                        'product_cate_case': [product_cate_case],
                        'shop_phone': [shop_phone],
                        'product_unique_id': [product_unique_id],    
                        'product_name': [product_name],
                        'product_category': [product_category],
                        'product_category_1': ['WOMEN'],
                        'product_category_2': [None],
                        'product_category_id': [None],
                        'product_price': [product_price],
                        'product_made': [product_made],
                        'product_image_url': [product_image_url],
                        'product_style': [product_style],
                        'product_size': [product_size],
                        'product_maxrate': [product_maxrate],
                        'product_seethrough': [product_seethrough], # 비침
                        'product_elasticity': [product_elasticity], # 신축성
                        'product_lining': [product_lining], # 안감
                        'product_fitting': [product_fitting], # 피팅감
                        'product_color': [product_color],
                        'product_link': [c_link] # 상품 링크가 따로 없어서 상품의 매장 링크로 대체
                    })
                    
                    df_product = pd.concat([df_product, df_product_one], ignore_index=True)
                
                except:
                    print(f"[EXCEPT] shop_name: {shop_name}, product_len_idx: {product_len_idx}")
                    
                finally:
                    try:
                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'close')))
                        driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'close'))
                        time.sleep(5)
                    except UnexpectedAlertPresentException:
                        print("[ERROR] 엉뚱한 font 에러.. 재현도 잘 안되고 이유도 알 수 없다.")
                        pass

            # 카테고리 체크박스 해제
            # element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'label')))
            # driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'info_check').\
            #                       find_elements(By.TAG_NAME, 'li')[cate_len_idx].find_element(By.TAG_NAME, 'label'))
            # time.sleep(10)
            driver.get(c_link)
            driver.implicitly_wait(10)
            time.sleep(5)
        
        df_product.to_csv(f'./shop/{shop_name}.csv', index=False)
        df_product.to_csv(f'./backup/shop/{shop_name}.csv', index=False)

        df_shop_one = pd.DataFrame({
            'shop_image_url': [None],
            'shop_address': [shop_address],
            'shop_name': [shop_name],
            'sizang_name': ['동대문'],
            'sangga_name': [sangga_name],
            'product_all_case': [product_all_case],
            'product_cate_case': [product_cate_case],
            'shop_phone': [shop_phone]
        })

        df_shop = pd.concat([df_shop, df_shop_one], ignore_index=True)
        # time.sleep(5)

    df_shop.to_csv(f'./shop_list.csv', index=False)
    df_shop.to_csv(f'./backup/shop_list.csv', index=False)

    df_all = pd.DataFrame()
    for i in glob('./shop/*.csv'):
        i = pd.read_csv(i)
        df_all = pd.concat([df_all, i], ignore_index=True)
        
    print(f"[DataFrame] 저장된 상품의 shape: {df_all.shape}")
    df_all.to_csv(f'./shop_total/product_list.csv', index=False)
    df_all.to_csv(f'./backup/shop_total/product_list.csv', index=False)

    # load
    # df_all = pd.read_csv(f'./shop_total/product_list.csv')

    df_all = df_db_convert_name(df_all)

    # DB table crawling data insert

    # ■■■■■■■■■■■■■■■■ Shops ■■■■■■■■■■■■■■■■
    total_table_shops = []

    sql_shops = "SELECT * FROM Shops"
    cur.execute(sql_shops)
    rows_shops = cur.fetchall()
    # print(rows_shops)
    shop_id = rows_shops[-1][0] + 1

    d_shop_name = df_all['shop_name'].unique().tolist()

    for d in d_shop_name:
        SHOP_DUPLICATION_SWITCH = False
        for s in rows_shops:
            if d == s[6]:
                SHOP_DUPLICATION_SWITCH = True
                break
        
        if not SHOP_DUPLICATION_SWITCH:
            table_shops = (
                shop_id, # shop_id
                None, # shop_image
                ''.join(df_all[df_all['shop_name'] == d]['shop_address'].unique()), 
                0, # transactions
                0, # team_transactions
                datetime.today().strftime("%Y-%m-%d %H:%M:%S"), # create_at
                d, # shop_name
                ''.join(df_all[df_all['shop_name'] == d]['sizang_name'].unique()), # sizang_name
                ''.join(df_all[df_all['shop_name'] == d]['sangga_name'].unique()), # sanga_name
                0, # is_recommend
                None, # sinsang_거래처수,
                df_all[df_all['shop_name'] == d]['product_cate_case'].value_counts().tolist()[0], # sinsang_전체상품수
                None, # sinsang_거래처상품수,
                None, # partners_count
                None, # sinsang_store_id,
                '미정', # main_items
                ''.join(df_all[df_all['shop_name'] == d]['shop_phone'].unique()), # sinsang_store_phone
                ''.join(df_all[df_all['shop_name'] == d]['product_link'].unique()) # shop_link
            )
        
            total_table_shops.append(table_shops)
            shop_id += 1
            
    # sql_shops = """INSERT INTO Shops (shop_id, shop_image, address, transactions, team_transactions, create_at,
    #                                   shop_name, sizang_name, sanga_name, is_recommend, sinsang_거래처수,
    #                                   sinsang_전체상품수, sinsang_거래처상품수, partners_count, sinsang_store_id,
    #                                   main_items, sinsang_store_phone, shop_link)
    #                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    # cur.executemany(sql_shops, total_table_shops)
    # conn.commit()
    # print("[DB table] (Shops) insert complete")

    # ■■■■■■■■■■■■■■■■ Table : Products, FabricInfos, WashInfos ■■■■■■■■■■■■■■■■
    # table - Products 
    sql_shops = "SELECT * FROM Shops"
    cur.execute(sql_shops)
    rows_shops = cur.fetchall()

    sql_products = "SELECT * FROM Products"
    cur.execute(sql_products)
    rows_products = cur.fetchall()
    # print(rows_products)
    product_id = rows_products[-1][0] + 1

    # table - FabricInfos 
    sql_fabricinfos = "SELECT * FROM FabricInfos"
    cur.execute(sql_fabricinfos)
    rows_fabricinfos = cur.fetchall()
    fabric_id = rows_fabricinfos[-1][0] + 1

    # table - WashInfos
    sql_washinfos = "SELECT * FROM WashInfos"
    cur.execute(sql_washinfos)
    rows_washinfos = cur.fetchall()
    wash_info_id = rows_washinfos[-1][0] + 1

    # table - ProductImages
    sql_productimages = "SELECT * FROM ProductImages"
    cur.execute(sql_productimages)
    rows_productimages = cur.fetchall()
    image_id = rows_productimages[-1][0] + 1

    # table - ProductOptions
    sql_productoptions = "SELECT * FROM ProductOptions"
    cur.execute(sql_productoptions)
    rows_productoptions = cur.fetchall()
    product_option_id = rows_productoptions[-1][0] + 1

    # table - CategoryOfProduct
    sql_categoryofproduct = "SELECT * FROM CategoryOfProduct"
    cur.execute(sql_categoryofproduct)
    rows_categoryofproduct = cur.fetchall()
    category_of_product_id = rows_categoryofproduct[-1][0] + 1

    # table - ProductStyles, Styles
    sql_productstyles = "SELECT * FROM ProductStyles"
    cur.execute(sql_productstyles)
    rows_productstyles = cur.fetchall()
    product_style_id = rows_productstyles[-1][0] + 1

    sql_styles = "SELECT * FROM Styles"
    cur.execute(sql_styles)
    rows_styles = cur.fetchall()
    style_id_dict = dict((y, x) for x, y in rows_styles)

    total_table_products = []
    total_table_fabricinfos = []
    total_table_washinfos = []
    total_table_productimages = []
    total_table_productoptions = []
    total_table_categoryofproduct = []
    total_table_productstyles = []

    json_data_list = []

    for i in range(df_all.shape[0]):
        # SHOP_ID_SWITCH = False
        PRODUCT_UNIQUE_ID_SWITCH = False
        
        # for ch in rows_shops:
            # if df_all.loc[i, 'shop_name'] == ch[6]:
                # shop_id = ch[0]
                # SHOP_ID_SWITCH = True
                # break
        
        # if SHOP_ID_SWITCH:
        for pr in rows_products:
            if pr[17] == str(df_all.loc[i, 'product_unique_id']):
                PRODUCT_UNIQUE_ID_SWITCH = False
                break
            else:
                PRODUCT_UNIQUE_ID_SWITCH = True

        if PRODUCT_UNIQUE_ID_SWITCH:
            json_data_one = {}

            json_data_one['shop_image_url'] = None # shop_image
            json_data_one['shop_address'] = shop_address
            json_data_one['shop_name'] = shop_name
            json_data_one['sizang_name'] = '동대문'
            json_data_one['sangga_name'] = sangga_name
            json_data_one['product_all_case'] = product_all_case
            json_data_one['product_cate_case'] = product_cate_case
            json_data_one['shop_phone'] = shop_phone
            json_data_one['product_unique_id'] = df_all.loc[i, 'product_unique_id'] # product_unique_id
            json_data_one['product_name'] = df_all.loc[i, 'product_name'], # prod_name
            json_data_one['product_category'] = product_category
            json_data_one['product_category_1'] = 'WOMEN'
            json_data_one['product_category_2'] = category2_dict(df_all.loc[i, 'product_category']) # category2
            if product_category_id == None:
                json_data_one['product_category_id'] = product_category_classification(df_all.loc[i, 'product_name'])
            else:
                json_data_one['product_category_id'] = product_category_id
            json_data_one['product_price'] = df_all.loc[i, 'product_price'] # price(= real_price = team_price)
            json_data_one['product_made'] = df_all.loc[i, 'product_made'] # nation
            json_data_one['product_image_url'] = df_all.loc[i, 'product_image_url'] # image_url
            json_data_one['product_style'] = df_all.loc[i, 'product_style']
            json_data_one['product_size'] =  df_all.loc[i, 'product_size'] # size
            json_data_one['product_maxrate'] = df_all.loc[i, 'product_maxrate']
            json_data_one['product_seethrough'] = df_all.loc[i, 'product_seethrough'] # 비침 
            json_data_one['product_elasticity'] = df_all.loc[i, 'product_elasticity'] # 신축성
            json_data_one['product_lining'] = df_all.loc[i, 'product_lining'] # 안감
            json_data_one['product_fitting'] = df_all.loc[i, 'product_fitting'] # 핏정보
            json_data_one['product_color'] = df_all.loc[i, 'product_color']
            json_data_one['product_link'] = c_link # 상품 링크가 따로 없어서 상품의 매장 링크로 대체
            print(f"json_data_one: {json_data_one}")

            json_data_list.append(json_data_one)

            break

                    # # Products
                    # table_products = (
                    #     str(product_id), # product_id
                    #     shop_id, # shop_id
                    #     df_all.loc[i, 'product_name'], # prod_name
                    #     df_all.loc[i, 'product_price'], # real_price
                    #     df_all.loc[i, 'product_price'], # price
                    #     df_all.loc[i, 'product_price'], # team_price
                    #     df_all.loc[i, 'product_made'], # nation
                    #     'T', # is_unit
                    #     None, # contents
                    #     datetime.today().strftime("%Y-%m-%d %H:%M:%S"), # create_at
                    #     df_all.loc[i, 'product_maxrate'], # maxrate
                    #     0, # is_sold_out
                    #     df_all.loc[i, 'product_style'], # style
                    #     category1_dict(df_all.loc[i, 'product_category_1']), # category1
                    #     df_all.loc[i, 'product_link'], # prod_link
                    #     category2_dict(df_all.loc[i, 'product_category']), # category2
                    #     0, # star
                    #     df_all.loc[i, 'product_unique_id'] # product_unique_id
                    # )

                    # # FabricInfos
                    # table_fabricinfos = (
                    #     str(fabric_id), # fabric_id
                    #     str(product_id), # product_id
                    #     df_all.loc[i, 'product_fitting'], # 핏정보
                    #     '보통', # 두께감
                    #     df_all.loc[i, 'product_elasticity'], # 신축성,
                    #     df_all.loc[i, 'product_seethrough'], # 비침
                    #     df_all.loc[i, 'product_lining'], # 안감
                    #     '없음', # 광택
                    #     '보통', # 촉감
                    #     '없음' # 밴딩
                    # )

                    # # WashInfos
                    # table_washinfos = (
                    #     str(wash_info_id), # wash_info_id
                    #     str(product_id), # product_id
                    #     None # category
                    # )

                    # # ProductImages
                    # for url in df_all.loc[i, 'product_image_url'].split(','):
                    #     image_url = url
                    #     image_name = url.split('/')[-1].split('.')[0]

                    #     table_productimages = (
                    #         str(image_id), # image_id
                    #         str(product_id), # product_id
                    #         image_name, # image_name
                    #         image_url # image_url
                    #     )
                        
                    #     total_table_productimages.append(table_productimages)
                    #     image_id += 1

                    # # ProductOptions
                    # table_productoptions = (
                    #     str(product_option_id), # product_option_id
                    #     str(product_id), # product_id
                    #     df_all.loc[i, 'product_size'], # size
                    #     df_all.loc[i, 'product_color'] # color
                    # )

                    # # CategoryOfProduct
                    # table_categoryofproduct = (
                    #     str(category_of_product_id), # category_of_product_id
                    #     product_category_classification(df_all.loc[i, 'product_name']), # category_id
                    #     str(product_id) # product_id
                    # )

                    # # ProductStyles
                    # for sty in df_all.loc[0, 'product_style'].split(','):
                    #     style_id = style_id_dict[sty]

                    #     table_productstyles = (
                    #         str(product_style_id), # product_style_id
                    #         str(product_id), # product_id
                    #         str(style_id) # style_id
                    #     )
                        
                    #     total_table_productstyles.append(table_productstyles)
                    #     product_style_id += 1

                    # total_table_products.append(table_products)
                    # total_table_fabricinfos.append(table_fabricinfos)
                    # total_table_washinfos.append(table_washinfos)
                    # total_table_productoptions.append(table_productoptions)
                    # total_table_categoryofproduct.append(table_categoryofproduct)

                    # product_id += 1
                    # fabric_id += 1
                    # wash_info_id += 1
                    # product_option_id += 1
                    # category_of_product_id += 1
                    
                    # break

    print(f"다음 추가될 product_id 번호: {product_id}")
    # ■■■■■■■■■■■■■■■■ DB insert ■■■■■■■■■■■■■■■■
    # sql_products = """INSERT IGNORE INTO Products (product_id, shop_id, prod_name, real_price, price, team_price,
    #                                                nation, is_unit, contents, create_at, maxrate, is_sold_out,
    #                                                style, category1, prod_link, category2, star, product_unique_id)
    #                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    # cur.executemany(sql_products, total_table_products)
    # conn.commit()
    # print("[DB table] (Products) insert complete")

    # sql_fabricinfos = """INSERT IGNORE INTO FabricInfos (fabric_id, product_id, 핏정보, 두께감, 신축성, 비침, 안감, 광택, 촉감, 밴딩)
    #                                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    # cur.executemany(sql_fabricinfos, total_table_fabricinfos)
    # conn.commit()
    # print("[DB table] (FabricInfos) insert complete")

    # sql_washinfos = """INSERT IGNORE INTO WashInfos (wash_info_id, product_id, category)
    #                                          VALUES (%s, %s, %s)"""
    # cur.executemany(sql_washinfos, total_table_washinfos)
    # conn.commit()
    # print("[DB table] (WashInfos) insert complete")

    # sql_productimages = """INSERT IGNORE INTO ProductImages (image_id, product_id, image_name, image_url)
    #                                                  VALUES (%s, %s, %s, %s)"""
    # cur.executemany(sql_productimages, total_table_productimages)
    # conn.commit()
    # print("[DB table] (ProductImages) insert complete")

    # sql_productoptions = """INSERT IGNORE INTO ProductOptions (product_option_id, product_id, size, color)
    #                                                    VALUES (%s, %s, %s, %s)"""
    # cur.executemany(sql_productoptions, total_table_productoptions)
    # conn.commit()
    # print("[DB table] (ProductOptions) insert complete")

    # sql_categoryofproducts = """INSERT IGNORE INTO CategoryOfProduct (category_of_product_id, category_id, product_id)
    #                                                           VALUES (%s, %s, %s)"""
    # cur.executemany(sql_categoryofproducts, total_table_categoryofproduct)
    # conn.commit()
    # print("[DB table] (CategoryOfProduct) insert complete")

    # sql_productstyles = """INSERT IGNORE INTO ProductStyles (product_style_id, product_id, style_id)
    #                                                  VALUES (%s, %s, %s)"""

    # cur.executemany(sql_productstyles, total_table_productstyles)
    # conn.commit()
    # print("[DB table] (ProductStyles) insert complete")

    driver.quit()
    print("■■■■■■■■■■■■■■■■ END ■■■■■■■■■■■■■■■■")

    # log_message = {f"'Message':'Success Insert DB & Call IP : {request.remote_addr}'"}
    # resp = Response(json.dumps(log_message, ensure_ascii=False).encode('utf8'), status=200, mimetype='application/json')

    with open(f'./json_shop/{shop_name}.json', 'w') as fw:
        json.dumps(json_data_list, fw, ensure_ascii=False, cls=NumpyEncoder, indent=4)

    resp = Response(json.dumps(json_data_list, ensure_ascii=False, cls=NumpyEncoder, indent=4).encode('utf8'), status=200, mimetype='application/json')

    return resp

@app.errorhandler(Exception)
@cross_origin(origin="*", headers=['Content-Type', 'Authorization'])
def exception_handler(error):
    if driver != None:
        driver.quit()
    print(error)
    log_message = {f"'Message':'Fail Insert DB & Call IP : {request.remote_addr}'"}
    return log_message

if __name__ == '__main__': 
	app.run(host='0.0.0.0', debug=True, port=5002)