import struct

MSG_TYPE_DATA = 0x00
MSG_TYPE_OPEN = 0x01
MSG_TYPE_CLOSE = 0x02

def pack_msg_data(data: bytes):
    return struct.pack("!cI", bytes([MSG_TYPE_DATA]), len(data)) + data

def pack_msg_open(hostname: str, port: int):
    hostname_bin = hostname.encode(encoding="utf-8")
    # 0 is reserved for udp connections
    return struct.pack("!ccII", bytes([MSG_TYPE_OPEN]), bytes([0]), port, len(hostname_bin)) + hostname_bin

def pack_msg_close():
    return struct.pack("!c", bytes([MSG_TYPE_CLOSE]))

def unpack_msg_data(data: bytes):
    meta_size = struct.calcsize("!cI")
    _, data_len = struct.unpack("!cI", data[:meta_size])
    return data[-data_len:]

def unpack_msg_open(data: bytes):
    meta_size = struct.calcsize("!ccII")
    _, _, port, hostname_len = struct.unpack("!ccII", data[:meta_size])
    return data[-hostname_len:].decode(encoding="utf-8"), port

def pack_msg_provider(client_id: int, inner_msg: bytes):
    return struct.pack("!II", client_id, len(inner_msg)) + inner_msg

def unpack_msg_provider(msg: bytes):
    client_id, client_msg_len = struct.unpack("!II", msg[:8])
    client_msg = msg[-client_msg_len:]

    return client_id, client_msg