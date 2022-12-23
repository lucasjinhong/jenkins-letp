import pytest
import time
import swilog
import pexpect
import VarGlobal
from autotest import *
import os

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
def A_HL_INT_HTTPS_0000(target_at, read_config, network_tests_setup_teardown, http_cleanup):
    """
    Check HTTPS AT Commands. Nominal/Valid use case
    """
    print("\nA_HL_INT_HTTPS_0000 TC Start:\n")
    test_environment_ready = "Ready"
    print("\n------------Test's preambule Start------------")

    # Variable Init
    timeout = 15
    https_server = "httpbin.org"
    #https_server = "https://httpbin.legato.io"
    https_port = 443
    https_cert = os.path.expandvars("$LETP_TESTS/config/cert/cert")
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase < 2:
        pytest.skip("Phase < 2 : No AT+KHTTPxxx commands")

    # cipher_indices
    if ("04.06.00.00" <= Soft_Version < "05.03.00.00") or (Soft_Version >= "05.03.03.00"):
        cipher_index = r"\(0\-7\)"
    else:
        cipher_index = r"\(0\-15\)"

    # Module Init
    target_at.run_at_cmd("ate0", timeout,["OK"])
    target_at.run_at_cmd("AT+CMEE=1", timeout, ["OK"])
    target_at.run_at_cmd("AT+CGMR", timeout, ["OK"])
    target_at.run_at_cmd("AT+CREG=2", timeout, ["OK"])
    target_at.run_at_cmd("AT+CEREG=2", timeout, ["OK"])

    test_nb = ""
    test_ID = "A_HL_INT_HTTPS_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        swilog.info( "\n----- Testing Start -----\n")

        # Install HTTPS Certificate
        try:
            # Keep DOS like newlines
            with open(https_cert,"rb") as f:
                cert = f.read().decode()
        except:
            raise Exception("https certificate file %s can not be read" % https_cert)

        # Install HTTPS Certificate
        target_at.run_at_cmd("AT&K3\r\n", timeout,["OK\r\n"])
        time.sleep(5)  # Need delay.
        target_at.run_at_cmd("AT+KCERTDELETE=0\r\n", timeout,["OK\r\n"])
        target_at.run_at_cmd("AT+KCERTSTORE=0,%d" % len(cert), timeout,["CONNECT\r\n"])
        target_at.run_at_cmd(cert+"--EOF--Pattern--\r\n", timeout+10)
        target_at.run_at_cmd("AT+KCERTSTORE?", timeout,["OK"])

        # Check HTTPS AT Test Commands
        target_at.run_at_cmd("AT+KHTTPCFG=?", timeout, [r"\+KHTTPCFG:\s\(1-2\),<server_name/ip>,\(1-65535\),\(0,2\),\(0-64\),\(0-64\),\(0-1\),\(0-1\)," + cipher_index, "OK"])
        target_at.run_at_cmd("AT+KHTTPCNX=?", timeout, [r"\+KHTTPCNX:\s\(1-6\)","OK"])
        target_at.run_at_cmd("AT+KHTTPGET=?", timeout, [r"\+KHTTPGET:\s\(1-6\),<request_uri>,\(0-1\)", "OK"])
        target_at.run_at_cmd("AT+KHTTPHEADER=?", timeout, [r"\+KHTTPHEADER:\s\(1-6\)", "OK"])
        target_at.run_at_cmd("AT+KHTTPHEAD=?", timeout, [r"\+KHTTPHEAD:\s\(1-6\),<request_uri>", "OK"])
        target_at.run_at_cmd("AT+KHTTPPOST=?", timeout, [r"\+KHTTPPOST:\s\(1-6\),<local_uri>,<request_uri>,\(0-1\)", "OK"])
        target_at.run_at_cmd("AT+KHTTPCLOSE=?", timeout, [r"\+KHTTPCLOSE:\s\(1-6\),\(0-1\)", "OK"])
        target_at.run_at_cmd("AT+KHTTPDEL=?", timeout, [r"\+KHTTPDEL:\s\(1-6\)", "OK"])
        target_at.run_at_cmd("AT+KHTTPPUT=?", timeout, [r"\+KHTTPPUT:\s\(1-6\),<local_uri>,<request_uri>,\(0-1\)", "OK"])
        target_at.run_at_cmd("AT+KHTTPDELETE=?", timeout, [r"\+KHTTPDELETE:\s\(1-6\),<request_uri>,\(0-1\)", "OK"])

        # Check HTTPS AT Read/Write Commands
        target_at.run_at_cmd("AT+KHTTPCFG=1,\"%s\",%s,2,\"\",\"\",0,0,0" %(https_server,https_port), timeout, [r"\+KHTTPCFG:\s1", "OK"])
        target_at.run_at_cmd("AT+KHTTPCFG?", timeout, [r"\+KHTTPCFG:\s1,1,\"%s\",%s,2,\"\",\"\",0,0,0" %(https_server,https_port),"OK"])

        rsp = target_at.run_at_cmd("AT+KCNXCFG?", timeout, ["OK"])
        pdp_state = rsp.split(",")[-1].split("\r\n")[0]

        # pdp_state = 2 (connected)
        if pdp_state == "2":
            print("\n-- PDP connection already established --\n")
            target_at.run_at_cmd("AT+KHTTPCNX=1", timeout, ["OK", r"\+KHTTP_IND:\s1,1"])
        else:
            print("\n-- New PDP connection --\n")
            target_at.run_at_cmd("AT+KHTTPCNX=1", timeout, ["OK", r"\+KCNX_IND:\s1", r"\+KHTTP_IND:\s1,1"])
        target_at.run_at_cmd("AT+KHTTPCFG?", timeout, [r"\+KHTTPCFG:\s1,1,\"%s\",%s,2,\"\",\"\",1,0,0" %(https_server,https_port),"OK"])

        if "RC51" in HARD_INI:
            target_at.run_at_cmd("AT+KHTTPDELETE=1,\"/delete\"", timeout,["json","OK"])
        else:
            target_at.run_at_cmd("AT+KHTTPDELETE=1,\"/delete\"", timeout,["CONNECT","200 OK",r"\"url\": \"https://%s/delete\"" %https_server,"OK",r"\+KHTTP_IND: ?,?"])

        target_at.run_at_cmd("AT+KHTTPGET=1,\"/get\"", timeout,["CONNECT","200 OK",r"\"url\": \"https://%s/get\"" %https_server,"OK",r"\+KHTTP_IND: 1,3,\d+,200,\"OK\""])
        target_at.run_at_cmd("AT+KHTTPHEAD=1,\"/get\"", timeout, ["CONNECT","200 OK",r"\+KHTTP_IND: 1,3,\d+,200,\"OK\""])
        target_at.run_at_cmd("AT+KHTTPHEADER=1", timeout, ["CONNECT"])
        target_at.run_at_cmd("Content-Length: 10\r\n--EOF--Pattern--\r\n", timeout, ["OK"])
        target_at.run_at_cmd("AT+KHTTPHEADER?", timeout,[r"\+KHTTPHEADER: 1,1", "Content-Length: 10", "OK"])
        target_at.run_at_cmd("AT+KHTTPPOST=1,,\"/post\"", timeout,["CONNECT"])
        target_at.run_at_cmd("1234567890\r\n", timeout,["200 OK",r"\"data\":\s\"1234567890\"",r"\"url\": \"https://%s/post\"" %https_server,"OK",r"\+KHTTP_IND: 1,3,12,200,\"OK\""])
        target_at.run_at_cmd("AT+KHTTPPUT=1,,\"/put\"", timeout,["CONNECT"])
        target_at.run_at_cmd("1234567890\r\n", timeout,["200 OK",r"\"data\":\s\"1234567890\"",r"\"url\": \"https://%s/put\"" %https_server,"OK",r"\+KHTTP_IND: 1,3,12,200,\"OK\""])

        target_at.run_at_cmd("AT+KHTTPCLOSE=1", timeout, ["NO CARRIER|OK"])
        target_at.run_at_cmd("AT+KHTTPDEL=1", timeout, ["OK"])

        swilog.info( "\n----- Testing End -----\n")

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

swilog.info( "\n----- Program End -----\n")
