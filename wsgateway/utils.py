from typing import Dict, Union
import asyncio
import logging

class KeyedQueueMap(object):
    queue_map: Dict[Union[int, str], asyncio.Queue]
    queue_map_lock: asyncio.Lock
    id_counter: int

    def __init__(self):
        self.queue_map = {}
        self.queue_map_lock = asyncio.Lock()
        self.id_counter = 0

    async def get_queue(self, id: Union[int, str]):
        async with self.queue_map_lock:
            return self.queue_map[id] if id in self.queue_map else None

    async def has_queue(self, id: Union[int, str]):
        async with self.queue_map_lock:
            return id in self.queue_map

    async def create_named_queue(self, id: Union[int, str]):
        async with self.queue_map_lock:
            queue = asyncio.Queue()
            self.queue_map[id] = queue
            return queue

    async def create_inc_queue(self):
        async with self.queue_map_lock:
            self.id_counter += 1
            new_id = self.id_counter
            queue = asyncio.Queue()
            self.queue_map[new_id] = queue
            return new_id, queue

    async def remove_queue(self, id: Union[int, str]):
        async with self.queue_map_lock:
            self.queue_map.pop(id, None)

async def read_into_queue(queue: asyncio.Queue, reader: asyncio.StreamReader, close_event: Union[asyncio.Event, None] = None):
    try:
        while not reader.at_eof():
            message = await reader.read(4096)
            if len(message) > 0:
                await queue.put(message)
            else:
                await asyncio.sleep(0.001)
    finally:
        if close_event:
            close_event.set()