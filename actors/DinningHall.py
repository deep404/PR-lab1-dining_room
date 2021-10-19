import uuid
import queue
import random
import time
import requests
import logging
import threading
from actors.Table import Table
from actors.Waiter import Waiters

logger = logging.getLogger(__name__)
lock = threading.Lock()

# KITCHEN_HOST = 'localhost'
KITCHEN_HOST = 'kitchen'


class DinningHall:
    def __init__(self, config):
        self.config = config
        self.id_ = config["restaurant_id"]
        self.name = f'DH-{self.id_}'
        self.done_orders = []
        self.orders = []
        self.tables = [Table(self, i) for i in range(config['tables_no'])]
        self.waiters = [Waiters(self, i) for i in range(config['waiters_no'])]
        self.orders_q = queue.Queue()
        self.rating_stars = []
        self.avg_rating = config['rating']
        self.TIME_UNIT = 1

        # start waiters work
        for i, waiter in enumerate(self.waiters):
            threading.Thread(target=waiter.search_order, daemon=True).start()

    def generate_dh_order(self):
        while True:
            time.sleep(2)
            (table_idx, table) = next(((i, table) for i, table in enumerate(self.tables) if table.status == 'FREE'), (None, None))
            max_wait = 0
            items = []
            if table_idx is not None:
                time.sleep(random.randint(2, 10) * self.TIME_UNIT)
                for i in range(random.randint(1, 5)):
                    food = random.choice(self.config['menu'])
                    if max_wait < food['preparation-time']:
                        max_wait = food['preparation-time']
                    items.append(food['id'])
                max_wait *= 1.3

                order_id = uuid.uuid4().hex[0:7]
                order = {
                    'id': order_id,
                    'items': items,
                    'priority': random.randint(1, 5),
                    'max_wait': max_wait,
                    'table_id': table.id
                }
                self.orders_q.put_nowait(order)
                self.orders.append(order)
                table.status = 'WAITING_WAITER'
                table.order_id = order_id
                logger.info(f'{self.name} Table-{table.id} generated new order-{order_id}')

            else:
                # free one random table that is already served
                time.sleep(random.randint(2, 10) * self.TIME_UNIT)
                idxs = [table for table in self.tables if table.status == 'ORDER_SERVED']
                if len(idxs):
                    rand_idx = random.randrange(len(idxs))
                    self.tables[rand_idx].status = 'FREE'

    def get_restaurant_data(self):
        return {'config': self.config}

    def get_menu(self):
        return {'menu': self.config['menu'], 'restaurant_name': self.config['name']}

    def order(self, data):
        logger.info(f'{self.name}, NEW order: {data["order_id"]} | request to kitchen PORT: {self.config["kitchen_port"]}\n')
        self.orders.append(data)
        res = requests.post(f'http://{KITCHEN_HOST}:{self.config["kitchen_port"]}/order', json=data)
        return res.json()

    def get_order(self, order_id):
        logger.info(f'{self.name}, client requested for order: {order_id}\n')
        order = next((x for x in self.done_orders if x['order_id'] == order_id), None)
        if order is not None:
            logger.info(f'{self.name}, client received order: {order_id}\n')
            return {**order, 'is_ready': True}
        else:
            logger.info(f'{self.name}, client order: {order_id} is not ready!\n')
            return {'order_id': order_id, 'is_ready': False, 'estimated_waiting_time': 3}

    def distribution(self, order):
        self.done_orders.append(order)
        if order['table_id'] is not None:
            # serve the order to table
            logger.info(f'{self.name} NEW distribution for table: {order["table_id"]}')
            waiter = next((w for w in self.waiters if w.id == order['waiter_id']), None)
            waiter.serve_order(order)
        else:
            # keep the order, so client can request it
            logger.info(f'{self.name} NEW distribution for client service')
        return {'isSuccess': True}

    def update_rating(self, data):
        lock.acquire()
        self.rating_stars.append(data['stars'])
        avg = float(sum(s for s in self.rating_stars)) / len(self.rating_stars)
        self.avg_rating = avg
        lock.release()
        logger.info(f'{self.name} order_id: {data["order_id"]} | updated RATING: {self.avg_rating}')
        return {'updated_rating': self.avg_rating}
