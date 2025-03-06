# General Py Libs
import time
import os
# HomeMade Py Libs
from units import bcr, tm
import psycopg2
import socket
from threading import *
import threading
from subprocess import Popen
import struct
import db_manager
import ctypes
import serial
import random, logging, time, json
from queue import Queue

shared_bool = threading.Event()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

def tmtc_manager(models_to_update, db_name, host, user, password, conf_file, localIP, tclocalPort):
    UDPServerSocket = configurator(localIP, tclocalPort)

    rtos_checker = db_manager.db_manager(db_name, host, user, password, conf_file)
    rtos_checker.db_connect()
    
    threads = {}
    while rtos_checker.check_rtos() == '1':
        customize_listening(UDPServerSocket, threads, db_name, host, user, password, conf_file)
    else:
        time.sleep(1)
        rtos_checker.db_disconnect()
        UDPServerSocket.close()

def cmd_processing(j_command_packet, apid, type, subtype, address, UDPServerSocket, db_name, host, user, password, conf_file, count):
    match type:
        case 0x05:
            EvR, type_r, subtype_r = bcr.Event_reporting(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file)
            EvRcheck, type_checkr, subtype_checkr = bcr.Request_completion_verification(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file)
            Response_EvRcheck = SpacePacketCommand(count, json.dumps(EvRcheck), apid, type_checkr, subtype_checkr)
            UDPServerSocket.sendto(Response_EvRcheck, address)
            if (EvR != 0) and (subtype_r != 0):
                Response_EvR = SpacePacketCommand(count, json.dumps(EvR), apid, type_r, subtype_r)
                UDPServerSocket.sendto(Response_EvR, address)
                LOGGER.info(f"SEMSIM to OBC: {Response_EvR}")
        case 0x06:
            Mem, type_r, subtype_r = bcr.Memory_management(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file)
            Memcheck, type_checkr, subtype_checkr = bcr.Request_completion_verification(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file)
            if (Mem != 0) and (subtype_r != 0):
                Response_Mem = SpacePacketCommand(count, json.dumps(Mem), apid, type_r, subtype_r)
                UDPServerSocket.sendto(Response_Mem, address)
                LOGGER.info(f"SEMSIM to OBC: {Response_Mem}")
            Response_Memcheck = SpacePacketCommand(count, json.dumps(Memcheck), apid, type_checkr, subtype_checkr)
            UDPServerSocket.sendto(Response_Memcheck, address)
        case 0x08:
            Fman, type_r, subtype_r = bcr.Function_management(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file)
            Fmancheck, type_checkr, subtype_checkr = bcr.Request_completion_verification(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file)
            if (Fman != 0) and (subtype_r != 0):
                Response_Fman = SpacePacketCommand(count, json.dumps(Fman), apid, type_r, subtype_r)
                UDPServerSocket.sendto(Response_Fman, address)
                LOGGER.info(f"SEMSIM to OBC: {Response_Fman}") 
            Response_Fmancheck = SpacePacketCommand(count, json.dumps(Fmancheck), apid, type_checkr, subtype_checkr)
            UDPServerSocket.sendto(Response_Fmancheck, address)         
        case 0x11:
            RTest, type_r, subtype_r = bcr.Test_test(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file)
            RTestcheck, type_checkr, subtype_checkr = bcr.Request_completion_verification(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file)
            if (RTest != 0) and (subtype_r != 0):
                if isinstance(RTest, list):
                    for rt_test in RTest:
                        Response_RTest = SpacePacketCommand(count, json.dumps(rt_test), apid, type_r, subtype_r)
                        UDPServerSocket.sendto(Response_RTest, address)
                        LOGGER.info(f"SEMSIM to OBC: {Response_RTest}")
                else:
                    Response_RTest = SpacePacketCommand(count, json.dumps(RTest), apid, type_r, subtype_r)
                    UDPServerSocket.sendto(Response_RTest, address)
                    LOGGER.info(f"SEMSIM to OBC: {Response_RTest}")
            Response_RTestcheck = SpacePacketCommand(count, json.dumps(RTestcheck), apid, type_checkr, subtype_checkr)
            UDPServerSocket.sendto(Response_RTestcheck, address)
        case 0x14:
            ObpM, type_r, subtype_r = bcr.OnBoard_parameter_management(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file)
            ObpMcheck, type_checkr, subtype_checkr = bcr.Request_completion_verification(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file)
            if (ObpM != 0) and (subtype_r != 0):
                Response_ObpM = SpacePacketCommand(count, json.dumps(ObpM), apid, type_r, subtype_r)
                UDPServerSocket.sendto(Response_ObpM, address)
                LOGGER.info(f"SEMSIM to OBC: {Response_ObpM}")
            Response_ObpMcheck = SpacePacketCommand(count, json.dumps(ObpMcheck), apid, type_checkr, subtype_checkr)
            UDPServerSocket.sendto(Response_ObpMcheck, address)
        case  _:
            LOGGER.info(f"BCR type: {type}, subtype: {subtype} not Implemented")
    count =count + 1

def cmd_unloader(packet_data_field):
    command_packet = packet_data_field[12:]
    j_command_packet = json.loads(command_packet)
    return j_command_packet

def cmd_ack_generator(j_command_packet, apid, type, subtype, address, db_name, host, user, password, conf_file, UDPServerSocket):
    try:
        verification_dict, type_r, subtype_r = bcr.Request_acceptance_verification(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file)
        verification_message = SpacePacketCommand(0x01, json.dumps(verification_dict), apid, type_r, subtype_r)
        UDPServerSocket.sendto(verification_message, address)
        LOGGER.info(f"SEMSIM to OBC ACK: {verification_message}")
    except:
        print("Failed to Create Ack SpacePacket")

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

def SpacePacketCommand(count, command, apid, type, subtype):
    try:
        packet_dataframelength = len(bytes(command, 'utf-8'))
        tc_version = 0x00
        tc_type = 0x00
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
        #LOGGER.info(f"SEMSIM to OBC FRAME: {databytes}")
    except:
         databytes = 0
         print("Failed to Create SpacePacket")
    return databytes

def configurator(localIP, tclocalPort):
    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPServerSocket.bind((localIP, tclocalPort))
    return UDPServerSocket

def customize_listening(UDPServerSocket, threads, db_name, host, user, password, conf_file):
    bufferSize = 8192
    count = 0
    byteAddressPair = UDPServerSocket.recvfrom(bufferSize)
    message = byteAddressPair[0]
    address = byteAddressPair[1]
    if message:
        #clientIP  = "Client IP Address:{}".format(address)
        #LOGGER.info(f"{clientIP}")
        #LOGGER.info(f"SIZE OF MESSAGE {len(message)}")
        #LOGGER.info(f"MESSAGE {message}")
        LOGGER.info(f"OBC to SEMSIM: {message}")
        data, apid, type, subtype = SpacePacketDecoder(message)
        j_command_packet = cmd_unloader(data)
        #LOGGER.info(f"OBC to SEMSIM: {j_command_packet}")
        cmd_ack_generator(j_command_packet, apid, type, subtype, address, db_name, host, user, password, conf_file, UDPServerSocket)
        cmd_processing(j_command_packet, apid, type, subtype, address, UDPServerSocket, db_name, host, user, password, conf_file, count)