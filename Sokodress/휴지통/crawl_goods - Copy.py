from selenium import webdriver
import pandas as pd
import numpy as np
import time
import datetime
from selenium.webdriver.common.action_chains import ActionChains
from flask_cors import CORS, cross_origin
from flask import Flask, request, jsonify
from flask_restful import reqparse, abort, Api, Resource
import json
from flask import Response
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--start-maximized')

# path='/usr/bin/chromedriver'


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/call', methods=['GET','POST'])
@cross_origin()
def predict_code():   
	store_id = (request.args.get('store_id'))
	days_ago = int(request.args.get('days_ago'))
	return (model_predict(store_id,days_ago))

def model_predict(store_id,days_ago):
	global driver
	driver = webdriver.Chrome('C:/Users/Administrator/Desktop/Sokodress/chromedriver.exe', chrome_options=chrome_options)
	
	driver.get("https://sinsangmarket.kr/login")
	time.sleep(1)
	driver.save_screenshot('screenie.png')
	# 태그가 해당 경로에서 1개면 그대로 사용(div), 여러 개면 구분자 사용(div[1], div[2]..)
	driver.find_element(By.XPATH,'//*[@id="app"]/div[1]/div/header/div/div[2]/div[3]').click()
	driver.find_elements(By.CLASS_NAME,'text-input')[0].send_keys('rayout2022')
	driver.find_elements(By.CLASS_NAME,'text-input')[1].send_keys('elesther2022!')
	driver.find_element(By.XPATH,'//*[@id="app"]/div[1]/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/button').click()
	time.sleep(1.0)

	driver.get('https://sinsangmarket.kr/search')


	driver.get(f'https://sinsangmarket.kr/store/{store_id}')

	time.sleep(2)

	total_goods_style=[]
	total_goods_name=[]
	total_goods_price=[]
	total_goods_star=[]
	total_goods_category_big=[]
	total_goods_category_small=[]
	total_goods_color=[]
	total_goods_size=[]
	total_goods_composition=[]
	total_goods_made=[]
	total_goods_sheet=[]
	total_goods_registration_date=[]
	total_goods_fabric_thickness=[]
	total_goods_fabric_seethrough=[]
	total_goods_fabric_stretchy=[]
	total_goods_fabric_lining=[]
	total_goods_laundry=[]
	total_goods_image=[]

	cloth_cate_list=[x for x in driver.find_elements_by_css_selector('ul.category-list') if '의류' in x.text]



	for i in range(len(cloth_cate_list)):
		time.sleep(1)
		driver.execute_script("window.scrollTo(0, 0)") 
		time.sleep(1)
		element = cloth_cate_list[i]
		actions = ActionChains(driver)
		actions.move_to_element(element).perform()
		time.sleep(0.3)
		cloth_cate_list[i].click()
		time.sleep(1)
		driver.find_element_by_xpath("//li[contains(text(), '전체')]").click()

		now = datetime.datetime.now()

		two_months_ago=now - datetime.timedelta(days=days_ago)

		try:
			driver.find_element_by_css_selector('button.list-more').click()
		except Exception as e:
			pass

		time.sleep(1)
		cate_list=driver.find_element_by_css_selector('ul.style__filter-list').find_elements_by_css_selector('span.block.flex.items-center')

		for j in range(1,len(cate_list)):
			driver.execute_script("window.scrollTo(0, 0)") 
			driver.find_element_by_css_selector('ul.style__filter-list').find_elements_by_css_selector('span.block.flex.items-center')[j].click() # 로맨틱 클릭
			goods_style=cate_list[j].text
			#break_loop=False

			for k in range(2):
				driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
				time.sleep(0.1)

			good_list=(driver.find_elements_by_xpath('//div[@data-group="goods-list"]')) # 상품리스트


			for k in range(len(good_list)):
				driver.execute_script("window.scrollTo(0, 0)") 
				driver.find_elements_by_xpath('//div[@data-group="goods-list"]')[k].click()

				#driver.switch_to.window(window_name=driver.window_handles[0])
				wait = WebDriverWait(driver, 10)
				try:
					element = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), '상품등록정보')]/following-sibling::div")))
				except Exception as e:
					driver.quit()
					return "api 다시 실행해주세요"
				time.sleep(0.1)
				
				try:
					goods_registration_date = driver.find_element_by_xpath("//div[contains(text(), '상품등록정보')]/following-sibling::div").text
				except Exception as e:
					goods_registration_date=''
				# 날짜가 2개월 보다 더 크면 break
				if datetime.datetime.strptime(goods_registration_date.split(' ')[0],'%Y.%m.%d')<two_months_ago:
					#break_loop=True
					driver.find_element_by_class_name('close-button').click()
					break
				
				try:
					goods_name=driver.find_element_by_xpath('//div[@class="goods-detail-right__row"]').find_element_by_css_selector('p.title').text
				except Exception as e:
					goods_name=''

				try:
					goods_price=driver.find_element_by_xpath('//*[@id="goods-detail"]').find_element_by_css_selector('div.price.flex.items-center').text
				except Exception as e:
					goods_price=''

				try:
					goods_star=driver.find_element_by_xpath('//*[@id="goods-detail"]').find_element_by_css_selector('p.zzim-button__count').text
				except Exception as e:
					goods_star=''

				try:
					temp_image=[]
					for kk in range(len(driver.find_elements_by_xpath('//img[@alt="thumbnail-image"]'))):
						temp_image.append(driver.find_elements_by_xpath('//img[@alt="thumbnail-image"]')[kk].get_attribute('src'))
					goods_image=temp_image
				except Exception as e:
					goods_image=''
				try:
					goods_category_big = driver.find_elements_by_xpath("//div[contains(text(), '카테고리')]/following-sibling::div/div")[0].text
				except Exception as e:
					goods_category_big=''
				try:
					goods_category_small = driver.find_elements_by_xpath("//div[contains(text(), '카테고리')]/following-sibling::div/div")[1].text
				except Exception as e:
					goods_category_small=''

				try:
					goods_color = driver.find_element_by_xpath("//div[contains(text(), '색상')]/following-sibling::div").text
				except Exception as e:
					goods_color=''

				try:
					goods_size = driver.find_element_by_xpath("//div[contains(text(), '사이즈')]/following-sibling::div").text
				except Exception as e:
					goods_size=''
				try:
					goods_composition = driver.find_element_by_xpath("//div[contains(text(), '혼용률')]/following-sibling::div").text
				except Exception as e:
					goods_composition=''

				try:
					goods_made = driver.find_element_by_xpath("//div[contains(text(), '제조국')]/following-sibling::div").text
				except Exception as e:
					goods_made=''
				try:
					goods_sheet = driver.find_element_by_xpath("//div[contains(text(), '낱장 여부')]/following-sibling::div").text
				except Exception as e:
					goods_sheet=''


				try:
					goods_laundry=driver.find_element_by_css_selector('div.laundry-item__name').text
				except Exception as e:
					goods_laundry=''
				try:
					goods_fabric_thickness=[x for x in driver.find_elements_by_xpath("//div[contains(text(), '두께감')]/following-sibling::div/div/div") if x.get_attribute('class')=='min-w-[42px] text-gray-100'][0].text
				except Exception as e:
					goods_fabric_thickness=''
				try:
					goods_fabric_seethrough=[x for x in driver.find_elements_by_xpath("//div[contains(text(), '비침')]/following-sibling::div/div/div") if x.get_attribute('class')=='min-w-[42px] text-gray-100'][0].text
				except Exception as e:
					goods_fabric_seethrough=''
				try:
					goods_fabric_stretchy=[x for x in driver.find_elements_by_xpath("//div[contains(text(), '신축성')]/following-sibling::div/div/div") if x.get_attribute('class')=='min-w-[42px] text-gray-100'][0].text
				except Exception as e:
					goods_fabric_stretchy=''
				try:
					goods_fabric_lining=[x for x in driver.find_elements_by_xpath("//div[contains(text(), '안감')]/following-sibling::div/div/div") if x.get_attribute('class')=='min-w-[42px] text-gray-100'][0].text
				except Exception as e:
					goods_fabric_lining=''
				total_goods_style.append(goods_style)
				total_goods_name.append(goods_name)
				total_goods_price.append(goods_price)
				total_goods_star.append(goods_star)
				total_goods_category_big.append(goods_category_big)
				total_goods_category_small.append(goods_category_small)
				total_goods_color.append(goods_color)
				total_goods_size.append(goods_size)
				total_goods_composition.append(goods_composition)
				total_goods_made.append(goods_made)
				total_goods_sheet.append(goods_sheet)
				total_goods_registration_date.append(goods_registration_date)
				total_goods_fabric_thickness.append(goods_fabric_thickness)
				total_goods_fabric_seethrough.append(goods_fabric_seethrough)
				total_goods_fabric_stretchy.append(goods_fabric_stretchy)
				total_goods_fabric_lining.append(goods_fabric_lining)
				total_goods_laundry.append(goods_laundry)
				total_goods_image.append(goods_image)
				
				driver.find_element_by_class_name('close-button').click()




	driver.quit()

	array = []  
	array.append({'스타일' : total_goods_style})
	array.append({'이름' : total_goods_name})
	array.append({'가격' : total_goods_price})
	array.append({'별점' : total_goods_star})
	array.append({'대카테고리' : total_goods_category_big})
	array.append({'소카테고리' : total_goods_category_small})
	array.append({'색상' : total_goods_color})
	array.append({'사이즈' : total_goods_size})
	array.append({'혼용률' : total_goods_composition})
	array.append({'제조국' : total_goods_made})
	array.append({'등록일' : total_goods_registration_date})
	array.append({'두께감' : total_goods_fabric_thickness})
	array.append({'비침' : total_goods_fabric_seethrough})
	array.append({'신축성' : total_goods_fabric_stretchy})
	array.append({'안감' : total_goods_fabric_lining})
	array.append({'세탁정보' : total_goods_laundry})
	array.append({'이미지' : total_goods_image})

	resp = Response(json.dumps(array, ensure_ascii=False).encode('utf8'), status=200, mimetype='application/json')
	return resp

@app.errorhandler(Exception)
@cross_origin(origin="*",headers=['Content- Type','Authorization'])
def exception_handler(error):
	print(error)
	resp2 = '다시 실행해주세요.'
	driver.quit()
	return resp2

if __name__ == '__main__': 
	app.run(host='0.0.0.0', debug=True, port=5002)