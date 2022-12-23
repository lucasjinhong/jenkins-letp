"""
Sanity test script to monitor HL78 memory from various network related tests.

Tests:
TCP (2000B) -> UDP (2000B) -> FTP (15B) -> HTTP/HTTPS -> PPP -> NVBU -> GNSS.

"""
from time import (strftime, sleep)
import os
from os import path
import re
import string
import random
import pexpect
import pytest
import VarGlobal
import swilog
import ast
from autotest import (PRINT_START_FUNC, PRINT_TEST_RESULT, two_digit_fw_version)
from autotest import pytestmark  # noqa # pylint: disable=unused-import
from autotest import SWI_Reset_Module
from hl78_memory_lib import (collect_swiheap, collect_meminfo)

timeout = 15
http_server = "httpbin.org"
http_port = 80
https_port = 443
END_CODE = "--EOF--Pattern--"
AT_CMD_List = ["AT", "ATI", "ATI3", "ATI9", "AT+COPS?"]
datetime = strftime("%Y%m%d_%H%M%S")

def string_generator(size):
    """
    Function to generate a random string of characters of size input
    """
    chars = string.ascii_uppercase + string.ascii_lowercase
    return ''.join(random.choice(chars) for _ in range(size))


@pytest.fixture()
def mem_network_setup_teardown(find_cli_port, network_tests_setup_teardown,
                               target_cli, target_at, read_config):
    """Test case setup and teardown."""

    global HARD_INI, Soft_Version, report_dir, hostnetworkif, rootpassword

    # Variable Init
    report_dir = path.expandvars('$LETP_WRAPPER_ATTACHMENTS')
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)
    if not SOFT_INI_Soft_Version.split(".")[-1] == "98":
        pytest.skip("Version is not .98 - swiheap command is not available on current version")
    hostnetworkif = read_config.findtext("host/network_if")
    network_apn = ast.literal_eval(read_config.findtext("autotest/Network_APN"))[0]
    rootpassword = read_config.findtext("autotest/Sudo")

    if not rootpassword:
        raise Exception("---->Problem: Enter your rootpassword \
                        in 'Sudo' field in autotest.xml for ppp management")
    network = read_config.findtext("autotest/Network")

    # Enable GNSS setting
    target_at.run_at_cmd("AT%SETACFG=locsrv.operation.locsrv_enable,true", timeout, ["OK"])

    # Reset module before test start
    print("Reset module before test to collect initial memory data...")
    SWI_Reset_Module(target_at, HARD_INI)

    # Setup network settings
    state = network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    print("\nA_HL_MEM_NETWORK_0000 TC Start:\n")

    print("\n------------Test's preambule Start------------")

    # Capture 'Before' meminfo
    collect_meminfo(target_cli, report_dir, HARD_INI + '_meminfo_before_' + datetime)

    # Start swiheap logging
    target_cli.send("swiheap startLog\r\n")

    # Set up module for tests
    print("\n\n----------------- Test Setup ----------------------\n")

    target_at.run_at_cmd("AT&V", timeout, ["OK"])
    target_at.run_at_cmd("AT&K3", timeout, ["OK"])
    target_at.run_at_cmd("AT+KIPOPT=0,\"TCPC\",20,100", timeout, ["OK"])
    target_at.run_at_cmd("AT+KIPOPT=0,\"TCPS\",20,200", timeout, ["OK"])
    target_at.run_at_cmd("AT+KIPOPT=0,\"UDP\",20,300", timeout, ["OK"])
    target_at.run_at_cmd("AT+KIPOPT=0,\"HTTP\",20,100", timeout, ["OK"])
    target_at.run_at_cmd("AT+KIPOPT=0,\"HTTPS\",20,100", timeout, ["OK"])
    target_at.run_at_cmd("AT+KIPOPT=0,\"TCP\",1,0", timeout, ["OK"])
    target_at.run_at_cmd("AT+KIPOPT=0,\"UDP\",2,1020", timeout, ["OK"])
    target_at.run_at_cmd("AT+KIPOPT=0,\"HTTP\",1,0", timeout, ["OK"])
    target_at.run_at_cmd("AT+KIPOPT=0,\"HTTPS\",1,0", timeout, ["OK"])
    target_at.run_at_cmd("AT+KURCCFG=?", timeout, ["OK"])
    target_at.run_at_cmd("AT+KURCCFG?", timeout, ["OK"])
    target_at.run_at_cmd("AT+KURCCFG=\"TCPC\",1,0", timeout, ["OK"])
    target_at.run_at_cmd("AT+KURCCFG=\"TCPS\",0,1", timeout, ["OK"])
    target_at.run_at_cmd("AT+KURCCFG=\"UDP\",0,0", timeout, ["OK"])
    target_at.run_at_cmd("AT+KURCCFG=\"HTTP\",0,1", timeout, ["OK"])
    target_at.run_at_cmd("AT+KURCCFG=\"HTTPS\",1,0", timeout, ["OK"])
    target_at.run_at_cmd("AT+KURCCFG?", timeout, ["OK"])
    target_at.run_at_cmd("AT+KURCCFG=\"TCP\",1,1", timeout, ["OK"])
    target_at.run_at_cmd("AT+KURCCFG=\"UDP\",1,1", timeout, ["OK"])
    target_at.run_at_cmd("AT+KURCCFG=\"HTTP\",1,1", timeout, ["OK"])
    target_at.run_at_cmd("AT+KURCCFG=\"HTTPS\",1,1", timeout, ["OK"])
    target_at.run_at_cmd("AT+KCNXTIMER=1,30,2,60,30", timeout, ["OK"])
    target_at.run_at_cmd("AT+CGATT=0", timeout, ["OK"])
    target_at.run_at_cmd("AT+CGDCONT=1,\"IP\",\"" + network_apn + "\"", timeout, ["OK"])

    target_at.run_at_cmd("AT+CGATT=1", timeout, ["OK"])
    target_at.run_at_cmd("AT+KCNXCFG=1,\"GPRS\",\"" + network_apn + "\",\"\",\"\"", timeout, ["OK"])
    sleep(2)

    # Capture initial swiheap dump
    collect_swiheap(target_cli, report_dir, HARD_INI + '_swiheap_data_' + datetime)

    test_nb = ""
    test_ID = "A_HL_MEM_NETWORK_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Testing Start------------")

    yield test_ID

    print("\n----- Mem Network TearDown -----\n")

    # Set back host network interface
    Command = 'sudo -S ifconfig %s up' % hostnetworkif
    swilog.info(Command)
    os.system('echo "%s" | ' % rootpassword + Command)
    sleep(2)

    # Capture 'After' meminfo
    collect_meminfo(target_cli, report_dir, HARD_INI + '_meminfo_after_' + datetime)

    # Reset module after test end
    SWI_Reset_Module(target_at, HARD_INI)


def A_HL_MEM_NETWORK_0000(mem_network_setup_teardown,
                          read_config,
                          target_cli, target_at,
                          tcp_server, udp_server):
    """
    Run common network related tests and monitor memory
    """
    test_ID = mem_network_setup_teardown

    # Variable Init
    DATA_EXCHANGED = string_generator(2000)
    nData = len(DATA_EXCHANGED)
    https_cert = os.path.expandvars("$LETP_TESTS/config/cert/cert")
    Network = read_config.findtext("autotest/Network")
    IMSI = read_config.findtext("autotest/SIM_IMSI")
    if "sierra" in str.lower(Network) or "telus" in str.lower(Network):
        ftp_filename = "files/kftp/test_" + IMSI + ".txt"
        PARAM_HL_ECHO_SERVER_IP = read_config.findtext("autotest/legato_flake_server")
        PARAM_HL_TCP_ECHO_PORT = read_config.findtext("autotest/flake_echo_port")
        PARAM_HL_UDP_ECHO_PORT = read_config.findtext("autotest/flake_echo_port")
    else:
        # Modify for TPE FTP server
        #ftp_filename = "test_" + IMSI + ".txt"
        ftp_filename = "files/test_" + IMSI + ".txt"

        PARAM_HL_ECHO_SERVER_IP = read_config.findtext("host/ip_address")
        PARAM_HL_TCP_ECHO_PORT = read_config.findtext("host/socket_server/tcp_1/port")
        PARAM_HL_UDP_ECHO_PORT = read_config.findtext("host/socket_server/udp_1/port")
    ftp_server = read_config.findtext("autotest/IntegrationVMServer")
    ftp_username = read_config.findtext("autotest/ftp_username")
    ftp_passwd = read_config.findtext("autotest/ftp_passwd")
    slink2 = read_config.findtext("module/slink2/name")
    Serial_BaudRate = read_config.findtext("module/slink2/speed")
    AmarisoftIPAddress = read_config.findtext("autotest/AmarisoftIPAddress")
    DeviceLocalIPAddress = read_config.findtext("autotest/DeviceLocalIPAddress")
    if not (ftp_server or ftp_username or ftp_passwd):
        VarGlobal.statOfItem = "NOK"
        raise Exception("---->Problem: Missing FTP parameters in autotest.xml")

    try:
        print("\n\n----------------- Test 1: TCP ----------------------\n")

        try:
            target_at.run_at_cmd("AT+KTCPCFG=1,0,\"" + PARAM_HL_ECHO_SERVER_IP + "\","
                                       + PARAM_HL_TCP_ECHO_PORT, timeout, [r"\+KTCPCFG:\s\d", "OK"])
            rsp = target_at.run_at_cmd("AT+KTCPCFG?", timeout, ["OK"])
            session_id = rsp.split("+KTCPCFG: ")[-1].split(",")[0]
            target_at.run_at_cmd("AT+KTCPSTAT=" + session_id, timeout,
                                       [r"\+KTCPSTAT:\s1,-1,0,0", "OK"])
            target_at.run_at_cmd("AT+KTCPCNX=" + session_id, timeout, ["OK"])
            target_at.run_at_cmd("AT+KTCPSTAT=" + session_id, timeout,
                                       [r"\+KTCPSTAT:\s2,-1,0,0", "OK",
                                        r"\+KTCP_IND:\s" + session_id + ",1"])
            target_at.run_at_cmd("AT+KTCPSND=" + session_id + "," + str(nData), timeout,
                                       ["CONNECT"])
            rsp = target_at.run_at_cmd(DATA_EXCHANGED + END_CODE, timeout,
                                             ["OK", r"\+KTCP_DATA:\s" + session_id + r",\d+"])
            tcp_data = rsp.split("+KTCP_DATA: ")[-1].split(",")[-1]
            rsp = target_at.run_at_cmd("AT+KTCPRCV=" + session_id + "," + tcp_data, timeout,
                                             ["CONNECT", "OK", r"\+KTCP_DATA:\s"
                                              + session_id + r",\d+"])
            tcp_data = rsp.split("+KTCP_DATA: ")[-1].split(",")[-1]
            rsp = target_at.run_at_cmd("AT+KTCPRCV=" + session_id + "," + tcp_data, timeout,
                                             ["CONNECT", "OK"])
            target_at.run_at_cmd("AT+KTCPCLOSE=" + session_id + ",1", timeout,
                                       ["OK"])
            target_at.run_at_cmd("AT+KTCPDEL=" + session_id, timeout, ["OK"])
        except AssertionError:
            swilog.error("TCP test failed, continue to next test...")
            VarGlobal.statOfItem = "NOK"

        collect_swiheap(target_cli, report_dir, HARD_INI + '_swiheap_data_' + datetime, note="TCP")
        sleep(2)

        print("\n\n----------------- Test 2: UDP ----------------------\n")

        try:
            target_at.run_at_cmd("AT+KUDPCFG=1,0,1234", timeout,
                                       [r"\+KUDPCFG:\s\d", "OK", r"\+KUDP_IND:\s\d,1"])
            rsp = target_at.run_at_cmd("AT+KUDPCFG?", timeout, ["OK"])
            session_id = rsp.split("+KUDPCFG: ")[-1].split(",")[0]
            target_at.run_at_cmd("AT+KCGPADDR=1", timeout, ["OK"])
            target_at.run_at_cmd("AT+KUDPSND=" + session_id + ",\""
                                       + PARAM_HL_ECHO_SERVER_IP + "\"," + PARAM_HL_UDP_ECHO_PORT
                                       + "," + str(nData), timeout,
                                       ["CONNECT"])
            rsp = target_at.run_at_cmd(DATA_EXCHANGED + END_CODE, timeout,
                                             ["OK", r"\+KUDP_DATA:\s" + session_id + r",\d+"])
            udp_data = rsp.split("+KUDP_DATA: ")[-1].split(",")[-1]
            rsp = target_at.run_at_cmd("AT+KUDPRCV=" + session_id + "," + udp_data, timeout,
                                             ["CONNECT", "OK", r"\+KUDP_DATA:\s"
                                              + session_id + r",\d+"])
            udp_data = rsp.split("+KUDP_DATA: ")[-1].split(",")[-1]
            rsp = target_at.run_at_cmd("AT+KUDPRCV=" + session_id + "," + udp_data, timeout,
                                             ["CONNECT", "OK"])
            target_at.run_at_cmd("AT+KUDPCLOSE=" + session_id + ",1", timeout, ["OK"])
            target_at.run_at_cmd("AT+KUDPDEL=" + session_id, timeout, ["OK"])
        except AssertionError:
            swilog.error("UDP test failed, continue to next test...")
            VarGlobal.statOfItem = "NOK"

        collect_swiheap(target_cli, report_dir, HARD_INI + '_swiheap_data_' + datetime, note="UDP")
        sleep(2)

        print("\n\n----------------- Test 3: FTP ----------------------\n")

        try:
            target_at.run_at_cmd("AT+KFTPCFG=1,\"%s\",\"%s\",\"%s\",,1,0,0"
                                       % (ftp_server, ftp_username, ftp_passwd),
                                       timeout, ["OK"])
            rsp = target_at.run_at_cmd("AT+KFTPCFG?", timeout, ["OK"])
            session_id = rsp.split("+KFTPCFG: ")[-1].split(",")[0]
            target_at.run_at_cmd("AT+KFTPCNX=" + session_id, timeout,
                                       ["OK", r"\+KFTP_IND:\s" + session_id + ",1"])
            target_at.run_at_cmd("AT+KFTPCFG?", timeout,
                                       [r"\+KFTPCFG:\s" + session_id +
                                        ",1,\"%s\",\"%s\",\"\",21,1,1,0"
                                        % (ftp_server, ftp_username), "OK\r\n"])
            _ = target_at.run_at_cmd("AT+KPATTERN?", timeout, ["OK"])
            pattern_string = re.findall(r'\+KPATTERN: "(.*?)"', _)
            content = "Hello, Vancouver"
            target_at.run_at_cmd("AT+KFTPSND=" + session_id
                                       + ",,,\"%s\"" % ftp_filename, timeout,
                                       ["\r\nCONNECT\r\n"])
            target_at.run_at_cmd("%s%s" % (content, pattern_string[0]), timeout,
                                       ["OK\r\n", r"\+KFTP_IND:\s" + session_id
                                        + ",2,%d\r\n" % len(content)])
            sleep(10) # Delay until file is ready on remote server
            target_at.run_at_cmd("AT+KFTPLS=" + session_id
                                       + ",,\"%s\"" % ftp_filename, timeout,
                                       [r"\+KFTPLS:\s%s\s%d\r\n" % (ftp_filename, len(content))])
            target_at.run_at_cmd("AT+KFTPRCV=" + session_id
                                       + ",,,\"%s\"" % ftp_filename, timeout,
                                       ["CONNECT", content, "OK\r\n",
                                        r"\+KFTP_IND:\s" + session_id
                                        + ",2,%d\r\n" % len(content)])
            target_at.run_at_cmd("AT+KFTPDEL=" + session_id
                                       + ",,\"%s\"" % ftp_filename, timeout,
                                       ["OK", r"\+KFTP_IND:\s" + session_id + ",2"])
            target_at.run_at_cmd("AT+KFTPLS=" + session_id
                                       + ",,\"%s\"" % ftp_filename, timeout,
                                       [r"\+KFTP_ERROR:\s" + session_id + ",*"])

            target_at.run_at_cmd("AT+KFTPCLOSE=" + session_id + ",1", timeout, ["OK"])
            target_at.run_at_cmd("AT+KFTPCFGDEL=" + session_id, timeout, ["OK"])
        except AssertionError:
            swilog.error("FTP test failed, continue to next test...")
            VarGlobal.statOfItem = "NOK"

        collect_swiheap(target_cli, report_dir, HARD_INI + '_swiheap_data_' + datetime, note="FTP")
        sleep(2)

        print("\n\n----------------- Test 4: HTTP ----------------------\n")

        try:
            # Check HTTP AT Read/Write Commands
            target_at.run_at_cmd("AT+KHTTPCFG=1,\"%s\",%s,0,\"\",\"\",0,0,0"
                                       % (http_server, http_port), timeout,
                                       ["OK"])
            rsp = target_at.run_at_cmd("AT+KHTTPCFG?", timeout, ["OK"])
            session_id = rsp.split("+KHTTPCFG: ")[-1].split(",")[0]
            target_at.run_at_cmd("AT+KHTTPCFG?", timeout,
                                       [r"\+KHTTPCFG:\s" + session_id
                                        + ",1,\"%s\",%s,0,\"\",\"\",0,0,0"
                                        % (http_server, http_port), "OK"])
            target_at.run_at_cmd("AT+KHTTPCNX=" + session_id, timeout,
                                       ["OK", r"\+KHTTP_IND:\s" + session_id + ",1"])
            target_at.run_at_cmd("AT+KHTTPDELETE=" + session_id + ",\"/delete\"", timeout,
                                       ["CONNECT", "200 OK", r"\"url\": \"http://%s/delete\"" % http_server,
                                        "OK", r"\+KHTTP_IND: ?,?"])
            target_at.run_at_cmd("AT+KHTTPGET=" + session_id + ",\"/get\"", timeout,
                                       ["CONNECT", "200 OK", r"\"url\": \"http://%s/get\"" % http_server,
                                        "OK", r"\+KHTTP_IND: " + session_id + r",3,\d+,200,\"OK\""])
            target_at.run_at_cmd("AT+KHTTPHEAD=" + session_id + ",\"/get\"", timeout,
                                       ["CONNECT", "200 OK", r"\+KHTTP_IND: " + session_id
                                        + r",3,\d+,200,\"OK\""])
            target_at.run_at_cmd("AT+KHTTPHEADER=" + session_id, timeout, ["CONNECT"])
            target_at.run_at_cmd("Content-Length: 10\r\n--EOF--Pattern--\r\n")
            target_at.run_at_cmd("AT+KHTTPHEADER?", timeout,
                                       [r"\+KHTTPHEADER: " + session_id + ",1", "Content-Length: 10", "OK"])
            target_at.run_at_cmd("AT+KHTTPPOST=" + session_id + ",,\"/post\"", timeout,
                                       ["CONNECT"])
            target_at.run_at_cmd("1234567890\r\n", timeout,
                                       ["200 OK", r"\"data\":\s\"1234567890\"",
                                        r"\"url\": \"http://%s/post\"" % http_server, "OK",
                                        r"\+KHTTP_IND: " + session_id + ",3,12,200,\"OK\""])

            target_at.run_at_cmd("AT+KHTTPPUT=" + session_id + ",,\"/put\"", timeout,
                                       ["CONNECT"])
            target_at.run_at_cmd("1234567890\r\n", timeout,
                                       ["200 OK", r"\"data\":\s\"1234567890\"",
                                        r"\"url\": \"http://%s/put\"" % http_server,
                                        "OK", r"\+KHTTP_IND: 1,3,12,200,\"OK\""])
            target_at.run_at_cmd("AT+KHTTPCLOSE=" + session_id, timeout, ["NO CARRIER|OK"])
            target_at.run_at_cmd("AT+KHTTPDEL=" + session_id, timeout, ["OK"])
        except AssertionError:
            swilog.error("HTTP test failed, continue to next test...")
            VarGlobal.statOfItem = "NOK"

        collect_swiheap(target_cli, report_dir, HARD_INI + '_swiheap_data_' + datetime, note="HTTP")
        sleep(2)

        print("\n\n----------------- Test 5: HTTPS ----------------------\n")

        # Install HTTPS Certificate
        try:
            # Keep DOS like newlines
            with open(https_cert, "rb") as file:
                cert = file.read().decode()
        except:
            raise Exception("https certificate file %s can not be read" % https_cert)

        try:
            # Install HTTPS Certificate
            target_at.run_at_cmd("AT+KCERTDELETE=0", timeout, ["OK"])
            target_at.run_at_cmd("AT+KCERTSTORE=0,%d" % len(cert), timeout, ["CONNECT\r\n"])
            target_at.run_at_cmd(cert + "--EOF--Pattern--\r\n", timeout + 10)

            # Check HTTPS AT Read/Write Commands
            target_at.run_at_cmd("AT+KHTTPCFG=1,\"%s\",%s,2,\"\",\"\",0,0,0"
                                       % (http_server, https_port), timeout, ["OK"])
            rsp = target_at.run_at_cmd("AT+KHTTPCFG?", timeout, ["OK"])
            session_id = rsp.split("+KHTTPCFG: ")[-1].split(",")[0]
            target_at.run_at_cmd("AT+KHTTPCFG?", timeout,
                                       [r"\+KHTTPCFG:\s" + session_id
                                        + ",1,\"%s\",%s,2,\"\",\"\",0,0,0"
                                        % (http_server, https_port), "OK"])
            target_at.run_at_cmd("AT+KHTTPCNX=" + session_id, timeout * 4,
                                       ["OK", r"\+KHTTP_IND:\s" + session_id + ",1"])
            target_at.run_at_cmd("AT+KHTTPDELETE=" + session_id + ",\"/delete\"", timeout,
                                       ["CONNECT", "200 OK", r"\"url\": \"https://%s/delete\"" % http_server,
                                        "OK", r"\+KHTTP_IND: ?,?"])
            target_at.run_at_cmd("AT+KHTTPGET=" + session_id + ",\"/get\"", timeout,
                                       ["CONNECT", "200 OK", r"\"url\": \"https://%s/get\"" % http_server,
                                        "OK", r"\+KHTTP_IND: " + session_id + r",3,\d+,200,\"OK\""])
            target_at.run_at_cmd("AT+KHTTPHEAD=" + session_id + ",\"/get\"", timeout,
                                       ["CONNECT","200 OK",
                                        r"\+KHTTP_IND: " + session_id + r",3,\d+,200,\"OK\""])
            target_at.run_at_cmd("AT+KHTTPHEADER=" + session_id, timeout, ["CONNECT"])
            target_at.run_at_cmd("Content-Length: 10\r\n--EOF--Pattern--\r\n", timeout, ["OK"])
            target_at.run_at_cmd("AT+KHTTPHEADER?", timeout,
                                       [r"\+KHTTPHEADER: " + session_id + ",1",
                                        "Content-Length: 10", "OK"])
            target_at.run_at_cmd("AT+KHTTPPOST=" + session_id
                                       + ",,\"/post\"", timeout, ["CONNECT"])
            target_at.run_at_cmd("1234567890\r\n", timeout,
                                       ["200 OK", r"\"data\":\s\"1234567890\"",
                                        r"\"url\": \"https://%s/post\"" % http_server,"OK",
                                        r"\+KHTTP_IND: " + session_id + ",3,12,200,\"OK\""])
            target_at.run_at_cmd("AT+KHTTPPUT=" + session_id
                                       + ",,\"/put\"", timeout, ["CONNECT"])
            target_at.run_at_cmd("1234567890\r\n", timeout,
                                       ["200 OK", r"\"data\":\s\"1234567890\"",
                                        r"\"url\": \"https://%s/put\"" % http_server, "OK",
                                        r"\+KHTTP_IND: 1,3,12,200,\"OK\""])
            target_at.run_at_cmd("AT+KHTTPCLOSE=" + session_id, timeout, ["NO CARRIER|OK"])
            target_at.run_at_cmd("AT+KHTTPDEL=" + session_id, timeout, ["OK"])
        except AssertionError:
            swilog.error("HTTPS test failed, continue to next test...")
            VarGlobal.statOfItem = "NOK"

        collect_swiheap(target_cli, report_dir, HARD_INI + '_swiheap_data_' + datetime, note="HTTPS")
        sleep(2)

        print("\n\n----------------- Test 6: PPP ----------------------\n")

        try:
            # close UART
            target_at.close()
            # Cut host network interface before PPP establishment
            Command = 'sudo -S ifconfig %s down' % hostnetworkif
            swilog.info(Command)
            os.system('echo "%s" | ' % rootpassword + Command)
            sleep(2)

            # PPP establishment
            Command = 'sudo -S \
                       $LETP_TESTS/tools/Create_DialUpNoComp.sh \
                       hl78xx %s 1 %s' %(slink2, Serial_BaudRate)
            swilog.info(Command)
            os.system('echo "%s" | ' % rootpassword + Command)
            sleep(2)

            Command = 'sudo -S $LETP_TESTS/tools/Start_Stop_Dialup.sh 1 hl78xx'
            swilog.info(Command)
            os.system('echo "%s" | ' % rootpassword + Command)
            sleep(5)

            # Send ping with ppp0 to Amarisoft
            if "amarisoft" in Network:
                Command = 'ping -c 4 -i 1 "%s"' % AmarisoftIPAddress
                swilog.info(Command)
                rsp = pexpect.run(Command)
                swilog.info(rsp)
                sleep(1)

            # Connect to device with FTP
            Command = 'ftp -n "%s"' % DeviceLocalIPAddress
            swilog.info(Command)
            child = pexpect.spawn(Command)
            child.expect([pexpect.TIMEOUT, 'unreachable', 'ftp> '])
            swilog.info(child.before + child.after)
            sleep(5)
            child.sendline('disconnect')
            swilog.info('disconnect')
            child.sendline('exit')
            swilog.info('exit')
            sleep(1)

            # Send ping with ppp0 to Amarisoft
            Command = 'ping -c 4 -i 1 "%s"' % AmarisoftIPAddress
            swilog.info(Command)
            rsp = pexpect.run(Command)
            swilog.info(rsp)
            sleep(1)

            # Stop ppp0 link
            Command = 'sudo -S $LETP_TESTS/tools/Start_Stop_Dialup.sh 0 hl78xx'
            swilog.info(Command)
            os.system('echo "%s" | ' % rootpassword + Command)
            sleep(5)

            # Set back host network interface
            Command = 'sudo -S ifconfig %s up' % hostnetworkif
            swilog.info(Command)
            os.system('echo "%s" | ' % rootpassword + Command)
            sleep(2)

            # reinit UART and wait for connection to establish
            target_at.reinit()
            sleep(5)

        except AssertionError:
            swilog.error("PPP test failed, continue to next test...")
            VarGlobal.statOfItem = "NOK"

        collect_swiheap(target_cli, report_dir, HARD_INI + '_swiheap_data_' + datetime, note="PPP")
        sleep(2)

        print("\n\n----------------- Test 7: NVBU ----------------------\n")

        try:
            print("\n---------- Perform Erase backup log ----------\n")
            target_at.run_at_cmd("AT+NVBU=2,1", timeout, ["OK"])

            print("\n---------- Perform +NVBU backup ----------\n")
            for part_id in range(4):
                target_at.run_at_cmd("AT+NVBU=0," + str(part_id), timeout * 2,
                                           ["OK", r"\+NVBU\_IND:\s0,0,0,*"])
                collect_swiheap(target_cli, report_dir, HARD_INI + '_swiheap_data_' + datetime)

            print("\n---------- Perform Read backup log ----------\n")
            target_at.run_at_cmd("AT+NVBU=2,0", timeout,
                                       [r"NVB\sgeneration\ssuccess*",
                                        r"NVB\sgeneration\ssuccess*",
                                        r"NVB\sgeneration\ssuccess*",
                                        r"NVB\sgeneration\ssuccess*"])

        except AssertionError:
            swilog.error("NVBU test failed, continue to next test...")
            VarGlobal.statOfItem = "NOK"

        collect_swiheap(target_cli, report_dir, HARD_INI + '_swiheap_data_' + datetime, note="NVBU")
        sleep(2)

        # Unable to run on RK_02_01_02 (EURY-2607)
        if Soft_Version >= "05.03.00.00":
            print("\n\n----------------- Test 8: GNSS ----------------------\n")

            try:
                target_at.run_at_cmd("AT+CFUN=0", timeout, ["OK"])
                target_at.run_at_cmd("AT+GNSSCONF=?", timeout, [r"\+GNSSCONF:\s10,\(0-1\)", "OK"])
                target_at.run_at_cmd("AT+GNSSNMEA=?", timeout,
                                           [r"\+GNSSNMEA:\s\(0,1,3-8\),\(1000\),\(0\),\(1FF\)", "OK"])
                target_at.run_at_cmd("AT+GNSSSTART=?", timeout, [r"\+GNSSSTART: \(0-3\)", "OK"])
                target_at.run_at_cmd("AT+GNSSNMEA=0,1000,0,1FF")
                loop = 0

                # Test: GPS and GLONASS
                for gtype in range(0, 2):
                    target_at.run_at_cmd("AT+GNSSCONF=10,%s" % str(gtype), timeout, ["OK"])
                    target_at.run_at_cmd("AT+GNSSCONF?", timeout,
                                               [r"\+GNSSCONF: 10,%s" % str(gtype), "OK"])

                    # Test: AUTO, WARM, COLD, FACTORY modes
                    for mode in range(0, 4):
                        loop += 1

                        # Start GNSS Session
                        target_at.run_at_cmd("AT+GNSSSTART=%s" % str(mode), timeout, ["OK"])
                        collect_swiheap(target_cli, report_dir, HARD_INI + '_swiheap_data_' + datetime)
                        swilog.info(" ")
                        swilog.info("Searching 2 min for GNSS signal... (Loop %i/8)" % loop)
                        swilog.info(" ")

                        # Collect swiheap every 30s during GNSS session
                        for i in range(4):
                            collect_swiheap(target_cli, report_dir, HARD_INI + '_swiheap_data_' + datetime)
                            sleep(30)

                        # Stop GNSS Session
                        target_at.run_at_cmd("AT+GNSSSTOP", timeout, ["OK"])
                        collect_swiheap(target_cli, report_dir, HARD_INI + '_swiheap_data_' + datetime)

                # Reconnect to network and perform analysis on swiheap_data
                target_at.run_at_cmd("AT+CFUN=1", timeout, ["OK"])

            except AssertionError:
                swilog.error("GNSS test failed, continue to end of test...")
                VarGlobal.statOfItem = "NOK"

            collect_swiheap(target_cli, report_dir, HARD_INI + '_swiheap_data_' + datetime, note="GNSS")
            sleep(2)

        print("\n\n------------- Capture End of Test Data ----------------\n")

        # Send AT commands to generate end of test swiheap log dump
        for cmd in AT_CMD_List:
            target_at.run_at_cmd(cmd, timeout, ["OK"])
            sleep(5)

        collect_swiheap(target_cli, report_dir, HARD_INI + '_swiheap_data_' + datetime, note="Cleanup", analysis=True)

        print("\n\n-----------------------------------------------------\n")

    except Exception as err_msg:  # pylint: disable=broad-except
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
