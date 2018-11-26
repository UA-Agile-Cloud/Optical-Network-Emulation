SRC_PATH='/var/opt/Optical-Network-Emulation/controller-TCD-d2'
ryu-manager --verbose --ofp-tcp-listen-port 6666 --wsapi-port 9091 \
$SRC_PATH/database/database_management.py \
$SRC_PATH/nbi/nbi.py \
$SRC_PATH/pce/pce.py \
$SRC_PATH/rwa/rwa.py \
$SRC_PATH/sbi/sbi.py
