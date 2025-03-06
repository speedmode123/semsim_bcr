import random, logging, time, json
import db_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

class hk_service:

    def __init__(self, db_name, host, user, password, conf_file):
        self.HK_Tlm = {}
        udb = db_manager.db_manager(db_name, host, user, password, conf_file)
        unit_list = [
            "cband_rx",
            "cband_tx",
            "dra_rx_nominal",
            "dra_rx_redundant",
            "dra_tx_nominal",
            "dra_tx_redundant",
            "mro",
            "dcp_nominal",
            "dcp_redundant",
        ]
        for unt in unit_list:
            HkTlm_tuple = udb.read_entire_table_db(unt)
            HkTlm = dict((x, y) for x, y in HkTlm_tuple)
            self.HK_Tlm[unt] = HkTlm
        #LOGGER.info(f"self.HK_Tlm: {self.HK_Tlm}")