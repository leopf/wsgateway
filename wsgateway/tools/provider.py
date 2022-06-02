import asyncio
import websockets
from wsgateway.utils import KeyedQueueMap, read_into_queue
from wsgateway.messages import *
from wsgateway.log import *
import logging
import argparse

GATEWAY_URL_FULL = ""
GATEWAY_PW = ""

websocket_send_queue: asyncio.Queue = None
websocket_recv_queue_map = KeyedQueueMap()

async def handle_client(client_id: int, open_msg: bytes):
    log_internal("creating client with id: {}".format(client_id))
    hostname, port = unpack_msg_open(open_msg)

    log_internal("resolving the recv queue")
    recv_queue = await websocket_recv_queue_map.get_queue(client_id)
    if not recv_queue:
        await websocket_send_queue.put(pack_msg_provider(client_id, pack_msg_close()))
        log_internal("client recv queue not found. Closing...")
        return

    log_internal("opening a tcp connection to {}:{}".format(hostname, port))
    reader, writer = await asyncio.open_connection(hostname, port)
    is_remote_connection_closed = False

    reader_closed = asyncio.Event()
    reader_queue = asyncio.Queue()
    asyncio.create_task(read_into_queue(reader_queue, reader, reader_closed))

    try:
        while not writer.is_closing() and not reader_closed.is_set():
            listener_task = asyncio.ensure_future(recv_queue.get())
            producer_task = asyncio.ensure_future(reader_queue.get())

            done, pending = await asyncio.wait(
                [listener_task, producer_task],
                return_when=asyncio.FIRST_COMPLETED)

            if listener_task in done:
                message = listener_task.result()

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
                    log_inbound("unexpected message: {}".format(message.hex()[:20]))
            else:
                listener_task.cancel()

            if producer_task in done:
                message = producer_task.result()
                if len(message) > 0:
                    log_outbound_msg_data()
                    await websocket_send_queue.put(pack_msg_provider(client_id, pack_msg_data(message)))
            else:
                producer_task.cancel()
    except Exception as e:
        log_internal("server had error event: {}".format(e))
    finally:
        log_internal("provider connectio has closed")
        if not is_remote_connection_closed:
            log_outbound_msg_close_connection()
            await websocket_send_queue.put(pack_msg_provider(client_id, pack_msg_close()))
        if not writer.is_closing():
            log_internal("closing the tcp socket")
            writer.close()
            await writer.wait_closed()
        await websocket_recv_queue_map.remove_queue(client_id)
        

async def start_provider():
    global websocket_send_queue

    websocket_send_queue = asyncio.Queue()
    async with websockets.connect(GATEWAY_URL_FULL) as websocket:
        await websocket.send(GATEWAY_PW.encode(encoding="utf-8"))

        while websocket.open:
            listener_task = asyncio.ensure_future(websocket.recv())
            producer_task = asyncio.ensure_future(websocket_send_queue.get())

            done, pending = await asyncio.wait(
                [listener_task, producer_task],
                return_when=asyncio.FIRST_COMPLETED)

            if listener_task in done:
                message = listener_task.result()
                client_id, client_msg = unpack_msg_provider(message)

                if client_msg[0] == MSG_TYPE_OPEN:
                    log_inbound_msg_open_connection()
                    await websocket_recv_queue_map.create_named_queue(client_id)
                    asyncio.create_task(handle_client(client_id, client_msg))

                else:
                    log_internal("received message, distributing")
                    recv_queue: asyncio.Queue = await websocket_recv_queue_map.get_queue(client_id)
                    if recv_queue:
                        await recv_queue.put(client_msg)
                    else:
                        await websocket_send_queue.put(pack_msg_provider(client_id, pack_msg_close()))
                        log_internal("client with id {} not found. Closing...".format(client_id))
            else:
                listener_task.cancel()

            if producer_task in done:
                message = producer_task.result()
                if len(message) > 0:
                    log_internal("sending message")
                    await websocket.send(message)
            else:
                producer_task.cancel()


def main():
    parser = argparse.ArgumentParser(description='Websocket Gateway - Gateway')
    parser.add_argument('--provider-name', dest='provider_name', help='name of this provider')
    parser.add_argument('--gateway-url', dest='gw_url', help='url to the gateway')
    parser.add_argument('--gateway-password', dest='gw_pw', help='password for the gateway')

    define_logging_parser_args(parser)

    args = parser.parse_args()

    if not setup_logging(args):
        print("bad logging arguments.")
        parser.print_help()
        return

    if not args.gw_url or not args.gw_pw or not args.provider_name:
        parser.print_help()
        return

    global GATEWAY_PW, GATEWAY_URL_FULL
    GATEWAY_PW = args.gw_pw

    gateway_url_base = args.gw_url + "p/" if args.gw_url.endswith("/") else args.gw_url + "/p/"
    GATEWAY_URL_FULL = gateway_url_base + args.provider_name

    asyncio.run(start_provider())

if __name__ == "__main__":
    main()