"""
Test :: CPSMS
"""

import pytest
import time
import os
import VarGlobal
import re
import time
from autotest import *
from otii_utility import *

def A_HL_INT_PWR_CPSMS_0000(target_at, read_config, network_tests_setup_teardown, otii_setup_teardown):

    print("\nA_HL_INT_PWR_CPSMS_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    phase = int(read_config.findtext("autotest/Features_PHASE"))
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)

    # Amarisoft SIM Card Detecting
    Network = read_config.findtext("autotest/Network")
    if "amarisoft" not in str.lower(Network):
        raise Exception("Problem: Amarisoft SIM and Config should be used.")

    test_nb = ""
    test_ID = "A_HL_INT_PWR_CPSMS_0000"
    PRINT_START_FUNC(test_nb + test_ID)
    sleep_mode = 0

    print("\n----- Testing Start -----\n")

    try:

        otii_object = otii_setup_teardown
        if not otii_object:
            raise Exception("OTII device not connected")
        devices = otii_object.get_devices()
        proj = otii_object.get_active_project()
        my_arc = devices[0]
        power_recording = threading.Thread(target=start_record_power, args=(otii_object, proj, my_arc,["mc"]))
        power_recording.start()

        # save default +KSREP
        SagSendAT(target_at, "AT+KSREP?\r")
        answer = SagWaitResp(target_at, ["\r\n+KSREP: ?,*\r\n"], 2000)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)
        ksrep = answer.split("\r\n")[1].split(": ")[1].split(",")[0]
        if (ksrep == "0"):
            SagSendAT(target_at, "AT+KSREP=1\r")
            SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 2000)

        # AT+CPSMS=?
        SagSendAT(target_at, "AT+CPSMS=?\r")
        #For HL780x & HL781x
        if phase > 0 and Soft_Version < "05.00.00.00":
            SagWaitnMatchResp(target_at, ["\r\n+CPSMS: (0-1),(),(),(\"00000000\"-\"11111111\"),(\"00000000\"-\"01011111\",\"11100000\"-\"11111111\")\r\n\r\nOK\r\n"], C_TIMER_LOW)
        elif phase > 0 and Soft_Version >= "05.00.00.00":
            SagWaitnMatchResp(target_at, ["\r\n+CPSMS: (0-2),(),(),(\"00000000\"-\"11111111\"),(\"00000000\"-\"01011111\",\"11100000\"-\"11111111\")\r\n\r\nOK\r\n"], C_TIMER_LOW)
        else:
            SagWaitnMatchResp(target_at, ["\r\n+CPSMS: (0-1),(0),(0),(0-X),(0-Y)\r\n\r\nOK\r\n"], C_TIMER_LOW)

        # AT+CPSMS?
        SagSendAT(target_at, "AT+CPSMS?\r")
        if phase > 0 and Soft_Version < "05.00.00.00":
            SagWaitnMatchResp(target_at, ["\r\n+CPSMS: ?,\"*\",\"*\",\"*\",\"*\"\r\n\r\nOK\r\n"], C_TIMER_LOW)
        elif phase > 0 and Soft_Version >= "05.00.00.00":
            SagWaitnMatchResp(target_at, ["\r\n+CPSMS: ?,*,*,*,*\r\n\r\nOK\r\n"], C_TIMER_LOW)
        else:
            SagWaitnMatchResp(target_at, ["\r\n+CPSMS: ?,*,*,*,*\r\n\r\nOK\r\n"], C_TIMER_LOW)

        # Disable the use of PSM
        # AT+CPSMS=0
        SagSendAT(target_at, "AT+CPSMS=0\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        # AT+CEREG=1
        SagSendAT(target_at, "AT+CEREG=1\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        # Enable the use of PSM
        # AT+CPSMS=1,244,244,162,15
        #<mode>                             :   1: enable the use of PSM
        #<Requested_Periodic-RAU>           : 244: not applicable
        #<Requested_GPRS-READY-timer>(T3314): 244: not applicable
        #<Requested_Periodic-TAU>    (T3412): 162: 02 minutes
        #<Requested_Active-Time>     (T3324):  15: 30 seconds

        SagSendAT(target_at, "AT+CPSMS=1,244,244,162,15\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        start_time = time.time()

        # AT+KSLEEP=1,2
        SagSendAT(target_at, "AT+KSLEEP=1,2,10\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        SagSleep(10000)
        # Check no answer for AT cmd
        target_at.send('AT\r')
        idx = target_at.expect(['\r\nOK\r\n', pexpect.TIMEOUT], 4)
        if idx != 1:
            print("Failed!!! Timeout expected. No answer is supposed to be returned")
            VarGlobal.statOfItem = "NOK"

        sleep_mode = 1

        print("--------------------------------------------------------------")
        print("the device will be reachable during 30 seconds every 2 minutes")
        print("--------------------------------------------------------------")

        SagWaitnMatchResp(target_at, ['*+CEREG: 4*'], 120000)
        idleTime = []
        awakeTime = []
        for k in range (3):

            print("*** loop %d ***" % k)
            idleStartTime = time.time()

            SagWaitnMatchResp(target_at, ['*CEREG: 1*'], 120000)
            idleEndTime = time.time()
            idleDuration = idleEndTime - idleStartTime
            idleTime.append(idleDuration)
            print("Idle mode duration : %f second(s)" % idleDuration)
            awakeStartTime = time.time()

            SagWaitnMatchResp(target_at, ['*+CEREG: 4*'], 120000)
            awakeEndTime = time.time()
            awakeDuration = awakeEndTime - awakeStartTime
            print("awake mode duration : %f second(s)" % awakeDuration)
            awakeTime.append(awakeDuration)

        power_recording.join()
        proj.stop_recording()
        print("Stopped recording with id: " + str(proj.get_last_recording().id))

        recording = proj.get_last_recording()

        prepare_csv_file(recording, test_ID, my_arc, read_config)

        for i in range (len(idleTime)):
            assert 80 <= idleTime[i] <= 100
            assert 25 <= awakeTime[i] <= 35

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    if sleep_mode == 1:
        # set wakeup pin
        my_arc.set_gpo(1,True)
        SagSleep(5000)

        # AT
        SagSendAT(target_at, "AT\r")
        SagWaitnMatchResp(target_at, ['\r\n*\r\n'], 5000)

        # AT+KSLEEP=2
        SagSendAT(target_at, "AT+KSLEEP=2\r")
        SagWaitnMatchResp(target_at, ["*\r\nOK\r\n*"], 5000)

        # unset wakeup pin
        my_arc.set_gpo(1,False)
        SagSleep(2000)

        # AT
        SagSendAT(target_at, "AT\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

    # Disable the use of PSM
    # AT+CPSMS=0
    SagSendAT(target_at, "AT+CPSMS=0\r")
    SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

    # Restore default KSREP
    if ksrep != "":
        SagSendAT(target_at, "AT+KSREP=" + ksrep + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

