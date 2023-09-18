import requests
from fastapi import HTTPException, status
import os
import random
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import re
import datetime
from dateutil.relativedelta import relativedelta

ips = []


def rand_proxy():
    pass




def check_product_register_date(text_date:str, days_ago) -> bool:

    if text_date is None:
        return False

    date_obj = datetime.datetime.strptime(text_date, "%Y-%m-%d")

    # Calculate the current date
    current_date = datetime.datetime.now()

    # Calculate the difference between the two dates
    date_difference = current_date - date_obj

    # Calculate a timedelta for two months (approximately 60 days)
    two_months = datetime.timedelta(days=days_ago)

    print('two_months', two_months)
    # Compare the date difference with two months
    if date_difference < two_months:
        result = True
    else:
        result = False
    return result


def downloadImage(url: str, path: str):
    try:
        # url = 'https://image-v4.sinsang.market/?f=https://image-cache.sinsang.market/images/25232/92085305/167655035100655297_1462791657.jpg&w=1500&h=2000'
        # url = 'https://www.searchenginejournal.com/wp-content/uploads/2022/06/image-search-1600-x-840-px-62c6dc4ff1eee-sej-1280x720.png'

        headers = {
            # A common user agent
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            with open(f'{path}', 'wb') as f:
                f.write(response.content)
            print("Image downloaded successfully.")
            
        else:
            print("Failed to download image. Status code:", response.status_code)

        # urlretrieve(url, './Products/test.png')

        # image_response = requests.get(url, stream=True)
        # with open('./Products/test.jpg', 'wb') as out_file:
        #     shutil.copyfileobj(image_response.raw, out_file)
        # del image_response
        # print(image_response.status_code)
        # if image_response.status_code == 200:
        #     with  open('./Products/test2.jpg', 'wb') as out_file:
        #         out_file.write(image_response.content)
        #     return HTTPException(
        #      status_code=status.HTTP_200_OK
        #     )

    except Exception as err:
        print(f'Error {err}')


def check_duplicate_product(name: str, rows_products) -> bool:

    is_duplicate = False
    for prod in rows_products:
        if prod[2] == name:
            is_duplicate = True
            break
        else:
            is_duplicate = False
    return is_duplicate


def check_duplicate_shop(name: str, rows_shops):
    print(f"new shop name {name}")
    shop_id = None
    for shop in rows_shops:
        if shop[6] == name:
            print(f'exist shop name {name}')
            shop_id = shop[0]
            break
        else:
            shop_id = None
    return shop_id


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


def calculate_category_id(prod_name, c_big, c_small):
    # level_3 = ''

    # 여성 의류
    if c_big == "Women's Clothing":  # '여성 의류'
        # level_1 = '1'
        # TOP 탑 '7'
        if '스포츠' in prod_name or '골프' in prod_name:
            level_3 = '35'
            return level_3

        if c_small == "T-shirts&Tops":  # '티&탑':
            if '니트' in prod_name:
                level_3 = '9'
                return level_3
            elif '후드' in prod_name:
                level_3 = '18'
                return level_3
            else:
                level_3 = '8'
                return level_3

        elif c_small == "Knitwear":  # '니트':
            if '가디건' in prod_name:
                level_3 = '14'
                return level_3
            elif '조끼' in prod_name:
                level_3 = '15'
                return level_3
            else:
                level_3 = '9'
                return level_3

        elif c_small == "Blouses":  # '블라우스':
            level_3 = '10'
            return level_3

        elif c_small == "Shirts":  # '셔츠/남방':
            level_3 = '11'
            return level_3

        # OUTER 아우터 '12'
        elif c_small == "Outer":  # '아우터':
            if '자켓' in prod_name or '쟈켓' in prod_name or 'jk' in prod_name or '재킷' in prod_name:
                level_3 = '13'
                return level_3
            elif '가디건' or 'CD' in prod_name:
                level_3 = '14'
                return level_3
            elif '조끼' in prod_name:
                level_3 = '15'
                return level_3
            elif '패딩' in prod_name or '점퍼' in prod_name or 'jp' in prod_name:
                level_3 = '16'
                return level_3
            elif '코트' or 'CT' or "ct" in prod_name:
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
        elif c_small == "Dresses":  # '원피스':
            if '세트' in prod_name or '셋트' in prod_name:
                level_3 = '22'
                return level_3
            elif '니트' in prod_name:
                level_3 = '23'
                return level_3
            else:
                level_3 = '21'
                return level_3

        elif c_small == "Set Products":  # '세트 아이템':
            level_3 = '22'
            return level_3

        # BOTTOM 하의
        elif c_small == "Skirts":  # '스커트':
            level_3 = '25'
            return level_3

        elif c_small == "Pants":  # '팬츠':
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

        elif c_small == "Jeans":  # '청바지':
            if '점프수트' in prod_name or '점프슈트' in prod_name:
                level_3 = '29'
                return level_3
            else:
                level_3 = '28'
                return level_3

        # +MORE
        elif c_small == "Plus Size":  # '빅사이즈':
            level_3 = '32'
            return level_3

        elif c_small == "Maternity Clothing":  # '임부복':
            level_3 = '34'
            return level_3

        if '파자마' in prod_name or '잠옷' in prod_name or '속옷' in prod_name:
            level_3 = '33'
            return level_3

        if '비키니' in prod_name or '수영복' in prod_name or '레쉬가드' in prod_name or '비치웨어' in prod_name \
                or '래시가드' in prod_name or '래쉬가드' in prod_name:
            level_3 = '36'
            return level_3
        else:
            level_3 = '98'
            return level_3

    # 남성 의류
    elif c_big == "Men's Clothing":  # '남성 의류'
        # level_1 = '2'

        # TOP '37'
        if c_small == "Shirts":  # '티&탑':
            level_3 = '38'
            return level_3
        elif c_small == "Knitwear":  # '니트':
            level_3 = '39'
            return level_3
        elif c_small == "Shirts":  # '셔츠/남방':
            level_3 = '40'
            return level_3

        # BOTTOM '41'
        elif c_small == "Pants":  # '팬츠':
            if '니트' in prod_name:
                level_3 = '44'
                return level_3
            else:
                level_3 = '42'
                return level_3

        elif c_small == "Jeans":  # '청바지':
            level_3 = '43'
            return level_3

        # OUTER '45'
        elif c_small == "Outer":  # '아우터':
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
        elif c_small == "Suit":  # '수트':
            level_3 = '53'
            return level_3

        else:
            level_3 = '98'
            return level_3

    # 유아 의류
    elif c_big == "Children's Clothing":  # '유아 의류'
        # level_1 = '3'
        if c_small == "Outer":  # '아우터':
            level_3 = '55'
            return level_3
        elif c_small == "Knitwear":  # '니트':
            level_3 = '56'
            return level_3
        elif c_small == "T-shirts/Tops":  # '티/탑':
            level_3 = '57'
            return level_3
        elif c_small == "Jeans":  # '청바지':
            level_3 = '58'
            return level_3
        elif c_small == "Dresses":  # '원피스':
            level_3 = '59'
            return level_3
        elif c_small == "Pants":  # '팬츠':
            level_3 = '60'
            return level_3
        elif c_small == "Blouses":  # '블라우스':
            level_3 = '61'
            return level_3
        elif c_small == "Skirts":  # '스커트':
            level_3 = '62'
            return level_3
        elif c_small == "Suit":  # '정장세트':
            level_3 = '63'
            return level_3
        elif c_small == "In Season":  # '시즌':
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


def upload_image(s3, product_id, i):
    s3.upload_file(
        f'./Products/{product_id}_{i}.jpg',
        'sokodress',
        f'Products/{product_id}_{i}.jpg',
        ExtraArgs={'ACL': 'public-read'}
    )
    image_url = f'https://sokodress.s3.ap-northeast-2.amazonaws.com/Products/{product_id}_{i}.jpg'
    return image_url


def papago_translate(text: str):
    naver_client_id = "ru5nr6sWDWYHykq_Fvaf"
    naver_secret_key = "JjDKMlBbmx"
    api_url = 'https://openapi.naver.com/v1/papago/n2mt'
    try:
        headers = {'X-Naver-Client-Id': naver_client_id, 'X-Naver-Client-Secret': naver_secret_key,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        body = {'source': 'ko', 'target': 'en', 'text': text}
        response = requests.post(api_url, body, headers=headers)
        response_json = response.json()

        return response_json.get('message').get('result').get('translatedText')
    except Exception as e:
        print(f'error: {e}')
        # const { data } = await axios.post(api_url, body, { headers })
        #    const api_url = 'https://openapi.naver.com/v1/papago/n2mt';


def parse_datetime(datetime_str):
    datetime_patern = r'\d{4}\.\d{2}\.\d{2}'
    matches = re.findall(datetime_patern, datetime_str)
    if matches:
        datetime_str = matches[0]

        parsed_datetime = datetime.datetime.strptime(datetime_str, '%Y.%m.%d')

        return parsed_datetime.strftime('%Y-%m-%d %H:%M:%S')

    else:
        return ''


# def parse_datetime(datetime_str):
#     datetime_patern = r'\d{4}\-\d{2}\-\d{2}'
#     matches = re.findall(datetime_patern, datetime_str)
#     if matches:
#         datetime_str = matches[0]

#         parsed_datetime = datetime.strptime(datetime_str, '%Y-%m-%d')

#         return parsed_datetime.strftime('%Y-%m-%d %H:%M:%S')

#     else:
#         return ''

def parse_relative_time(relative_phrase):
    print(f'ralative phrase time : {relative_phrase}')
    now = datetime.datetime.now()
    if 'year' in relative_phrase:
        delta = relativedelta(years=int(relative_phrase.split()[0]))
    elif 'month' in relative_phrase:
        delta = relativedelta(months=int(relative_phrase.split()[0]))
    elif 'day' in relative_phrase:
        delta = relativedelta(days=int(relative_phrase.split()[0]))
    elif 'hour' in relative_phrase:
        delta = relativedelta(hours=int(relative_phrase.split()[0]))
    elif 'second' in relative_phrase: 
        delta = relativedelta(seconds=int(relative_phrase.split()[0]))
    else:
        raise ValueError("Unsupported relative time phrase")

    result_datetime = now - delta
    return result_datetime







def create_folder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)

    except OSError:
        print(f"Error: Creating directory {directory}")


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

category1_dict = {
    "Women's Clothing": '여성 의류', "Men's Clothing": '남성 의류', "Children's Clothing": '유아 의류'
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




def check_create_date_ago(driver, create_at):
    
    if 'Boosted' in create_at:
        print(f'boosted at {create_at}')
        uplift_at = parse_relative_time(create_at)
        print(f"uplift_at {uplift_at}")

            #     if 'hours' in create_at or 'minutes' in create_at:
            #         pass
            #     elif 'year' in create_at:
            #         driver.execute_script('arguments[0].click();', driver.find_element(
            #             By.CLASS_NAME, 'close-button'))
            #         continue
            #     elif 'days' in create_at:
            #         if int(re.sub(r'[^0-9]', '', create_at.split('\n')[1])) < days_ago:
            #             pass
            #         else:
            #             driver.execute_script('arguments[0].click();', driver.find_element(
            #                 By.CLASS_NAME, 'close-button'))
            #             continue
            #     else:
            #         print(f"[LOG] 등록일: {create_at}")
            # elif datetime.datetime.strptime(create_at.split(' ')[0], '%Y.%m.%d') < standard_date_ago:

            #     # driver.find_element(By.CLASS_NAME, 'close-button').click()
            #     driver.execute_script('arguments[0].click();', driver.find_element(
            #         By.CLASS_NAME, 'close-button'))
            #     continue

    else:
            original_create_at = parse_datetime(create_at)
            print(f"original_create_at {original_create_at}")
            pass


def scrap_prodcut_only(driver, total_product_count, rows_products, standard_date_ago, wait, s3, store_id, style, c, style_id, cur, conn, MAX_COUNT, inference_id, scraped_item, image_id, product_id, days_ago):
    total_table_ProductImages = []
    total_table_Products = []
    total_table_CategoryOfProduct = []
    total_table_FabricInfos = []
    total_table_ProductOptions = []
    total_table_WashInfos = []
    total_table_ProductStyles = []

    print(f'total_product_count: {total_product_count}')

    # for goo in range(0, int(total_product_count)):
    for product_number in range(int(total_product_count)):

        if product_number == 0:
            continue

        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        
        time.sleep(2)
        
        print(f'in progress item {product_number}')

        driver.execute_script("window.scrollTo(0, 1000)")
        
        try:
            active_product = driver.find_element(
                # //*[@id="25232"]/div/div[2]/div[2]/div/div/div/div/div[3]
                By.XPATH, f'//*[@id="{store_id}"]/div/div[2]/div[2]/div/div/div/div/div[{product_number}]')
            driver.execute_script("arguments[0].click();", active_product)
        except Exception as e:
            break

        time.sleep(1)

        try:
            prod_name = driver.find_element(
                By.CSS_SELECTOR, '#goods-detail > div > div.content__section > div.goods-detail-right > div:nth-child(1) > p').text
        except Exception as e:
            prod_name = ''
            continue

        if check_duplicate_product(prod_name, rows_products) is True:
            print('check duplicate')
            driver.execute_script('arguments[0].click();', driver.find_element(By.CLASS_NAME, 'close-button'))
            continue
        else:
            print('not duplicate')
            pass

        try:
                  # goods-detail > div > div.content__section > div.goods-detail-right > div:nth-child(1) > p
            prod_name = driver.find_element(
                By.CSS_SELECTOR, '#goods-detail > div > div.content__section > div.goods-detail-right > div:nth-child(1) > p').text
            print(f'inner prod name ->>> {prod_name}')
                  # TODO: change this later

            prod_name_en = papago_translate(prod_name)
            time.sleep(2)

        except Exception as e:
            prod_name_en = ''
            print(f'papago error::: {e}')
            pass
        
        try:
            element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[contains(text(), 'Updated at')]/following-sibling::div")))

            create_at = driver.find_element(
                By.XPATH, "//div[contains(text(), 'Updated at')]/following-sibling::div").text
            
        except Exception as e:
            create_at = ''
            continue
            
        
        original_create_at = check_create_date_ago(driver, create_at)

           # 날짜가 days_ago보다 더 크면 break 
        # if 'Boosted' in create_at:
        #     uplift_at = parse_relative_time(create_at)
            
        #     print(f"uplift_at {uplift_at}")

        #         # if 'hours' in create_at or 'minutes' in create_at:
        #         #     pass
        #         # elif 'year' in create_at:
        #         #     driver.execute_script('arguments[0].click();', driver.find_element(
        #         #         By.CLASS_NAME, 'close-button'))
        #         #     continue
        #         # elif 'days' in create_at:
        #         #     if int(re.sub(r'[^0-9]', '', create_at.split('\n')[1])) < days_ago:
        #         #         pass
        #         #     else:
        #         #         driver.execute_script('arguments[0].click();', driver.find_element(
        #         #             By.CLASS_NAME, 'close-button'))
        #         #         continue
        #         # else:
        #         #     print(f"[LOG] 등록일: {create_at}")
        #     # elif datetime.datetime.strptime(create_at.split(' ')[0], '%Y.%m.%d') < standard_date_ago:

        #     #     # driver.find_element(By.CLASS_NAME, 'close-button').click()
        #     #     driver.execute_script('arguments[0].click();', driver.find_element(
        #     #         By.CLASS_NAME, 'close-button'))
        #     #     continue

        # else:
        #     original_create_at = parse_datetime(create_at)
        #     print(f"original_create_at {original_create_at}")
        #     pass

            # 위의 날짜 계산이 끝나면 입력할 create_at로 변환
        if create_at != '':
            create_at = create_at.split(' ')[0].replace('.', '-')

            # prod_link
        try:
            prod_id = driver.find_elements(By.XPATH, '//div[@data-group="goods-list"]')[product_number].get_attribute('data-gid')
            prod_link = f'https://sinsangmarket.kr/goods/{prod_id}'
                # print(f'prod link ->>> {prod_link}')
        except Exception as e:
            print(f'prod link error ->>> {e}')
            prod_link = ''

            # prod_name

            # real_price, price, team_price
        try:
                # goods_price = driver.find_element(By.XPATH, '//*[@id="goods-detail"]').find_element(By.CSS_SELECTOR, 'div.price.flex.items-center').text
            goods_price = driver.find_element(By.CLASS_NAME, 'price.flex.items-center').find_element(By.CLASS_NAME, 'ml-\[2px\]').text
            goods_price = re.sub(r'[^0-9]', '', goods_price)
            real_price = price = team_price = goods_price
                # print(
                #     f'goods price : {goods_price} real price : {real_price}')
        except Exception as e:
            print(f'goods price error ->>> {e}')
            goods_price = ''

            # star
        try:
            star = driver.find_element(By.XPATH, '//*[@id="goods-detail"]').find_element(By.CSS_SELECTOR, 'p.zzim-button__count').text
                # print(f'start ->>> {star}')
        except Exception as e:
                print(f'start error ->>> {e}')
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
        images_list = driver.find_elements(By.XPATH, '//img[@alt="thumbnail-image"]')
        print(f'images list ->>> {images_list}')
        try:
            for i in range(1, len(images_list), 1):
                time.sleep(2)
                print(f'image loop ->> {i}')

                    # goods_src = driver.find_elements(
                    #     By.XPATH, '//img[@alt="thumbnail-image"]')[i].get_attribute('src')
                    # print(f'goods src {goods_src}')

                driver.execute_script('arguments[0].click();', driver.find_element(By.XPATH, f'//*[@id="goods-detail"]/div/div[2]/div[1]/div[1]/div/div[1]/div[3]/div/div[{i}]/div'))
                time.sleep(1)
                goods_src = driver.find_element(
                By.XPATH, f'//*[@id="goods-detail"]/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div[1]/div/div[{i}]/div/img').get_attribute('src')
                print(f'image src =>>> {goods_src}')
                image_path = f'./Products/{product_id}_{i}.jpg'

                downloadImage(goods_src, image_path)

                image_url = upload_image(s3, product_id, i)

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
            category1 = driver.find_elements(By.XPATH, "//div[contains(text(), 'Categories')]/following-sibling::div/div")[0].text
                # print(f'category 1 ->>> {category1}')

        except Exception as e:
                category1 = ''

            # category2
        try:
            category2 = driver.find_elements(By.XPATH, "//div[contains(text(), 'Categories')]/following-sibling::div/div")[1].text
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
            size = driver.find_element(By.XPATH, "//div[contains(text(), 'Size')]/following-sibling::div").text

            print(f"size ==> {size}")
        except Exception as e:
            size = ''

            # maxrate
        try:
            maxrate = driver.find_element(By.XPATH, "//div[contains(text(), 'Proposition')]/following-sibling::div").text
                # print(f'maxrate ->>> {maxrate}')

        except Exception as e:
            maxrate = ''

            # nation
        try:
            nation = driver.find_element(By.XPATH, "//div[contains(text(), 'Origin')]/following-sibling::div").text
            nation = nation_dict[nation]
                # print(f'nation ->>> {nation}')
        except Exception as e:
            nation = ''

            # is_unit
        try:
            contents_text = driver.find_element(By.CLASS_NAME, 'mb-\[80px\]').find_element(By.CLASS_NAME, 'row__content').text
            print(f'contents text ->>> {contents_text}')
            if contents_text == 'No details.':
                is_unit = 'T'
            else: is_unit = calculate_is_unit(contents_text)
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
            goods_fabric_thickness = [x for x in driver.find_elements(By.XPATH, "//div[contains(text(), 'Thickness')]/following-sibling::div/div/div") if x.get_attribute('class') == 'min-w-[42px] text-gray-100'][0].text
            goods_fabric_thickness = fabric_dict[goods_fabric_thickness]
        except Exception as e:
            goods_fabric_thickness = ''

            # goods_fabric_seethrough
        try:
            goods_fabric_seethrough = [x for x in driver.find_elements(By.XPATH, "//div[contains(text(), 'Transparency')]/following-sibling::div/div/div") if x.get_attribute('class') == 'min-w-[42px] text-gray-100'][0].text
            goods_fabric_seethrough = fabric_dict[goods_fabric_seethrough]
        except Exception as e:
            goods_fabric_seethrough = ''

            # goods_fabric_elasticity
        try:
            goods_fabric_elasticity = [x for x in driver.find_elements(By.XPATH, "//div[contains(text(), 'Elasticity')]/following-sibling::div/div/div") if x.get_attribute('class') == 'min-w-[42px] text-gray-100'][0].text
            goods_fabric_elasticity = fabric_dict[goods_fabric_elasticity]
        except Exception as e:
            goods_fabric_elasticity = ''

            # goods_fabric_lining
        try:
            goods_fabric_lining = [x for x in driver.find_elements(By.XPATH, "//div[contains(text(), 'Lining')]/following-sibling::div/div/div") if x.get_attribute('class') == 'min-w-[42px] text-gray-100'][0].text
            print(f'goods fabric_linking ->>> {goods_fabric_lining}')
            goods_fabric_lining = fabric_dict[goods_fabric_lining]
        except Exception as e:
            goods_fabric_lining = ''

            # category_id
        category_id = calculate_category_id(prod_name, category1, category2)
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
                color,  # color
                original_create_at,
                uplift_at
        )

        table_ProductStyles = (
                # str(product_style_id),  # autoincrement
                str(product_id),
                str(style_id)
        )

        total_table_Products.append(table_Products)
        total_table_CategoryOfProduct.append(table_CategoryOfProduct)
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

                sql_productoptions = """INSERT INTO ProductOptions (product_id, size, color, original_create_at, uplift_at)
                                                                    VALUES ( %s, %s, %s, %s, %s)"""
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
#    reset all tables
    total_table_ProductImages = []
    total_table_Products = []
    total_table_CategoryOfProduct = []
    total_table_FabricInfos = []
    total_table_ProductOptions = []
    total_table_WashInfos = []
    total_table_ProductStyles = []

    product_number = 0