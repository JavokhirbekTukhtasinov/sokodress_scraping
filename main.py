from fastapi import FastAPI
import uvicorn
import datetime
from Shinsangmarket.product import router as ShinsangRouter
from Shinsangmarket.shop import router as ShinsangShopRouter 
from Linkshops.product import router as LinkshopRouter
from Linkshops.product import job as LinkshopJob , mupliple_prods_excecute as LinkshopJobMultiple
# from Linkshops.product_new import router as LinkshopRouter
from fastapi.middleware.cors import CORSMiddleware
# from ddmmarket.product import router as DDDMRouter
from ddmmarket.product_new import router as DDDMRouter, job as ddmmarketJob
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


app = FastAPI(title='Sokodress scraping')




@app.get('/')
def root():
    return {'msg' : 'Healthy'}



app.include_router(prefix='/dddm' , router=DDDMRouter)
app.include_router(prefix='/linkshop', router=LinkshopRouter)
app.include_router(prefix='/shinsang' , router=ShinsangRouter)
app.include_router(prefix='/shinsang/shopp', router=ShinsangShopRouter)
load_dotenv()


@app.on_event('startup')
def init():
    scheduler = BackgroundScheduler()
    
    scheduler.add_job(LinkshopJobMultiple, minutes=1, max_instances=3,trigger=CronTrigger(minute=0, hour=0))
    scheduler.add_job(ddmmarketJob, minutes=1, max_instances=3,trigger=CronTrigger(minute=0, hour=5))
    scheduler.start()


app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])


if __name__ == '__main__':
     uvicorn.run("__main__:app", port=5000, host='0.0.0.0', reload=True, log_level='info', factory=True)
