"""
Devices AT commands test cases :: IPR
originated from A_HL_Common_V25TER_IPR_0001.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import re
import com
from autotest import *

def A_HL_INT_DEV_IPR_0000(target_at, read_config, non_network_tests_setup_teardown):
    """
    Check IPR AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_DEV_IPR_0000 TC Start:\n")
    test_environment_ready = "Ready"
    global baudrate
    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    slink = read_config.findtext("module/slink2/name")
    Serial_BaudRate = read_config.findtext("module/slink2/speed")
    baudrate = int(Serial_BaudRate)

    test_nb = ""
    test_ID = "A_HL_INT_DEV_IPR_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        SagSendAT(target_at, "AT+IPR=?\r")
        if "HL78" in HARD_INI:
            SagWaitnMatchResp(target_at, ["\r\n+IPR: (1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600)\r\n"], 1000)
        elif "RC51" in HARD_INI:
            SagWaitnMatchResp(target_at, ["\r\r\n+IPR:300 600 1200 2400 4800 9600 14400 19200 38400 57600 115200 230400 460800 921600 1000000 1200000 1209677 1250000 1293103 1339286 1388889 1442308 1500000 1562500 1630435 1704545 1785714 2000000 3000000 3200000 3686400 4000000 \r\r\n"], 1000)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 1000)

        SagSendAT(target_at, "AT+IPR?\r")
        SagWaitnMatchResp(target_at, ["\r\n+IPR: " + str(Serial_BaudRate) + "\r\n"], 1000)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 1000)

        for bd in [9600, 57600, 230400, int(Serial_BaudRate)]:
            target_at.run_at_cmd("AT+IPR=%d" % bd)
            target_at.baudrate = bd
            baudrate = bd
            time.sleep(3)
            # Run AT cmd with updated baudrate
            target_at.run_at_cmd("AT")

        # Restore setting"
        SagSendAT(target_at, "ATE1\r")
        SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 5000)
        SagSendAT(target_at, "AT\r")
        SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 2000)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    if baudrate != int(Serial_BaudRate):
        time.sleep(2)
        # reinit UART
        target_at.close()
        target_at.reinit(baudrate = baudrate)
        time.sleep(2)
        # AT
        SagSendAT(target_at, "AT\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)
        # AT+IPR=115200
        SagSendAT(target_at, "AT+IPR=%d\r" % int(Serial_BaudRate))
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)
        target_at.baudrate = int(Serial_BaudRate)
        time.sleep(2)
        # AT
        SagSendAT(target_at, "AT\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
