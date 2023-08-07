from waitress import serve
import api_goods

serve(api_goods.app, host='0.0.0.0', port=5002, threads=4)