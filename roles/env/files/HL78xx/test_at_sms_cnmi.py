"""
SMS AT commands test cases :: CNMI
originated from A_HL_Common_SMS_CNMI_0004.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import re
from autotest import *

def  A_HL_INT_SMS_CNMI_0000(target_at, read_config, network_tests_setup_teardown):
    """
    Check CMGS AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_SMS_CNMI_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")

    SagSendAT(target_at, "AT+KSLEEP=2\r")
    SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

    test_nb = ""
    test_ID = "A_HL_INT_SMS_CNMI_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        # AT+CNMI=?
        SagSendAT(target_at, "AT+CNMI=?\r")
        if "HL78" in HARD_INI:
            SagWaitnMatchResp(target_at, ["\r\n+CNMI: (1,2),(0-2),(0,2),(0-2),(0-1)\r\n\r\nOK\r\n"], C_TIMER_LOW)
        elif "RC51" in HARD_INI:
            SagWaitnMatchResp(target_at, ["\r\n+CNMI: (0,1,2),(0,1,2,3),(0,2),(0,1,2),(0,1)\r\n\r\nOK\r\n"], C_TIMER_LOW)

        # AT+CNMI?
        SagSendAT(target_at, "AT+CNMI?\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], C_TIMER_LOW)
        result = SagMatchResp(answer, ["\r\n+CNMI: ?,?,?,?,?\r\n"])
        # default CNMI
        if result:
            cnmi = answer.split(": ")[1].split("\r\n")[0]
            print("\nDefault cnmi is: "+cnmi)
        else:
            cnmi = "1,0,0,0,0"

        SagSendAT(target_at, "AT+CNMI=1,0,0,0,0\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        # CMD : AT+CNMI?
        SagSendAT(target_at, "AT+CNMI?\r")
        SagWaitnMatchResp(target_at, ["\r\n+CNMI: 1,0,0,0,0\r\n\r\nOK\r\n"], C_TIMER_LOW)

        # Restart module
        SWI_Reset_Module(target_at, HARD_INI)

        SagSendAT(target_at, "ATE0\r")
        SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 5000)

        # Check CNMI value is saved in non-volatile memory after reboot module
        SagSendAT(target_at, "AT+CNMI?\r")
        SagWaitnMatchResp(target_at, ["\r\n+CNMI: 1,0,0,0,0\r\n\r\nOK\r\n"], C_TIMER_LOW)

        SagSendAT(target_at, "AT+CNMI=2,1,0,1,1\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        # CMD : AT+CNMI?
        SagSendAT(target_at, "AT+CNMI?\r")
        SagWaitnMatchResp(target_at, ["\r\n+CNMI: 2,1,0,1,1\r\n\r\nOK\r\n"], C_TIMER_LOW)

        # Restart module
        SWI_Reset_Module(target_at, HARD_INI)

        SagSendAT(target_at, "ATE0\r")
        SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 5000)

        # Check CNMI value is saved in non-volatile memory after reboot module
        SagSendAT(target_at, "AT+CNMI?\r")
        SagWaitnMatchResp(target_at, ["\r\n+CNMI: 2,1,0,1,1\r\n\r\nOK\r\n"], C_TIMER_LOW)

        SagSendAT(target_at, "AT+CNMI=1,2,0,2,0\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        # CMD : AT+CNMI?
        SagSendAT(target_at, "AT+CNMI?\r")
        SagWaitnMatchResp(target_at, ["\r\n+CNMI: 1,2,0,2,0\r\n\r\nOK\r\n"], C_TIMER_LOW)

        # Restart module
        SWI_Reset_Module(target_at, HARD_INI)

        SagSendAT(target_at, "ATE0\r")
        SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 5000)

        # Check CNMI value is saved in non-volatile memory after reboot module
        SagSendAT(target_at, "AT+CNMI?\r")
        SagWaitnMatchResp(target_at, ["\r\n+CNMI: 1,2,0,2,0\r\n\r\nOK\r\n"], C_TIMER_LOW)

        # Restore default CNMI
        SagSendAT(target_at, "AT+CNMI=" + cnmi + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

