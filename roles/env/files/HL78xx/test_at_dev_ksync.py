"""
Devices AT commands test cases :: KSYNC
"""

import pytest
import time
import os
import VarGlobal
import re
from autotest import *

def A_HL_INT_DEV_KSYNC_0000(target_at, read_config, non_network_tests_setup_teardown):
    """
    Check KSYNC AT Command. Nominal/Valid use case
    """
    print("\nA_HL_INT_DEV_KSYNC_0000 TC Start:\n")
    test_environment_ready = "Ready"

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    phase = int(read_config.findtext("autotest/Features_PHASE"))
    GPIO_str = read_config.findtext("autotest/Enabled_GPIO")
    GPIO_list = list(map(lambda a: int(a), GPIO_str.split(",")))
    if phase == 0:
        pytest.skip("Phase 0 : No AT+KSYNC command")

    test_nb = ""
    test_ID = "A_HL_INT_DEV_KSYNC_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        # AT+KSYNC=?
        SagSendAT(target_at, "AT+KSYNC=?\r")
        SagWaitnMatchResp(target_at, ["\r\n+KSYNC: (0,2),(%s)\r\n\r\nOK\r\n" % GPIO_str], 4000)

        # AT+KSYNC?
        SagSendAT(target_at, "AT+KSYNC?\r")
        answer = SagWaitResp(target_at, ["\r\n*\r\n\r\nOK\r\n"], 4000)
        result = SagMatchResp(answer,["\r\n+KSYNC: *,*\r\n"])
        if result:
            ksync = answer.split("\r\n")[1].split(": ")[1]
            print("\nDefault ksync is: "+ksync)
            mode = int(ksync.split(",")[0])
            gpio = int(ksync.split(",")[1])
            if not mode in [0,2]:
                print("Failed!!! Synchronization signal mode must be 0/2")
                VarGlobal.statOfItem = "NOK"
            if not gpio in GPIO_list:
                print("Failed!!! Not supported GPIO value %d" % gpio)
                VarGlobal.statOfItem = "NOK"
        else:
            ksync = "0,1"

        for io in [1,8,15]:
            # AT+KSYNC=2,io
            SagSendAT(target_at, "AT+KSYNC=2,%d\r" % io)
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

            # AT+KSYNC?
            SagSendAT(target_at, "AT+KSYNC?\r")
            SagWaitnMatchResp(target_at, ["\r\n+KSYNC: 2,%d\r\n\r\nOK\r\n" % io], 4000)

            # AT+KGPIOCFG?
            SagSendAT(target_at, "AT+KGPIOCFG?\r")
            answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 4000)
            result = SagMatchResp(answer, ["*\r\n+KGPIOCFG: %d,*,*\r\n*" % io], 4000)
            if result:
                print("Failed!!! GPIO pin is not output.")
                VarGlobal.statOfItem = "NOK"

            # Restore Module
            SWI_Reset_Module(target_at, HARD_INI)

            # AT+KSYNC?
            SagSendAT(target_at, "AT+KSYNC?\r")
            SagWaitnMatchResp(target_at, ["\r\n+KSYNC: 2,%d\r\n\r\nOK\r\n" % io], 4000)

        # Restore default value
        SagSendAT(target_at, "AT+KSYNC=%s\r" % ksync)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    # Restore Module
    SWI_Reset_Module(target_at, HARD_INI)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
