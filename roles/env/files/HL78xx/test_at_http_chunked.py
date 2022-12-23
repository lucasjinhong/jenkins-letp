"""
Test :: FWINT-366/EURY-887/HLLEAPP-595: Support +KHTTPPOST sending data to HTTP server in chunked transfer encoding
"""

import pytest
import time
import swilog
import pexpect
import VarGlobal
import ast
from autotest import *

swilog.info( "\n----- Program start -----\n")

def http_cleanup_func(target_at):
    print("\n===================================================")
    print("Performing http connection cleanup START...")
    print("===================================================\n")
    rsp = target_at.run_at_cmd("AT+KHTTPCFG?", 20, ["OK"])
    for cfg in rsp.split('\r\n'):
        if "KHTTPCFG:" in cfg:
            _ = cfg.split(',')
            cfg_num = _[0].replace('+KHTTPCFG: ', '')
            if _[-3] == '1':
                target_at.run_at_cmd("AT+KHTTPCLOSE=%s" % cfg_num, 20, ["OK"])
            target_at.run_at_cmd("AT+KHTTPDEL=%s" % cfg_num, 20, ["OK"])
    print("\n===================================================")
    print("Performing http connection cleanup END...")
    print("===================================================\n")

@pytest.fixture
def http_cleanup(target_at):
    http_cleanup_func(target_at)
    yield
    http_cleanup_func(target_at)

# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_HTTP_CHUNKED_0000(target_at, read_config, network_tests_setup_teardown, http_cleanup):
    """
    Check HTTP AT Commands. Nominal/Valid use case
    """
    print("\nA_HL_INT_HTTP_0000 TC Start:\n")
    test_environment_ready = "Ready"
    print("\n------------Test's preambule Start------------")

    HARD_INI = read_config.findtext("autotest/HARD_INI")

    # Firmware version check
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Firmware_Ver = two_digit_fw_version(SOFT_INI_Soft_Version)
    if Firmware_Ver < "04.05.03.00" or "05.03.00.00" < Firmware_Ver < "05.03.03.00":
        pytest.skip("FW<4.5.3 or 5.3.0.0<FW<5.3.3.0 : HTTP data sending in chunked transfer encoding is not supported")

    # Variable Init
    timeout = 15
    http_server = "enr8c9frpzhkf.x.pipedream.net"
    http_port = 80

    SIM_GPRS_APN = ast.literal_eval(read_config.findtext("autotest/Network_APN"))[0]
    SIM_GPRS_LOGIN = ast.literal_eval(read_config.findtext("autotest/Network_APN_login"))[0]
    SIM_GPRS_PASSWORD = ast.literal_eval(read_config.findtext("autotest/Network_APN_password"))[0]
    PARAM_GPRS_PDP = ast.literal_eval(read_config.findtext("autotest/Network_PDP_type"))[0]
    Config_Name = read_config.findtext("autotest/Network_Config/Config_Name")

    # Module Init
    target_at.run_at_cmd("ate0", timeout,["OK"])
    target_at.run_at_cmd("AT+CMEE=1", timeout, ["OK"])
    target_at.run_at_cmd("AT+CGMR", timeout, ["OK"])
    target_at.run_at_cmd("AT+CREG=2", timeout, ["OK"])
    target_at.run_at_cmd("AT+CEREG=2", timeout, ["OK"])

    test_nb = ""
    test_ID = "A_HL_INT_HTTP_CHUNKED_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        swilog.info( "\n----- Testing Start -----\n")

        # Configure HTTP server connection
        target_at.run_at_cmd("AT+CGDCONT=1,\"%s\",\"%s\"" % (PARAM_GPRS_PDP, SIM_GPRS_APN), timeout, ["OK"])
        target_at.run_at_cmd("AT+KCNXCFG=1,\"GPRS\",\"%s\",\"%s\",\"%s\"" % (SIM_GPRS_APN, SIM_GPRS_LOGIN, SIM_GPRS_PASSWORD), timeout, ["OK"])
        target_at.run_at_cmd("AT+KHTTPCFG=1,\"%s\",%s,,,,0" %(http_server,http_port), timeout, [r"\+KHTTPCFG:\s1", "OK"])
        target_at.run_at_cmd("AT+KHTTPCFG?", timeout, [r"\+KHTTPCFG:\s1,1,\"%s\",%s,0,\"\",\"\",0,0,0" %(http_server,http_port),"OK"])

        rsp = target_at.run_at_cmd("AT+KCNXCFG?", timeout, ["OK"])
        pdp_state = rsp.split(",")[-1].split("\r\n")[0]

        # pdp_state = 2 (connected)
        if pdp_state == "2":
            print("\n-- PDP connection already established --\n")
            target_at.run_at_cmd("AT+KHTTPCNX=1", timeout, ["OK", r"\+KHTTP_IND:\s1,1"])
        else:
            print("\n-- New PDP connection --\n")
            target_at.run_at_cmd("AT+KHTTPCNX=1", timeout, ["OK", r"\+KCNX_IND:\s1", r"\+KHTTP_IND:\s1,1"])

        target_at.run_at_cmd("AT+KHTTPHEADER=1", timeout, ["CONNECT"])
        target_at.run_at_cmd("Accept: application/octet-stream\r\nContent-Type: application/octet-stream\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n--EOF--Pattern--\r\n")

        target_at.run_at_cmd("AT+KHTTPPOST=1,,\"/post\"", timeout,["CONNECT"])
        target_at.run_at_cmd("5\r\nMedia\r\n8\r\nServices\r\n4\r\nLive\r\n0\r\n\r\n", timeout, [r"\+KHTTP_IND: 1,3,37,200,\"OK\"", r"\+KHTTP_IND: 1,0" ])

        # Verify header is "Transfer-Encoding: chunked"
        target_at.run_at_cmd("AT+KHTTPHEADER?", timeout, ["Transfer-Encoding: chunked", "OK"])

        target_at.run_at_cmd("AT+KHTTPDEL=1", timeout, ["OK"])

        swilog.info( "\n----- Testing End -----\n")

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

swilog.info( "\n----- Program End -----\n")
