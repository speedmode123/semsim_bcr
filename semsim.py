# General Py Libs
import time
import sys
import os

# HomeMade Py Libs
import db_manager
from units import bcr
import psycopg2, socket, threading
from threading import *
import threading
from subprocess import Popen
from tmtc_manager import tmtc_manager
from subprocess import Popen
from configurator import rtos_configurator
import random, logging, time, json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)


def update_system(cursor, models_to_update, db_name, host, user, password, conf_file):
    for mdu in models_to_update:
        match str(mdu):
            case "bcr_nominal":
                bcr.bcr_nominal(mdu[7:], db_name, host, user, password, conf_file)
            case "bcr_redundant":
                bcr.bcr_redundant(mdu[7:], db_name, host, user, password, conf_file)
            case _:
                LOGGER.info(f"models_to_update : {mdu} does not exist")

def get_configuration_from_file():
    conf_read = rtos_configurator().get_conf_from_file()
    mode = conf_read['dst_conf']
    models = conf_read['models']
    return mode, models

def db_initialisation(db_name, host, user, password, conf_file_init):
    udb = db_manager.db_manager(db_name, host, user, password, conf_file_init)
    udb.create_db(f'{db_name}')
    udb.db_connect()
    udb.db_table_creator()
    udb.db_table_filler()
    udb.db_disconnect()

def rtos_initialisation(db_name, host, user, password, conf_file):
    LOGGER.info("RTOS INITIALIZATION")
    #Activating Loop
    rtos_launch = db_manager.db_manager(db_name, host, user, password, conf_file)
    rtos_launch.db_connect()
    rtos_launch.control_rtos(1)
    rtos_launch.db_disconnect()

def main():
    time.sleep(5)
    #Creating own db
    conf_file_init = "db_config"
    conf_file = "hw_conf_sem"
    localIP = "0.0.0.0"
    db_name = "sem_demo"
    host = "postgres"
    user = "postgres"
    password ="postgres"
    tclocalPort = 84

    db_initialisation(db_name, host, user, password, conf_file_init)

    rtos_initialisation(db_name, host, user, password, conf_file)

    #Cursor for update units
    conn = psycopg2.connect(database=db_name, host=host, user=user, password=password)
    cursor = conn.cursor()

    #Cursor for rtos_checker
    rtos_checker = db_manager.db_manager(db_name, host, user, password, conf_file)
    rtos_checker.db_connect()

    configuration_loader = rtos_configurator(f'conf_file/{conf_file}.json')
    configuration_detected = configuration_loader.get_conf_from_file()
    models_to_update = configuration_detected['models']

    # Initialize TMTC threads
    listen_udp_thread = Thread(target=tmtc_manager, args=(models_to_update, db_name, host, user, password, conf_file, localIP, tclocalPort))
    #listen_mcp_thread = Thread(target=mcp_manager, args=(db_name, host, user, password, conf_file))

    # Start threads
    time.sleep(1)
    listen_udp_thread.start()
    LOGGER.info("UDP server up and listening")

    time.sleep(1)
    # listen_mcp_thread.start()
    # LOGGER.info("MCP server up and listening")

    #LOOP
    LOGGER.info("RTOS READY")
    while rtos_checker.check_rtos() == '1':
        update_system(cursor, models_to_update, db_name, host, user, password, conf_file)
    else:
        listen_udp_thread.join()
        rtos_checker.db_disconnect()
        cursor.close()
        conn.close()
        rtos_checker.db_disconnect()
        LOGGER.info("RTOS STOPPED")

if __name__ == "__main__":
    main()
