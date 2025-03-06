import socket
import json
from threading import *

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

if __name__ == "__main__":
  
   APID = 0x0A

   LOGGER.info(f"### TEST EVENT REPORTING PUS 5 2560 ###")
   REPORT_GEN = [[List_Disable_Report_Gen, 7], [Enable_Report_Gen_2560, 5], [List_Disable_Report_Gen, 7],  [Disable_Report_Gen_2560, 6], [List_Disable_Report_Gen, 7]]
   seq_count = 0x00
   for test in REPORT_GEN:
      test_id = test[0]
      LOGGER.info(f"# SCENARIO {seq_count}: {test_id} TEST ")
      json_object = json.dumps(test[0])
      #                           SEQCOUNT MESS       APID  T ST
      cmd2pdu = SpacePacketCommand(seq_count, json_object, APID, 5, test[1])
      UDPCon = send_message(cmd2pdu)
      if test[1] == 7:
         for i in [0,1,2]:   
            tlm_rcv = expecting_ack(UDPCon)
            packet_data_field, apid, type, subtype = SpacePacketDecoder(tlm_rcv)
            decode_tlm(packet_data_field, apid, type, subtype)
      else:
          for i in [0,1]:   
            tlm_rcv = expecting_ack(UDPCon)
            packet_data_field, apid, type, subtype = SpacePacketDecoder(tlm_rcv)
            decode_tlm(packet_data_field, apid, type, subtype)
      time.sleep(5)
      seq_count = seq_count+1
   LOGGER.info(f"### END TEST EVENT REPORTING PUS 5 2560 ###")

   LOGGER.info(f"### TEST EVENT REPORTING PUS 5 2561 ###")
   REPORT_GEN = [[List_Disable_Report_Gen, 7], [Enable_Report_Gen_2561, 5], [List_Disable_Report_Gen, 7], [Disable_Report_Gen_Both, 6], [List_Disable_Report_Gen, 7]]
   seq_count = 0x00
   for test in REPORT_GEN:
      test_id = test[0]
      LOGGER.info(f"# SCENARIO {seq_count}: {test_id} TEST ")
      json_object = json.dumps(test[0])
      #                           SEQCOUNT MESS       APID  T ST
      cmd2pdu = SpacePacketCommand(seq_count, json_object, APID, 5, test[1])
      UDPCon = send_message(cmd2pdu)
      if test[1] == 7:
         for i in [0,1,2]:   
            tlm_rcv = expecting_ack(UDPCon)
            packet_data_field, apid, type, subtype = SpacePacketDecoder(tlm_rcv)
            decode_tlm(packet_data_field, apid, type, subtype)
      else:
          for i in [0,1]:   
            tlm_rcv = expecting_ack(UDPCon)
            packet_data_field, apid, type, subtype = SpacePacketDecoder(tlm_rcv)
            decode_tlm(packet_data_field, apid, type, subtype)
      time.sleep(5)
      seq_count = seq_count+1
   LOGGER.info(f"### END TEST EVENT REPORTING PUS 5 2561###")

   LOGGER.info(f"### TEST EVENT REPORTING PUS 5 BOTH ###")
   REPORT_GEN = [[List_Disable_Report_Gen, 7], [Enable_Report_Gen_Both, 5], [List_Disable_Report_Gen, 7], [Disable_Report_Gen_Both, 6], [List_Disable_Report_Gen, 7]]
   seq_count = 0x00
   for test in REPORT_GEN:
      test_id = test[0]
      LOGGER.info(f"# SCENARIO {seq_count}: {test_id} TEST ")
      json_object = json.dumps(test[0])
      #                           SEQCOUNT MESS       APID  T ST
      cmd2pdu = SpacePacketCommand(seq_count, json_object, APID, 5, test[1])
      UDPCon = send_message(cmd2pdu)
      if test[1] == 7:
         for i in [0,1,2]:   
            tlm_rcv = expecting_ack(UDPCon)
            packet_data_field, apid, type, subtype = SpacePacketDecoder(tlm_rcv)
            decode_tlm(packet_data_field, apid, type, subtype)
      else:
          for i in [0,1]:   
            tlm_rcv = expecting_ack(UDPCon)
            packet_data_field, apid, type, subtype = SpacePacketDecoder(tlm_rcv)
            decode_tlm(packet_data_field, apid, type, subtype)
      time.sleep(5)
      seq_count = seq_count+1
   LOGGER.info(f"### END TEST EVENT REPORTING PUS 5 BOTH###")