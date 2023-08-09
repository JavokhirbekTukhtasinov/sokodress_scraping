import requests
from fastapi import HTTPException, status

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
       