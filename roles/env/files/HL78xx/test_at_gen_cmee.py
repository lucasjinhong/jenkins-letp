"""
General AT commands test cases :: CMEE
originated from A_HL_Common_MECS_CMEE_0001.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import re
from autotest import *

def A_HL_INT_GEN_CMEE_0000(target_at, read_config, non_network_tests_setup_teardown):
    """
    Check CMEE AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_GEN_CMEE_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    phase = int(read_config.findtext("autotest/Features_PHASE"))
    HARD_INI = read_config.findtext("autotest/HARD_INI")

    test_nb = ""
    test_ID = "A_HL_INT_GEN_CMEE_0000"
    PRINT_START_FUNC(test_nb + test_ID)
    VarGlobal.statOfItem = "OK"

    print("\n----- Testing Start -----\n")

    try:
        #AT+CMEE?
        SagSendAT(target_at, "AT+CMEE?\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
        result = SagMatchResp(answer, ["\r\n+CMEE: ?\r\n"])
        # default cmee
        if result:
            cmee = answer.split("\r\n")[1].split(": ")[1]
            print("\nDefault cmee is: "+cmee)
        else:
            cmee = "1"

        #Test Command
        SagSendAT(target_at, 'AT+CMEE=?\r')
        if "HL78" in HARD_INI:
            if (phase > 0):
              SagWaitnMatchResp(target_at, ['*+CMEE: (0-1)*OK\r\n'], 2000)
            else:
              SagWaitnMatchResp(target_at, ['*+CMEE: (0-2)*OK\r\n'], 2000)
        elif "RC51" in HARD_INI:
            SagWaitnMatchResp(target_at, ['*+CMEE: (0,1,2)*OK\r\n'], 2000)

        #Read Command
        SagSendAT(target_at, "AT+CMEE?\r")
        SagWaitnMatchResp(target_at, ['*OK\r\n'], 2000)

        #Write and test Command (only 0 and 1 which are documented)
        for value in range (0, 2):
            atCommand = "AT+CMEE=%d\r" % value
            SagSendAT(target_at, atCommand)
            SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 2000)

            SagSendAT(target_at, "AT+CMEE?\r")
            result = '*+CMEE: %d*OK\r\n' % value
            SagWaitnMatchResp(target_at, [result], 2000)

        # Restore default cmee
        SagSendAT(target_at, "AT+CMEE=" + cmee + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

