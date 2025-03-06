from fastcrc import crc16
from enum import IntEnum
from cobs import cobs
import struct


# ASL Bus Header

class ASL_type(IntEnum):
    TC_PACKET = 0x00
    TM_PACKET = 0X01
    BUS_ACK = 0X02  # sent during the routing of a TC to acknowledge delivery. No payload is provided
    CUSTOM_DATA = 0x04

class STDIF_type(IntEnum):
    HEARTBEAT = 0x00
    BOOTUP = 0x25
    USER_PACKET = 0xA5  # will be used with SEMSIM

asl_header_format = ">bhhhb"


def encode_bcr_frame(asl_type, payload, apid=0x0A, ack_count=0):
    asl_header = struct.pack(asl_header_format, asl_type, 0, apid, ack_count, 0)
    stdif_header = struct.pack(">b", STDIF_type.USER_PACKET.value)
    stdif_data = asl_header + payload
    crc = crc16.ibm_3740(stdif_data)
    if len(crc) > 0:
        crc_field = struct.pack(">h", crc)
    stdif_frame = stdif_header + stdif_data + crc
    cobs_frame = cobs.encode(stdif_frame)
    return cobs_frame + b'0x00'  # add delimiter

def decode_bcr_frame(bcr_frame):
    stdif_frame = cobs.decode(bcr_frame[:-1])
    ccsds = stdif_frame[9:-2]  # remove stdif_header asl_header & crc
    return ccsds
