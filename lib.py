import requests
from fastapi import HTTPException, status
import os
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
