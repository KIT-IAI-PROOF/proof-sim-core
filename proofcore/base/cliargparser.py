"""
 Copyright (c) 2025-2026
 Karlsruhe Institute of Technology - Institute for Automation and Applied Informatics (IAI)
"""
import argparse
"""
A common function to read and interpret command line arguments for each wrapper
"""
def parse_known_args():
    parser = argparse.ArgumentParser(description="Mein Programm")

    parser.add_argument('--logLevel', '-L', dest='logLevel', default="ERROR")
    parser.add_argument('--userdata_directory', '-w', dest='userdata_directory', default="/tmp/proof/userdata")  # example: "/home/BHKW"
    parser.add_argument('--inputs', '-i', dest='inputs', default='[]', type=str)  # example: "['setpoint', 'power']"
    parser.add_argument('--outputs', '-o', dest='outputs', default='[]', type=str)  # example: "['P_el', 'Q']"
    parser.add_argument('--loggingDir', '-d', dest='loggingDir', default="/tmp/proof/logs")  # example: "/tmp"
    parser.add_argument('--ports', '-P', dest='ports',
                   default='[]')  # socket ports to read and write data from/to worker example: "[40000, 50000]" ([readPort,writePort])
    parser.add_argument('--local_block_id', '-b', dest='local_block_id')  # example: "2"
    parser.add_argument('--waitForSync', '-s', dest='waitForSync', default=None)  # example: "false"
    return parser.parse_known_args()
