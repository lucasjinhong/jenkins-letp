"""
Carrier AT commands test cases :: KCARRIERCFG
"""

import time
import pytest
import time
import os
import VarGlobal
import re
from autotest import *

def A_HL_INT_KCARRIERCFG_0000(target_at, read_config, network_tests_setup_teardown):
    """
    Check KCARRIERCFG AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_KCARRIERCFG_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    phase = int(read_config.findtext("autotest/Features_PHASE"))

    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)

    test_nb = ""
    test_ID = "A_HL_INT_KCARRIERCFG_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        # KCARRIERCFG=?
        SagSendAT(target_at, "AT+KCARRIERCFG=?\r")
        if (phase > 0):
            #For HL7800 and HL781x
            if Soft_Version < "05.00.00.00":
                SagWaitnMatchResp(target_at, ["\r\n+KCARRIERCFG: (0-15)\r\n\r\nOK\r\n"], 5000)
            else:
                SagWaitnMatchResp(target_at, ["\r\n+KCARRIERCFG: (0-17)\r\n\r\nOK\r\n"], 5000)
        else:
            SagWaitnMatchResp(target_at, ["\r\n+KCARRIERCFG: (0-13)\r\n\r\nOK\r\n"], 5000)

        # default KCARRIERCFG
        SagSendAT(target_at, "AT+KCARRIERCFG?\r")
        answer = SagWaitResp(target_at, ["\r\n*\r\n\r\nOK\r\n"], 5000)
        result = SagMatchResp(answer, ["\r\n+KCARRIERCFG: ?\r\n"])
        if result:
            kcarriercfg = answer.split("\r\n")[1].split(": ")[1]
            print("\nDefault kcarriercfg is: "+kcarriercfg)
        else:
            kcarriercfg = "0"

        # default CGDCONT
        cgdcont = []
        SagSendAT(target_at, "AT+CGDCONT?\r")
        answer = SagWaitResp(target_at, ["\r\n*\r\n\r\nOK\r\n"], 5000)
        for line_answer in answer.split("\r\n"):
            result = SagMatchResp(line_answer, ["+CGDCONT: *"])
            if result:
                cgdcont.append(line_answer.split(": ")[1])
                print("\nDefault cgdcont is: "+cgdcont[-1])

        if kcarriercfg == "0":
            operator_idx = [1, 5, 13]
        else:
            operator_idx = [0, 1, 5, 13]

        for idx in operator_idx:
            # AT+CFUN=0 is needed due to ALT1250-1912/DIZZY-2257 (Since RK_02.82)
            SagSendAT(target_at, "AT+CFUN=0\r")
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)

            time.sleep(20)

            # KCARRIERCFG=idx
            SagSendAT(target_at, "AT+KCARRIERCFG=" + str(idx) + "\r")
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000 * 30)

            # KCARRIERCFG?
            SagSendAT(target_at, "AT+KCARRIERCFG?\r")
            SagWaitnMatchResp(target_at, ["\r\n+KCARRIERCFG: " + str(idx) + "\r\n\r\nOK\r\n"], 5000)

            SWI_Reset_Module(target_at, HARD_INI)

            time.sleep(10)

            # KCARRIERCFG?
            SagSendAT(target_at, "AT+KCARRIERCFG?\r")
            SagWaitnMatchResp(target_at, ["\r\n+KCARRIERCFG: " + str(idx) + "\r\n\r\nOK\r\n"], 5000)

        # Restore default KCARRIERCFG
        # AT+CFUN=0 is needed due to ALT1250-1912/DIZZY-2257 (Since RK_02.82)
        SagSendAT(target_at, "AT+CFUN=0\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)

        time.sleep(20)

        SagSendAT(target_at, "AT+KCARRIERCFG=" + kcarriercfg + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000 * 30)

        SWI_Reset_Module(target_at, HARD_INI)

        time.sleep(10)

        # Restore default CGDCONT
        for cgdcont_elem in cgdcont:
            SagSendAT(target_at, "AT+CGDCONT=" + cgdcont_elem + "\r")
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

