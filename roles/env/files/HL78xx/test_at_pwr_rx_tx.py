"""
Power AT commands test cases :: WMRXPOWER/WMTXPOWER
originated from A_HL_Common_MECS_WMRXPOWER_1001.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import re
import ast
import collections
from autotest import *

def A_HL_INT_PWR_RX_TX_0000(target_at, read_config, network_tests_setup_teardown):
    """
    Check POWER AT Command. Nominal/Valid use case
    """
    print("\nA_HL_INT_PWR_RX_TX_0000 TC Start:\n")
    test_environment_ready = "Ready"

    # Variable Init
    Band_LTE = ast.literal_eval(read_config.findtext("autotest/Bands/Band_LTE"))
    RX_Channel = ast.literal_eval(read_config.findtext("autotest/Bands/RX_Channel"))
    TX_Channel = ast.literal_eval(read_config.findtext("autotest/Bands/TX_Channel"))

    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)

    if len(Band_LTE) < 1:
        VarGlobal.statOfItem="NOK"
        raise Exception("---->Problem: Invalid Band_LTE input from INI file !!!")

    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase == 0:
        pytest.skip("Phase 0 : No AT+WMRXPOWER/AT+WMTXPOWER commands")

    test_nb = ""
    test_ID = "A_HL_INT_PWR_RX_TX_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        RX_Channel = collections.OrderedDict(sorted(RX_Channel.items()))
        TX_Channel = collections.OrderedDict(sorted(TX_Channel.items()))

        ModuleBands = str(Band_LTE).strip('[]').replace(" ", "")
        RX_ModuleChannels = str(list(RX_Channel.values())).strip('[]').replace(" ", "").replace("\'", "")
        TX_ModuleChannels = str(list(TX_Channel.values())).strip('[]').replace(" ", "").replace("\'", "")

        #AT+CMEE=1
        SagSendAT(target_at, "AT+CMEE=1\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        print("----- RX POWER TEST -----")

        # AT+WMRXPOWER=?
        SagSendAT(target_at, "AT+WMRXPOWER=?\r")
        SagWaitnMatchResp(target_at, ["\r\n+WMRXPOWER: (0-1),(%s),(%s)\r\n" % (ModuleBands, RX_ModuleChannels)], C_TIMER_LOW)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        # AT+WMRXPOWER?
        SagSendAT(target_at, "AT+WMRXPOWER?\r")
        answer = SagWaitResp(target_at, ["\r\n+WMRXPOWER: *\r\n\r\nOK\r\n"], C_TIMER_LOW)
        result = SagMatchResp(answer, ["\r\n+WMRXPOWER: *\r\n"])
        if result:
            rx = answer.split("\r\n")[1].split(": ")[1]
            if rx != "0" and rx != "255":
                print("-----> Failed!!! Defautl WMRXPOWER is 0/255")
                VarGlobal.statOfItem = "NOK"

        print("----- TX POWER TEST -----")

        # AT+WMTXPOWER=?
        SagSendAT(target_at, "AT+WMTXPOWER=?\r")
        # Modify for HL780x & HL781x
        if Soft_Version < "05.00.00.00":
            SagWaitnMatchResp(target_at, ["\r\n+WMTXPOWER: (0-1),(%s),(%s),(0-2300),(0-1),(0)\r\n" % (ModuleBands, TX_ModuleChannels)], C_TIMER_LOW)
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)
        else:
            SagWaitnMatchResp(target_at, ["\r\n+WMTXPOWER: (0-1),(%s),(%s),(0-2600),(0-1),(0)\r\n" % (ModuleBands, TX_ModuleChannels)], C_TIMER_LOW)
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        # AT+WMTXPOWER?
        SagSendAT(target_at, "AT+WMTXPOWER?\r")
        answer = SagWaitResp(target_at, ["\r\n+WMTXPOWER: *\r\n\r\nOK\r\n"], C_TIMER_LOW)
        result = SagMatchResp(answer, ["\r\n+WMTXPOWER: *\r\n"])
        if result:
            tx = answer.split("\r\n")[1].split(": ")[1]
            if tx != "0" and tx != "255":
                print("-----> Failed!!! Defautl WMTXPOWER is 0/255")
                VarGlobal.statOfItem = "NOK"

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
