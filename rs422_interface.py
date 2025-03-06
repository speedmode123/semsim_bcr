import socket
import struct
import time
import serial
import ast
import codecs
import json
import sys
import ast
from threading import *
import threading
import random, logging, time, json
import ctypes
from ctypes import *
from bcr_frame import encode_bcr_frame, decode_bcr_frame

bufferSize = 4096
EventId_list = [2560, 2561]

Enable_Report_Gen_2560 ={
   "n": 0x01,
   "EventId": EventId_list[0],
}

Enable_Report_Gen_2561 ={
   "n": 0x01,
   "EventId": EventId_list[1],
}

Enable_Report_Gen_Both ={
   "n": 0x02,
   "EventId": EventId_list,
}

Disable_Report_Gen_2560 ={
   "n": 0x01,
   "EventId": EventId_list[0],
}

Disable_Report_Gen_2561 ={
   "n": 0x01,
   "EventId": EventId_list[1],
}

Disable_Report_Gen_Both ={
   "n": 0x02,
   "EventId": EventId_list,
}

List_Disable_Report_Gen ={}

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
    LOGGER.info(f"SEMSIM to COBC: {message}")
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
    #LOGGER.info(f"SEMSIM to COBC CCDS tlm_name: {jv_command_packet}")
    return jv_command_packet, apid, type, subtype

def send_semsim_ccsds_frame(count, Command, apid, type, subtype):
    json_object = json.dumps(Command)
    cmd2pdu = SpacePacketCommand(count, json_object, apid, type, subtype)
    # print(f" RS422 TO CCSDS: {cmd2pdu.hex()}")
    UDPCon = send_message(cmd2pdu)
    return UDPCon 

def receive_semsim_ccsds_frame(UDPCon):   
    tlm_rcv = expecting_ack(UDPCon)
    packet_data_field, apid, type, subtype = SpacePacketDecoder(tlm_rcv)
    # print(f" CCSDS TO RS422: {packet_data_field.hex()}")
    dict_command_rcv, apid, type, subtype = decode_tlm(packet_data_field, apid, type, subtype)
    return dict_command_rcv, apid, type, subtype 

def rs422_comm(port, speed):
    try:
        ser_port = serial.Serial(
        port=port,
        baudrate=speed,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
         )
        print("Created RS 422 PORT")
        ser_port.flushInput()
        ser_port.flushOutput()
        if ser_port.isOpen(): # try to open port, if possible print message and proceed with 'while True:'
            print ("port is opened!")
        else:
            ser_port.open()
    except IOError: # if port is already opened, close it and open it again and print message
        ser_port.close()
        ser_port.open()
    return ser_port

def read_command(ser_port):
    try:
        while True:
            APID = 0x0A
            #print(f"Reading RS 422 PORT {ser_port.port}")
            bs = b''
            start_byte = ser_port.read()
            bs += start_byte
            #LOGGER.info(f"number of bytes input buffer {ser_port.in_waiting} | port {ser_port.port}")
            LOGGER.info(f"start byte {hex(ord(bs))}")
            if hex(ord(start_byte)) == '0x55':
                read_byte = ser_port.read()
                bs += read_byte
                while hex(ord(read_byte)) != '0x55':
                    read_byte = ser_port.read()
                    bs += read_byte
                LOGGER.info(f"read_buffer {bs}")
                if bs:
                    if "USB0" in ser_port.port:
                        #DECODE MESSAGE on RS422
                        #LOGGER.info(f"Received RS422 frame OBC to PDU {bs}")
                        ccsds_packet = decode_bcr_frame(bs)
                        # comm0 = rs422_comm("/dev/ttyUSB1", 115200)

                        if mid == 0x1:
                            #ENCODE MESSAGE on CCSDS
                            ObcHeartBeat ={
                                pdu_cmd:{
                                    "HeartBeat": int.from_bytes(pld, "big")
                                }
                            }
                            #SEND MESSAGE on CCSDS
                            Reply = send_semsim_ccsds_frame(0x07, ObcHeartBeat, APID, 2, 1)
                            #RECEIVE MESSAGE on CCSDS
                            dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
                            dict_heartbeat = json.loads(dict_command_rcv)["PduHeartBeat"]
                            pld = []
                            hrbt = int.to_bytes(dict_heartbeat["HeartBeat"], 4, "big")
                            sts = dict_heartbeat["PduState"]
                            pld.extend([hb_byte for hb_byte in hrbt])
                            pld.append(sts)
                            print(f"heartbeat: {[hb_byte for hb_byte in hrbt]}")
                            print(f"pdustate: {sts}")
                            #ENCODE MESSAGE on RS422
                            reply_encoded_frame = encode_obc_rs422_frame(0x01, 0x00, pld)
                            write_command(ser_port, reply_encoded_frame, len(reply_encoded_frame))
                                            
                        if mid == 0x2:
                            #ENCODE MESSAGE on CCSDS
                            GetPduStatus ={
                                pdu_cmd:{}
                            }
                            #SEND MESSAGE on CCSDS
                            Reply = send_semsim_ccsds_frame(0x03, GetPduStatus, APID, 2, 5)

                            #RECEIVE MESSAGE on CCSDS
                            dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
                            status = json.loads(dict_command_rcv)
                            pdu_status_list = []
                            for k,v in status["PduStatus"].items():
                                pdu_status_list.append(int(v))
                                
                            #ENCODE ON RS422
                            reply_encoded_frame = encode_obc_rs422_frame(mid, lid, pdu_status_list)
                            write_command(ser_port, reply_encoded_frame, len(reply_encoded_frame))

                        if mid == 0x8:
                            #ENCODE MESSAGE on CCSDS
                            PduGoLoad ={
                                pdu_cmd:{}
                            }
                            #SEND MESSAGE on CCSDS
                            Reply = send_semsim_ccsds_frame(0x02, PduGoLoad, APID, 2, 5)
                            #RECEIVE MESSAGE on CCSDS
                            dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
                            ack1 = dict_command_rcv["MsgAcknowlegement"]["RequestedMsgId"]
                            ack2 = dict_command_rcv["MsgAcknowlegement"]["PduReturnCode"]
                            #ENCODE ON RS422
                            reply_encoded_frame = encode_obc_rs422_frame(0x01, 0x00, [list(PDU_COMMANDS.keys())[list(PDU_COMMANDS.values()).index(ack1)], int(ack2)])
                            write_command(ser_port, reply_encoded_frame, len(reply_encoded_frame))

                        if mid == 0x0A:
                            PduGoLoad ={
                                pdu_cmd:{}
                            }
                            #SEND MESSAGE on CCSDS
                            Reply = send_semsim_ccsds_frame(0x05, PduGoLoad, APID, 2, 9)
                            #RECEIVE MESSAGE on CCSDS
                            dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
                            ack1 = dict_command_rcv["MsgAcknowlegement"]["RequestedMsgId"]
                            ack2 = dict_command_rcv["MsgAcknowlegement"]["PduReturnCode"]
                            #ENCODE ON RS422
                            reply_encoded_frame = encode_obc_rs422_frame(0x01, 0x00, [list(PDU_COMMANDS.keys())[list(PDU_COMMANDS.values()).index(ack1)], int(ack2)])
                            write_command(ser_port, reply_encoded_frame, len(reply_encoded_frame))
                        
                        if mid == 0x0B:                 
                            SetUnitPwLines = {
                                pdu_cmd: {
                                    "LogicUnitId": int(lid),
                                    "Parameters": int.from_bytes(pld, "big")
                                }
                            }
                            #SEND MESSAGE on CCSDS
                            Reply = send_semsim_ccsds_frame(0x09, SetUnitPwLines, APID, 2, 1)
                            #RECEIVE MESSAGE on CCSDS
                            dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
                            #ENCODE MESSAGE on RS422
                            ack1 = dict_command_rcv["MsgAcknowlegement"]["RequestedMsgId"]
                            ack2 = dict_command_rcv["MsgAcknowlegement"]["PduReturnCode"]
                            #ENCODE ON RS422
                            reply_encoded_frame = encode_obc_rs422_frame(0x01, 0x00, [list(PDU_COMMANDS.keys())[list(PDU_COMMANDS.values()).index(ack1)], int(ack2)])
                            # LOGGER.info(f"GET reply_encoded_frame : {reply_encoded_frame.hex()}")
                            write_command(ser_port, reply_encoded_frame, len(reply_encoded_frame))

                        if mid == 0x0E:
                            #ENCODE MESSAGE on CCSDS
                            GetUnitLineStates ={
                            pdu_cmd:{}
                            }
                            
                            #SEND MESSAGE on CCSDS
                            Reply = send_semsim_ccsds_frame(0x08, GetUnitLineStates, APID, 2, 1)
                            #RECEIVE MESSAGE on CCSDS
                            dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
                            status = json.loads(dict_command_rcv)
                            pdu_status_list = []
                            for k,v in status["PduUnitLineStates"].items():
                                pdu_status_list.append(int(v))
                                
                            #ENCODE ON RS422
                            reply_encoded_frame = encode_obc_rs422_frame(mid, lid, pld)
                            #LOGGER.info(f"GET RAW reply_encoded_frame : {reply_encoded_frame}")
                            write_command(ser_port, reply_encoded_frame, len(reply_encoded_frame))

                        if mid == 0x0F:
                            GetRawMeasurements ={
                                pdu_cmd: {
                                    "LogicUnitId": int(lid),
                                    "Parameters": int.from_bytes(pld, "big")
                                }
                            }

                            #SEND MESSAGE on CCSDS
                            Reply = send_semsim_ccsds_frame(0x0B, GetRawMeasurements, APID, 2, 16)

                            #RECEIVE MESSAGE on CCSDS
                            dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
                            status1 = dict_command_rcv["GetRawMeasurements"]
                            pdu_status_list = []
                            for k,v in status1.items():
                                pdu_status_list.append(int(v))
                            raw_value = struct.pack('!Q', pdu_status_list[0])

                            #ENCODE ON RS422
                            reply_encoded_frame = encode_obc_rs422_frame(0x05, 0x00, raw_value)
                            write_command(ser_port, reply_encoded_frame, len(reply_encoded_frame))

                    else:
                        LOGGER.info(f"Receive OBC Message: {bs}")
                        logging.info(f"OBC message: {bs}")
                        ser_port.flushInput()
                        ser_port.flushOutput()
                    # generate_ack(ser_port, sps.packet_data_field)
    except Exception as e:
        print("Failed Reading Break Code!", e)

def write_command(ser_port, sccp_cmd_null, len_spc=None):
    try:
        if "USB1" in ser_port.port:
            #LOGGER.info(f"Sending RS422 Break Code OBC to PDU: {str(len(str(len_spc))).encode() + str(len_spc).encode() + sccp_cmd_null}")
            LOGGER.info(f"OBC to PDU Raw Command: {sccp_cmd_null.hex()}")
        else:
            #LOGGER.info(f"Sending RS422 Break Code PDU to OBC: {str(len(str(len_spc))).encode() + str(len_spc).encode() + sccp_cmd_null}")
            LOGGER.info(f"PDU to OBC Raw Command: {sccp_cmd_null.hex()}")
        #LOGGER.info(f"write command: {serial.to_bytes(sccp_cmd_null)}")
        ser_port.write(serial.to_bytes(sccp_cmd_null))
        #ser_port.write(sccp_cmd_null)
    except:
        print("Failed Sending Break Code!")

def rs_422_listener(ser_port):
    
    
    try:
        print("Listening on RS 422 PORT")
        listen_rs_thread = Thread(target=read_command, args=(ser_port,))
    except:
        print("Failed To Create Listening thread")
    try:
        # Start threads
        time.sleep(1)
        listen_rs_thread.start()
    except:
        print("Failed To Start Listening thread")

# if __name__ == "__main__":
#    comm1 = rs422_comm("/dev/ttyUSB1", 115200)
#    rs_422_listener(comm1)