"""
Devices AT commands test cases :: KGPIOCFG
originated from A_HL_Common_MECS_KGPIOCFG_0001.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import re
from autotest import *

def A_HL_INT_DEV_KGPIOCFG_0000(target_at, read_config, non_network_tests_setup_teardown):
    """
    Check KGPIOCFG AT Command. Nominal/Valid use case
    """
    print("\nA_HL_INT_DEV_KGPIOCFG_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    phase = int(read_config.findtext("autotest/Features_PHASE"))
    GPIO_str = read_config.findtext("autotest/Enabled_GPIO")

    test_nb = ""
    test_ID = "A_HL_INT_DEV_KGPIOCFG_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:

        GPIO_list = list(map(lambda a: int(a), GPIO_str.split(",")))

        # AT+KGPIOCFG=?
        SagSendAT(target_at, "AT+KGPIOCFG=?\r")
        SagWaitnMatchResp(target_at, ["\r\n+KGPIOCFG: (%s),(0-1),(0-2)\r\n" % GPIO_str], 3000)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        # AT+KGPIOCFG?
        SagSendAT(target_at, "AT+KGPIOCFG?\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 3000)
        result = SagMatchResp(answer,["*\r\n+KGPIOCFG: ?,?,?\r\n*"])

        if not result:
            print('Failed!!! unable to read KGPIOCFG configuration.')
            VarGlobal.statOfItem = "NOK"
        else:
            # default kgpiocfg : GPIO number 2
            kgpiocfg = answer.split("\r\n")[2].split(": ")[1]
            print("\nDefault kgpiocfg is: "+kgpiocfg)

            # Checking output parameters
            i = 0
            for GPIO in GPIO_list:
                i = i+1

                if (phase == 0):
                    # issue in gpio 1
                    # JIRA : HLLEAPP-255
                    #        DIZZY-1698
                    if GPIO == 1:
                        continue

                GPIO_CFG = answer.split("\r\n")[i]
                print("line : " + str(i))
                print("GPIO_CFG : " + GPIO_CFG)
                GPIO_CFG_STR = GPIO_CFG.split(": ")[0]
                n = GPIO_CFG.split(": ")[1].split(",")[0]
                dir = int(GPIO_CFG.split(": ")[1].split(",")[1])
                pull_mode = int(GPIO_CFG.split(": ")[1].split(",")[2])
                if GPIO_CFG_STR != "+KGPIOCFG":
                    print("GPIO_CFG_STR = ", GPIO_CFG_STR)
                    print('Failed!!! The output is not started with +KGPIOCFG.')
                    VarGlobal.statOfItem = "NOK"
                if n != str(GPIO):
                    print("n =", n)
                    print('Failed!!! parameter <n> error')
                    VarGlobal.statOfItem = "NOK"
                if dir not in list(range(0,2)):
                    print("dir = ", dir)
                    print('Failed!!! parameter <dir> error')
                    VarGlobal.statOfItem = "NOK"
                if pull_mode not in list(range(0,3)):
                    print("pull_mode = ", pull_mode)
                    print('Failed!!! parameter <pull mode> error')
                    VarGlobal.statOfItem = "NOK"
                if dir==0 and pull_mode!=2:
                    print('Failed!!! parameter <pull mode> should be 2 no pull for output GPIO.')
                    VarGlobal.statOfItem = "NOK"
                if dir==1 and pull_mode!=1 and pull_mode!=0:
                    print('Failed!!! parameter <pull mode> should be 0 or 1 pull up/down for input GPIO.')
                    VarGlobal.statOfItem = "NOK"

            testList = ['2,1,0', '2,1,1', '2,0,2']
            for s in testList:
                # AT+KGPIOCFG=<n>,<dir>,<pull mode>
                SagSendAT(target_at, "AT+KGPIOCFG=" + s + "\r")
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

                # AT+KGPIOCFG?
                SagSendAT(target_at, "AT+KGPIOCFG?\r")
                SagWaitnMatchResp(target_at, ["*\r\n+KGPIOCFG: " + s + "\r\n"], 3000)
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

                # Restart module
                SWI_Reset_Module(target_at, HARD_INI)

                # AT+KGPIOCFG?
                SagSendAT(target_at, "AT+KGPIOCFG?\r")
                SagWaitnMatchResp(target_at, ["*\r\n+KGPIOCFG: " + s + "\r\n"], 3000)
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

            # Restore default kgpiocfg
            SagSendAT(target_at, "AT+KGPIOCFG=" + kgpiocfg + "\r")
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
