import asyncio
import socket
import struct
import logging
import websockets
import os
import json
from wsgateway.messages import pack_msg_close, pack_msg_data, pack_msg_open, unpack_msg_data, MSG_TYPE_CLOSE, MSG_TYPE_DATA
from wsgateway.log import *
from wsgateway.utils import read_into_queue
import configparser
import argparse

# config

REMOTE_PORT = 0
REMOTE_HOSTNAME = ""

GATEWAY_URL_FULL = ""
GATEWAY_PW = ""

LOCAL_PORT = 0

async def handle_client(reader, writer):
    log_internal("opening the websocket connection")
    websocket = await websockets.connect(GATEWAY_URL_FULL)
    log_outbound("logging in")
    await websocket.send(GATEWAY_PW.encode(encoding="utf-8"))
    log_outbound_msg_open_connection()
    await websocket.send(pack_msg_open(REMOTE_HOSTNAME, REMOTE_PORT))

    reader_closed = asyncio.Event()
    reader_queue = asyncio.Queue()
    asyncio.create_task(read_into_queue(reader_queue, reader, reader_closed))

    is_remote_connection_closed = False

    try:
        while not writer.is_closing() and not reader_closed.is_set():
            listener_task = asyncio.ensure_future(reader_queue.get())
            producer_task = asyncio.ensure_future(websocket.recv())
            done, pending = await asyncio.wait(
                [listener_task, producer_task],
                return_when=asyncio.FIRST_COMPLETED)

            if listener_task in done:
                message = listener_task.result()
                if len(message) > 0:
                    log_outbound_msg_data()
                    await websocket.send(pack_msg_data(message))
            else:
                listener_task.cancel()

            if producer_task in done:
                message = producer_task.result()

                if message[0] == MSG_TYPE_DATA:
                    message_data = unpack_msg_data(message)
                    log_inbound_msg_data()
                    writer.write(message_data)
                    await writer.drain()
                elif message[0] == MSG_TYPE_CLOSE:
                    log_inbound_msg_close_connection()
                    is_remote_connection_closed = True
                    writer.close()
                    await writer.wait_closed()
                else:
                    log_inbound("client received an unexpected message: {}".format(message.hex()[:10]))
            else:
                producer_task.cancel()
    finally:
        log_internal("client host closed!")
        if not is_remote_connection_closed:
            log_outbound_msg_close_connection()
            await websocket.send(pack_msg_close())
        log_internal("closing the websocket connection!")
        await websocket.close()

async def run_server():
    log_internal("starting server")
    server = await asyncio.start_server(handle_client, 'localhost', LOCAL_PORT)
    async with server:
        await server.serve_forever()

def main():
    parser = argparse.ArgumentParser(description='Websocket Gateway - Client')
    parser.add_argument('--profile', dest='profile', help='.ini file storing the profile configuration.')
    
    define_logging_parser_args(parser)
    
    args = parser.parse_args()

    if not setup_logging(args):
        print("bad logging arguments.")
        parser.print_help()
        return

    if not args.profile or not os.path.exists(args.profile):
        print("profile not set or file not found!")
        print("---")
        parser.print_help()
        return

    config = configparser.ConfigParser()
    config.read(args.profile)

    remote_provider = None

    if "remote" in config:
        remote_config = config["remote"]

        global REMOTE_PORT, REMOTE_HOSTNAME
        remote_provider = remote_config.get("provider")
        REMOTE_PORT = remote_config.getint("port")
        REMOTE_HOSTNAME = remote_config.get("hostname")
    else:
        print("ERROR: the remote section was not found in the profile file!")

    if "local" in config:
        local_config = config["local"]

        global LOCAL_PORT
        LOCAL_PORT = local_config.getint("port")
    else:
        print("ERROR: the local section was not found in the profile file!")

    if "gateway" in config:
        gw_config = config["gateway"]

        global GATEWAY_URL_FULL, GATEWAY_PW

        gateway_url = gw_config.get("url")
        gateway_url_base = gateway_url + "c/" if gateway_url.endswith("/") else gateway_url + "/c/"
        GATEWAY_URL_FULL = gateway_url_base + remote_provider

        GATEWAY_PW = gw_config.get("password")
    else:
        print("ERROR: the gateway section was not found in the profile file!")

    asyncio.run(run_server())

if __name__ == "__main__":
    main()