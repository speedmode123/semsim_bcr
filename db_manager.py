# HomeMade Py Libs
import psycopg2
import json
import random, logging, time, json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

class db_manager:
    
    def __init__(self, database, host, user, password, conf_file):
        self.database = database
        self.host = host
        self.user = user
        self.password = password
        self.db_config_file = open(f'conf_file/{conf_file}.json', )
        self.database_to_load = json.load(self.db_config_file)
        self.port = 5432

    def db_connect(self):
        self.conn = psycopg2.connect(database=f"{self.database}", host=f"{self.host}", user=f"{self.user}", password=f"{self.password}", port=f"{self.port}")
        self.cursor = self.conn.cursor()

    def db_disconnect(self):
        self.conn.close()
        self.cursor.close()

    def sql_request(self, request):
        self.cursor.execute(request)
        self.conn.commit()

    def sql_fetch_all(self, request):
        self.cursor.execute(request)
        table = self.cursor.fetchall()
        return table[0]

    def read_db(self, unit, telemetry_name):
        self.db_connect()
        self.cursor.execute(f"SELECT * FROM {unit} WHERE unit='{telemetry_name}';")
        table = list(self.cursor.fetchall())
        self.db_disconnect()
        data_set = table[0]
        unit = data_set[0]
        tlm_read = data_set[1]
        return unit, tlm_read
    
    def read_entire_table_db(self, unit):
        self.db_connect()
        self.cursor.execute(f"SELECT * FROM {unit};")
        table = list(self.cursor.fetchall())
        self.db_disconnect()
        return table
    
    def update_db(self, unit, tln_name, new_value):
        self.db_connect()
        self.cursor.execute(f"UPDATE {unit} SET value = '{new_value}' WHERE unit = '{tln_name}';")
        self.conn.commit()
        self.db_disconnect()

    def db_table_creator(self):
        self.table_name = self.database_to_load['table_name']
        self.table_type = self.database_to_load['table_type']
        self.columns = list(self.table_type.keys())
        self.values = list(self.table_type.values())
        for unit in self.table_name:
            if "rtos" in unit:
                self.sql_request(f"CREATE TABLE {unit}(unit varchar(32), value varchar(8));")
            else:
                self.sql_request(f"CREATE TABLE {unit}({self.columns[0]} varchar({self.values[0]}), {self.columns[1]} varchar({self.values[1]}));")
        LOGGER.info("empty tables are created")

    def db_table_filler(self):
        self.table_name = self.database_to_load['table_name']
        self.table_type = self.database_to_load['table_type']
        self.columns = list(self.table_type.keys())
        for unit in self.table_name:
            if "rtos" in unit:
                self.sql_request("INSERT INTO rtos(unit, value) VALUES('activate', 0);")
                self.sql_request("INSERT INTO rtos(unit, value) VALUES('hktm', 0);")
            else:
                self.sub_table = self.database_to_load[f'{unit}']
                for items in self.sub_table:
                    self.sql_request(f"INSERT INTO {unit}({self.columns[0]}, {self.columns[1]}) VALUES ('{items[self.columns[0]]}', '{items[self.columns[1]]}');")

    def create_rtos(self):
        self.sql_request("CREATE TABLE rtos(unit varchar(32), value varchar(8);")
        self.sql_request("INSERT INTO rtos(unit, value) VALUES('activate', 0);")
        self.sql_request("INSERT INTO rtos(unit, value) VALUES('hktm', 0);")
        LOGGER.info("rtos created")

    def create_db(self, db_name):
        # establishing the connection
        conn = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='postgres')
        conn.autocommit = True
        # Creating a cursor object using the cursor() method
        cursor = conn.cursor()
        # Preparing query to create a database
        sql = f'''CREATE DATABASE {db_name}''';
        # Creating a database
        cursor.execute(sql)
        LOGGER.info("Database created successfully........")
        # Closing the connection
        conn.close()
        LOGGER.info("db_created created")

    def drop_db(self, db_name):
        # establishing the connection
        conn = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='postgres')
        conn.autocommit = True
        # Creating a cursor object using the cursor() method
        cursor = conn.cursor()
        # Preparing query to create a database
        sql = f'''DROP DATABASE {db_name}''';
        # Creating a database
        cursor.execute(sql)
        LOGGER.info("Database dropped successfully........")
        # Closing the connection
        conn.close()
        LOGGER.info("db_created drop")

    def control_rtos(self, new_value):
        self.sql_request(f"UPDATE rtos SET value = {new_value} WHERE unit = 'activate';")

    def control_hktm(self, new_value):
        self.sql_request(f"UPDATE rtos SET value = {new_value} WHERE unit = 'hktm';")

    def check_rtos(self):
        table = self.sql_fetch_all(f"SELECT * FROM rtos WHERE unit='activate';")
        return table[1]

    def check_hktm(self):
        table = self.sql_fetch_all(f"SELECT * FROM rtos WHERE unit='hktm';")
        return table[1]


if __name__ == "__main__":
    pass
    #Step 1 : log in psql to create a database CREATE DATABASE sem_demo;
    #Step 2 : Uncomment and run the following lines;
    # udb = db_manager("sem_demo", "postgres", "postgres", "postgres")
    # udb.create_db('sem_demo')
    # udb.db_connect()
    # udb.db_table_creator()
    # udb.db_table_filler()
    # udb.db_disconnect()
    # time.sleep(3)
    # udb2 = db_manager("sem_demo", "postgres", "postgres", "postgres")
    # udb.drop_db('sem_demo')
