"""
Test :: CEDRXS
"""

import pytest
import time
import os
import VarGlobal
import re
import time
from datetime import datetime
from autotest import *
import threading
from otii_utility import *
from statistics import mean

def A_HL_INT_PWR_CEDRXS_0000(target_at, read_config, network_tests_setup_teardown, otii_setup_teardown):

    print("\nA_HL_INT_PWR_CEDRXS_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    SIM_Pin1 = read_config.findtext("autotest/PIN1_CODE")
    Config_Name = read_config.findtext("autotest/Network_Config/Config_Name")
    phase = int(read_config.findtext("autotest/Features_PHASE"))
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)
    ksrep = ""
    sleep_mode = 0

    # Requires Amarisoft SIM Card for the test case
    Network = read_config.findtext("autotest/Network")
    if "amarisoft" not in str.lower(Network):
        raise Exception("Problem: Amarisoft SIM and Config should be used.")

    test_nb = ""
    test_ID = "A_HL_INT_PWR_CEDRXS_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")


    try:
        otii_object = otii_setup_teardown
        if not otii_object:
            raise Exception("OTII device not connected")
        devices = otii_object.get_devices()
        proj = otii_object.get_active_project()
        my_arc = devices[0]

        startTime = time.time()
        power_recording = threading.Thread(target=start_record_power, args=(otii_object, proj, my_arc,["mc"]))
        power_recording.start()

        # default <AcT-type>
        if Config_Name == "M1":
            act_type = 4 # LTEM
        else:
            act_type = 5 # NBIOT

        # save default +KSREP
        SagSendAT(target_at, "AT+KSREP?\r")
        answer = SagWaitResp(target_at, ["\r\n+KSREP: ?,*\r\n"], 2000)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)
        ksrep = answer.split("\r\n")[1].split(": ")[1].split(",")[0]
        if (ksrep == "0"):
            SagSendAT(target_at, "AT+KSREP=1\r")
            SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 2000)

        # AT+CEDRXRDP=?
        SagSendAT(target_at, "AT+CEDRXRDP=?\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

        # AT+CEDRXS=?
        SagSendAT(target_at, "AT+CEDRXS=?\r")
        if (phase > 0):
            SagWaitnMatchResp(target_at, ["\r\n+CEDRXS: (0-3),(4-5),(\"0000\"-\"1111\")\r\n\r\nOK\r\n"], C_TIMER_LOW)
        else:
            SagWaitnMatchResp(target_at, ["\r\n+CEDRXS: (0-3),(%d),(\"0000\"-\"1101\")\r\n\r\nOK\r\n" % act_type], C_TIMER_LOW)

        # AT+CEDRXS?
        SagSendAT(target_at, "AT+CEDRXS?\r")
        SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], C_TIMER_LOW)

        # Disable the use of eDRX
        # AT+CEDRXS=0
        SagSendAT(target_at, "AT+CEDRXS=0\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        # AT+CEDRXRDP
        SagSendAT(target_at, "AT+CEDRXRDP\r")
        SagWaitnMatchResp(target_at, ["\r\n+CEDRXRDP: 0*\r\n\r\nOK\r\n"], 2000)

        # AT+CEREG=1
        SagSendAT(target_at, "AT+CEREG=1\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        # Enable the use of eDRX
        # AT+CEDRXS=1,x,5
        #<mode>                :   1: enable the use of eDRX
        #<AcT-type>            : 4/5: LTEM/NBIOT
        #<Requested_eDRX_value>:   5: timer (81,92s)

        SagSendAT(target_at, "AT+CEDRXS=1,%d,5\r" % act_type)
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)
        SagSleep(15000)

        # AT+CEDRXRDP
        SagSendAT(target_at, "AT+CEDRXRDP\r")
        SagWaitnMatchResp(target_at, ["\r\n+CEDRXRDP: %d,\"0101\",\"0101\",\"????\"\r\n\r\nOK\r\n" % act_type], 2000)

        SagSleep(5000)
        firstNormalTimeStamp = time.time()
        SagSleep(2000)
        # AT+KSLEEP=1,2
        SagSendAT(target_at, "AT+KSLEEP=1,2\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        sleep_mode = 1

        # auto reboot
        SagSleep(Booting_Duration+5000)

        # Check no answer for AT cmd
        target_at.send('AT\r')
        idx = target_at.expect(['\r\nOK\r\n', pexpect.TIMEOUT], 4)

        if idx != 1:
            print("Failed!!! Timeout expected. No answer is supposed to be returned")
            VarGlobal.statOfItem = "NOK"


        hibernateTimeStamp = time.time()
        SagSleep(5000)


        power_recording.join()
        proj.stop_recording()
        print("Stopped recording with id: " + str(proj.get_last_recording().id))

        recording = proj.get_last_recording()

        prepare_csv_file(recording, test_ID, my_arc, read_config)

        data = read_otii_current_value_by_timestamp(proj, my_arc, firstNormalTimeStamp-startTime)

        normalCurrent = mean(data["values"])
        print("firstNormalTimeStamp at " + str(data["timestamp"]) + " value " + str(normalCurrent))

        data = read_otii_current_value_by_timestamp(proj, my_arc, hibernateTimeStamp-startTime)

        hibernateCurrent = mean(data["values"])
        print("hibernateTimeStamp at " + str(data["timestamp"]) + " value " + str(hibernateCurrent))

        assert normalCurrent/10 > hibernateCurrent

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    if sleep_mode == 1:
        # set wakeup pin
        my_arc.set_gpo(1,True)
        SagSleep(2000)

        # Modify base on the JIRA ticket ALT1250-3877
        if Soft_Version < "05.00.00.00":
            SagWaitnMatchResp(target_at, ["\r\n*+KSUP: *\r\n"], 4000)
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

    # Disable the use of eDRX
    # AT+CEDRXS=0
    SagSendAT(target_at, "AT+CEDRXS=0\r")
    SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

    # Restore default KSREP
    if ksrep != "":
        SagSendAT(target_at, "AT+KSREP=" + ksrep + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

