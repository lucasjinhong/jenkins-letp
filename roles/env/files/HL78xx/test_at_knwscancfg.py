"""
Carrier AT commands test cases :: KNWSCANCFG
"""

import pytest
import time
import os
import VarGlobal
import re
from autotest import *

def A_HL_INT_KNWSCANCFG_0000(target_at, read_config, network_tests_setup_teardown):
    """
    Check KNWSCANCFG AT Command. Nominal/Valid use case
    """
    print("\nA_HL_INT_KNWSCANCFG_0000 TC Start:\n")
    test_environment_ready = "Ready"

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase == 0:
        pytest.skip("Phase 0 : No AT+KNWSCANCFG command")

    test_nb = ""
    test_ID = "A_HL_INT_KNWSCANCFG_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        # AT+KNWSCANCFG=?
        SagSendAT(target_at, "AT+KNWSCANCFG=?\r")
        SagWaitnMatchResp(target_at, ["\r\n+KNWSCANCFG: (0-1),(0-1),(2-65535),(2-65535),(2-32767)\r\n\r\nOK\r\n"], 4000)

        # AT+KNWSCANCFG?
        SagSendAT(target_at, "AT+KNWSCANCFG?\r")
        SagWaitnMatchResp(target_at, ["\r\n+KNWSCANCFG: 0,1,2,30\r\n+KNWSCANCFG: 1,1,2,30\r\n\r\nOK\r\n"], 4000)

        # Linear scheme without step
        # AT+KNWSCANCFG=mode,scheme,min,max,step
        SagSendAT(target_at, "AT+KNWSCANCFG=0,0,10,90,2\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

        # AT+KNWSCANCFG?
        SagSendAT(target_at, "AT+KNWSCANCFG?\r")
        SagWaitnMatchResp(target_at, ["\r\n+KNWSCANCFG: 0,0,10,90,2\r\n+KNWSCANCFG: 1,1,2,30\r\n\r\nOK\r\n"], 4000)

        # Restore Module
        SWI_Reset_Module(target_at, HARD_INI)

        # AT+KNWSCANCFG?
        SagSendAT(target_at, "AT+KNWSCANCFG?\r")
        SagWaitnMatchResp(target_at, ["\r\n+KNWSCANCFG: 0,0,10,90,2\r\n+KNWSCANCFG: 1,1,2,30\r\n\r\nOK\r\n"], 4000)

        # Exponential scheme without step
        # AT+KNWSCANCFG=mode,scheme,min,max
        SagSendAT(target_at, "AT+KNWSCANCFG=0,1,10,90\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

        # AT+KNWSCANCFG?
        SagSendAT(target_at, "AT+KNWSCANCFG?\r")
        SagWaitnMatchResp(target_at, ["\r\n+KNWSCANCFG: 0,1,10,90\r\n+KNWSCANCFG: 1,1,2,30\r\n\r\nOK\r\n"], 4000)

        # Restore Module
        SWI_Reset_Module(target_at, HARD_INI)

        # AT+KNWSCANCFG?
        SagSendAT(target_at, "AT+KNWSCANCFG?\r")
        SagWaitnMatchResp(target_at, ["\r\n+KNWSCANCFG: 0,1,10,90\r\n+KNWSCANCFG: 1,1,2,30\r\n\r\nOK\r\n"], 4000)

        # Linear scheme without step
        SagSendAT(target_at, "AT+KNWSCANCFG=0,0,10,90\r")
        SagWaitnMatchResp(target_at, ["\r\n*ERROR*\r\n"], 4000)

        # Reset to default values
        # AT+KNWSCANCFG=0
        SagSendAT(target_at, 'AT+KNWSCANCFG=0\r')
        SagWaitnMatchResp(target_at, ['*\r\nOK\r\n'], 6000)

        # AT+KNWSCANCFG?
        SagSendAT(target_at, "AT+KNWSCANCFG?\r")
        SagWaitnMatchResp(target_at, ["\r\n+KNWSCANCFG: 0,1,2,30\r\n+KNWSCANCFG: 1,1,2,30\r\n\r\nOK\r\n"], 4000)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
