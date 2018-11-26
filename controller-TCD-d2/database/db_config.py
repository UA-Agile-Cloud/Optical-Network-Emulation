import sys
sys.path.insert(0, '/var/opt/Optical-Network-Emulation/controller-TCD-d2')

DB_USER = 'root'
DB_PASSWORD = 'xequebo'
DB_DATABASE = 'network_management_2'
DB_HOST = '127.0.0.1'
DB_CONFIG = {
  'user': DB_USER,
  'password': DB_PASSWORD,
  'host': DB_HOST,
  'database': DB_DATABASE,
  'raise_on_warnings': True,
}

DB_MGMT_INSTANCE_NAME = 'db_mgmt_api_app'
