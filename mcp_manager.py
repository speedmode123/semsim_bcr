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


def mcp_manager(db_name, host, user, password, conf_file):
    rtos_checker = db_manager.db_manager(db_name, host, user, password, conf_file)
    rtos_checker.db_connect()
    GetPduStatus ={
    "GetPduStatus":{}
    }
    GetUnitLineStates ={
    "GetUnitLineStates":{}
    }
    threads = {}
    prev_Pos_to_ON = 0
    prev_Pos_to_OFF = 0
    while rtos_checker.check_rtos() == '1':
        Pos_to_ON = []
        Pos_to_OFF = []
        detect_change_on = False
        detect_change_off = False
        json_pdu_statusN = pdu.GetPduStatus(GetPduStatus, 0x65, db_name,host, user, password,  conf_file)
        json_pdu_statusR = pdu.GetPduStatus(GetPduStatus, 0x66, db_name,host, user, password,  conf_file)
        #LOGGER.info(f"json_pdu_statusN: {json_pdu_statusN} | json_pdu_statusR: {json_pdu_statusR}")
        pdu_statusN = json.loads(json_pdu_statusN)["PduStatus"]["PduState"]
        pdu_statusR = json.loads(json_pdu_statusR)["PduStatus"]["PduState"]
        #LOGGER.info(f"pdu_statusN: {pdu_statusN} | pdu_statusR: {pdu_statusR}")
        PduNLines = 0
        PduRLines = 0
        if int(pdu_statusN) != 0 and int(pdu_statusN) != 1:
            PduUnitLineStatesN = pdu.GetUnitLineStates(GetUnitLineStates, 0x65, db_name,host, user, password,  conf_file)
            #print(f"json_pdu_lines_statusN: {PduUnitLineStatesN}")
            PduNLines = json.loads(PduUnitLineStatesN)["PduUnitLineStates"]
            Pos_to_ON, Pos_to_OFF = get_switch_for_mcp(PduNLines, Pos_to_ON, Pos_to_OFF)
            Pos_to_ON_sorted = sorted(Pos_to_ON)
            Pos_to_OFF_sorted = sorted(Pos_to_OFF)
            if prev_Pos_to_ON != 0 or prev_Pos_to_OFF != 0:
                prev_Pos_to_ON_sorted = sorted(prev_Pos_to_ON)
                prev_Pos_to_OFF_sorted = sorted(prev_Pos_to_OFF)
            else:
                prev_Pos_to_ON_sorted = prev_Pos_to_ON
                prev_Pos_to_OFF_sorted = prev_Pos_to_OFF
            if Pos_to_ON_sorted != prev_Pos_to_ON_sorted:
                prev_Pos_to_ON = Pos_to_ON
                detect_change_on = True
            if Pos_to_OFF_sorted != prev_Pos_to_OFF_sorted:
                prev_Pos_to_OFF = Pos_to_OFF
                detect_change_off = True
        if detect_change_on:
            LOGGER.info(f"PDU N FLPos_to_ON : {Pos_to_ON}")  
        if detect_change_off:
            LOGGER.info(f"PDU N FLPos_to_OFF : {Pos_to_OFF}")
        if int(pdu_statusR) != 0 and int(pdu_statusR) != 1:
            PduUnitLineStatesR = pdu.GetUnitLineStates(GetUnitLineStates, 0x66, db_name,host, user, password,  conf_file)
            #print(f"json_pdu_lines_statusR: {PduUnitLineStatesR}")
            PduRLines = json.loads(PduUnitLineStatesR)["PduUnitLineStates"]
            Pos_to_ON, Pos_to_OFF = get_switch_for_mcp(PduRLines, Pos_to_ON, Pos_to_OFF)
            Pos_to_ON_sorted = sorted(Pos_to_ON)
            Pos_to_OFF_sorted = sorted(Pos_to_OFF)
            if prev_Pos_to_ON != 0 and prev_Pos_to_OFF != 0:
                prev_Pos_to_ON_sorted = sorted(prev_Pos_to_ON)
                prev_Pos_to_OFF_sorted = sorted(prev_Pos_to_OFF)
            else:
                prev_Pos_to_ON_sorted = prev_Pos_to_ON
                prev_Pos_to_OFF_sorted = prev_Pos_to_OFF
            if Pos_to_ON_sorted != prev_Pos_to_ON_sorted:
                prev_Pos_to_ON = Pos_to_ON
                detect_change_on = True
            if Pos_to_OFF_sorted != prev_Pos_to_OFF_sorted:
                prev_Pos_to_OFF = Pos_to_OFF
                detect_change_off = True
        if detect_change_on:
            LOGGER.info(f"PDU R FLPos_to_ON : {Pos_to_ON}")  
        if detect_change_off:
            LOGGER.info(f"PDU R FLPos_to_OFF : {Pos_to_OFF}") 
    else:
        time.sleep(1)
        rtos_checker.db_disconnect()


def get_switch_for_mcp(PduLines, Pos_to_ON, Pos_to_OFF):
    if PduLines != 0:
        idx = 0
        for k,v in PduLines.items():
                match k:
                    case "HighPwHeaterEnSel":
                        htr_hp = list(format(int(v), '024b'))
                        htr_hp.reverse()
                        for p in htr_hp[0:18]:
                            if int(p) == 1:
                                Pos_to_ON.append(idx)
                            else:
                                Pos_to_OFF.append(idx)
                            idx = idx + 1
                        #LOGGER.info(f"{k} FLPos_to_ON : {Pos_to_ON} |  FLPos_to_OFF : {Pos_to_OFF}")
                    case "LowPwHeaterEnSel":
                        htr_lp = list(format(int(v), '024b'))
                        htr_lp.reverse()
                        for p in htr_lp[0:18]:
                            if int(p) == 1:
                                Pos_to_ON.append(idx)
                            else:
                                Pos_to_OFF.append(idx)
                            idx = idx + 1
                        #LOGGER.info(f"{k} FLPos_to_ON : {Pos_to_ON} |  FLPos_to_OFF : {Pos_to_OFF}")
                    case "AvionicLoadEnSel":
                        av_load = list(format(int(v), '016b'))
                        av_load.reverse()
                        for p in av_load[0:10]:
                            if int(p) == 1:
                                Pos_to_ON.append(idx)
                            else:
                                Pos_to_OFF.append(idx)
                            idx = idx + 1
                        #LOGGER.info(f"{k} FLPos_to_ON : {Pos_to_ON} |  FLPos_to_OFF : {Pos_to_OFF}")
                    case "HdrmEnSel":
                        hdrm_load = list(format(int(v), '016b'))
                        hdrm_load.reverse()
                        for p in hdrm_load[0:10]:
                            if int(p) == 1:
                                Pos_to_ON.append(idx)
                            else:
                                Pos_to_OFF.append(idx)
                            idx = idx + 1
                        #LOGGER.info(f"{k} FLPos_to_ON : {Pos_to_ON} |  FLPos_to_OFF : {Pos_to_OFF}")
                    case "ReactionWheelEnSel":
                        rw_load = list(format(int(v), '016b'))
                        rw_load.reverse()
                        for p in rw_load[0:4]:
                            if int(p) == 1:
                                Pos_to_ON.append(idx)
                            else:
                                Pos_to_OFF.append(idx)
                            idx = idx + 1
                        #LOGGER.info(f"{k} FLPos_to_ON : {Pos_to_ON} |  FLPos_to_OFF : {Pos_to_OFF}")
                    case "PropEnSel":
                        prop_load = list(format(int(v), '008b'))
                        prop_load.reverse()
                        for p in prop_load[0:2]:
                            if int(p) == 1:
                                Pos_to_ON.append(idx)
                            else:
                                Pos_to_OFF.append(idx)
                            idx = idx + 1
                        #LOGGER.info(f"{k} FLPos_to_ON : {Pos_to_ON} |  FLPos_to_OFF : {Pos_to_OFF}")
                    case "StAndMagEnSel":
                        stm_load = list(format(int(v), '008b'))
                        stm_load.reverse()
                        for p in stm_load[0:3]:
                            if int(p) == 1:
                                Pos_to_ON.append(idx)
                            else:
                                Pos_to_OFF.append(idx)
                            idx = idx + 1
                        #LOGGER.info(f"{k} FLPos_to_ON : {Pos_to_ON} |  FLPos_to_OFF : {Pos_to_OFF}")
                    case "IsolatedPwEnSel":
                        iso_load = list(format(int(v), '008b'))
                        iso_load.reverse()
                        for p in iso_load[0:3]:
                            if int(p) == 1:
                                Pos_to_ON.append(idx)
                            else:
                                Pos_to_OFF.append(idx)
                            idx = idx + 1
                        #LOGGER.info(f"{k} FLPos_to_ON : {Pos_to_ON} |  FLPos_to_OFF : {Pos_to_OFF}")
                    case  _:
                        pass
    else:
        pass
    return Pos_to_ON, Pos_to_OFF

if __name__ == "__main__":
    conf_file = "hw_conf_sem"
    db_name = "sem_demo"
    host = "localhost"
    user = "postgres"
    password ="postgres"
    mcp_manager(db_name, host, user, password, conf_file)