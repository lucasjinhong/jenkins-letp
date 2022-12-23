"""
General AT commands test cases :: CCLK
originated from A_HL_Common_MECS_CCLK_0001.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import re
from autotest import *

def A_HL_INT_GEN_CCLK_0000(target_at, read_config, non_network_tests_setup_teardown):
    """
    Check CCLK AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_GEN_CCLK_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    AT_CCID = int(read_config.findtext("autotest/Features_AT_CCID"))
    AT_percent_CCID = int(read_config.findtext("autotest/Features_AT_percent_CCID"))
    HARD_INI = read_config.findtext("autotest/HARD_INI")

    # Check Module state / Restart if required
    SWI_Check_Module(target_at, AT_CMD_List_Check_Module, AT_Resp_List_Check_Module, AT_Timeout_List_Check_Module, AT_Restart_CMD, AT_Restart_Resp, Booting_Duration)

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
    test_ID = "A_HL_INT_GEN_CCLK_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        #Test Command
        SagSendAT(target_at, "AT+CCLK=?\r")
        SagWaitnMatchResp(target_at, ['*OK\r\n'], 2000)

        #Read Command
        SagSendAT(target_at, "AT+CCLK?\r")
        SagWaitnMatchResp(target_at, ['*+CCLK: "??/??/??,??:??:??*OK\r\n'], 2000)


        atCommand = 'AT+CCLK="18/08/09,12:34:56-08"\r\n'
        SagSendAT(target_at, atCommand)
        SagWaitnMatchResp(target_at, ['*OK\r\n'], 5000)

        SagSendAT(target_at, 'AT+CCLK?\r')
        atResult = '*+CCLK: "18/08/09,12:34:5?-08"*OK\r\n'
        SagWaitnMatchResp(target_at, [atResult], 2000)

        # Check point 2
        if VarGlobal.statOfItem != "OK":
            raise Exception("Check point failed")

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

