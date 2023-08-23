from fastapi import FastAPI
import uvicorn
import datetime
from Shinsangmarket.product import router as ShinsangRouter
from Shinsangmarket.shop import router as ShinsangShopRouter 
from Linkshops.product import router as LinkshopRouter
from fastapi.middleware.cors import CORSMiddleware
import time
import math
from lib import papago_translate
app = FastAPI(title='Sokodress scraping')

@app.get('/')
def root():
    return {'msg' : 'Healthy'}

# Bunker 벙커 id : 25232
# max_runtime = 3

# start_time = time.time()

# for i in range(100000000):
#     print(f'time {i}')
#     break
#     for j in range(10000):
#         time.sleep(1)

#         elapsed_time = time.time() - start_time
#         print(f'{math.floor(elapsed_time)}')
#         for a in range(10000):
#             time.sleep(1)
#             if elapsed_time >= max_runtime:
#                 print("Maximum runtime exceeded. Exiting loop.")
#             break


app.include_router(prefix='/shinsang' , router=ShinsangRouter)
app.include_router(prefix='/shinsang/shopp', router=ShinsangShopRouter)
app.include_router(prefix='/linkshop', router=LinkshopRouter)

app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
if __name__ == '__main__':
     uvicorn.run("__main__:app", port=5000, host='0.0.0.0', reload=True, log_level='info', factory=True)
