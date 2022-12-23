"""
General AT commands test cases :: CLAC
originated from A_HL_Common_MECS_CLAC_0001.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import re
from autotest import *

def A_HL_INT_GEN_CLAC_0000(target_at, read_config, non_network_tests_setup_teardown):
    """
    Check CLAC AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_GEN_CLAC_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    clacFileName = read_config.findtext("autotest/ClacFilePath")
    AT_CCID = int(read_config.findtext("autotest/Features_AT_CCID"))
    AT_percent_CCID = int(read_config.findtext("autotest/Features_AT_percent_CCID"))
    HARD_INI = read_config.findtext("autotest/HARD_INI")

    # Check file existance
    if not os.path.isfile(clacFileName):
        raise Exception("---->Problem: NO FILE: " + clacFileName)

    if AT_CCID:
        SagSendAT(target_at, 'AT+CCID\r')
        SagWaitnMatchResp(target_at, ['\r\n+CCID: *\r\n'], 4000)
        SagWaitnMatchResp(target_at, ['OK'], 4000)
        if "RC51" in HARD_INI:
            SagSendAT(target_at, 'AT+ICCID\r')
            SagWaitnMatchResp(target_at, ['\r\nICCID: *\r\n'], 4000)
            SagWaitnMatchResp(target_at, ['OK'], 4000)

    if AT_percent_CCID:
        SagSendAT(target_at, 'AT%CCID\r')
        SagWaitnMatchResp(target_at, ['\r\n%CCID: *\r\n'], 4000)
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 4000)

    test_nb = ""
    test_ID = "A_HL_INT_GEN_CLAC_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        #Read File
        with open(clacFileName) as f:
            lines = f.readlines()
        cmds = []

        if ".h" in clacFileName:
            for cmd in lines:
                if (cmd[0] == "\""):
                    cmds.append(cmd.split('"')[1])

        elif ".txt" in clacFileName:
            for cmd in lines:
                if (cmd[0] != "#"):
                    cmds.append(cmd.rstrip('\n'))

        #Read Command
        SagSendAT(target_at, "AT+CLAC\r")

        for cmd in cmds:
            SagWaitResp(target_at, [cmd + '\r\n'], 2000)

        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 2000)

        # Check point 2
        if VarGlobal.statOfItem != "OK":
            raise Exception("Check point failed")

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

