# General Py Libs
import time
import os
# HomeMade Py Libs
from units import pdu
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
    for cmd, param_list in j_command_packet.items():
        match cmd:
            case "ObcHeartBeat":
                PduHeartBeat = pdu.ObcHeartBeat(j_command_packet, apid, db_name, host, user, password, conf_file)
                json_object = json.dumps(PduHeartBeat)
                Response_PduHeartBeat = SpacePacketCommand(count, json_object, apid, type, subtype+1)
                UDPServerSocket.sendto(Response_PduHeartBeat, address)
                LOGGER.info(f"SEMSIM to OBC: {PduHeartBeat}")
            case "GetPduStatus":
                PduStatus = pdu.GetPduStatus(param_list, apid, db_name, host, user, password, conf_file)
                json_object = json.dumps(PduStatus)
                Response_PduStatus = SpacePacketCommand(count, json_object, apid, type, subtype+1)
                UDPServerSocket.sendto(Response_PduStatus, address)
                LOGGER.info(f"SEMSIM to OBC: {PduStatus}")
            case "AddrUloadStart":
                reply = param_list
                LOGGER.info(f"param_list: {reply}")
            case "AddrUloadData":
                reply = param_list
                LOGGER.info(f"param_list: {reply}")
            case "AddrUloadAbort":
                pass
            case "AddrDloadRqst":
                reply = param_list
                LOGGER.info(f"param_list: {reply}")
            case "AddrDAcknowledge":
                reply = param_list
                LOGGER.info(f"param_list: {reply}")
            case "PduGoLoad":
                pdu.PduGoTo(cmd, apid, db_name,host, user, password, conf_file)
            case "PduGoSafe":
                pdu.PduGoTo(cmd, apid, db_name,host, user, password, conf_file)
            case "PduGoOperate":
                pdu.PduGoTo(cmd, apid, db_name,host, user, password, conf_file)
            case "SetUnitPwLines":
                pdu.SetUnitPwLines(j_command_packet, apid, db_name, host, user, password,conf_file)
            case "GetUnitLineStates":
                PduUnitLineStates = pdu.GetUnitLineStates(param_list, apid, db_name,host, user, password, conf_file)
                json_object = json.dumps(PduUnitLineStates)
                Response_PduUnitLineStates = SpacePacketCommand(count, json_object, apid, type, subtype+1)
                UDPServerSocket.sendto(Response_PduUnitLineStates, address)
                LOGGER.info(f"SEMSIM to OBC: {PduUnitLineStates}")
            case "ResetUnitPwLines":
                pdu.SetUnitPwLines(j_command_packet, apid, db_name,host, user, password, conf_file)
            case "OverwriteUnitPwLines":
                pdu.SetUnitPwLines(j_command_packet, apid, db_name,host, user, password, conf_file)
            case "GetRawMeasurements":
                GetRawMeasurements = pdu.GetRawMeasurements(j_command_packet, apid, db_name, host, user, password, conf_file)
                GetRawMeasurements_L = json.loads(GetRawMeasurements)
                temp = GetRawMeasurements_L["GetRawMeasurements"]["RawMeasurements"]
                voltage_measured = float(GetRawMeasurements_L["GetRawMeasurements"]["RawMeasurements"])
                voltage_binary_representation = struct.unpack('!Q', struct.pack('!d',float(voltage_measured)))[0]
                GetRawMeasurements_L["GetRawMeasurements"]["RawMeasurements"] = voltage_binary_representation
                json_object = json.dumps(GetRawMeasurements_L)
                Response_GetRawMeasurements = SpacePacketCommand(count, json_object, apid, type, subtype+1)
                UDPServerSocket.sendto(Response_GetRawMeasurements, address)
            case  _:
                LOGGER.info(f"OBC cmd_name: {cmd} Not Implemented")
    count =count + 1

def cmd_unloader(packet_data_field):
    command_packet = packet_data_field[12:]
    j_command_packet = json.loads(command_packet)
    return j_command_packet


def cmd_ack_generator(j_command_packet, apid, address, db_name, host, user, password, conf_file, UDPServerSocket):
    try:
        MsgAcknowlegement, TYPE, SUBTYPE = pdu.GetMsgAcknowlegement(j_command_packet, apid, db_name,host, user, password, conf_file)
        json_object = json.dumps(MsgAcknowlegement)
        ack_command = SpacePacketCommand(0x02, json_object, apid, TYPE, SUBTYPE)
        UDPServerSocket.sendto(ack_command, address)
        LOGGER.info(f"SEMSIM to OBC: {MsgAcknowlegement}")
    except:
        print("Failed to Create Ack SpacePacket")
        ack_command = {}

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
        LOGGER.info(f"SEMSIM to OBC FRAME: {databytes}")
    except:
         databytes = 0
         print("Failed to Create SpacePacket")
    return databytes

def configurator(localIP, tclocalPort):
    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPServerSocket.bind((localIP, tclocalPort))
    return UDPServerSocket

def customize_listening(UDPServerSocket, threads, db_name, host, user, password, conf_file):
    bufferSize = 4096
    count = 0
    byteAddressPair = UDPServerSocket.recvfrom(bufferSize)
    message = byteAddressPair[0]
    address = byteAddressPair[1]
    if message:
        clientIP  = "Client IP Address:{}".format(address)
        LOGGER.info(f"{clientIP}")
       # LOGGER.info(f"SIZE OF MESSAGE {len(message)}")
        #LOGGER.info(f"MESSAGE {message}")
        data, apid, type, subtype = SpacePacketDecoder(message)
        j_command_packet = cmd_unloader(data)
        LOGGER.info(f"OBC to SEMSIM: {j_command_packet}")
        cmd_ack_generator(j_command_packet, apid, address, db_name, host, user, password, conf_file, UDPServerSocket)
        cmd_processing(j_command_packet, apid, type, subtype, address, UDPServerSocket, db_name, host, user, password, conf_file, count)