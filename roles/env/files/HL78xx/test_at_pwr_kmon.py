"""
Power AT commands test cases :: KMON
"""

import pytest
import time
import os
import VarGlobal
import ast
from autotest import *
from otii_utility import *


def A_HL_INT_PWR_KMON_0000(target_cli, target_at, read_config, otii_setup_teardown, non_network_tests_setup_teardown):
    """
    Check KMON AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_PWR_KMON_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")

    test_nb = ""
    test_ID = "A_HL_INT_PWR_KMON_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

    print("\n------------Test Case Start------------")

    try:

        otii_object = otii_setup_teardown
        if not otii_object:
            raise Exception("OTII device not connected")
        devices = otii_object.get_devices()
        proj = otii_object.get_active_project()
        my_arc = devices[0]
        # save default +KSREP
        SagSendAT(target_at, "AT+KSREP?\r")
        answer = SagWaitResp(target_at, ["\r\n+KSREP: ?,*\r\n"], 2000)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)
        ksrep = answer.split("\r\n")[1].split(": ")[1].split(",")[0]
        if (ksrep == "0"):
            SagSendAT(target_at, "AT+KSREP=1\r")
            SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 2000)

        # AT+KMON=?
        SagSendAT(target_at, 'AT+KMON=?\r')
        SagWaitnMatchResp(target_at, ['\r\n+KMON: (0-2)\r\n\r\nOK\r\n'], 3000)

        # AT+KMON?
        SagSendAT(target_at, 'AT+KMON?\r')
        answer = SagWaitResp(target_at, ["\r\n+KMON: ?\r\n\r\nOK\r\n"], 3000)
        result = SagMatchResp(answer, ["\r\n+KMON: ?\r\n"])

        if result:
            kmon = answer.split("\r\n")[1].split(": ")[1]
            print("\nDefault kmon is: "+kmon)
        else:
            kmon = "1"

        # AT+switracemode?
        SagSendAT(target_at, 'AT+switracemode?\r')
        switracemode = SagWaitResp(target_at, ["\r\n*\r\n\r\nOK\r\n"], 3000)
        if switracemode.find("RnD") != -1:
            if kmon != "1" and kmon != "2":
                print('Failed!!! RnD switracemode : default KMON should be 1/2.')
                VarGlobal.statOfItem = "NOK"

            # AT+switracemode=CUSTOMER
            SagSendAT(target_at, 'AT+switracemode=CUSTOMER\r')
            SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 15000)
            # Manual reboot after +SWITRACEMODE
            SWI_Reset_Module(target_at, HARD_INI)

            # AT+KMON?
            SagSendAT(target_at, 'AT+KMON?\r')
            answer = SagWaitResp(target_at, ["\r\n+KMON: ?\r\n\r\nOK\r\n"], 5000)
            result = SagMatchResp(answer, ["*\r\n+KMON: 0\r\n*"])

            if not result:
                print('Failed!!! CUSTOMER switracemode : default KMON should be 0.')
                VarGlobal.statOfItem = "NOK"

            # AT+switracemode=RnD
            SagSendAT(target_at, 'AT+switracemode=RnD\r')
            SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 15000)
            # Manual reboot after +SWITRACEMODE
            SWI_Reset_Module(target_at, HARD_INI)

        if kmon != "0":
            # AT+KMON=0
            SagSendAT(target_at, 'AT+KMON=0\r')
            SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 3000)

            # AT+KMON?
            SagSendAT(target_at, 'AT+KMON?\r')
            SagWaitnMatchResp(target_at, ['\r\n+KMON: 0\r\n\r\nOK\r\n'], 3000)

        # Check auto reboot after crash
        # Entering "exception" on CLI provokes a crash
        target_cli.run("exception")
        SagSleep(Crash_Duration + Booting_Duration+5000)
        SagWaitnMatchResp(target_at, ["\r\n*+KSUP: *\r\n"], 4000)

        # AT+KMON=1
        SagSendAT(target_at, 'AT+KMON=1\r')
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 3000)

        # AT+KMON?
        SagSendAT(target_at, 'AT+KMON?\r')
        SagWaitnMatchResp(target_at, ['\r\n+KMON: 1\r\n\r\nOK\r\n'], 3000)

        # Entering "exception" on CLI provokes a crash
        try:
            target_cli.run("exception")
        except Exception:
            pass
        SagSleep(5000)
        # set reset pin
        print("set Reset button")
        my_arc.set_gpo(2,False)
        SagSleep(2000)
        my_arc.set_gpo(2,True)

        SagSleep(Crash_Duration + Booting_Duration+5000 + 5000)
        SagWaitnMatchResp(target_at, ["\r\n*+KSUP: *\r\n"], 4000)

        # AT+KMON?
        SagSendAT(target_at, 'AT+KMON?\r')
        SagWaitnMatchResp(target_at, ['\r\n+KMON: 2\r\n\r\nOK\r\n'], 3000)

        # Check auto reboot after crash
        # Entering "exception" on CLI provokes a crash
        target_cli.run("exception")
        SagSleep(Crash_Duration + Booting_Duration+5000)
        SagWaitnMatchResp(target_at, ["\r\n*+KSUP: *\r\n"], 4000)

        # Restore default KSREP
        SagSendAT(target_at, "AT+KSREP=" + ksrep + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

        # Restore default KMON
        SagSendAT(target_at, "AT+KMON=" + kmon + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
