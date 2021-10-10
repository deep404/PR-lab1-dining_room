import time
import random
import threading
import requests
import queue
import logging
import config as config


logger = logging.getLogger(__name__)


class Waiter(threading.Thread):
    def __init__(self, info, *args, **kwargs):
        super(Waiter, self).__init__(*args, **kwargs)
        self.name = info['name']
        self.id = info['id']
        self.daemon = True

    def run(self):
        while True:
            self.search_order()

    def serve_order(self, order_to_serve):
        # check if the order is the same order that what was requested
        req_order = next((order for i, order in enumerate(config.ORDER_LIST) if order['id'] == order_to_serve['order_id']), None)
        if req_order is not None and req_order['items'].sort() == order_to_serve['items'].sort():
            # update table state
            table_idx = next((i for i, table in enumerate(config.TABLES_LIST) if table['id'] == order_to_serve['table_id']), None)
            config.TABLES_LIST[table_idx]['state'] = config.TABLE_ORDER_SERVED

            # calculate total order time
            order_total_preparing_time = int(time.time() - order_to_serve['time_start'])

            # calculate nr of start
            order_stars = {'order_id': order_to_serve['order_id']}
            if order_to_serve['max_wait'] > order_total_preparing_time:
                order_stars['star'] = 5
            elif order_to_serve['max_wait'] * 1.1 > order_total_preparing_time:
                order_stars['star'] = 4
            elif order_to_serve['max_wait'] * 1.2 > order_total_preparing_time:
                order_stars['star'] = 3
            elif order_to_serve['max_wait'] * 1.3 > order_total_preparing_time:
                order_stars['star'] = 2
            elif order_to_serve['max_wait'] * 1.4 > order_total_preparing_time:
                order_stars['star'] = 1
            else:
                order_stars['star'] = 0

            config.ORDER_STARS.append(order_stars)
            avg = float(sum(s['star'] for s in config.ORDER_STARS)) / len(config.ORDER_STARS)

            served_order = {**order_to_serve, 'total_preparing_time': order_total_preparing_time, 'status': config.ORDER_SERVED}
            config.SERVED_ORDERS.append(served_order)
            logger.info(f'#{self.id}-{threading.current_thread().name}-$ SERVED orderId: {served_order["order_id"][0:4]} | tableId: {served_order["table_id"]} | maxWait: {served_order["max_wait"]} | cookingTime: {served_order["cooking_time"]} | totalTime: {served_order["total_preparing_time"]} sec. [avg-star]: {avg}')
        else:
            raise Exception(f'The order is not the same as was requested. Original: {req_order}, given: {order_to_serve}')

    def search_order(self):
        try:
            order = config.ORDER_Q.get()
            config.ORDER_Q.task_done()

            table_idx = next((i for i, table in enumerate(config.TABLES_LIST) if table['id'] == order['table_id']), None)
            logger.info(f'#{self.id}-{threading.current_thread().name}-$ PICKED UP orderId: {order["id"][0:4]} | priority: {order["priority"]} | items: {order["items"]}')
            config.TABLES_LIST[table_idx]['state'] = config.TABLE_WAITING_FOR_ORDER_TO_BE_SERVED
            payload = dict({
                'order_id': order['id'],
                'table_id': order['table_id'],
                'waiter_id': self.id,
                'items': order['items'],
                'priority': order['priority'],
                'max_wait': order['max_wait'],
                'time_start': time.time()
            })
            time.sleep(random.randint(2, 4) * config.TIME_UNIT)
            # requests.post('http://kitchen:8000/order', json=payload, timeout=0.0000000001)
            requests.post('http://localhost:8000/order', json=payload, timeout=0.0000000001)

        except (queue.Empty, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            pass