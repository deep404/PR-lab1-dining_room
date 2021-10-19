import requests
import threading
from flask import Flask, request
import logging
import coloredlogs
import addons
from actors.DinningHall import DinningHall

logging.basicConfig(filename='dinning.log', level=logging.DEBUG, format='%(asctime)s: %(message)s', datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')

restaurants = addons.get_restaurant()

HOST = '0.0.0.0'
FO_PORT = 3000
# FO_HOST = 'localhost'
FO_HOST = 'food_ordering'

app1 = Flask(restaurants[0]['name'])
app2 = Flask(restaurants[1]['name'])
app3 = Flask(restaurants[2]['name'])
app4 = Flask(restaurants[3]['name'])

d1 = DinningHall(restaurants[0])
d2 = DinningHall(restaurants[1])
d3 = DinningHall(restaurants[2])
d4 = DinningHall(restaurants[3])

dinning_halls = [{
    'app': app1,
    'dh': d1
}, {
    'app': app2,
    'dh': d2
}, {
    'app': app3,
    'dh': d3
}, {
    'app': app4,
    'dh': d4
}]

# set up each Dinning-Hall (dh) endpoints
for i, app_data in enumerate(dinning_halls):
    app = app_data['app']
    dh = app_data['dh']

    # POST /distribution : exposed for Kitchens
    @app.route('/distribution', methods=['POST'])
    def distribution(app_dh=dh):
        order = request.get_json()
        return app_dh.distribution(order)

    # GET /menu            : exposed for Client Service
    @app.route('/menu', methods=['GET'])
    def menu(app_dh=dh):
        return app_dh.get_menu()

    # POST /v2/order       : exposed for Client Service
    @app.route('/v2/order', methods=['POST'])
    def order_v2(app_dh=dh):
        data = request.get_json()
        return app_dh.order(data)

    # GET /v2/order/id     : exposed for Food Ordering
    @app.route('/v2/order/<order_id>', methods=['GET'])
    def get_order(order_id, app_dh=dh):
        return app_dh.get_order(order_id)

    # GET /restaurant_data : exposed for Kitchens
    @app.route('/restaurant_data', methods=['GET'])
    def get_restaurant_data(app_dh=dh):
        # start generating orders once the kitchen was configured
        threading.Thread(target=app_dh.generate_dh_order, daemon=True).start()
        return app_dh.get_restaurant_data()

    # POST /rating         : exposed for Client Service
    @app.route('/rating', methods=['POST'])
    def rating(app_dh=dh):
        data = request.get_json()
        return app_dh.update_rating(data)


def register_all():
    rests = addons.get_restaurant()
    requests.post(f'http://{FO_HOST}:{FO_PORT}/register', json=rests[0])
    requests.post(f'http://{FO_HOST}:{FO_PORT}/register', json=rests[1])
    requests.post(f'http://{FO_HOST}:{FO_PORT}/register', json=rests[2])
    requests.post(f'http://{FO_HOST}:{FO_PORT}/register', json=rests[3])
    logger.info(f'Registered {len(rests)} restaurants\n')


def main():
    open("dinning.log", "w").close()

    # each dinning hall is a separate flask application
    threading.Thread(target=lambda: app1.run(host=HOST, port=d1.config['dinning_port'], debug=False, use_reloader=False, threaded=True), name=f'FLASK-DH1', daemon=True).start()
    threading.Thread(target=lambda: app2.run(host=HOST, port=d2.config['dinning_port'], debug=False, use_reloader=False, threaded=True), name=f'FLASK-DH2', daemon=True).start()
    threading.Thread(target=lambda: app3.run(host=HOST, port=d3.config['dinning_port'], debug=False, use_reloader=False, threaded=True), name=f'FLASK-DH3', daemon=True).start()
    threading.Thread(target=lambda: app4.run(host=HOST, port=d4.config['dinning_port'], debug=False, use_reloader=False, threaded=True), name=f'FLASK-DH4', daemon=True).start()

    # register 'em to food ordering service
    register_all()

    while True:
        pass


if __name__ == '__main__':
    main()
