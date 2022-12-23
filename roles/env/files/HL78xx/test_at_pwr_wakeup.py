"""
Test :: EURY-3235/FWINT-287: UART wakeuptime does not exceed 2.7 sec
The test case should be tested in 4.5.1.0 and above FW.
"""

import pytest
import os
import VarGlobal
import re
import time
from packaging import version
from datetime import datetime
from autotest import *
from otii_utility import *

def A_HL_INT_PWR_WAKEUP_0000(target_cli, target_at, read_config, network_tests_setup_teardown, otii_setup_teardown):

    print("\nA_HL_INT_PWR_WAKEUP_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")
    ksrep = ""
    sleep_mode = 0

    test_nb = ""
    test_ID = "A_HL_INT_PWR_WAKEUP_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        # Check FW Version is 4.5.1.0 and above
        SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
        Firmware_Ver = two_digit_fw_version(SOFT_INI_Soft_Version)
        if Firmware_Ver < "04.05.01.00":
            pytest.skip("Firmware < 4.5.1.0 : Feature Is Not Supported")

        otii_object = otii_setup_teardown
        if not otii_object:
            pytest.skip("OTII device not connected: Must connect to OTII device to perform the test!!!")
        devices = otii_object.get_devices()
        proj = otii_object.get_active_project()
        my_arc = devices[0]

        # save default +KSREP
        SagSendAT(target_at, "AT+KSREP?\r")
        answer = SagWaitResp(target_at, ["\r\n+KSREP: ?,?,*\r\n"], 2000)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)
        ksrep = answer.split("\r\n")[1].split(": ")[1].replace(",0,",",")

        # set +KSREP=0,0
        SagSendAT(target_at, "AT+KSREP=0,0\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 2000)

        for scenario in range(1,3):
            if scenario == 1:
                print ("====== Test Scenario %d in RnD mode ======" % scenario)
            if scenario == 2:
                print ("===== Test Scneario %d in CUSTOMER mode =====" % scenario)
                #Set Customer mode
                SagSendAT(target_at, "AT+SWITRACEMODE=CUSTOMER\r")
                SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)
                SagSendAT(target_at, "AT+CFUN=1,1\r")
                SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)
                SagSleep(30000)
                SagSendAT(target_at, "AT+SWITRACEMODE?\r")
                SagWaitnMatchResp(target_at, ['\r\n*CUSTOMER*\r\n'], 5000)
                # enable WDSI indicator
                SagSendAT(target_at, "AT+WDSI=4479\r")
                SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 2000)
                SagSleep(5000)

            # AT+KSLEEP=1,2
            SagSendAT(target_at, "AT+KSLEEP=1,2\r")
            SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 2000)
            sleep_mode = 1
            SagSleep(5000)

            for k in range (10):
                print("*** loop %d ***" % k)
                # set wakeup pin
                print ('set wakeup pin')
                wakeupTimeStamp =  datetime.now()
                my_arc.set_gpo(1,True)
                wakeupTimeStamp =  datetime.now()
                print('wakeupTimeStatmp ===', wakeupTimeStamp)

                if scenario == 1:
                    SagWaitResp(target_cli, ["\r\n*uart_flow_control_task is called HW FLOW is ON\r\n"], 3000)
                    UART_activeTime =  datetime.now()
                    print('UART_activeTime with CLI port "urat flow control task ===', UART_activeTime)
                elif scenario == 2:
                    SagWaitResp(target_at, ["\r\n+WDSI: 0\r\n"], 50000)
                    UART_activeTime =  datetime.now()
                    print("UART_activeTime with AT port +WDSI:0 indicator ===", UART_activeTime)

                UART_active_Duration = (UART_activeTime - wakeupTimeStamp).seconds * 1000.0 \
                        + (UART_activeTime - wakeupTimeStamp).microseconds / 1000.0
                swilog.info("UART_active is in %.2f second(s) after wakeup\n" % (UART_active_Duration/1000.0))

                if (UART_active_Duration/1000.0) > 2.7:
                    raise Exception ("UART should become active in less than 2.7 sec after wakeup")

                # unset wakeup pin
                my_arc.set_gpo(1,False)
                SagSleep(20000)

            if sleep_mode == 1:
                # set wakeup pin
                my_arc.set_gpo(1,True)
                print ('Finish Loop. To disalbe Ksleep mode. Set wakeup pin')
                SagSleep(5000)

                # AT
                SagSendAT(target_at, "AT\r")
                SagWaitnMatchResp(target_at, ['\r\n*\r\n'], 5000)

                # AT+KSLEEP=2
                SagSendAT(target_at, "AT+KSLEEP=2\r")
                SagWaitnMatchResp(target_at, ["*\r\nOK\r\n*"], 5000)

                # unset wakeup pin
                print ('Ksleep mode was disabled. Unset wakeup pin')
                my_arc.set_gpo(1,False)
                SagSleep(5000)

                # AT
                SagSendAT(target_at, "AT\r")
                SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)
                sleep_mode = 0

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    # Restore default KSREP
    if ksrep != "":
        SagSendAT(target_at, "AT+KSREP=" + ksrep + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

    # set back to RnD mode
    SagSendAT(target_at, "AT+SWITRACEMODE=RnD\r")
    SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 2000)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)