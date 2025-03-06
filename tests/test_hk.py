import socket
import time
import json
from threading import *

bufferSize = 4096

import random, logging, time, json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

def send_message(Command):
    LOGGER.info(f"COBC to SEMSIM FRAME: {Command}")
    bytesToSend = Command
    serverAddressPort = ("127.0.0.1", 5004)
    # Create UDP socket
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    # Send CMD to PAYSIM
    UDPClientSocket.sendto(bytesToSend, serverAddressPort)
    return UDPClientSocket

def expecting_ack(UDPCon):
    byteAddressPair = UDPCon.recvfrom(bufferSize)
    message = byteAddressPair[0]
    address = byteAddressPair[1]
    #LOGGER.info(f"SEMSIM to COBC: {message}")
    return message

def SpacePacketCommand(count, command, apid, type, subtype):
    try:
        packet_dataframelength = len(bytes(command, 'utf-8'))
        tc_version = 0x00
        tc_type = 0x01
        tc_dfh_flag = 0x01
        tc_apid = apid
        tc_seq_flag = 0x03
        tc_seq_count = count
        data_field_header = [0x10, type, subtype, 0x00]
        data_pack_cuck = [0x2F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        data_field_header_frame = data_field_header + data_pack_cuck
        data_pack_data_field_header_frame = b''
        for p in data_field_header_frame:
            data_pack_data_field_header_frame += p.to_bytes(1, 'big')
        packet_dataheaderlength = len(data_pack_data_field_header_frame)
        packet_datalength = packet_dataheaderlength + packet_dataframelength - 2
        databytes = bytes([(tc_version << 5) + (tc_type << 4) + (tc_dfh_flag << 3) + (tc_apid >> 8), (tc_apid & 0xFF), (tc_seq_flag << 6) + (tc_seq_count >> 8), (tc_seq_count & 0xFF), (packet_datalength >> 8), (packet_datalength & 0xFF)])
        databytes += data_pack_data_field_header_frame
        databytes += bytes(command, 'utf-8')
    except:
         databytes = 0
         print("Failed to Create SpacePacket")
    return databytes

def SpacePacketDecoder(buffer):
    try:
        packet_data_field = b''
        packet_type = (buffer[0] >> 4) & 0x01
        packet_sec_hdr_flag = (buffer[0] >> 3) & 0x01
        apid = ((buffer[0] & 0x07) << 8) + buffer[1]
        sequence_flags = buffer[2] >> 6
        packet_sequence_count = ((buffer[2] & 0x3F) << 8) + buffer[3]
        packet_version = buffer[0] >> 5
        packet_data_length = (buffer[4] << 8) + buffer[5] + 1
        packet_data_field += buffer[6:]
        type = buffer[7]
        subtype = buffer[8]
    except:
        print("Failed to Create SpacePacket")
        packet_data_field = {}
    return packet_data_field, apid, type, subtype

def decode_tlm(packet_data_field, apid, type, subtype):
    command_packet = packet_data_field[12:]
    #print(command_packet)
    jv_command_packet = json.loads(command_packet)

    #LOGGER.info(f"SEMSIM to COBC CCDS apid: {apid}")
    #LOGGER.info(f"SEMSIM to COBC CCDS type: {type}")
    #LOGGER.info(f"SEMSIM to COBC CCDS subtype: {subtype}")
    #LOGGER.info(f"SEMSIM HKTLM: {jv_command_packet}")
    return jv_command_packet, apid, type, subtype

if __name__ == "__main__":
  
    while True:
        APID = 0x10

        LOGGER.info(f"### HK TLM TEST ###")

        HkTLm ={
        "CommandId": 0x00,
        "SequenceNum": 0x00, 
        "Length": 0x00,
        "Unit_Select": 0x00,
        "Params": 0x00
        }

        json_object = json.dumps(HkTLm)
        cmd2pdu = SpacePacketCommand(0, json_object, APID, 2, 1)
        UDPCon = send_message(cmd2pdu)
        FullHK = []
        for i in range(9):
            tlm_rcv = expecting_ack(UDPCon)
            packet_data_field, apid, type, subtype = SpacePacketDecoder(tlm_rcv)
            jv_command_packet, apid, type, subtype = decode_tlm(packet_data_field, apid, type, subtype)
            for k, v in jv_command_packet.items():
               #LOGGER.info(f"_______________________{k}     {v}_______________________")
                if "cband" in k or "mro" in k:
                    #LOGGER.info(f"_______________________SUBSYSTEM :{k}_______________________")
                    for k1, v1 in v.items():
                        if k1 != "STATE":
                            #LOGGER.info(f"________UNIT:{k1}________")
                            for k2, v2 in json.loads(v1).items():
                                for k3, v3 in v2.items():
                                    if isinstance(v3, list):
                                        FullHK.extend(v3)
                                    else:
                                        FullHK.append(v3)
                                #LOGGER.info(f"TELEMETRY NAME: {k2} == VALUE READ: {v2}")
                            #LOGGER.info(f"_________________________")
                else:
                    #LOGGER.info(f"_______________________SUBSYSTEM :{k}_______________________")
                    for k1, v1 in v.items():
                        if k1 != "STATE":
                            #LOGGER.info(f"________UNIT:{k1}________")
                            for k2, v2 in json.loads(v1).items():
                                if ((not 'Register' in k1) and (not 'Acknowledge' in k1) and (not 'HealthTLM' in k1) and (not 'POSTResponse' in k1) and (not 'DCP_DSP_Configuration_Response' in k1) and (not 'DCP_DSP_RTN_TLM' in k1) and (not 'DCP_DSP_FWD_TLM' in k1)):
                                    if "epc_z_sspa" in k1:
                                        for k3, v3 in v2.items():
                                                if isinstance(v3, list):
                                                    FullHK.extend(v3)
                                                else:
                                                    FullHK.append(v3)
                                    else:
                                        if isinstance(v2, list):
                                            FullHK.extend(v2)
                                        else:
                                            FullHK.append(v2)
                                #LOGGER.info(f"TELEMETRY NAME: {k2} == VALUE READ: {v2}")
                            #LOGGER.info(f"_________________________")
                #LOGGER.info(f"____________________________________________________________")
                LOGGER.info(f"FULL_HK LIST: {FullHK}")
        time.sleep(0.5)