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
from flask_cors import CORS, cross_origin
from flask import Flask, request, jsonify, Response
from flask_restful import reqparse, abort, Api, Resource
import json
import numpy as np
import schedule


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


def job():

    # chrome option - 토르 테스트 중
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--proxy-server=socks5://127.0.0.1:9150")
    chrome_options.add_argument('--mute-audio')
    chrome_options.add_argument('disable-gpu')
    chrome_options.add_argument('lang=ko')
    # chrome_options.add_argument('user-agent=User_Agent: Mozilla/5.0 \(Windows NT 10.0; Win64; x64\) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    s3 = boto3.client(
        's3',
        aws_access_key_id = 'AKIAXHNKF4YFB6E7I7OI',
        aws_secret_access_key = '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',
    )
    s3_domain = 'https://sokodress.s3.ap-northeast-2.amazonaws.com'

    folder_shops = 'shops2'
    folder_products_image = 'products_image2'
    create_folder(folder_products_image)
    create_folder(folder_shops)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    # driver.get('https://www.linkshops.com/')

    # 회원 정보 입력 창 접속
    driver.get('https://www.linkshops.com/?signIn=')
    driver.implicitly_wait(10)
    time.sleep(2)

    # 로그인
    driver.find_element(By.CLASS_NAME, 'input-wrapper').find_element(By.NAME, 'email').send_keys('waldoyun2@gmail.com')
    driver.find_element(By.CLASS_NAME, 'input-wrapper').find_element(By.NAME, 'password').send_keys('Linkshops9138')
    event_click(driver, driver.find_element(By.CLASS_NAME, 'login-modal-content-wrapper').find_element(By.ID, 'btn'))
    driver.implicitly_wait(10)
    time.sleep(2)

    # 매장(티엔씨) 접속
    shop_link = 'https://www.linkshops.com/tnc_theot'
    driver.get(shop_link)
    driver.implicitly_wait(10)
    time.sleep(2)

    df_product = pd.DataFrame()

    #
    shop_name = driver.find_element(By.CLASS_NAME, 'title-container-title').find_element(By.CLASS_NAME, 'name').text

    sangga_and_address = driver.find_element(By.CLASS_NAME, 'brandTitleContainer-location-content').text

    sangga_name = sangga_and_address.split(' ')[0]
    shop_address = ' '.join(sangga_and_address.split(' ')[1:])

    shop_phone = driver.find_element(By.CLASS_NAME, 'brandTitleContainer-phone-content').find_element(By.TAG_NAME, 'span').text

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

    # driver.get(shop_link)
    # driver.implicitly_wait(10)
    # time.sleep(2)

    product_all_cnt = 0

    start_time = time.time()

    for lp in range(last_page_num):
        try:
            one_start_time = time.time()
            
            ONE_PAGE_FLAG = True

            driver.get(f'{shop_link}?pageNum={lp+1}')
            driver.implicitly_wait(10)
            time.sleep(2)

            FIRST_PRODUCT_SWITCH = True
            
            while ONE_PAGE_FLAG:
                if FIRST_PRODUCT_SWITCH:
                    # 첫상품 클릭
                    event_click(driver, driver.find_element(By.CLASS_NAME, 'center-container').\
                                               find_elements(By.CLASS_NAME, 'flex-container')[0].\
                                               find_element(By.CLASS_NAME, 'inner-wrap'))
                    FIRST_PRODUCT_SWITCH = False

                # 상품 정보
                try:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '상품 번호')]")))
                    
                    if driver.find_element(By.XPATH, "//div[contains(text(), '상품 번호')]").text:
                        product_unique_id_and_create_at = driver.find_elements(By.CLASS_NAME, 'product-info-item')[3].text
                        product_unique_id = product_unique_id_and_create_at.split('      ')[0].replace('상품 번호\n', '')
                        product_create_at = product_unique_id_and_create_at.split('      ')[1].replace('업데이트(', '').replace(')', '')
                except:
                    # product_unique_id = None
                    # product_create_at = None
                    
                    time.sleep(2)
                    # 상품 다음 > 클릭
                    try:
                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-product-next')))

                        if driver.find_element(By.CLASS_NAME, 'modal-product-next-button.next').find_element(By.CLASS_NAME, 'icon-product-next'):
                            # time.sleep(5)
                            event_click(driver, driver.find_element(By.CLASS_NAME, 'modal-product-next-button.next').\
                                            find_element(By.CLASS_NAME, 'icon-product-next'))
                            print("다음 상품 >")

                    except NoSuchElementException:
                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-product-modal-close')))

                        print("스킵 후 끝")
                        event_click(driver, driver.find_element(By.CLASS_NAME, 'icon-product-modal-close'))
                        ONE_PAGE_FLAG = False

                    finally:
                        time.sleep(5)
                        continue
                    

                try:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '카테고리')]")))
                    
                    if driver.find_element(By.XPATH, "//div[contains(text(), '카테고리')]").text:
                        product_category = driver.find_elements(By.CLASS_NAME, 'product-info-item')[4].text # '잡화,패션아이템,헤어핀/밴드/브로치,쥬얼리/시계'
                        product_category = product_category.replace('카테고리\n', '')
                        product_category = product_category.split(' > ')
                        # product_category = ','.join(product_category)
                        product_category_1, product_category_2, product_category_3 = category_classification(product_category)
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

                # 세탁방법이 있는게 있고 없는게 있어서 달라짐
                try:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '세탁방법')]")))
                    
                    if driver.find_element(By.XPATH, "//div[contains(text(), '세탁방법')]").text:
                        product_fabric = driver.find_elements(By.CLASS_NAME, 'product-info-item')[7].text
                        product_fabric = product_fabric.replace('세탁방법\n', '').replace(' / ', ',')
                        
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '원산지')]")))

                    if driver.find_element(By.XPATH, "//div[contains(text(), '원산지')]").text:
                        product_made = driver.find_elements(By.CLASS_NAME, 'product-info-item')[8].text

                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '낱장여부')]")))
                    
                    if driver.find_element(By.XPATH, "//div[contains(text(), '낱장여부')]").text:
                        product_is_unit = driver.find_elements(By.CLASS_NAME, 'product-info-item')[9].text 
                    
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '도매판매가')]")))

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
                    product_thickness = None
                    product_elasticity = None
                    product_seethrough = None
                    product_lining = None
                    product_gloss = None
                    product_touch = None
                    product_banding = None
                
                try:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'slick-slide')))

                    slick_hidden = driver.find_element(By.CLASS_NAME, 'slick-initialized.slick-slider.productProductModalThumbnailSlider').\
                                        find_element(By.CLASS_NAME, 'slick-track').\
                                        find_elements(By.CLASS_NAME, 'slick-slide')

                    product_image_url = []

                    for idx, i in enumerate(slick_hidden):
                        img_ele = i.find_element(By.CLASS_NAME, 'img').get_attribute('style')
                        img_ele = img_ele.split('url("')[1].split('");')[0]
                        img_ele = image_resize_url(img_ele)

                        urlretrieve(f'https:{img_ele}', f'./{folder_products_image}/{product_unique_id}_{idx}.png')

                        s3.upload_file(
                            f'{folder_products_image}/{product_unique_id}_{idx}.png',
                            'sokodress',
                            f'{folder_products_image}/{product_unique_id}_{idx}.png',
                            ExtraArgs={'ACL':'public-read'}
                        )

                        product_image_url.append(f'{s3_domain}/{folder_products_image}/{product_unique_id}_{idx}.png')
                    
                    product_image_url = ','.join(product_image_url)
                
                except:
                    product_image_url = None
                    

                df_product_one = pd.DataFrame({
                    'shop_name': [shop_name],
                    'sizang_name': ['동대문'],
                    'sangga_name': [sangga_name],
                    'shop_address': [shop_address],
                    'shop_phone': [shop_phone],
                    'product_unique_id': [product_unique_id],
                    'product_create_at': [product_create_at],
                    'product_category_1': [product_category_1],
                    'product_category_2': [product_category_2],
                    'product_category_3': [product_category_3],
                    'product_name': [product_name],
                    'product_maxrate': [product_maxrate],
                    'product_fabric': [product_fabric],
                    'product_made': [product_made],
                    'product_is_unit': [product_is_unit],
                    'product_price': [product_price],
                    'product_color': [product_color],
                    'product_size': [product_size],
                    'product_fitting': [product_fitting], # 핏정보
                    'product_thickness': [product_thickness], # 두께감
                    'product_elasticity': [product_elasticity], # 신축성
                    'product_seethrough': [product_seethrough], # 비침
                    'product_lining': [product_lining], # 안감
                    'product_gloss': [product_gloss], # 광택
                    'product_touch': [product_touch], # 촉감
                    'product_banding': [product_banding],
                    'product_image_url': [product_image_url],
                    'product_link': [shop_link]
                })

                df_product = pd.concat([df_product, df_product_one], ignore_index=True)

                # 상품 다음 > 클릭
                try:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-product-next')))

                    if driver.find_element(By.CLASS_NAME, 'modal-product-next-button.next').find_element(By.CLASS_NAME, 'icon-product-next'):
                        # time.sleep(5)
                        event_click(driver, driver.find_element(By.CLASS_NAME, 'modal-product-next-button.next').\
                                                   find_element(By.CLASS_NAME, 'icon-product-next'))
                        print("다음 상품 >")
                        
                        product_all_cnt += 1

                except NoSuchElementException:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-product-modal-close')))
                    
                    print("한 페이지 크롤링 끝")
                    event_click(driver, driver.find_element(By.CLASS_NAME, 'icon-product-modal-close'))
                    ONE_PAGE_FLAG = False

                finally:
                    time.sleep(5)
            
            one_result_time = str(datetime.timedelta(seconds=time.time()-one_start_time)).split('.')[0]
            print(f"한 페이지 도는 시간: {one_result_time}")
                    
            # now_time = datetime.datetime.today().strftime('%Y%m%d_%H%M')
            # df_product.to_csv(f'./{folder_shops}/{shop_name}_{now_time}.csv', index=False)
                    
        except Exception as e:
            print("하다 끊겨서 저장")
            now_time = datetime.datetime.today().strftime('%Y%m%d_%H%M')
            df_product.to_csv(f'./{folder_shops}/{shop_name}_{now_time}.csv', index=False)
            # df_product.to_csv(f'./{folder_shops}/{shop_name}_fail.csv', index=False)
            
            print(e)
            # df_product.to_csv(f'./{folder_shops}/{shop_name}.csv', index=False)        

    print("크롤링 완료")
    df_product['product_all_cnt'] = product_all_cnt
    df_product.to_csv(f'{folder_shops}/{shop_name}.csv', index=False)

    result_time = str(datetime.timedelta(seconds=time.time()-start_time)).split('.')[0]
    print(f"runtime: {result_time}")

    s3.upload_file(
        f'{folder_shops}/{shop_name}.csv',
        'sokodress',
        f'{folder_shops}/{shop_name}.csv',
        ExtraArgs={'ACL':'public-read'}
    )


schedule.every().day.at("08:00").do(job) # day 날마다

while True:
    schedule.run_pending()
    time.sleep(10) # 3

job()