import asyncio
import websockets
import random
import struct
from typing import Dict, Union
import logging
import argparse

from wsgateway.messages import unpack_msg_provider, pack_msg_provider, pack_msg_close
from wsgateway.utils import KeyedQueueMap
from wsgateway.config import setup_args_and_config
from wsgateway.log import *

PW = ""

client_recv_queue_map = KeyedQueueMap()
provider_recv_queue_map = KeyedQueueMap()

async def handle_client_message(msg: bytes, client_id: int, provider_name: str, client_queue: asyncio.Queue):
    provider_msg = pack_msg_provider(client_id, msg)

    provider_queue = await provider_recv_queue_map.get_queue(provider_name)
    if provider_queue:
        log_outbound("sending message to provider")
        await provider_queue.put(provider_msg)
    else: 
        log_outbound("sending message to client")
        await client_queue.put(pack_msg_close())
        log_internal_warn("provider with id {} was no found! A connection closed message should be sent to the client!".format(provider_name))


async def handle_connection_client(websocket, provider_name: str):
    client_id, recv_queue = await client_recv_queue_map.create_inc_queue()

    try:
        while websocket.open:
            listener_task = asyncio.ensure_future(websocket.recv())
            producer_task = asyncio.ensure_future(recv_queue.get())

            done, pending = await asyncio.wait(
                [listener_task, producer_task],
                return_when=asyncio.FIRST_COMPLETED)

            if listener_task in done:
                message = listener_task.result()
                log_inbound("received message for provider")
                await handle_client_message(message, client_id, provider_name, recv_queue)
            else:
                listener_task.cancel()

            if producer_task in done:
                message = producer_task.result()
                log_inbound("received message for client")
                log_outbound("sending message to client")
                await websocket.send(message)
            else:
                producer_task.cancel()
    except Exception as e:
        logging.info("server had error event: {}".format(e))
    finally:
        await client_recv_queue_map.remove_queue(client_id)

async def handle_provider_message(msg: bytes, provider_queue: asyncio.Queue):
    client_id, client_msg = unpack_msg_provider(msg)

    client_queue = await client_recv_queue_map.get_queue(client_id)
    if client_queue:
        log_outbound("sending message to client with id {}".format(client_id))
        await client_queue.put(client_msg)
    else: 
        log_outbound("sending close message to provider")
        await provider_queue.put(pack_msg_provider(client_id, pack_msg_close()))
        log_internal_warn("client with id {} was no found! A connection closed message should be sent to the provider!".format(client_id))

async def handle_connection_provider(websocket, provider_name: str):
    log_internal("creating provider with name: {}".format(provider_name))
    
    recv_queue = await provider_recv_queue_map.create_named_queue(provider_name)
    try:
        while websocket.open:
            listener_task = asyncio.ensure_future(websocket.recv())
            producer_task = asyncio.ensure_future(recv_queue.get())

            done, pending = await asyncio.wait(
                [listener_task, producer_task],
                return_when=asyncio.FIRST_COMPLETED)

            if listener_task in done:
                message = listener_task.result()
                log_inbound("received message for client")
                await handle_provider_message(message, recv_queue)
            else:
                listener_task.cancel()

            if producer_task in done:
                message = producer_task.result()
                log_inbound("received message for provider")
                log_outbound("sending message to provider")
                await websocket.send(message)
            else:
                producer_task.cancel()
    except Exception as e:
        logging.info("server had error event: {}".format(e))
    finally:
        await provider_recv_queue_map.remove_queue(provider_name)

async def handle_connection(websocket, path: str):
    log_internal("ws-client connected to path: {}".format(path))
    
    pw_data: bytes = await websocket.recv()
    pw_text = pw_data.decode(encoding="utf-8")
    log_inbound("receiving password")

    if pw_text != PW:
        log_internal("password was wrong closing the connection...")
        await websocket.close()
        return
    
    if path.startswith("/c/"):
        log_internal("connection is used as client")
        provider_name = path[3:]
        await handle_connection_client(websocket, provider_name)
    elif path.startswith("/p/"):
        log_internal("connection is used as provider")
        provider_name = path[3:]
        await handle_connection_provider(websocket, provider_name)

def main():
    config = setup_args_and_config("Gateway")
    config.parse_gateway_password()
    config.parse_gateway_port()
    config.finish()

    global PW
    PW = config.gateway_pw

    start_server = websockets.serve(handle_connection, 'localhost', config.gateway_port)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()