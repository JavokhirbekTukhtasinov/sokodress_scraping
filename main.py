from fastapi import FastAPI
import uvicorn
import datetime
from Shinsangmarket.product import router as ShinsangRouter
from Shinsangmarket.shop import router as ShinsangShopRouter 
from Linkshops.product import router as LinkshopRouter
from Linkshops.product import job as LinkshopJob , mupliple_prods_excecute as LinkshopJobMultiple

from fastapi.middleware.cors import CORSMiddleware
from ddmmarket.product import router as DDDMRouter, job as ddmmarketJob
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pymysql
import os
from fastapi import HTTPException, status

load_dotenv()


app = FastAPI(title='Sokodress scraping')




@app.get('/')
def root():
    return {'msg' : 'Healthy'}

# 임시로 만들어진 라우트
@app.delete('/product/{product_id}')
def delete_product(product_id):
    conn = pymysql.connect(
        host=os.getenv('host'),
        port=int(str(os.getenv('port'))),
        user=os.getenv('user'),
        passwd=os.getenv('passwd'),
        db=os.getenv('db'),
        charset='utf8'
    )
    try:
        cur = conn.cursor()
        sql_img = """DELETE FROM ProductImages WHERE product_id = %s"""
        sql_option = """DELETE FROM ProductOptions WHERE product_id = %s"""
        sql_fabric = """DELETE FROM FabricInfos WHERE product_id = %s"""
        sql_cat = """DELETE FROM CategoryOfProduct WHERE product_id = %s"""
        sql_prod = """DELETE FROM Products WHERE product_id = %s"""
        cur.execute(sql_img, (product_id))
        cur.execute(sql_option, (product_id))
        cur.execute(sql_fabric, (product_id))
        cur.execute(sql_prod, (product_id))
        cur.execute(sql_cat, (product_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as err:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err)

app.include_router(prefix='/dddm' , router=DDDMRouter)
app.include_router(prefix='/linkshop', router=LinkshopRouter)
app.include_router(prefix='/shinsang' , router=ShinsangRouter)
app.include_router(prefix='/shinsang/shopp', router=ShinsangShopRouter)



@app.on_event('startup')
def init():
    scheduler = BackgroundScheduler()
    
    scheduler.add_job(LinkshopJobMultiple, minutes=1, max_instances=3,trigger=CronTrigger(minute=0, hour=0))
    scheduler.add_job(ddmmarketJob, minutes=1, max_instances=3,trigger=CronTrigger(minute=0, hour=5))
    scheduler.start()


app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])


if __name__ == '__main__':
     uvicorn.run("__main__:app", port=5000, host='0.0.0.0', reload=True, log_level='info', factory=True)
