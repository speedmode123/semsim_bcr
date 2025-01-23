# General Py Libs
import time
import os
# HomeMade Py Libs
import psycopg2
import socket
import json
import configparser
import re
import random, logging, time, json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

class rtos_configurator:
    
    def __init__(self, filename):
        self.db_config_file = open(f'{filename}',)
        self.mode_to_load = json.load(self.db_config_file)


    def get_conf_from_file(self):
        return self.mode_to_load


if __name__ == "__main__":
    pass
    #Step 1 : log in psql to create a database CREATE DATABASE paysim_demo;

    #Step 2 : Uncomment and run the following lines;
    # udb = rtos_configurator('units/mro_pin_allocations.json')
    # pins = udb.get_conf_from_file()
    # LOGGER.info(pins['TC']["mro_epc_1_cmd_on"])
    # udb = rtos_configurator('hw_conf.json')
    # hw_conf = udb.get_conf_from_file()
    # LOGGER.info(hw_conf)
    #udb.db_connect()
    #udb.create_rtos()
    #udb.check_rtos()
    #udb.db_table_creator()
    #udb.db_table_filler()
    #base_address_dict = udb.register_ini_to_dict('/home/mrotest/thunder/pay_sim/db_register/', "base_address")
    #register_dict = udb.register_ini_to_dict('/home/mrotest/thunder/pay_sim/db_register/', "memory_map")
    #udb.write_register_in_target(base_address_dict, register_dict)
    #udb.db_disconnect()