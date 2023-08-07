from fastapi import FastAPI
import uvicorn

from Shinsangmarket.product import router as ShinsangRouter

app = FastAPI(title='Sokodress scraping')


@app.get('/')
def root():
    return {'msg' : 'Healthy'}


# Bunker 벙커 id : 25232


app.include_router(prefix='/shinsang' , router=ShinsangRouter)

if __name__ == '__main__':
     uvicorn.run(app, port=5000, reload=True, log_level='info', factory=True)
