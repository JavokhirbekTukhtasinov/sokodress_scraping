from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

@app.route('/sangga/<param>') #get echo api
def get_sangga_call(param):
    df = pd.read_csv(f'./csv/{param}.csv')

    sangga_total = []
    sangga_one = {}

    for i in range(df.shape[0]):
        sangga_one = {
            # 'store_id_num': df['store_id_num'].loc[i],
            'sangga_name': df['sangga_name'].loc[i],
            'store_name': df['store_name'].loc[i],
            'store_phone': df['store_phone'].loc[i],
            'store_address': df['store_address'].loc[i],
            'store_aws_image': df['store_aws_image'].loc[i],
            'accounts': df['accounts'].loc[i],
            'number_of_total_products': df['number_of_total_products'].loc[i],
            'accounts_products': df['accounts_products'].loc[i]
        }
        
        sangga_total.append(sangga_one)
    
    return jsonify(sangga_total)

if __name__ == "__main__":
    app.run(debug=True)