import requests
from fastapi import HTTPException, status
import os
import random


ips = []

def rand_proxy():
    pass

def downloadImage(url:str, path:str): 
    try:
        # url = 'https://image-v4.sinsang.market/?f=https://image-cache.sinsang.market/images/25232/92085305/167655035100655297_1462791657.jpg&w=1500&h=2000'
        # url = 'https://www.searchenginejournal.com/wp-content/uploads/2022/06/image-search-1600-x-840-px-62c6dc4ff1eee-sej-1280x720.png'

        headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'  # A common user agent
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
        print(f"new product name {name}")
        is_duplicate = False
        for prod in rows_products:
            if prod[2] == name:
                print(f'exist product name {name}')
                is_duplicate = True
                break
            else:
                is_duplicate = False
        return is_duplicate
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
        ExtraArgs={'ACL':'public-read'}
    )
    image_url = f'https://sokodress.s3.ap-northeast-2.amazonaws.com/Products/{product_id}_{i}.jpg'
    return image_url





def papago_translate(text:str): 
    naver_client_id = "ru5nr6sWDWYHykq_Fvaf"
    naver_secret_key = "JjDKMlBbmx"
    api_url = 'https://openapi.naver.com/v1/papago/n2mt';
    try:
        headers = { 'X-Naver-Client-Id': naver_client_id, 'X-Naver-Client-Secret': naver_secret_key, 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' }
        body = { 'source': 'ko', 'target': 'en', 'text': text }
        response = requests.post(api_url, body, headers=headers)
        response_json = response.json()

        return response_json.get('message').get('result').get('translatedText')
    except Exception as e:
        print(f'error: {e}')
        # const { data } = await axios.post(api_url, body, { headers })
        #    const api_url = 'https://openapi.naver.com/v1/papago/n2mt';



  

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
