"""
Devices AT commands test cases :: KHWIOCFG
"""

import pytest
import time
import os
import VarGlobal
import re
from autotest import *
from fw_dict import fw_ver_khwiocfg

def A_HL_INT_DEV_KHWIOCFG_0000(target_at, read_config, network_tests_setup_teardown):
    """
    Check KHWIOCFG AT Command. Nominal/Valid use case
    """
    print("\nA_HL_INT_DEV_KHWIOCFG_0000 TC Start:\n")
    test_environment_ready = "Ready"

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)
    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase == 0:
        pytest.skip("Phase 0 : No AT+KHWIOCFG command")

    test_nb = ""
    test_ID = "A_HL_INT_DEV_KHWIOCFG_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        # AT+KHWIOCFG=?
        SagSendAT(target_at, "AT+KHWIOCFG=?\r")
        if Soft_Version in fw_ver_khwiocfg:
            SagWaitnMatchResp(target_at, [fw_ver_khwiocfg[Soft_Version][0]], 4000)
        elif Soft_Version > "05.04.05.00":
            SagWaitnMatchResp(target_at, ["\r\n+KHWIOCFG: (0-2,5-8),(0,1)\r\n+KHWIOCFG: 3,(0,1),6\r\n+KHWIOCFG: 4,(0,1),8\r\n\r\nOK\r\n"], 4000)
        else:
            SagWaitnMatchResp(target_at, ["\r\n+KHWIOCFG: (0-2,5),(0,1)\r\n+KHWIOCFG: 3,(0,1),6\r\n+KHWIOCFG: 4,(0,1),8\r\n\r\nOK\r\n"], 4000)
        # AT+KHWIOCFG?
        SagSendAT(target_at, "AT+KHWIOCFG?\r")
        if Soft_Version in fw_ver_khwiocfg:
            SagWaitnMatchResp(target_at, [fw_ver_khwiocfg[Soft_Version][1]], 4000)
        elif Soft_Version > "05.04.05.00":
            SagWaitnMatchResp(target_at, ["\r\n+KHWIOCFG: 0,0\r\n+KHWIOCFG: 1,0\r\n+KHWIOCFG: 2,0\r\n+KHWIOCFG: 3,0,6\r\n+KHWIOCFG: 4,0,8\r\n+KHWIOCFG: 5,0\r\n+KHWIOCFG: 6,0\r\n+KHWIOCFG: 7,0\r\n+KHWIOCFG: 8,1\r\n\r\nOK\r\n"], 4000)
        else:
            SagWaitnMatchResp(target_at, ["\r\n+KHWIOCFG: 0,0\r\n+KHWIOCFG: 1,0\r\n+KHWIOCFG: 2,0\r\n+KHWIOCFG: 3,0,6\r\n+KHWIOCFG: 4,0,8\r\n+KHWIOCFG: 5,0\r\n\r\nOK\r\n"], 4000)

        # AT+KHWIOCFG=feature,mode,io
        # feature : 0  Power On button
        #           1  32kHz clock output
        #           2  26MHz clock output
        #           3  Low Power mode Monitoring
        #           4  External RF voltage control
        for feature in range(3):
            for mode in [1,0]:
                SagSendAT(target_at, "AT+KHWIOCFG=%d,%d\r" % (feature, mode))
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 100000)
                # AT+KHWIOCFG?
                SagSendAT(target_at, "AT+KHWIOCFG?\r")
                SagWaitnMatchResp(target_at, ["*\r\n+KHWIOCFG: %d,%d\r\n*" % (feature, mode)], 4000)
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

                if feature == 1:
                    # Restore Module
                    SWI_Reset_Module(target_at, HARD_INI)

                    # AT+KHWIOCFG?
                    SagSendAT(target_at, "AT+KHWIOCFG?\r")
                    SagWaitnMatchResp(target_at, ["*\r\n+KHWIOCFG: %d,%d\r\n*" % (feature, mode)], 4000)
                    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

        for feature, gpio in zip([3,4], [6,8]):
            for mode in [1,0]:
                # AT+KHWIOCFG=feature,mode,gpio
                SagSendAT(target_at, "AT+KHWIOCFG=%d,%d,%d\r" % (feature, mode, gpio))
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)
                # AT+KHWIOCFG?
                SagSendAT(target_at, "AT+KHWIOCFG?\r")
                SagWaitnMatchResp(target_at, ["*\r\n+KHWIOCFG: %d,%d,%d\r\n*" % (feature, mode, gpio)], 4000)
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
