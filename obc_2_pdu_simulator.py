import socket
import struct
import time
import ctypes
import serial
import ast
import codecs
import json
from threading import *
import threading
from pdu_packetization import PduPacket, PduPacketCStruct, PduPacketSerializerCStruct, PduPacketDeserializerCStruct
pdu_packetization_lib = ctypes.cdll.LoadLibrary("../bin/pdu_packetization.dll")
pdu_packetization_lib.PS_HasNextByte.restype = ctypes.c_bool
pdu_packetization_lib.PS_NextByte.restype = ctypes.c_ubyte
pdu_packetization_lib.PD_Apply.restype = ctypes.c_int
MAX_PAYLOAD_SIZE = 255
bufferSize = 4096

import random, logging, time, json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

def send_message(Command):
    #LOGGER.info(f"COBC to SEMSIM FRAME: {Command}")
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
    #LOGGER.info(f"SEMSIM to COBC reply: {command_packet}")
    jv_command_packet = json.loads(command_packet)
    #LOGGER.info(f"SEMSIM to COBC CCDS apid: {apid}")
    #LOGGER.info(f"SEMSIM to COBC CCDS type: {type}")
    #LOGGER.info(f"SEMSIM to COBC CCDS subtype: {subtype}")
    #LOGGER.info(f"SEMSIM REPLY: {jv_command_packet}")
    return jv_command_packet, apid, type, subtype

def encode_pdu_packet(pdu_packet: PduPacket) -> bytes:
    # Convert python PDU packet to c type for passing to lib
    c_packet = PduPacketCStruct()
    c_packet.u8MessageAndLogicalUnitId = (pdu_packet.message_id << 4) | pdu_packet.logical_unit_id
    c_packet.u8PayloadLength = len(pdu_packet.payload)
    c_packet.au8Payload = (ctypes.c_ubyte * MAX_PAYLOAD_SIZE)(*pdu_packet.payload)

    # Setup C serializer
    serializer_pointer = (PduPacketSerializerCStruct * 1)(PduPacketSerializerCStruct())
    packet_pointer = (PduPacketCStruct * 1)(c_packet)
    pdu_packetization_lib.PS_ResetSerializer(serializer_pointer, packet_pointer)

    # Setup python list for storing encoded values and call C lib functions to encode and store into it
    encoded_packet = bytearray()
    while pdu_packetization_lib.PS_HasNextByte(serializer_pointer):
        current_byte = pdu_packetization_lib.PS_NextByte(serializer_pointer)
        encoded_packet.extend(current_byte.to_bytes(length=1, byteorder='little'))

    return bytes(encoded_packet)

def decode_pdu_packet(encoded_packet: bytes) -> PduPacket:
    # Setup C PduPacket
    packet_pointer = (PduPacketCStruct * 1)(PduPacketCStruct())
    pdu_packetization_lib.PP_InitializePacket(packet_pointer, 0)

    # Setup C deserializer
    deserializer_pointer = (PduPacketDeserializerCStruct * 1)(PduPacketDeserializerCStruct())
    pdu_packetization_lib.PD_ResetDeSerializer(deserializer_pointer)

    # Call C lib function for decoding encoded packet, one byte at a time, stop and print if status code is not
    # InProgress=1
    for byte_value in encoded_packet:
        status = pdu_packetization_lib.PD_Apply(deserializer_pointer, byte_value, packet_pointer)

        if status != 1:
            print(f"Final status code for decoding was: {status}")
            break

    # Build python PduPacket object from C PduPacket type
    pdu_packet = PduPacket()
    pdu_packet.logical_unit_id = packet_pointer[0].u8MessageAndLogicalUnitId & 0xF
    pdu_packet.message_id = (packet_pointer[0].u8MessageAndLogicalUnitId >> 4) & 0xF
    for x in range(0, packet_pointer[0].u8PayloadLength):
        pdu_packet.payload.append(packet_pointer[0].au8Payload[x])

    return pdu_packet

def encode_obc_rs422_frame(message_id, Logic_Id, Payload):
      packet = PduPacket()
      packet.message_id = message_id
      packet.logical_unit_id = Logic_Id
      for p in Payload:
        packet.payload.append(p)
      RSObcFrame = encode_pdu_packet(packet)
      return RSObcFrame

def decode_obc_rs422_frame(RSObcFrame):
   decoded_packet = decode_pdu_packet(RSObcFrame)
   mid = decoded_packet.message_id
   lid = decoded_packet.logical_unit_id
   pld = decoded_packet.payload
   pdu_cmd = PDU_COMMANDS[int(mid)]
   return pdu_cmd, mid, lid , pld

def encode_rs422_ccsds_frame(RSObcFrame):
   mid, lid , pld = RSObcFrame.decode_message(RSObcFrame.databytes)
   pdu_cmd = PDU_COMMANDS[int(mid)]
   return pdu_cmd, mid, lid, pld

def send_semsim_ccsds_frame(count, Command, apid, type, subtype):
   json_object = json.dumps(Command)
   cmd2pdu = SpacePacketCommand(count, json_object, apid, type, subtype)
   print(f" RS422 TO CCSDS: {cmd2pdu.hex()}")
   UDPCon = send_message(cmd2pdu)
   return UDPCon 

def receive_semsim_ccsds_frame(UDPCon):   
   tlm_rcv = expecting_ack(UDPCon)
   packet_data_field, apid, type, subtype = SpacePacketDecoder(tlm_rcv)
   print(f" CCSDS TO RS422: {packet_data_field.hex()}")
   dict_command_rcv, apid, type, subtype = decode_tlm(packet_data_field, apid, type, subtype)
   return dict_command_rcv, apid, type, subtype   
    
if __name__ == "__main__":
  
   APID = 0x65
   PDU_COMMANDS = {
       0: "Invalid",
       1: "ObcHeartBeat",
       2: "GetPduStatus",
       3: "AddrUloadStart",
       4: "AddrUloadData",
       5: "AddrUloadAbort",
       6: "AddrDloadRqst",
       7: "AddrDAcknowledge",
       8: "PduGoLoad",
       9: "PduGoSafe",
       10: "PduGoOperate",
       11: "SetUnitPwLines",
       12: "ResetUnitPwLines",
       13: "OverwriteUnitPwLines",
       14: "GetUnitLineStates",
       15: "GetRawMeasurements"
   }

   LOGGER.info("# SCENARIO 0: SEND ObcHeartBeat")
   Message_Id = 0x01
   Logic_Id = 0x00
   Payload = [0x01]
   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)
   ObcHeartBeat ={
   pdu_cmd:{
       "HeartBeat": int.from_bytes(pld, "big")
   }
   }
   #ENCODE MESSAGE on CCSDS
   #SEND MESSAGE on CCSDS
   Reply = send_semsim_ccsds_frame(0x01, ObcHeartBeat, APID, 2, 1)
   #RECEIVE MESSAGE on CCSDS
   dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
   heartbeat = json.loads(dict_command_rcv)["PduHeartBeat"]["HeartBeat"]
   #ENCODE MESSAGE on RS422
   reply_encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, [heartbeat])
   print(f" PDU SEND RS422: {reply_encoded_frame.hex()}")


   LOGGER.info("# SCENARIO 1: SEND PduGoLoad")
   Message_Id = 0x08
   Logic_Id = 0x00
   Payload = []
   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)
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
   reply_encoded_frame = encode_obc_rs422_frame(0x03, 0x00, [list(PDU_COMMANDS.keys())[list(PDU_COMMANDS.values()).index(ack1)], int(ack2)])
   print(f" PDU SEND RS422: {reply_encoded_frame.hex()}")

   time.sleep(10)
   
   LOGGER.info("# SCENARIO 2: SEND GetPduStatus")
   Message_Id = 0x02
   Logic_Id = 0x00
   Payload = []

   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)

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
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, pdu_status_list)
   print(f" PDU SEND RS422: {encoded_frame.hex()}")


   LOGGER.info("# SCENARIO 3: SEND ObcHeartBeat")
   Message_Id = 0x01
   Logic_Id = 0x00
   Payload = [0x01]
   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)
   ObcHeartBeat ={
   pdu_cmd:{
       "HeartBeat": int.from_bytes(pld, "big")
   }
   }
   #SEND MESSAGE on CCSDS
   Reply = send_semsim_ccsds_frame(0x04, ObcHeartBeat, APID, 2, 1)
   #RECEIVE MESSAGE on CCSDS
   dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
   heartbeat = json.loads(dict_command_rcv)["PduHeartBeat"]["HeartBeat"]
   #ENCODE MESSAGE on RS422
   reply_encoded_frame = encode_obc_rs422_frame(0x01, 0x00, [heartbeat])
   print(f" PDU SEND RS422: {reply_encoded_frame.hex()}")

   
   LOGGER.info("# SCENARIO 4: SEND PduGoOperate")
   Message_Id = 0x0A
   Logic_Id = 0x00
   Payload = []
   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)
   PduGoOperate ={
   pdu_cmd:{}
   }
   #SEND MESSAGE on CCSDS
   Reply = send_semsim_ccsds_frame(0x05, PduGoOperate, APID, 2, 9)
   #RECEIVE MESSAGE on CCSDS
   dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
   ack1 = dict_command_rcv["MsgAcknowlegement"]["RequestedMsgId"]
   ack2 = dict_command_rcv["MsgAcknowlegement"]["PduReturnCode"]
   #ENCODE ON RS422
   reply_encoded_frame = encode_obc_rs422_frame(0x03, 0x00, [list(PDU_COMMANDS.keys())[list(PDU_COMMANDS.values()).index(ack1)], int(ack2)])
   print(f" PDU SEND RS422: {reply_encoded_frame.hex()}")


   LOGGER.info("# SCENARIO 5: SEND GetPduStatus")
   Message_Id = 0x02
   Logic_Id = 0x00
   Payload = []

   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)

   #ENCODE MESSAGE on CCSDS
   GetPduStatus ={
   pdu_cmd:{}
   }

   #SEND MESSAGE on CCSDS
   Reply = send_semsim_ccsds_frame(0x06, GetPduStatus, APID, 2, 5)

   #RECEIVE MESSAGE on CCSDS
   dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
   status = json.loads(dict_command_rcv)
   pdu_status_list = []
   for k,v in status["PduStatus"].items():
      pdu_status_list.append(int(v))
       
   #ENCODE ON RS422
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, pdu_status_list)
   print(f" PDU SEND RS422: {encoded_frame.hex()}")


   LOGGER.info("# SCENARIO 6: SEND ObcHeartBeat")
   Message_Id = 0x01
   Logic_Id = 0x00
   Payload = [0x01]
   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)
   ObcHeartBeat ={
   pdu_cmd:{
       "HeartBeat": int.from_bytes(pld, "big")
   }
   }
   #SEND MESSAGE on CCSDS
   Reply = send_semsim_ccsds_frame(0x07, ObcHeartBeat, APID, 2, 1)
   #RECEIVE MESSAGE on CCSDS
   dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
   heartbeat = json.loads(dict_command_rcv)["PduHeartBeat"]["HeartBeat"]
   #ENCODE MESSAGE on RS422
   reply_encoded_frame = encode_obc_rs422_frame(0x01, 0x00, [heartbeat])
   print(f" PDU SEND RS422: {reply_encoded_frame.hex()}")


   LOGGER.info("# SCENARIO 7: SEND GetUnitLineStates")
   Message_Id = 0x0E
   Logic_Id = 0x00
   Payload = []

   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)

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
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, pdu_status_list)
   print(f" PDU SEND RS422: {encoded_frame.hex()}")


   LOGGER.info("# SCENARIO 8: SEND SetUnitPwLines")
   Message_Id = 0x0B
   Logic_Id = 0x00
   Payload = [0x00,  0x00, 0x01]
   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)
   SetUnitPwLines ={
   pdu_cmd:{
      "LogicUnitId": int(lid),
      "HighPwHeaterEnSel":int.from_bytes(pld, "big"),
      "LowPwHeaterEnSel":0x00,
      "ReactionWheelEnSel":0x00,
      "PropEnSel":0x00,
      "AvionicLoadEnSel":0x00,
      "HdrmEnSel":0x00,
      "StAndMagEnSel":0x00,
      "IsolatedPwEnSel":0x00,
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
   print(f" PDU SEND RS422: {reply_encoded_frame.hex()}")


   LOGGER.info("# SCENARIO 9: SEND GetUnitLineStates")
   #COBC FORM MESSAGE
   Message_Id = 0x0E
   Logic_Id = 0x00
   Payload = []
   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)
   GetUnitLineStates ={
   pdu_cmd:{}
   }

   #SEND MESSAGE on CCSDS
   Reply = send_semsim_ccsds_frame(0x0A, GetUnitLineStates, APID, 2, 16)

   #RECEIVE MESSAGE on CCSDS
   dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
   status = json.loads(dict_command_rcv)
   pdu_status_list = []
   for k,v in status["PduUnitLineStates"].items():
      pdu_status_list.append(int(v))
       
   #ENCODE ON RS422
   encoded_frame = encode_obc_rs422_frame(0x02, Logic_Id, pdu_status_list)
   print(f" PDU SEND RS422: {encoded_frame.hex()}")


   LOGGER.info("# SCENARIO 10: SEND GetRawMeasurements")

   #COBC FORM MESSAGE
   Message_Id = 0x0F
   Logic_Id = 0x00
   Payload = [0x00, 0x00, 0x01]
   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)
   GetRawMeasurements ={
      pdu_cmd:{
         "LogicUnitId": int(lid),
         "HighPwHeaterSel": int.from_bytes(pld, "big"),
         "LowPwHeaterSel":0x00,
         "ReactionWheelEnSel":0x00,
         "PropEnSel":0x00,
         "AvionicLoadEnSel":0x00,
         "HdrmEnSel":0x00,
         "StAndMagEnSel":0x00,
         "IsolatedPwEnSel":0x00,
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
   encoded_data = encode_obc_rs422_frame(0x05, 0x00, raw_value)
   print(f" PDU SEND RS422: {encoded_data.hex()}")

   time.sleep(30)

   
   LOGGER.info("# SCENARIO 11: SEND SetUnitPwLines")
   Message_Id = 0x0B
   Logic_Id = 0x00
   Payload = [0x00,  0x00, 0x00]
   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)
   SetUnitPwLines ={
   pdu_cmd:{
      "LogicUnitId": int(lid),
      "HighPwHeaterEnSel":int.from_bytes(pld, "big"),
      "LowPwHeaterEnSel":0x00,
      "ReactionWheelEnSel":0x00,
      "PropEnSel":0x00,
      "AvionicLoadEnSel":0x00,
      "HdrmEnSel":0x00,
      "StAndMagEnSel":0x00,
      "IsolatedPwEnSel":0x00,
   }
   }
   #SEND MESSAGE on CCSDS
   Reply = send_semsim_ccsds_frame(0x0C, SetUnitPwLines, APID, 2, 1)
   #RECEIVE MESSAGE on CCSDS
   dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
   #ENCODE MESSAGE on RS422
   ack1 = dict_command_rcv["MsgAcknowlegement"]["RequestedMsgId"]
   ack2 = dict_command_rcv["MsgAcknowlegement"]["PduReturnCode"]
   #ENCODE ON RS422
   reply_encoded_frame = encode_obc_rs422_frame(0x01, 0x00, [list(PDU_COMMANDS.keys())[list(PDU_COMMANDS.values()).index(ack1)], int(ack2)])
   print(f" PDU SEND RS422: {reply_encoded_frame.hex()}")

   LOGGER.info("# SCENARIO 12: SEND GetUnitLineStates")
   #COBC FORM MESSAGE
   Message_Id = 0x0E
   Logic_Id = 0x00
   Payload = []
   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)
   GetUnitLineStates ={
   pdu_cmd:{}
   }

   #SEND MESSAGE on CCSDS
   Reply = send_semsim_ccsds_frame(0x0D, GetUnitLineStates, APID, 2, 16)

   #RECEIVE MESSAGE on CCSDS
   dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
   status = json.loads(dict_command_rcv)
   pdu_status_list = []
   for k,v in status["PduUnitLineStates"].items():
      pdu_status_list.append(int(v))
       
   #ENCODE ON RS422
   encoded_frame = encode_obc_rs422_frame(0x02, Logic_Id, pdu_status_list)
   print(f" PDU SEND RS422: {encoded_frame.hex()}")


   LOGGER.info("# SCENARIO 13: SEND GetRawMeasurements")

   #COBC FORM MESSAGE
   Message_Id = 0x0F
   Logic_Id = 0x00
   Payload = [0x00, 0x00, 0x01]
   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)
   GetRawMeasurements ={
      pdu_cmd:{
         "LogicUnitId": int(lid),
         "HighPwHeaterSel": int.from_bytes(pld, "big"),
         "LowPwHeaterSel":0x00,
         "ReactionWheelEnSel":0x00,
         "PropEnSel":0x00,
         "AvionicLoadEnSel":0x00,
         "HdrmEnSel":0x00,
         "StAndMagEnSel":0x00,
         "IsolatedPwEnSel":0x00,
      }
   }

   #SEND MESSAGE on CCSDS
   Reply = send_semsim_ccsds_frame(0x08, GetRawMeasurements, APID, 2, 16)

   #RECEIVE MESSAGE on CCSDS
   dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
   status1 = dict_command_rcv["GetRawMeasurements"]
   pdu_status_list = []
   for k,v in status1.items():
      pdu_status_list.append(int(v))
   raw_value = struct.pack('!Q', pdu_status_list[0])

   #ENCODE ON RS422
   encoded_data = encode_obc_rs422_frame(0x0E, 0x00, raw_value)
   print(f" PDU SEND RS422: {encoded_data.hex()}")
   
   
   LOGGER.info("# SCENARIO 14: SEND PduGoSafe")
   Message_Id = 0x09
   Logic_Id = 0x00
   Payload = []
   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)
   PduGoSafe ={
   pdu_cmd:{}
   }

   #SEND MESSAGE on CCSDS
   Reply = send_semsim_ccsds_frame(0x0F, PduGoSafe, APID, 2, 16)

   #RECEIVE MESSAGE on CCSDS
   dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
   #ENCODE MESSAGE on RS422
   ack1 = dict_command_rcv["MsgAcknowlegement"]["RequestedMsgId"]
   ack2 = dict_command_rcv["MsgAcknowlegement"]["PduReturnCode"]

   #ENCODE ON RS422
   encoded_frame = encode_obc_rs422_frame(0x03, 0x00, [list(PDU_COMMANDS.keys())[list(PDU_COMMANDS.values()).index(ack1)], int(ack2)])
   print(f" PDU SEND RS422: {encoded_frame.hex()}")

   LOGGER.info("# SCENARIO 15: SEND GetPduStatus")
   Message_Id = 0x02
   Logic_Id = 0x00
   Payload = []

   #COBC FORM MESSAGE
   encoded_frame = encode_obc_rs422_frame(Message_Id, Logic_Id, Payload)
   print(f" OBC SEND RS422: {encoded_frame.hex()}")
   #DECODE MESSAGE on RS422
   pdu_cmd, mid, lid, pld = decode_obc_rs422_frame(encoded_frame)

   #ENCODE MESSAGE on CCSDS
   GetPduStatus ={
   pdu_cmd:{}
   }

   #SEND MESSAGE on CCSDS
   Reply = send_semsim_ccsds_frame(0x10, GetPduStatus, APID, 2, 5)

   #RECEIVE MESSAGE on CCSDS
   dict_command_rcv, apid, type, subtype = receive_semsim_ccsds_frame(Reply)
   status = json.loads(dict_command_rcv)
   pdu_status_list = []
   for k,v in status["PduStatus"].items():
      pdu_status_list.append(int(v))
       
   #ENCODE ON RS422
   encoded_frame = encode_obc_rs422_frame(0x02, 0x00, pdu_status_list)
   print(f" PDU SEND RS422: {encoded_frame.hex()}")