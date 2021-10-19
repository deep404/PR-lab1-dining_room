import requests
import logging
import random
import time


logger = logging.getLogger(__name__)

KITCHEN_HOST = 'kitchen'


class Waiter:
    def __init__(self, dh, i):
        self.name = f'{dh.name} Waiter-{i}'
        self.dh = dh
        self.id = i
        self.TIME_UNIT = 1

    def serve_order(self, order_to_serve):
        # check if the order is the same order that what was requested
        req_order = next((order for i, order in enumerate(self.dh.orders) if order['id'] == order_to_serve['order_id']), None)
        if req_order is not None and req_order['items'].sort() == order_to_serve['items'].sort():
            # update table state
            table_idx = next((i for i, table in enumerate(self.dh.tables) if table.id == order_to_serve['table_id']), None)
            self.dh.tables[table_idx].status = 'ORDER_SERVED'

            # calculate total order time
            order_total_preparing_time = int(time.time() - order_to_serve['time_start'])

            # calculate nr of start
            stars = self.rating_stars(order_to_serve['max_wait'], order_total_preparing_time)
            self.dh.update_rating({'order_id': order_to_serve['order_id'], 'stars': stars})

            served_order = {**order_to_serve, 'total_preparing_time': order_total_preparing_time}
            self.dh.done_orders.append(served_order)
            logger.info(f'{self.name}-$ SERVED orderId: {served_order["order_id"]} | '
                        f'table_id: {served_order["table_id"]} | '
                        f'max_wait: {served_order["max_wait"]} | '
                        f'total_preparing_time: {served_order["total_preparing_time"]} sec. | '
                        f'stars | : {stars}')
        else:
            raise Exception(f'{self.name} The order is not the same as was requested. Original: {req_order}, given: {order_to_serve}')

    def search_order(self):
        while True:
            try:
                order = self.dh.orders_q.get_nowait()
                if order:
                    time.sleep(random.randint(2, 4) * self.TIME_UNIT)
                    table_idx = next((i for i, table in enumerate(self.dh.tables) if table.id == order['table_id']), None)
                    logger.info(f'{self.name}-$ PICKED UP orderId: {order["id"]} | priority: {order["priority"]} | items: {order["items"]}')
                    self.dh.tables[table_idx].status = 'ORDER_PICKED_UP'
                    req = {
                        'order_id': order['id'],
                        'table_id': order['table_id'],
                        'waiter_id': self.id,
                        'items': order['items'],
                        'priority': order['priority'],
                        'max_wait': order['max_wait'],
                        'time_start': time.time()
                    }
                    requests.post(f'http://{KITCHEN_HOST}:{self.dh.config["kitchen_port"]}/order', json=req, timeout=0.0000000001)
            except Exception as e:
                pass

    @staticmethod
    def rating_stars(max_wait, total):
        stars = 0
        if max_wait >= total:
            stars = 5
        elif max_wait * 1.1 >= total:
            stars = 4
        elif max_wait * 1.2 >= total:
            stars = 3
        elif max_wait * 1.3 >= total:
            stars = 2
        elif max_wait * 1.4 >= total:
            stars = 1
        return stars
