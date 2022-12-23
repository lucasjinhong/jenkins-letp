"""
Power AT commands test cases :: CFUN
originated from A_HL_Common_MECS_CFUN_0001.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import re
from autotest import *

def A_HL_INT_PWR_CFUN_0000(target_at, read_config, network_tests_setup_teardown):
    """
    Check CFUN AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_PWR_CFUN_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    SIM_Pin1 = read_config.findtext("autotest/PIN1_CODE")

    test_nb = ""
    test_ID = "A_HL_INT_PWR_CFUN_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        #ERROR CASE
        """
        #AT&W
        SagSendAT(target_at, "AT&W\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)
        """
        # check if SIM is locked
        lockedSIM = 0
        SagSendAT(target_at, 'AT+CLCK="SC",2\r')
        lock_resp = SagWaitResp(target_at,["\r\n+CLCK: ?\r\n\r\nOK\r\n"], 4000)
        if lock_resp.find('+CLCK: 0')==-1:
            # SIM locked => unlock SIM
            lockedSIM = 1
            SagSendAT(target_at, 'AT+CLCK="SC",0,"' + SIM_Pin1 + '"\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

        #AT+CFUN=?
        SagSendAT(target_at, "AT+CFUN=?\r")
        if "HL78" in HARD_INI:
            SagWaitnMatchResp(target_at, ["\r\n+CFUN: (0-1,4),(0-1)\r\n\r\nOK\r\n"], 2000)
        elif "RC51" in HARD_INI:
            SagWaitnMatchResp(target_at, ["\r\n+CFUN: (0-1,4-7),(0-1)\r\n\r\nOK\r\n"], 2000)

        #AT+CFUN?
        SagSendAT(target_at, "AT+CFUN?\r")
        SagWaitnMatchResp(target_at, ["\r\n+CFUN: 1\r\n"], 2000)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

        #AT+CFUN=x
        for x in [1,4]:
            SagSendAT(target_at, "AT+CFUN="+str(x)+"\r")
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)
            SagSleep(30000)
            SagSendAT(target_at, "AT\r")
            SagWaitResp(target_at, ["\r\nOK\r\n"], 2000)

        #AT+CFUN=x,0
        for x in [1,4]:
            for y in [0]:
                SagSendAT(target_at, "AT+CFUN="+str(x)+","+str(y)+"\r")
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 20000)

        #AT+CFUN=x,1
        for x in [1,4]:
            for y in [1]:
                SagSendAT(target_at, "AT+CFUN="+str(x)+","+str(y)+"\r")
                if "RC51" in HARD_INI and x == 4:
                    SagWaitnMatchResp(target_at, ["\r\n+CME ERROR: operation not supported\r\n"], 10000)
                else:
                    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)
                SagSleep(30000)
                SagSendAT(target_at, "AT\r")
                SagWaitResp(target_at, ["\r\nOK\r\n"], 2000)
                SagSendAT(target_at, "ATE0\r")
                SagWaitnMatchResp(target_at, ["*OK\r\n"], 5000)

        #QC supported commands
        if "RC51" in HARD_INI:
            for x in [4,5,6,7]:

                # Verify AT write command
                SagSendAT(target_at, "AT+CFUN=" + str(x) + "\r")
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)
                SagSleep(20000)

                # Verify AT read command
                SagSendAT(target_at, "AT+CFUN?\r")
                if x == 6:
                    # Reset UE - default value = 1
                    SagWaitnMatchResp(target_at, ["\r\n+CFUN: 1\r\n\r\nOK\r\n"], 5000)
                else:
                    SagWaitnMatchResp(target_at, ["\r\n+CFUN: " + str(x) + "\r\n\r\nOK\r\n"], 5000)

                # Verify correct behaviour
                SagSendAT(target_at, "AT+CREG?\r")
                if x == 6:
                    SagWaitnMatchResp(target_at, ["\r\n+CREG: 2,1*\r\nOK\r\n"], 5000)
                else:
                    SagWaitnMatchResp(target_at, ["\r\n+CREG: 2,0*\r\nOK\r\n"], 5000)

        # Restore default value
        if (lockedSIM == 1):
            SagSendAT(target_at, 'AT+CLCK="SC",1,"' + SIM_Pin1 + '"\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

        # Check point 2
        if VarGlobal.statOfItem != "OK":
            raise Exception("Check point failed")

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    # Restore Module
    SWI_Reset_Module(target_at, HARD_INI)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
