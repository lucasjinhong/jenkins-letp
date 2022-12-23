import pytest
import time
import swilog
import pexpect
import VarGlobal
from autotest import *


swilog.info( "\n----- Program start -----\n")
# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_GNSS_0000(target_at, read_config, non_network_tests_setup_teardown):

    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase < 2:
        pytest.skip("Phase < 2 : No AT+GNSSxxx commands")

    test_nb = ""
    test_ID = "A_HL_INT_GNSS_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    timeout = 10

    # Module Init
    target_at.run_at_cmd("AT%SETACFG=locsrv.operation.locsrv_enable,true", 10, ["OK"])
    SWI_Reset_Module(target_at, HARD_INI, ((Booting_Duration+5000)/1000))

    for i in range(0,3):
        try:
            target_at.run_at_cmd("ATI", timeout, ["OK"])
            break
        except:
            if i == 2:
                raise Exception("Device did not enumerate")
            time.sleep(timeout)

    swilog.info( "\n----- Testing Start -----\n")
    try:
        target_at.run_at_cmd("ATE0", timeout, ["OK"])
        target_at.run_at_cmd("AT+CMEE=1", timeout, ["OK"])
        target_at.run_at_cmd("AT+CGMR", timeout, ["OK"])
        target_at.run_at_cmd("AT+CFUN=0", timeout, ["OK"])

        target_at.run_at_cmd("AT+GNSSCONF=?", timeout, [r"\+GNSSCONF:\s10,\(0-1\)","OK"])
        target_at.run_at_cmd("AT+GNSSNMEA=?", timeout, [r"\+GNSSNMEA:\s\(0,1,3-8\),\(1000\),\(0\),\(1FF\)", "OK"])
        target_at.run_at_cmd("AT+GNSSSTART=?", timeout, [r"\+GNSSSTART: \(0\-3\)", "OK"])
        target_at.run_at_cmd("AT+GNSSNMEA=0,1000,0,1FF")
        for gtype in range(0,2):
            target_at.run_at_cmd("AT+GNSSCONF=10,%s" % str(gtype), timeout, ["OK"])
            target_at.run_at_cmd("AT+GNSSCONF?", timeout, [r"\+GNSSCONF: 10,%s" % str(gtype),"OK"])
            for mode in range(0,4):
                target_at.run_at_cmd("AT+GNSSSTART=%s" % str(mode), timeout * 30, ["OK", r"\+GNSSEV:\s1,1", r"\+GNSSEV:\s3,3"])

                target_at.run_at_cmd("AT+GNSSSTART?", timeout, [r"\+GNSSSTART:\s%s" % str(mode), "OK"])

                target_at.run_at_cmd("AT+GNSSNMEA=4", timeout*8, ["CONNECT",r"\$GPGSV", r"\$GPGNS", r"\$GPRMC", r"\$GPVTG", r"\$GPZDA", r"\$GPGST", r"\$GPGGA", r"\$GPGLL", r"\$GPGSA",])

                print("Exit from DATA mode by typing +++ after 30s seconds")
                time.sleep(timeout*3)
                target_at.at.send("+++")
                target_at.at.expect([r"\r\nOK\r\n"], timeout)

                response = target_at.run_at_cmd("AT+GNSSTTFF?", timeout, ["OK"])
                if "GNSSTTFF: -30, -30" in response:
                    raise Exception("Device did not get TTFF")

                response = target_at.run_at_cmd("AT+GNSSLOC?", timeout, ["OK"])
                if "FIX NOT AVAILABLE" in response:
                    raise Exception("Device did not get Location data")
                if not("Deg" in response and "Min" in response):
                    raise Exception("Device did not get Location data")

                target_at.run_at_cmd("AT+GNSSSTOP", timeout*5, ["OK", r"\+GNSSEV:\s2,1",r"\+GNSSEV:\s3,0"])

                target_at.run_at_cmd("AT+GNSSTTFF?", timeout, [r"GNSSTTFF:\s-30,\s-30"])

                target_at.run_at_cmd("AT+GNSSLOC?", timeout, ["Min","Deg","OK"])
    except AssertionError as msg:
        print(AssertionError, msg)
        VarGlobal.statOfItem = "NOK"

    SWI_Reset_Module(target_at, HARD_INI)

    swilog.info( "\n----- Testing End -----\n")

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

swilog.info( "\n----- Program End -----\n")
