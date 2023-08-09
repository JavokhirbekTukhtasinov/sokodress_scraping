from fastapi import FastAPI
import uvicorn
import datetime
from Shinsangmarket.product import router as ShinsangRouter
from Shinsangmarket.shop import router as ShinsangShopRouter 
import time
import math
app = FastAPI(title='Sokodress scraping')

@app.get('/')
def root():
    return {'msg' : 'Healthy'}


# Bunker 벙커 id : 25232
max_runtime = 3

start_time = time.time()

for i in range(100000000):
    print(f'time {i}')
    break
    for j in range(10000):
        time.sleep(1)

        elapsed_time = time.time() - start_time
        print(f'{math.floor(elapsed_time)}')
        for a in range(10000):
            time.sleep(1)
            if elapsed_time >= max_runtime:
                print("Maximum runtime exceeded. Exiting loop.")
            break
        
create_at = '2023.04.24 registered'
last_registered = datetime.datetime.strptime(create_at.split(' ')[0],'%Y.%m.%d')
# print(f"{}")2023.04.24 registered
current_time = datetime.datetime.now()

if last_registered > current_time: 
    print('larger')
else: 
    print('smaller')
# print(f"{datetime.datetime.now()}")
# 2023-04-24 00:00:00
# print(f'day {days}')
app.include_router(prefix='/shinsang/product' , router=ShinsangRouter)
app.include_router(prefix='/shinsang/shopp', router=ShinsangShopRouter)
if __name__ == '__main__':
     uvicorn.run("__main__:app", port=5000, host='0.0.0.0', reload=True, log_level='info', factory=True)
