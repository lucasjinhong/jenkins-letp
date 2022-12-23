"""
Test :: KSLEEP
"""

import pytest
import time
import os
import VarGlobal
import re
from autotest import *
import time
import sys, os
import threading
from otii_utility import *
from statistics import mean

def A_HL_INT_PWR_KSLEEP_0000(target_at, read_config, otii_setup_teardown, non_network_tests_setup_teardown):

    print("\nA_HL_INT_PWR_KSLEEP_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    test_nb = ""
    test_ID = "A_HL_INT_PWR_KSLEEP_0000"
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

        # AT+KSLEEP=?
        SagSendAT(target_at, "AT+KSLEEP=?\r")
        #SagWaitnMatchResp(target_at, ["\r\n+KSLEEP: (0-2)[,(0-2)[,(0-99)]]\r\n\r\nOK\r\n"], C_TIMER_LOW)
        SagWaitnMatchResp(target_at, ["\r\n+KSLEEP: (0-2)?,(0-2)?,(0-99)??\r\n\r\nOK\r\n"], C_TIMER_LOW)

        # AT+KSLEEP?
        SagSendAT(target_at, "AT+KSLEEP?\r")
        SagWaitnMatchResp(target_at, ["\r\n+KSLEEP: *\r\n\r\nOK\r\n"], C_TIMER_LOW)

        # AT+KSLEEP=2
        SagSendAT(target_at, "AT+KSLEEP=2\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        # AT+CEREG=0
        SagSendAT(target_at, "AT+CEREG=0\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        # AT%COUNT="PWR"
        SagSendAT(target_at, "AT%COUNT=\"PWR\"\r")
        SagWaitnMatchResp(target_at, ['\r\n*\r\n\r\nOK\r\n'], 5000)

        print("---------- HIBERNATE TEST + WAKE UP ----------")

        SagSleep(5000)
        firstNormalTimeStamp = time.time()
        # AT+CFUN=0
        SagSendAT(target_at, "AT+CFUN=0\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        # AT+KSLEEP=1,2
        SagSendAT(target_at, "AT+KSLEEP=1,2\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        SagSleep(15000)

        # Check no answer for AT cmd
        target_at.send('AT\r')
        idx = target_at.expect(['\r\nOK\r\n', pexpect.TIMEOUT], 4)

        if idx != 1:
            print("Failed!!! Timeout expected. No answer is supposed to be returned")
            VarGlobal.statOfItem = "NOK"

        # note conso value
        hibernateTimeStamp1 = time.time()
        SagSleep(1000)
        hibernateTimeStamp2 = time.time()
        SagSleep(1000)
        hibernateTimeStamp3 = time.time()
        SagSleep(5000)
        # set wakeup pin
        my_arc.set_gpo(1,True)
        SagSleep(5000)
        # AT
        SagSendAT(target_at, "AT\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        # AT+KSLEEP=2
        SagSendAT(target_at, "AT+KSLEEP=2\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        # unset wakeup pin
        my_arc.set_gpo(1,False)
        SagSleep(2000)
        wakeupTimeStamp = time.time()
        SagSleep(1000)
        # AT
        SagSendAT(target_at, "AT\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        # AT%COUNT="PWR"
        SagSendAT(target_at, "AT%COUNT=\"PWR\"\r")
        SagWaitnMatchResp(target_at, ['\r\n*\r\n\r\nOK\r\n'], 5000)

        print("---------- SLEEP TEST + DTR ----------")

        secondNormalTimeStamp = time.time()
        # AT+CGATT=0
        SagSendAT(target_at, "AT+CGATT=0\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        print("Set DTR to 1")
        # set DTR to 1
        target_at.set_dtr(1)

        # AT+KSLEEP=0,0
        SagSendAT(target_at, "AT+KSLEEP=0,0\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        print("Set DTR to 0")
        # set DTR to 0
        target_at.set_dtr(0)

        SagSleep(5000)

        # Check no answer for AT cmd
        target_at.send('AT\r')
        idx = target_at.expect(['\r\nOK\r\n', pexpect.TIMEOUT], 4)

        if idx != 1:
            print("Failed!!! Timeout expected. No answer is supposed to be returned")
            VarGlobal.statOfItem = "NOK"

        sleepTimeStamp1 = time.time()
        SagSleep(1000)
        sleepTimeStamp2 = time.time()
        SagSleep(1000)
        sleepTimeStamp3 = time.time()

        print("Set DTR to 1")
        # set DTR to 1
        target_at.set_dtr(1)

        SagSleep(1000)

        # AT
        SagSendAT(target_at, "AT\r")
        SagWaitnMatchResp(target_at, ['\r\n*\r\n'], 5000)

        # AT+KSLEEP=2
        SagSendAT(target_at, "AT+KSLEEP=2\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        # AT%COUNT="PWR"
        SagSendAT(target_at, "AT%COUNT=\"PWR\"\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 5000)

        endTime = time.time()
        duration = endTime - startTime
        print ( "Time elapse " + str(duration))
        power_recording.join()
        proj.stop_recording()
        print("Stopped recording with id: " + str(proj.get_last_recording().id))

        recording = proj.get_last_recording()

        prepare_csv_file(recording, test_ID, my_arc, read_config)

        data = read_otii_current_value_by_timestamp(proj, my_arc, hibernateTimeStamp1-startTime)

        hibernateCurrent1 = mean(data["values"])
        print("hibernateTimeStamp1 at " + str(data["timestamp"]) + " value " + str(hibernateCurrent1))

        data = read_otii_current_value_by_timestamp(proj, my_arc, hibernateTimeStamp2-startTime)
        hibernateCurrent2 = mean(data["values"])
        print("hibernateTimeStamp2 at " + str(data["timestamp"]) + " value " + str(hibernateCurrent2))

        data = read_otii_current_value_by_timestamp(proj, my_arc, hibernateTimeStamp3-startTime)
        hibernateCurrent3 = mean(data["values"])
        print("hibernateTimeStamp3 at " + str(data["timestamp"]) + " value " + str(hibernateCurrent3))

        data = read_otii_current_value_by_timestamp(proj, my_arc, sleepTimeStamp1-startTime)

        sleepCurrent1 = mean(data["values"])
        print("sleepTimeStamp1 at " + str(data["timestamp"]) + " value " + str(sleepCurrent1))

        data = read_otii_current_value_by_timestamp(proj, my_arc, sleepTimeStamp2-startTime)

        sleepCurrent2 = mean(data["values"])
        print("sleepTimeStamp2 at " + str(data["timestamp"]) + " value " + str(sleepCurrent2))

        data = read_otii_current_value_by_timestamp(proj, my_arc, sleepTimeStamp3-startTime)

        sleepCurrent3 = mean(data["values"])
        print("sleepTimeStamp3 at " + str(data["timestamp"]) + " value " + str(sleepCurrent3))

        data = read_otii_current_value_by_timestamp(proj, my_arc, wakeupTimeStamp-startTime)

        wakeupCurrent = mean(data["values"])
        print("wakeupTimeStamp at " + str(data["timestamp"]) + " value " + str(wakeupCurrent))

        assert 0.01 > hibernateCurrent1 > 0
        assert 0.01 > hibernateCurrent2 > 0
        assert 0.01 > hibernateCurrent3 > 0
        assert 0.1 > sleepCurrent1 > 0
        assert 0.1 > sleepCurrent2 > 0
        assert 0.1 > sleepCurrent3 > 0
        assert wakeupCurrent > 0

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

