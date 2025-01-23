import os
from random import uniform
import time
import psycopg2
import random, logging, time, json
import ast
import db_manager
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

PduHeartBeat ={
    "PduHeartBeat":{
        "HeartBeat": 0
    }
}

PduStatus ={
                "PduStatus":{
                    "PduState": 0x00,
                    "ProtectionStatus": 0x07,
                    "CommHwStatus": 0x00,
                    "CommSwStatus": 0x00,
                    "UloadError": 0x00,
                    "DloadError": 0x00,
                    "CmdError": 0x00,
                    "OperError": 0x00,
                    "ConfigStatus": 0x00,
                    "RequestAcceptedCount": 0x00,
                    "RequestRejectedCount": 0x00
                }
}

PduState = {
    "PduGoBoot": 0,
    "PduGoLoad": 1,
    "PduGoOperate": 2,
    "PduGoSafe": 3
}
LogicalUnitId = {
    0: "HighPwHeaterEnSel",
    1: "LowPwHeaterEnSel",
    2: "ReactionWheelEnSel",
    3: "PropEnSel",
    4: "AvionicLoadEnSel",
    5: "HdrmEnSel",
    6: "StAndMagEnSel",
    7: "IsolatedPwEnSel",
    8: "Thermistors",
}

PduUnitLineStates={
                "PduUnitLineStates":{
                    "HighPwHeaterEnSel": 0x00,
                    "LowPwHeaterEnSel": 0x00,
                    "ReactionWheelEnSel": 0x00,
                    "PropEnSel": 0x00,
                    "AvionicLoadEnSel": 0x00,
                    "HdrmEnSel": 0x00,
                    "StAndMagEnSel": 0x00,
                    "IsolatedPwEnSel": 0x00
                }
}

PduRawMeasurements ={
    "GetRawMeasurements":{
        "RawMeasurements": "28.01"
    }
}

PduConvertedMeasurements ={
    "GetConvertedMeasurements":{
        "ConvertedMeasurements": 0x703
    }
}

MsgAcknowlegement ={
                "MsgAcknowlegement":{
                    "RequestedMsgId": 0,
                    "PduReturnCode": 0
                }
}

AddrDloadStart ={
                "AddrDloadStart":{
                    "PduDLoadLength": 0,
                    "PduDLoadAddr": 0
                }
}

AddrDloadData ={
                "AddrDloadData":{
                    "PduDLoadData": 0
                }
}

EmergencyReport = {
                "PduStatus":{
                    "PduState": 0x04,
                    "ProtectionStatus": 0x07,
                    "CommHwStatus": 0x00,
                    "CommSwStatus": 0x00,
                    "UloadError": 0x00,
                    "DloadError": 0x00,
                    "CmdError": 0x00,
                    "OperError": 0x00,
                    "ConfigStatus": 0x00,
                    "RequestAcceptedCount": 0x00,
                    "RequestRejectedCount": 0x00
                }
}

class pdu_n:

    def __init__(self, cursor, db_name, host, user, password, conf_file):
        unit, state = get_state(db_name, host, user, password, "pdu_n", "STATE", conf_file)
        previous_states = json.loads(state)
        if int(previous_states) == 0:
            LOGGER.info(f"previous_states: {type(previous_states)}")
            init_bytes_state(db_name, host, user, password,"pdu_n", 'PduHeartBeat', PduHeartBeat, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_n", 'PduStatus', PduStatus, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_n", 'MsgAcknowledgment', MsgAcknowlegement, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_n", 'PduUnitLineStates', PduUnitLineStates, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_n", 'PduRawMeasurements', PduRawMeasurements, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_n", 'PduConvertedMeasurements', PduConvertedMeasurements, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_n", 'AddrDloadStart', AddrDloadStart, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_n", 'AddrDloadData', AddrDloadData, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_n", 'EmergencyReport', EmergencyReport, conf_file)
            udb = db_manager.db_manager(db_name, host, user, password, conf_file)
            udb.update_db("pdu_n", "STATE", 1)

class pdu_r:

    def __init__(self, cursor, db_name, host, user, password, conf_file):
        unit, state = get_state(db_name, host, user, password, "pdu_r", "STATE", conf_file)
        previous_states = json.loads(state)
        if int(previous_states) == 0:
            LOGGER.info(f"previous_states: {type(previous_states)}")
            init_bytes_state(db_name, host, user, password,"pdu_r", 'PduHeartBeat', PduHeartBeat, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_r", 'PduStatus', PduStatus, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_r", 'MsgAcknowledgment', MsgAcknowlegement, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_r", 'PduUnitLineStates', PduUnitLineStates, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_r", 'PduRawMeasurements', PduRawMeasurements, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_r", 'PduConvertedMeasurements', PduConvertedMeasurements, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_r", 'AddrDloadStart', AddrDloadStart, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_r", 'AddrDloadData', AddrDloadData, conf_file)
            init_bytes_state(db_name, host, user, password,"pdu_r", 'EmergencyReport', EmergencyReport, conf_file)
            udb = db_manager.db_manager(db_name, host, user, password, conf_file)
            udb.update_db("pdu_r", "STATE", 1)


def GetMsgAcknowlegement(GetMsgAcknowlegement, apid, db_name, host, user, password, conf_file):
    for cmd, param_list in GetMsgAcknowlegement.items():
            LOGGER.info(f"CMD: {cmd}")
            condition_1 = ("ObcHeartBeat" in str(cmd))
            condition_2 = ("GetUnitLineStates" in str(cmd))
            condition_3 = ("GetRawMeasurements" in str(cmd))
            condition_4 = ("GetPduStatus" in str(cmd))
            LOGGER.info(f"Check for ACK: {(condition_1 or condition_2 or condition_3 or condition_4)}")
            if not (condition_1 or condition_2 or condition_3 or condition_4):
                udb = db_manager.db_manager(db_name, host, user, password, conf_file)
                if apid == 0x65:
                    unit, oldMsgAcknowlegement = udb.read_db('pdu_n', 'MsgAcknowledgment')
                    oldMsgAcknowlegement = json.loads(oldMsgAcknowlegement)
                    oldMsgAcknowlegement["MsgAcknowlegement"]["RequestedMsgId"] = cmd
                    init_bytes_state(db_name,  host, user, password, "pdu_n", 'MsgAcknowlegement', oldMsgAcknowlegement, conf_file)
                else: 
                    unit, oldMsgAcknowlegement = udb.read_db("pdu_r", 'MsgAcknowlegement')
                    oldMsgAcknowlegement = json.loads(oldMsgAcknowlegement)
                    oldMsgAcknowlegement["MsgAcknowlegement"]["RequestedMsgId"] = cmd
                    init_bytes_state(db_name,  host, user, password, "pdu_n", 'MsgAcknowlegement', oldMsgAcknowlegement, conf_file)
            condition_5 = ("CmdOk" in str(oldMsgAcknowlegement["MsgAcknowlegement"]["PduReturnCode"]))
            if condition_5:
                TYPE = 1
                SUBTYPE = 7
            else:
                TYPE = 1
                SUBTYPE = 8
    return oldMsgAcknowlegement, TYPE, SUBTYPE

def ObcHeartBeat(ObcHeartBeat, apid, db_name, host, user, password, conf_file):
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    PduHeartBeat["PduHeartBeat"].update(ObcHeartBeat["ObcHeartBeat"])
    if apid == 0x65:
        init_bytes_state(db_name, host, user, password, "pdu_n", 'PduHeartBeat', PduHeartBeat, conf_file)
        unit, Update_PduHeartBeat = udb.read_db('pdu_n', 'PduHeartBeat')
    else: 
        init_bytes_state(db_name, host, user, password, "pdu_r", 'PduHeartBeat', PduHeartBeat, conf_file)
        unit, Update_PduHeartBeat = udb.read_db('pdu_r', 'PduHeartBeat')
    return Update_PduHeartBeat

def GetPduStatus(GetPduStatus, apid, db_name, host, user, password, conf_file):
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    if apid == 0x65:
        unit, tlm_read = udb.read_db('pdu_n', 'PduStatus')
    else: 
        unit, tlm_read = udb.read_db("pdu_r", 'PduStatus')
    Update_GetPduStatus = tlm_read
    return Update_GetPduStatus

def GetUnitLineStates(GetUnitLineStates, apid, db_name, host, user, password, conf_file):
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    if apid == 0x65:
        unit, tlm_read = udb.read_db('pdu_n', 'PduUnitLineStates')
    else: 
        unit, tlm_read = udb.read_db("pdu_r", 'PduUnitLineStates')
    Update_GetPduStatus = tlm_read
    return Update_GetPduStatus

def SetUnitPwLines(SetUnitPwLines, apid, db_name, host, user, password, conf_file):
    LogicalUnitIdn = LogicalUnitId[SetUnitPwLines["SetUnitPwLines"]["LogicUnitId"]]
    LOGGER.info(f"LogicalUnitId: {LogicalUnitIdn}")
    match LogicalUnitIdn:
        case "HighPwHeaterEnSel":
            NewItem_SetUnitPwLines = SetUnitPwLines["SetUnitPwLines"]["HighPwHeaterEnSel"]
        case "LowPwHeaterEnSel":
            NewItem_SetUnitPwLines = SetUnitPwLines["SetUnitPwLines"]["LowPwHeaterEnSel"]
        case "ReactionWheelEnSel":
            NewItem_SetUnitPwLines = SetUnitPwLines["SetUnitPwLines"]["ReactionWheelEnSel"]
        case "PropEnSel":
            NewItem_SetUnitPwLines = SetUnitPwLines["SetUnitPwLines"]["PropEnSel"]
        case "AvionicLoadEnSel":
            NewItem_SetUnitPwLines = SetUnitPwLines["SetUnitPwLines"]["AvionicLoadEnSel"]
        case "HdrmEnSel":
            NewItem_SetUnitPwLines = SetUnitPwLines["SetUnitPwLines"]["HdrmEnSel"]
        case "StAndMagEnSel":
            NewItem_SetUnitPwLines = SetUnitPwLines["SetUnitPwLines"]["StAndMagEnSel"]
        case "IsolatedPwEnSel":
            NewItem_SetUnitPwLines = SetUnitPwLines["SetUnitPwLines"]["IsolatedPwEnSel"]
        case "Thermistors":
            NewItem_SetUnitPwLines = SetUnitPwLines["SetUnitPwLines"]["Thermistors"]
        case  _:
            LOGGER.info(f"Logical Id: {LogicalUnitIdn} Not Implemented")
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    if apid == 0x65:
        unit, old_PduUnitLineStates = udb.read_db('pdu_n', 'PduUnitLineStates')
        oldj_PduUnitLineStates = json.loads(old_PduUnitLineStates)
        oldj_PduUnitLineStates["PduUnitLineStates"][LogicalUnitIdn] = NewItem_SetUnitPwLines
        init_bytes_state(db_name, host, user, password,"pdu_n", 'PduUnitLineStates', oldj_PduUnitLineStates, conf_file)
    else: 
        unit, old_PduUnitLineStates = udb.read_db("pdu_r", 'PduUnitLineStates')
        oldj_PduUnitLineStates = json.loads(old_PduUnitLineStates)
        oldj_PduUnitLineStates["PduUnitLineStates"][LogicalUnitIdn] = NewItem_SetUnitPwLines
        init_bytes_state(db_name, host, user, password, "pdu_r", 'PduUnitLineStates', oldj_PduUnitLineStates, conf_file)

def GetRawMeasurements(RawMeasurements, apid, db_name, host, user, password, conf_file):
    Unit_Lines_Str = GetUnitLineStates(RawMeasurements, apid, db_name, host, user, password, conf_file)
    Unit_Lines = json.loads(Unit_Lines_Str)
    Unit_Lines_Status = Unit_Lines["PduUnitLineStates"]
    LogicId = RawMeasurements["GetRawMeasurements"]["LogicUnitId"]
    Single_Line_Status = Unit_Lines_Status[LogicalUnitId[int(LogicId)]]
    LOGGER.info(f"Single_Line_Status: {Single_Line_Status}")
    if int(Single_Line_Status) != 0:
        udb = db_manager.db_manager(db_name, host, user, password, conf_file)
        if apid == 0x65:
            unit, tlm_read = udb.read_db('pdu_n', 'PduRawMeasurements')
        else: 
            unit, tlm_read = udb.read_db("pdu_r", 'PduRawMeasurements')
    else:
        tlm_read_tmp ={
            "GetRawMeasurements":{
                "RawMeasurements": "00.00"
            }
        }
        tlm_read = json.dumps(tlm_read_tmp)
    Update_GetPduStatus = tlm_read
    return Update_GetPduStatus
    
def PduGoTo(cmd, apid, db_name, host, user, password, conf_file):
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    if apid == 0x65:
        unit, tlm_read = udb.read_db('pdu_n', 'PduStatus')
        PduStates = json.loads(tlm_read)
        PduStates["PduStatus"]["PduState"] = PduState[cmd]
        init_bytes_state(db_name, host, user, password, "pdu_n", 'PduStatus', PduStates, conf_file)
    else: 
        unit, tlm_read = udb.read_db("pdu_r", 'PduStatus')
        PduStates = json.loads(tlm_read)
        PduStates["PduStatus"]["PduState"] = cmd
        init_bytes_state(db_name, host, user, password, "pdu_r", 'PduStatus', PduStates, conf_file)

def init_bytes_state(db_name, host, user, password, unit, tlm_name, tlm_dict, conf_file):
    json_object = json.dumps(tlm_dict)
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    udb.update_db(unit, tlm_name, json_object)

def get_state(db_name, host, user, password, component,telemetry_name, conf_file):
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    unit, tlm_read = udb.read_db(component, telemetry_name)
    return unit, tlm_read