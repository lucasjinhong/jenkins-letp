"""
Cellular AT commands test cases :: KALTCFG
originated from A_HL_Common_MECS_KALTCFG_0001.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import re
import ast
from autotest import *

def A_HL_INT_CEL_KALTCFG_0000(target_at, read_config, network_tests_setup_teardown):
    """
    Check KALTCFG AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_CEL_KALTCFG_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    params = ['"RRC_INACTIVITY_TIMER"', '"PS_DEV_MOB_TYPE"']
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)

    if Soft_Version <= "04.00.00.00":
        params_default_mode = [0,1]
    else:
        params_default_mode = [35,1]
    params_values = [25,2]
    kaltcfg_params = []
    kaltcfg_defaults = []

    test_nb = ""
    test_ID = "A_HL_INT_CEL_KALTCFG_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        print("\n----- Query Command -----\n")
        # AT+KALTCFG=?
        SagSendAT(target_at, "AT+KALTCFG=?\r")
        answer = SagWaitResp(target_at, ['\r\n+KALTCFG: *\r\n\r\nOK\r\n'], C_TIMER_LOW)
        result = SagMatchResp(answer, ['\r\n+KALTCFG: (0-1),("RRC_INACTIVITY_TIMER"*)\r\n'])
        if result:
            kaltcfg_params = answer.split("\r\n")[1].split(",(")[1].split(")")[0].split(",")

        # kaltcfg params
        for param in kaltcfg_params:
            if not param in params:
                print("Failed!! unknown AT+KALTCFG parameter %s" % param)
                VarGlobal.statOfItem = "NOK"

        # default kaltcfg params
        for param in kaltcfg_params:
            # AT+KALTCFG=1,param
            SagSendAT(target_at, 'AT+KALTCFG=1,%s\r' % param)
            answer = SagWaitResp(target_at, ["\r\n+KALTCFG: *\r\n\r\nOK\r\n"], C_TIMER_LOW)
            result = SagMatchResp(answer, ["\r\n+KALTCFG: *\r\n"])
            if result:
                kaltcfg = answer.split("\r\n")[1].split(": ")[1]
                print("\nDefault %s is: %s\n" % (param, kaltcfg))
                kaltcfg_defaults.append(kaltcfg)
            else:
                kaltcfg_defaults.append("")


        print("\n----- Write/Read Command (random value) -----\n")
        for param, value in zip (kaltcfg_params, params_values):
            # AT+KALTCFG=0,param,value
            SagSendAT(target_at, 'AT+KALTCFG=0,%s,%d\r' % (param, value))
            SagWaitResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

            # AT+KALTCFG=1,param
            SagSendAT(target_at, 'AT+KALTCFG=1,%s\r' % param)
            SagWaitResp(target_at, ["\r\n+KALTCFG: %d\r\n\r\nOK\r\n" % value], C_TIMER_LOW)


        print("\n----- RRC_INACTIVITY_TIMER is persistant to reboot -----\n")
        # Restart module
        SWI_Reset_Module(target_at, HARD_INI)

        for param, value in zip(kaltcfg_params, params_values):
            # Check RRC_INACTIVITY_TIMER is back to default
            SagSendAT(target_at, 'AT+KALTCFG=1,%s\r' % param)
            SagWaitResp(target_at, ["\r\n+KALTCFG: %d\r\n\r\nOK\r\n" % value], C_TIMER_LOW)

        print("\n----- Set to default mode -----\n")
        for param, value in zip(kaltcfg_params, params_default_mode):
            # AT+KALTCFG=0,param
            SagSendAT(target_at, 'AT+KALTCFG=0,%s\r' % param)
            SagWaitResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

            # AT+KALTCFG=1,param
            SagSendAT(target_at, 'AT+KALTCFG=1,%s\r' % param)
            SagWaitResp(target_at, ["\r\n+KALTCFG: %d\r\n\r\nOK\r\n" % value], C_TIMER_LOW)

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    # restore default values
    for kaltcfg, param in zip(kaltcfg_defaults, kaltcfg_params):
        if kaltcfg != "":
            SagSendAT(target_at, 'AT+KALTCFG=0,%s,%s\r' % (param, kaltcfg))
            SagWaitResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
