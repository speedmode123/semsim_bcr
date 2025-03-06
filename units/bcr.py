import random, logging, time, json
import db_manager
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)
RMAP_CRC_TABLE = [
    0x00, 0x91, 0xe3, 0x72, 0x07, 0x96, 0xe4, 0x75,
    0x0e, 0x9f, 0xed, 0x7c, 0x09, 0x98, 0xea, 0x7b,
    0x1c, 0x8d, 0xff, 0x6e, 0x1b, 0x8a, 0xf8, 0x69,
    0x12, 0x83, 0xf1, 0x60, 0x15, 0x84, 0xf6, 0x67,
    0x38, 0xa9, 0xdb, 0x4a, 0x3f, 0xae, 0xdc, 0x4d,
    0x36, 0xa7, 0xd5, 0x44, 0x31, 0xa0, 0xd2, 0x43,
    0x24, 0xb5, 0xc7, 0x56, 0x23, 0xb2, 0xc0, 0x51,
    0x2a, 0xbb, 0xc9, 0x58, 0x2d, 0xbc, 0xce, 0x5f,
    0x70, 0xe1, 0x93, 0x02, 0x77, 0xe6, 0x94, 0x05,
    0x7e, 0xef, 0x9d, 0x0c, 0x79, 0xe8, 0x9a, 0x0b,
    0x6c, 0xfd, 0x8f, 0x1e, 0x6b, 0xfa, 0x88, 0x19,
    0x62, 0xf3, 0x81, 0x10, 0x65, 0xf4, 0x86, 0x17,
    0x48, 0xd9, 0xab, 0x3a, 0x4f, 0xde, 0xac, 0x3d,
    0x46, 0xd7, 0xa5, 0x34, 0x41, 0xd0, 0xa2, 0x33,
    0x54, 0xc5, 0xb7, 0x26, 0x53, 0xc2, 0xb0, 0x21,
    0x5a, 0xcb, 0xb9, 0x28, 0x5d, 0xcc, 0xbe, 0x2f,
    0xe0, 0x71, 0x03, 0x92, 0xe7, 0x76, 0x04, 0x95,
    0xee, 0x7f, 0x0d, 0x9c, 0xe9, 0x78, 0x0a, 0x9b,
    0xfc, 0x6d, 0x1f, 0x8e, 0xfb, 0x6a, 0x18, 0x89,
    0xf2, 0x63, 0x11, 0x80, 0xf5, 0x64, 0x16, 0x87,
    0xd8, 0x49, 0x3b, 0xaa, 0xdf, 0x4e, 0x3c, 0xad,
    0xd6, 0x47, 0x35, 0xa4, 0xd1, 0x40, 0x32, 0xa3,
    0xc4, 0x55, 0x27, 0xb6, 0xc3, 0x52, 0x20, 0xb1,
    0xca, 0x5b, 0x29, 0xb8, 0xcd, 0x5c, 0x2e, 0xbf,
    0x90, 0x01, 0x73, 0xe2, 0x97, 0x06, 0x74, 0xe5,
    0x9e, 0x0f, 0x7d, 0xec, 0x99, 0x08, 0x7a, 0xeb,
    0x8c, 0x1d, 0x6f, 0xfe, 0x8b, 0x1a, 0x68, 0xf9,
    0x82, 0x13, 0x61, 0xf0, 0x85, 0x14, 0x66, 0xf7,
    0xa8, 0x39, 0x4b, 0xda, 0xaf, 0x3e, 0x4c, 0xdd,
    0xa6, 0x37, 0x45, 0xd4, 0xa1, 0x30, 0x42, 0xd3,
    0xb4, 0x25, 0x57, 0xc6, 0xb3, 0x22, 0x50, 0xc1,
    0xba, 0x2b, 0x59, 0xc8, 0xbd, 0x2c, 0x5e, 0xcf
]
# BCR on-board parameters and event reports 
systemMgr = {
    "ONBOARD_PARAMETERS": {
        2560: {
            "name": "PID_BCR_SYSTEM_MGR_APID",
            "value": [0x00, 0x00]
        }, 
        2561: {
            "name": "PID_BCR_SYSTEM_MGR_OBT_COARSE",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2562: {
            "name": "PID_BCR_SYSTEM_MGR_OBT_FINE",
            "value": [0x00, 0x00]
        }, 
        2563: {
            "name":  "PID_BCR_SYSTEM_MGR_BSL_CONTEXT_VALIDITY",
            "value": 0x00
        }, 
        2564: {
            "name":  "PID_BCR_SYSTEM_MGR_BSL_CONTEXT_PLANNED_RESET_COUNTER",
            "value": [0x00, 0x00, 0x00, 0x00]
        },
        2565: {
            "name":  "PID_BCR_SYSTEM_MGR_BSL_CONTEXT_UNPLANNED_RESET_COUNTER",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2566: {
            "name":  "PID_BCR_SYSTEM_MGR_BSL_CONTEXT_STATUS",
            "value": [0x00, 0x00]
        }, 
        2567: {
            "name":  "PID_BCR_SYSTEM_MGR_STATE",
            "value": 0x00
        }, 
        2568: {
            "name":  "PID_BCR_SYSTEM_MGR_FREE_STACK_SIZE_SYSTEM_MGR",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2569: {
            "name":  "PID_BCR_SYSTEM_MGR_FREE_STACK_SIZE_COM_MGR",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2570: {
            "name":  "PID_BCR_SYSTEM_MGR_FREE_STACK_SIZE",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2571: {
            "name":  "PID_BCR_SYSTEM_MGR_FREE_STACK_SIZE",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2572: {
            "name":  "PID_BCR_SYSTEM_MGR_FREE_STACK_SIZE",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2573: {
            "name":  "PID_BCR_SYSTEM_MGR_FREE_STACK_SIZE",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2574: {
            "name":  "PID_BCR_SYSTEM_MGR_FREE_STACK_SIZE",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2575: {
            "name":  "PID_BCR_SYSTEM_MGR_FREE_STACK_SIZE",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2576: {
            "name":  "PID_BCR_SYSTEM_MGR_FREE_STACK_SIZE",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2577: {
            "name":  "PID_BCR_SYSTEM_MGR_FREE_STACK_SIZE",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2578: {
            "name":  "PID_BCR_SYSTEM_MGR_FREE_STACK_SIZE",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2579: {
            "name":  "PID_BCR_SYSTEM_MGR_FREE_STACK_SIZE",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2580: {                 
            "name":  "PID_BCR_SYSTEM_MGR_FREE_STACK_SIZE",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2581: {
            "name":  "PID_BCR_SYSTEM_MGR_MEM_SCRUB_OBS_RAM_SBE",
            "value": [0x00, 0x00]
        }, 
        2582 : {
            "name":  "PID_BCR_SYSTEM_MGR_MEM_SCRUB_OBS_ROM_SBE",
            "value": [0x00, 0x00]
        }, 
        2581: {
            "name":  "PID_BCR_SYSTEM_MGR_MEM_SCRUB_OBS_RAM_MBE",
            "value": [0x00, 0x00]
        }, 
        2582 : {
            "name":  "PID_BCR_SYSTEM_MGR_MEM_SCRUB_OBS_ROM_MBE",
            "value": [0x00, 0x00]
        }, 
        2583: {
            "name":  "PID_BCR_SYSTEM_MGR_MEM_SCRUB_OBS_ROM_RETRIEVES",
            "value": [0x00, 0x00]
        }
    },
    "EVENT_REPORTS": {
        2560: {
            "name": "EID_BCR_SYSTEM_MGR_INITIALIZATION",
            "severity": "EVENT_SEVERITY_NORMAL",
            "enabled": 0x01
        }
    }, 
}

comMgr = {
    "ONBOARD_PARAMETERS": {
        2586: {
            "name": "PID_BCR_COM_MGR_OBC_UART_0_OBSERVABLES_SENT_PKT",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2587: {
            "name": "PID_BCR_COM_MGR_OBC_UART_0_OBSERVABLES_RECEIVED_PKT",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2588: {
            "name": "PID_BCR_COM_MGR_OBC_UART_0_OBSERVABLES_DROPPED_PKT",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2589: {
            "name": "PID_BCR_COM_MGR_OBC_UART_0_OBSERVABLES_DISCARDED_PKT",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2590: {
            "name": "PID_BCR_COM_MGR_OBC_UART_0_SEND_FAILURES",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2591: {
            "name": "PID_BCR_COM_MGR_OBC_UART_1_SENT_PKT",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2592: {
            "name": "PID_BCR_COM_MGR_OBC_UART_1_OBSERVABLES_RECEIVED_PKT",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2593: {
            "name": "PID_BCR_COM_MGR_OBC_UART_1_OBSERVABLES_DROPPED_PKT",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2594: {
            "name": "PID_BCR_COM_MGR_OBC_UART_1_OBSERVABLE_DISCARDED_PKT",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2595: {
            "name": "PID_BCR_COM_MGR_OBC_UART_1_SEND_FAILURES",
            "value": [0x00, 0x00, 0x00, 0x00]
        }
    },
    "EVENT_REPORTS": {
    }, 

}

fdirMgr = {
    "ONBOARD_PARAMETERS": {
        2596: {
            "name": "PID_BCR_FDIR_MGR_ENABLE",
            "value": 0x01 # bool-8 True (default)
        }, 
        2597: {
            "name": "PID_BCR_FDIR_MGR_ENTRY_CONTEXT_ERROR_COUNTER",
            "value": [0x00, 0x00, 0x00, 0x00]
        }, 
        2598: {
            "name": "PID_BCR_FDIR_MGR_ENTRY_PERSISTENT_0_ENABLE",
            "value": 0x01 # bool-8 True (default)
        }, 
        2599: {
            "name": "PID_BCR_FDIR_MGR_ENTRY_PERSISTENT_0_ENABLE_RECOVERY",
            "value": 0x01 # bool-8 True (default)
        }, 
        2600: {
            "name": "PID_BCR_FDIR_MGR_ENTRY_PERSISTENT_0_ENABLE_RECOVERY_COUNTER",
            "value": 0x00 # uint-8 0 (default)
        }, 
        2601: {
            "name": "PID_BCR_FDIR_MGR_ENTRY_PERSISTENT_0_NB_CYCLES_FAULT_REPETITION",
            "value": [0x00, 0x00, 0x00, 0x00]
        },
    },
    "EVENT_REPORTS": {
        2561: {
            "name": "EID_BCR_SYSTEM_MGR_ENTRY_DISABLED_AFTER_TOO_MANY_RECOVERIES",
            "severity": "EVENT_SEVERITY_LOW",
            "enabled": 0x00
        }
    }
}

solarArraysMgr = {
    "ONBOARD_PARAMETERS": {
        2602: {
            "name": "PID_BCR_SOLAR_ARRAYS_MGR_CONFIG_TASK_TIME_STEP",
            "value": [0x00, 0x00, 0x00, 0x00]
        }
    },
    "EVENT_REPORTS": {
    }
}

acceptanceVerificationReport = {
    "requestId": {
        "versionNumber": 0x00,
        "packet": {
            "packetId": 0x00,
            "packetType": 0x00,
            "secondaryHeaderFlag": 0x00,
            "apid": 0x00
        },
        "sequence": {
            "Control": 0x00,
            "sequenceFlag": 0x00,
            "packetName": 0x00
        }
    },
    "failure-notice": {
        "code": [0x00, 0x00],
        "data": [0x00, 0x00]
    }
}

CompletionOfExecVerificationReport = {
    "requestId": {
        "versionNumber": 0x00,
        "packet": {
            "packetId": 0x00,
            "packetType": 0x00,
            "secondaryHeaderFlag": 0x00,
            "apid": 0x00
        },
        "sequence": {
            "Control": 0x00,
            "sequenceFlag": 0x00,
            "packetName": 0x00
        }
    },
    "failure-notice": {
        "code": [0x00, 0x00],
        "data": [0x00, 0x00]
    }
}

Memory = {
    "swdb" : [0x00, 0x00, 0x00, 0x00],
    "dataFRAM": [0x00, 0x00, 0x00, 0x00],
    "programFRAM": [0x00, 0x00, 0x00, 0x00],
    "MAX": [0x00, 0x00, 0x00, 0x00]
}

class bcr_nominal:
    def __init__(self, cursor, db_name, host, user, password, conf_file):
        unit, state = get_state(db_name, host, user, password, "bcr_nominal", "STATE", conf_file)
        previous_states = json.loads(state)
        if int(previous_states) == 0:
            init_bytes_state(db_name, host, user, password,"bcr_nominal", 'systemMgr', systemMgr, conf_file)
            init_bytes_state(db_name, host, user, password,"bcr_nominal", 'comMgr', comMgr, conf_file)
            init_bytes_state(db_name, host, user, password,"bcr_nominal", 'fdirMgr', fdirMgr, conf_file)
            init_bytes_state(db_name, host, user, password,"bcr_nominal", 'solarArraysMgr', solarArraysMgr, conf_file)
            init_bytes_state(db_name, host, user, password,"bcr_nominal", 'acceptanceVerificationReport', acceptanceVerificationReport, conf_file)
            init_bytes_state(db_name, host, user, password,"bcr_nominal", 'completionOfExecVerificationReport', CompletionOfExecVerificationReport, conf_file)
            init_bytes_state(db_name, host, user, password,"bcr_nominal", 'Memory', Memory, conf_file)
            udb = db_manager.db_manager(db_name, host, user, password, conf_file)
            udb.update_db("bcr_nominal", "STATE", 1)

class bcr_redundant:
    def __init__(self, cursor, db_name, host, user, password, conf_file):
        unit, state = get_state(db_name, host, user, password, "bcr_redundant", "STATE", conf_file)
        previous_states = json.loads(state)
        if int(previous_states) == 0:
            init_bytes_state(db_name, host, user, password,"bcr_redundant", 'systemMgr', systemMgr, conf_file)
            init_bytes_state(db_name, host, user, password,"bcr_redundant", 'comMgr', comMgr, conf_file)
            init_bytes_state(db_name, host, user, password,"bcr_redundant", 'fdirMgr', fdirMgr, conf_file)
            init_bytes_state(db_name, host, user, password,"bcr_redundant", 'solarArraysMgr', solarArraysMgr, conf_file)
            init_bytes_state(db_name, host, user, password,"bcr_redundant", 'acceptanceVerificationReport', acceptanceVerificationReport, conf_file)
            init_bytes_state(db_name, host, user, password,"bcr_redundant", 'completionOfExecVerificationReport', CompletionOfExecVerificationReport, conf_file)
            init_bytes_state(db_name, host, user, password,"bcr_redundant", 'Memory', Memory, conf_file)
            udb = db_manager.db_manager(db_name, host, user, password, conf_file)
            udb.update_db("bcr_redundant", "STATE", 1)

def init_bytes_state(db_name, host, user, password, unit, tlm_name, tlm_dict, conf_file):
    json_object = json.dumps(tlm_dict)
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    udb.update_db(unit, tlm_name, json_object)

def get_state(db_name, host, user, password, component, telemetry_name, conf_file):
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    unit, tlm_read = udb.read_db(component, telemetry_name)
    return unit, tlm_read

def Request_acceptance_verification(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file):
    type_r = 1
    subtype_r = 0
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    if apid == 0x0A:
        unit, tlm_read = udb.read_db("bcr_nominal", "acceptanceVerificationReport")
    else:
        unit, tlm_read = udb.read_db("bcr_redundant", "acceptanceVerificationReport")
    aVR = json.loads(tlm_read)
    if aVR["failure-notice"]["code"] == [0, 0]:
        subtype_r = 1
    else:
        subtype_r = 2
    return aVR, type_r, subtype_r 

def Request_completion_verification(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file):
    type_r = 1
    subtype_r = 0
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    if apid == 0x0A:
        unit, tlm_read = udb.read_db("bcr_nominal", "completionOfExecVerificationReport")
    else:
        unit, tlm_read = udb.read_db("bcr_redundant", "completionOfExecVerificationReport")
    aVR = json.loads(tlm_read)
    if aVR["failure-notice"]["code"] == [0, 0]:
        subtype_r = 7
    else:
        subtype_r = 8
    return aVR, type_r, subtype_r

def Event_reporting(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file):
    unit_pre = "bcr_"
    unit_suff = 0
    type_r = 5
    subtype_r = 0
    reply_dict = 0
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    if apid == 0x0A:
        unit_suff = "nominal"
    else:
        unit_suff = "redundant"
    unit, tlm_read_systemMgr = udb.read_db(unit_pre+unit_suff, "systemMgr")
    unit, tlm_read_fdirMgr = udb.read_db(unit_pre+unit_suff, "fdirMgr")
    systemMgrDict = json.loads(tlm_read_systemMgr)
    fdirMgrDict = json.loads(tlm_read_fdirMgr)
    match subtype:
        case 0x05:
            #n_of_EV = j_command_packet["n"]
            EV = j_command_packet["EventId"]
            is_EVlist = isinstance(EV, list)
            if is_EVlist:
                for evi in EV:
                    if evi == 2560:
                        systemMgrDict["EVENT_REPORTS"][str(evi)]["enabled"] = 0x01
                        init_bytes_state(db_name, host, user, password, unit_pre+unit_suff, 'systemMgr', systemMgrDict, conf_file)
                    elif evi == 2561:
                        fdirMgrDict["EVENT_REPORTS"][str(evi)]["enabled"] = 0x01
                        init_bytes_state(db_name, host, user, password, unit_pre+unit_suff, 'fdirMgr', fdirMgrDict, conf_file)
            else:
                if EV == 2560:
                    systemMgrDict["EVENT_REPORTS"][str(EV)]["enabled"] = 0x01
                    init_bytes_state(db_name, host, user, password, unit_pre+unit_suff, 'systemMgr', systemMgrDict, conf_file)
                elif EV == 2561:
                    fdirMgrDict["EVENT_REPORTS"][str(EV)]["enabled"] = 0x01
                    init_bytes_state(db_name, host, user, password, unit_pre+unit_suff, 'fdirMgr', fdirMgrDict, conf_file)
        case 0x06:
            #n_of_EV = j_command_packet["n"]
            EV = j_command_packet["EventId"]
            is_EVlist = isinstance(EV, list)
            if is_EVlist:
                for evi in EV:
                    if evi == 2560:
                        systemMgrDict["EVENT_REPORTS"][str(evi)]["enabled"] = 0x00
                        init_bytes_state(db_name, host, user, password, unit_pre+unit_suff, 'systemMgr', systemMgrDict, conf_file)
                    elif evi == 2561:
                        fdirMgrDict["EVENT_REPORTS"][str(evi)]["enabled"] = 0x00
                        init_bytes_state(db_name, host, user, password, unit_pre+unit_suff, 'fdirMgr', fdirMgrDict, conf_file)
            else:
                if EV == 2560:
                    systemMgrDict["EVENT_REPORTS"][str(EV)]["enabled"] = 0x00
                    init_bytes_state(db_name, host, user, password, unit_pre+unit_suff, 'systemMgr', systemMgrDict, conf_file)
                elif EV == 2561:
                    fdirMgrDict["EVENT_REPORTS"][str(EV)]["enabled"] = 0x00
                    init_bytes_state(db_name, host, user, password, unit_pre+unit_suff, 'fdirMgr', fdirMgrDict, conf_file)
        case 0x07:
            subtype_r = 8
            reply_dict = {
                "n": 0x00,
                "eventId": 0x00
            }
            EVR_STATUS_2560 = systemMgrDict["EVENT_REPORTS"]["2560"]["enabled"]
            EVR_STATUS_2561 = fdirMgrDict["EVENT_REPORTS"]["2561"]["enabled"]
            if EVR_STATUS_2560 == 0x00: 
                reply_dict["n"] = 0x01
                reply_dict["eventId"] = 2560
            if EVR_STATUS_2561 == 0x00: 
                reply_dict["n"] = 0x01
                reply_dict["eventId"] = 2561
            if EVR_STATUS_2560 == 0x00 and EVR_STATUS_2561 == 0x00:
                reply_dict["n"] = 0x02
                reply_dict["eventId"] = [2560, 2561]
            else:
                LOGGER.info(f"All EVENTS are ACTIVE")
        case _:
            pass
    return reply_dict, type_r, subtype_r

def Memory_management(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file):
    unit_pre = "bcr_"
    unit_suff = 0
    type_r = 6
    subtype_r = 0
    reply_dict = 0
    Mem_Dict = {
        0: "swdb",
        1: "dataFRAM",
        2: "programFRAM",
        3: "MAX"
    }
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    if apid == 0x0A:
        unit_suff = "nominal"
    else:
        unit_suff = "redundant"
    unit, tlm_read_Memory = udb.read_db(unit_pre+unit_suff, "Memory")
    systemMemory = json.loads(tlm_read_Memory)
    match subtype:
        case 0x02:
            #n_of_EV = j_command_packet["n"]
            memId = Mem_Dict[j_command_packet["memoryId"]]
            s_address = j_command_packet["StartAddress"]
            length_data = j_command_packet["length"]
            data_to_Load = j_command_packet["dataToLoad"]
            if str(s_address) in systemMemory[memId]:
               if not "X" in  systemMemory[memId][str(s_address)]:
                  LOGGER.warning(f"LOAD {s_address} with {data_to_Load}")
                  systemMemory[memId][s_address] = data_to_Load
            else:
               LOGGER.warning(f"CREATING {s_address} with {data_to_Load}")
               systemMemory[memId] = {
                   str(s_address): data_to_Load
               }
            init_bytes_state(db_name, host, user, password, unit_pre+unit_suff, 'Memory', systemMemory, conf_file)
        case 0x05:
            MemRead = 0x00
            memId = Mem_Dict[j_command_packet["memoryId"]]
            s_address = j_command_packet["StartAddress"]
            length_data = j_command_packet["length"]
            if str(s_address)  in systemMemory[memId]:
               LOGGER.warning(f"systemMemory[memId][str(s_address)]: {systemMemory[memId][str(s_address)]}")   
               if not "X" in systemMemory[memId][str(s_address)]:
                  MemRead = systemMemory[memId][str(s_address)]
                  subtype_r = 6
                  reply_dict = {
                      "memoryId": int(j_command_packet["memoryId"]),
                      "startAddress": s_address,
                      "length": length_data,
                      "dumpedData": MemRead
                  }
            LOGGER.warning(f"DUMP MEM CMD: {reply_dict} t: {type_r} st: {subtype_r}")     
        case 0x09:
            MemRead = 0x00
            memId = Mem_Dict[j_command_packet["memoryId"]]
            s_address = j_command_packet["StartAddress"]
            length_data = j_command_packet["length"]
            if str(s_address) in systemMemory[memId]:
               if not "X" in systemMemory[memId][str(s_address)]:
                  subtype_r = 10
                  MemRead = systemMemory[memId][str(s_address)]
                  reply_dict = {
                      "memoryId": int(j_command_packet["memoryId"]),
                      "startAddress": s_address,
                      "length": length_data,
                      "checksum": compute_crc(MemRead)
                  }
            LOGGER.warning(f"CHECK MEM CMD : {reply_dict} t: {type_r} st: {subtype_r}") 
        case 0x80:
            LOGGER.warning(f"COPY MEM CMD")
            src_memId = Mem_Dict[j_command_packet["src"]["memoryId"]]
            src_memAddr = j_command_packet["src"]["address"]
            dst_memId = Mem_Dict[j_command_packet["dst"]["memoryId"]]
            dst_memAddr = j_command_packet["dst"]["address"]
            length_data = j_command_packet["length"]
            chunckSize = j_command_packet["chunckSize"]
            if str(src_memAddr) in systemMemory[src_memId]:
               if not "X" in  systemMemory[src_memId][str(src_memAddr)]:
                  LOGGER.warning(f"Data to Copy found @ {src_memAddr} with {systemMemory[src_memId]}")
                  MemRead = systemMemory[src_memId][str(src_memAddr)]
                  if str(dst_memAddr) in systemMemory[dst_memId]:
                     if not "X" in  systemMemory[dst_memId][str(dst_memAddr)]:
                        LOGGER.warning(f"Pasting Data to {dst_memAddr} with {MemRead}")
                        systemMemory[dst_memId][dst_memAddr] = MemRead
                     else:
                        LOGGER.warning(f"Creating {dst_memId}, {dst_memAddr} with {MemRead}")
                        systemMemory[dst_memId] = {
                            str(dst_memAddr): MemRead
                        }
                  init_bytes_state(db_name, host, user, password, unit_pre+unit_suff, 'Memory', systemMemory, conf_file)
        case 0x81:
            memId = Mem_Dict[j_command_packet["memoryId"]]
            s_address = j_command_packet["StartAddress"]
            length_data = j_command_packet["length"]
            Force = j_command_packet["force"]
            if str(s_address) in systemMemory[memId]:
               LOGGER.warning(f"ERASE MEM CMD: {s_address}, {memId}")
               systemMemory[memId][str(s_address)] = [0x00, 0x00, 0x00, 0x00]
               init_bytes_state(db_name, host, user, password, unit_pre+unit_suff, 'Memory', systemMemory, conf_file)
        case 0x82:
            memId = Mem_Dict[j_command_packet["memoryId"]]
            s_address = j_command_packet["StartAddress"]
            length_data = j_command_packet["length"]
            MemRead = 0x00
            rp_num = 0
            if str(s_address) in systemMemory[memId] :
               MemRead = systemMemory[memId][str(s_address)]
               if "X" in MemRead:
                   MemRead = 0x00
               reply_dict = {
                   "memoryId": int(j_command_packet["memoryId"]),
                   "reportNbr": s_address,
                   "reports": {
                       "areaAddress": s_address,
                       "areaLength": length_data,
                       "healthy": 0x01
                   }
               }
               rp_num = rp_num + 1
               subtype_r = 0x83
               LOGGER.warning(f"REPORT MEM CMD: {MemRead} t: {type_r} st: {subtype_r}") 
        case 0x84:
            LOGGER.warning(f"CHANGE HEALTH MEM CMD")
            memId = Mem_Dict[j_command_packet["memoryId"]]
            s_address = j_command_packet["StartAddress"]
            healthy = j_command_packet["healthy"]
            if int(healthy) == 0x00:
                if str(s_address) in systemMemory[memId]:
                   LOGGER.warning(f"LOAD {s_address} with {healthy}")
                   systemMemory[memId][str(s_address)] = "X"
                else:
                   LOGGER.warning(f"CREATING {s_address} with {healthy}")
                   systemMemory[memId] = {
                   str(s_address): "X"
               }
            init_bytes_state(db_name, host, user, password, unit_pre+unit_suff, 'Memory', systemMemory, conf_file)
        case _:
            pass
    return reply_dict, type_r, subtype_r

def Function_management(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file):
    unit_pre = "bcr_"
    unit_suff = 0
    type_r = 8
    subtype_r = 0
    reply_dict = 0
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    if apid == 0x0A:
        unit_suff = "nominal"
    else:
        unit_suff = "redundant"
    unit, tlm_read_systemMgr = udb.read_db(unit_pre+unit_suff, "systemMgr")
    systemMgrDict = json.loads(tlm_read_systemMgr)
    match subtype:
        case 0x01:
            funcId = j_command_packet['funId']
            arg = j_command_packet['argValues']
            match int(funcId):
                case 0x0201:
                    func_sw_img = int(arg[0])
                    func_code = [arg[1], arg[2]]
                    systemMgrDict["ONBOARD_PARAMETERS"]["PID_BCR_SYSTEM_MGR_STATE"] = func_sw_img
                    init_bytes_state(db_name, host, user, password, unit_pre+unit_suff, 'systemMgr', systemMgrDict, conf_file)
                case 0x0202:
                    obt = int(arg)
                    systemMgrDict["ONBOARD_PARAMETERS"]["PID_BCR_SYSTEM_MGR_OBT_COARSE"] = obt
                    init_bytes_state(db_name, host, user, password, unit_pre+unit_suff, 'systemMgr', systemMgrDict, conf_file)
                case _:
                    pass
        case _:
            pass
    return reply_dict, type_r, subtype_r 
         
def Test_test(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file):
    unit_pre = "bcr_"
    unit_suff = 0
    type_r = 8
    subtype_r = 0
    reply_dict = 0
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    if apid == 0x0A:
        unit_suff = "nominal"
    else:
        unit_suff = "redundant"
    unit, tlm_read_systemMgr = udb.read_db(unit_pre+unit_suff, "systemMgr")
    systemMgrDict = json.loads(tlm_read_systemMgr)
    match subtype:
        case 0x01:
            subtype_r = 0
        case 0x80:
            index = int(j_command_packet['n'])
            items = j_command_packet['VersionedItemIds']
            if isinstance(items, list):
                lp = []
                for i in items:
                    reply_dict = {
                        "n1": index,
                        "VersionedItemVersions": {
                            "VersionedItemId": i,
                            "major": [0x00, 0x00],
                            "minor": [0x00, 0x00],
                            "revision": [0x00, 0x00],
                            "rc": [0x00, 0x00],
                            "buildHash": [0x00, 0x00, 0x00, 0x00],
                            "numExtraCommits": 0x00,
                            "dirty": 0x00,
                            "metaData": {
                                "n2": 0x00,
                                "metaData": {
                                    "key": "Demo",
                                    "value": "HelloWorld!"
                                        }
                                    }
                        } 
                    }
                    index = index + 1
                    lp.append(reply_dict)
                    reply_dict = lp
            else:
                reply_dict = {
                    "n1": index,
                    "VersionedItemVersions": {
                        "VersionedItemId": items,
                        "major": [0x00, 0x00],
                        "minor": [0x00, 0x00],
                        "revision": [0x00, 0x00],
                        "rc": [0x00, 0x00],
                        "buildHash": [0x00, 0x00, 0x00, 0x00],
                        "numExtraCommits": 0x00,
                        "dirty": 0x00,
                        "metaData": {
                            "n2": 0x00,
                            "metaData": {
                                "key": "Demo",
                                "value": "HelloWorld!"
                                    }
                                }
                        } 
                    }
        case _:
            pass
    return reply_dict, type_r, subtype_r

def OnBoard_parameter_management(j_command_packet, apid, type, subtype, db_name, host, user, password, conf_file):
    unit_pre = "bcr_"
    unit_suff = 0
    type_r = 8
    subtype_r = 0
    reply_dict = 0
    udb = db_manager.db_manager(db_name, host, user, password, conf_file)
    if apid == 0x0A:
        unit_suff = "nominal"
    else:
        unit_suff = "redundant"
    unit, tlm_read_systemMgr = udb.read_db(unit_pre+unit_suff, "systemMgr")
    unit, tlm_read_comMgr = udb.read_db(unit_pre+unit_suff, "comMgr")
    unit, tlm_read_fdirMgr = udb.read_db(unit_pre+unit_suff, "fdirMgr")
    unit, tlm_read_solarArraysMgr = udb.read_db(unit_pre+unit_suff, "solarArraysMgr")
    systemMgrDict = json.loads(tlm_read_systemMgr)
    comMgrDict = json.loads(tlm_read_comMgr)
    fdirMgrDict = json.loads(tlm_read_fdirMgr)
    solarArraysMgrDict = json.loads(tlm_read_solarArraysMgr)  
    match subtype:
        case 0x01:
            rl = 0
            n_param = int(j_command_packet['n'])
            paramId = j_command_packet['paramId']
            if n_param > 1:
                idx =  0
                for pId in paramId:
                    if (pId < 2586) and (pId > 2559):
                        rl = systemMgrDict["ONBOARD_PARAMETERS"][str(pId)]
                    elif (pId < 2596) and (pId > 2585):
                        rl = comMgrDict["ONBOARD_PARAMETERS"][str(pId)]
                    elif (pId < 2602) and (pId > 2595):
                        rl = fdirMgrDict["ONBOARD_PARAMETERS"][str(pId)]
                    elif (pId < 2603) and (pId > 2601):
                        rl = solarArraysMgrDict["ONBOARD_PARAMETERS"][str(pId)]
                    reply_dict = {
                        "n": idx,
                        "params": {
                            "paramId": pId,
                            "paramValue": rl
                        }
                    }
                    idx = idx +1
            else:
                if (paramId < 2586) and (paramId > 2559):
                    rl = systemMgrDict["ONBOARD_PARAMETERS"][str(paramId)]
                elif (paramId < 2596) and (paramId > 2585):
                    rl = comMgrDict["ONBOARD_PARAMETERS"][str(paramId)]
                elif (paramId < 2602) and (paramId > 2595):
                    rl = fdirMgrDict["ONBOARD_PARAMETERS"][str(paramId)]
                elif (paramId < 2603) and (paramId > 2601):
                    rl = solarArraysMgrDict["ONBOARD_PARAMETERS"][str(paramId)]
                else:
                    pass
                reply_dict = {
                        "n": n_param,
                        "params": {
                            "paramId": paramId,
                            "paramValue": rl
                        }
                    }
        case 0x03:
            pass
        case 0x06:
            pass
        case _:
            pass
    return reply_dict, type_r, subtype_r

def compute_crc(bytearray):
    #Credit to J.Doucet
    crc = 0
    for x in bytearray:
        indx = (crc ^ x) & 0xff
        new_crc = RMAP_CRC_TABLE[indx]
        crc = new_crc
    return new_crc