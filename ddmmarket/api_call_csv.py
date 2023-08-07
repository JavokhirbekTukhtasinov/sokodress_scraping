# ■■■■■■■■■■■■■■■■ Library ■■■■■■■■■■■■■■■■
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
from urllib import parse
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
import webbrowser


# ■■■■■■■■■■■■■■■■ ■■■■■■■■■■■■■■■■
# AWS S3 server connect
s3 = boto3.client(
    's3',
    aws_access_key_id = 'AKIAXHNKF4YFB6E7I7OI',
    aws_secret_access_key = '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',
)

white_list = ['125.141.73.82', '124.56.158.191']


# ■■■■■■■■■■■■■■■■ ■■■■■■■■■■■■■■■■
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# IP check(white list)
@app.before_request
def limit_remote_addr():
    if request.remote_addr in white_list:
        pass
    else:
        abort(403)

# call(http://ip:port/call?store_id=매장고유링크값)
# e.g. http://34.200.179.185:5002/call?store_id=미코앤코
@app.route('/call', methods=['GET','POST'])
@cross_origin()
def predict_code():   
    store_id = (request.args.get('store_id'))
    print(f"store_id: {store_id} parsing: {parse.quote(store_id)}")

    return (model_predict(store_id))

def model_predict(store_id):
    '''
    # AWS S3 - shops 내의 csv 파일 불러오기
    bucket = 'sokodress'
    # https://sokodress.s3.ap-northeast-2.amazonaws.com/shops/%EB%AF%B8%EC%BD%94%EC%95%A4%EC%BD%94.csv
    # bucket_file = f'shops/{parse.quote(store_id)}.csv'
    bucket_file = f'shops/{store_id}.csv'
    local_file_path = f'aws_shops/{store_id}.csv'

    s3.download_file(
        bucket,
        bucket_file,
        local_file_path
    )
    '''

    webbrowser.open(f"https://sokodress.s3.ap-northeast-2.amazonaws.com/shops/{parse.quote(store_id)}.csv")

    # log_message = {"Message": "Success"}
    log_message = {f"'Message':'Success File & Call IP : {request.remote_addr}'"}

    resp = Response(json.dumps(log_message, ensure_ascii=False).encode('utf8'), status=200, mimetype='application/json')
    
    return resp
    

@app.errorhandler(Exception)
@cross_origin(origin="*", headers=['Content-Type', 'Authorization'])
def exception_handler(error):
    print(error)
    log_message = {f"'Message':'Fail File & Call IP : {request.remote_addr}'"}
    return log_message

if __name__ == '__main__': 
	app.run(host='0.0.0.0', debug=True, port=5002)