import threading
import random
import time
import uuid
import config as config



class DinningHall(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(DinningHall, self).__init__(*args, **kwargs)

    def run(self):
        while True:
            time.sleep(1)
            self.generate_random_order()

    @staticmethod
    def generate_random_order():
        (table_idx, table) = next(((i, table) for i, table in enumerate(config.TABLES_LIST) if table['state'] == config.TABLE_FREE), (None, None))
        if table_idx is not None:
            max_wait_time = 0
            items = []
            for i in range(random.randint(1, 5)):
                food = random.choice(config.FOOD_LIST)
                if max_wait_time < food['preparation-time']:
                    max_wait_time = food['preparation-time']
                items.append(food['id'])
            max_wait_time = round(max_wait_time * 1.3)

            new_order_id = uuid.uuid4().hex
            new_order = {
                'id': new_order_id,
                'items': items,
                'priority': random.randint(1, 5),
                'max_wait': max_wait_time,
                'table_id': table['id']
            }
            config.ORDER_Q.put(new_order)
            config.ORDER_LIST.append(new_order)

            config.TABLES_LIST[table_idx]['state'] = config.TABLE_WAITING_FOR_WAITER
            config.TABLES_LIST[table_idx]['order_id'] = new_order_id
        else:
            # free one random table that is already served
            time.sleep(random.randint(2, 10) * config.TIME_UNIT)
            idxs = [table for table in config.TABLES_LIST if table['state'] == config.TABLE_ORDER_SERVED]
            if len(idxs):
                rand_idx = random.randrange(len(idxs))
                config.TABLES_LIST[rand_idx]['state'] = config.TABLE_FREE