"""
Sanity test script to monitor HL78 memory behaviour from cmux testing

Tests:
AT Commands Test on CMUX0, CMUX1, CMUX2.

File Transfer over PPP Connection on CMUX3.

"""
from time import (strftime, sleep)
import os
from os import path
import pexpect
import pytest
import VarGlobal
import swilog
import ast
from autotest import (PRINT_START_FUNC, PRINT_TEST_RESULT)
from autotest import pytestmark  # noqa # pylint: disable=unused-import
from autotest import SWI_Reset_Module
from hl78_memory_lib import (collect_swiheap, collect_meminfo)

timeout = 15
AT_CMD_List = ["AT", "ATI", "ATI3", "ATI9", "AT+COPS?"]
datetime = strftime("%Y%m%d_%H%M%S")

def AT_CMD_Tests(com, network_apn):
    """
    Function to execute common AT commands
    """
    try:
        print("Run common AT Read/Test commands\n")
        com.run_at_cmd("ATI", timeout, ["OK"])
        com.run_at_cmd("ATI3", timeout, ["OK"])
        com.run_at_cmd("ATI9", timeout, ["OK"])
        com.run_at_cmd("AT+CGMR", timeout, ["OK"])
        com.run_at_cmd("AT+CMEE?", timeout, ["OK"])
        com.run_at_cmd("AT+KSRAT?", timeout, ["OK"])
        com.run_at_cmd("AT+CGDCONT?", timeout, ["OK"])
        com.run_at_cmd("AT+KBNDCFG?", timeout, ["OK"])
        com.run_at_cmd("AT+COPS?", timeout, ["OK"])
        com.run_at_cmd("AT+CSQ", timeout, ["OK"])
        com.run_at_cmd("AT+CREG?", timeout, ["OK"])
        com.run_at_cmd("AT+CREG=?", timeout, ["OK"])
        com.run_at_cmd("AT+CEREG?", timeout, ["OK"])
        com.run_at_cmd("AT+CEREG=?", timeout, ["OK"])
        com.run_at_cmd("AT+KCNXTIMER?", timeout, ["OK"])
        com.run_at_cmd("AT+KCNXTIMER=?", timeout, ["OK"])
        com.run_at_cmd("AT+KTCPCFG?", timeout, ["OK"])
        com.run_at_cmd("AT+KTCPCFG=?", timeout, ["OK"])
        com.run_at_cmd("AT+KTCPSTAT?", timeout, ["OK"])
        com.run_at_cmd("AT+KUDPCFG?", timeout, ["OK"])
        com.run_at_cmd("AT+KUDPCFG=?", timeout, ["OK"])
        com.run_at_cmd("AT+KFTPCFG?", timeout, ["OK"])
        com.run_at_cmd("AT+KFTPCFG=?", timeout, ["OK"])
        com.run_at_cmd("AT+KHTTPCFG?", timeout, ["OK"])
        com.run_at_cmd("AT+KHTTPCFG=?", timeout, ["OK"])
        com.run_at_cmd("AT+WPPP?", timeout, ["OK"])
        com.run_at_cmd("AT+WPPP=?", timeout, ["OK"])
        com.run_at_cmd("AT+CFUN?", timeout, ["OK"])
        com.run_at_cmd("AT+CFUN=?", timeout, ["OK"])
        com.run_at_cmd("AT+CPIN?", timeout, ["OK"])
        com.run_at_cmd("AT+CPIN=?", timeout, ["OK"])
        com.run_at_cmd("AT+CCLK?", timeout, ["OK"])
        com.run_at_cmd("AT+CCLK=?", timeout, ["OK"])
        com.run_at_cmd("AT+KSLEEP?", timeout, ["OK"])
        com.run_at_cmd("AT+KSLEEP=?", timeout, ["OK"])
        com.run_at_cmd("AT+WDSC?", timeout, ["OK"])
        com.run_at_cmd("AT+WDSC=?", timeout, ["OK"])
        com.run_at_cmd("AT+WDSS?", timeout, ["OK"])
        com.run_at_cmd("AT+WDSS=?", timeout, ["OK"])
        com.run_at_cmd("AT+WDSI?", timeout, ["OK"])
        com.run_at_cmd("AT+WDSI=?", timeout, ["OK"])
        sleep(2)

        print("\n\nRun AT Write commands to set up IP testing\n")
        com.run_at_cmd("AT&V", timeout, ["OK"])
        com.run_at_cmd("AT&K3", timeout, ["OK"])
        com.run_at_cmd("AT+KIPOPT=0,\"TCPC\",20,100", timeout, ["OK"])
        com.run_at_cmd("AT+KIPOPT=0,\"TCPS\",20,200", timeout, ["OK"])
        com.run_at_cmd("AT+KIPOPT=0,\"UDP\",20,300", timeout, ["OK"])
        com.run_at_cmd("AT+KIPOPT=0,\"HTTP\",20,100", timeout, ["OK"])
        com.run_at_cmd("AT+KIPOPT=0,\"HTTPS\",20,100", timeout, ["OK"])
        com.run_at_cmd("AT+KIPOPT=0,\"TCP\",1,0", timeout, ["OK"])
        com.run_at_cmd("AT+KIPOPT=0,\"UDP\",2,1020", timeout, ["OK"])
        com.run_at_cmd("AT+KIPOPT=0,\"HTTP\",1,0", timeout, ["OK"])
        com.run_at_cmd("AT+KIPOPT=0,\"HTTPS\",1,0", timeout, ["OK"])
        com.run_at_cmd("AT+KURCCFG=?", timeout, ["OK"])
        com.run_at_cmd("AT+KURCCFG?", timeout, ["OK"])
        com.run_at_cmd("AT+KURCCFG=\"TCPC\",1,0", timeout, ["OK"])
        com.run_at_cmd("AT+KURCCFG=\"TCPS\",0,1", timeout, ["OK"])
        com.run_at_cmd("AT+KURCCFG=\"UDP\",0,0", timeout, ["OK"])
        com.run_at_cmd("AT+KURCCFG=\"HTTP\",0,1", timeout, ["OK"])
        com.run_at_cmd("AT+KURCCFG=\"HTTPS\",1,0", timeout, ["OK"])
        com.run_at_cmd("AT+KURCCFG?", timeout, ["OK"])
        com.run_at_cmd("AT+KURCCFG=\"TCP\",1,1", timeout, ["OK"])
        com.run_at_cmd("AT+KURCCFG=\"UDP\",1,1", timeout, ["OK"])
        com.run_at_cmd("AT+KURCCFG=\"HTTP\",1,1", timeout, ["OK"])
        com.run_at_cmd("AT+KURCCFG=\"HTTPS\",1,1", timeout, ["OK"])
        com.run_at_cmd("AT+KCNXTIMER=1,30,2,60,30", timeout, ["OK"])
        com.run_at_cmd("AT+CGATT=0", timeout, ["OK"])
        com.run_at_cmd("AT+CGDCONT=1,\"IP\",\"" + network_apn + "\"", timeout, ["OK"])
        com.run_at_cmd("AT+CGATT=1", timeout, ["OK"])
        com.run_at_cmd("AT+KCNXCFG=1,\"GPRS\",\"" + network_apn + "\",\"\",\"\"", timeout, ["OK"])
        sleep(2)

    except AssertionError:
        raise Exception("AT command failure!!!")


@pytest.fixture()
def mem_cmux_setup_teardown(find_cli_port, network_tests_setup_teardown,
                            target_cli, target_at, read_config):
    """Test case setup and teardown."""

    global HARD_INI, report_dir, hostnetworkif, rootpassword

    report_dir = path.expandvars('$LETP_WRAPPER_ATTACHMENTS')
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    if not SOFT_INI_Soft_Version.split(".")[-1] == "98":
        pytest.skip("Version is not .98 - swiheap command is not available on current version")
    hostnetworkif = read_config.findtext("host/network_if")
    rootpassword = read_config.findtext("autotest/Sudo")
    if not rootpassword:
        raise Exception("---->Problem: Enter your rootpassword \
                        in 'Sudo' field in autotest.xml for ppp management")
    network = read_config.findtext("autotest/Network")

    # Reset module before test start
    print("Reset module before test to collect initial memory data...")
    SWI_Reset_Module(target_at, HARD_INI)

    # Setup network settings
    state = network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    print("\nA_HL_MEM_CMUX_0000 TC Start:\n")

    print("\n------------Test's preambule Start------------")

    # Capture 'Before' meminfo
    collect_meminfo(target_cli, report_dir, HARD_INI + '_cmux_meminfo_before_' + datetime)

    # Start swiheap logging
    target_cli.send("swiheap startLog\r\n")
    collect_swiheap(target_cli, report_dir, HARD_INI + '_cmux_swiheap_data_' + datetime)

    test_nb = ""
    test_ID = "A_HL_MEM_CMUX_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Testing Start------------")

    yield test_ID

    print("\n----- Mem CMUX TearDown -----\n")

    # sleep to wait for killing of CMUX virtual ports
    sleep(2)

    # Set back host network interface
    command = 'sudo -S ifconfig %s up' % hostnetworkif
    swilog.info(command)
    os.system('echo "%s" | ' % rootpassword + command)
    sleep(2)

    print("\n\n------------- Capture End of Test Data ----------------\n")

    # Send AT commands to generate end of test swiheap log dump
    for cmd in AT_CMD_List:
        target_at.run_at_cmd(cmd, timeout, ["OK"])
        sleep(5)

    collect_swiheap(target_cli, report_dir, HARD_INI + '_cmux_swiheap_data_' + datetime, note="Cleanup", analysis=True)

    print("\n\n-------------------------------------------------------\n")

    # Capture 'After' meminfo
    collect_meminfo(target_cli, report_dir, HARD_INI + '_cmux_meminfo_after_' + datetime)

    # Reset module after test end
    SWI_Reset_Module(target_at, HARD_INI)


def A_HL_MEM_CMUX_0000(mem_cmux_setup_teardown,
                       read_config, target_cli, target_at,
                       target_cmux0, target_cmux1,
                       target_cmux2, target_cmux3):
    """
    Run AT Command tests and PPP/FTP test on various cmux channels
    """
    test_ID = mem_cmux_setup_teardown

    # Variable Init
    count = 0
    cmux_ports = [target_cmux0, target_cmux1, target_cmux2, target_cmux3]
    IMSI = read_config.findtext("autotest/SIM_IMSI")
    network = read_config.findtext("autotest/Network")
    if "sierra" in str.lower(network) or "telus" in str.lower(network):
        ftp_filename = "files/kftp/test_" + IMSI + ".txt"
    else:
        ftp_filename = "test_" + IMSI + ".txt"
    network_apn = ast.literal_eval(read_config.findtext("autotest/Network_APN"))[0]
    ftp_server = read_config.findtext("autotest/IntegrationVMServer")
    ftp_username = read_config.findtext("autotest/ftp_username")
    ftp_passwd = read_config.findtext("autotest/ftp_passwd")
    slink = read_config.findtext("module/slink7/name")
    Serial_BaudRate = read_config.findtext("module/slink7/speed")
    DeviceLocalIPAddress = read_config.findtext("autotest/DeviceLocalIPAddress")
    if not (ftp_server or ftp_username or ftp_passwd):
        VarGlobal.statOfItem = "NOK"
        raise Exception("---->Problem: Missing parameters in xml files")

    try:

        for target_cmux in cmux_ports:

            # Run AT Commands test on cmux0, cmux1 and cmux2
            if target_cmux != target_cmux3:
                print("\n\n----------------- Test %i: CMUX%i - AT Commands ----------------------\n"
                      % ((count + 1), count))

                # Print out current CMUX port
                swilog.info("Test CMUX Port: %s" % target_cmux)

                # Execute list of AT Commands
                AT_CMD_Tests(target_cmux, network_apn)

            # Run FTP over PPP connection test on cmux3
            else:
                try:
                    print("\n\n-------- Test %i: CMUX%i - File Transfer over PPP Connection ---------\n"
                          % ((count + 1), count))

                    # Cut host network interface before PPP establishment
                    target_cmux3.close()
                    command = 'sudo -S ifconfig %s down' % hostnetworkif
                    swilog.info(command)
                    os.system('echo "%s" | ' % rootpassword + command)
                    sleep(1)

                    # PPP establishment
                    command = 'sudo -S \
                               $LETP_TESTS/tools/Create_DialUpNoComp.sh \
                               hl78xx %s 1 %s' %(slink, Serial_BaudRate)
                    swilog.info(command)
                    os.system('echo "%s" | ' % rootpassword + command)
                    sleep(2)

                    command = 'sudo -S $LETP_TESTS/tools/Start_Stop_Dialup.sh 1 hl78xx'
                    swilog.info(command)
                    os.system('echo "%s" | ' % rootpassword + command)
                    sleep(5)

                    # Send ping with ppp0 to device
                    command = 'ping -c 4 -i 1 "%s"' % DeviceLocalIPAddress
                    swilog.info(command)
                    rsp = pexpect.run(command)
                    swilog.info(rsp.decode())
                    sleep(5)

                    # Connect to device with FTP
                    command = 'ftp -n "%s"' % DeviceLocalIPAddress
                    swilog.info(command)
                    child = pexpect.spawn(command)
                    child.expect([pexpect.TIMEOUT, 'unreachable', 'ftp> '])
                    swilog.info((child.before).decode() + (child.after).decode())
                    sleep(5)
                    child.sendline('disconnect')
                    swilog.info('disconnect')
                    child.sendline('exit')
                    swilog.info('exit')
                    sleep(1)

                    # Connect to integration FTP server and perform file upload/download
                    command = 'ftp "%s"' % ftp_server
                    swilog.info(command)
                    child = pexpect.spawn(command)
                    child.expect([pexpect.TIMEOUT, 'Name .*:'])
                    child.sendline(ftp_username)
                    print((child.before).decode() + (child.after).decode())
                    child.expect([pexpect.TIMEOUT, 'Password:'])
                    child.sendline(ftp_passwd)
                    print((child.before).decode() + (child.after).decode())
                    child.expect([pexpect.TIMEOUT, 'ftp> '])
                    child.sendline('pass')
                    print((child.before).decode() + (child.after).decode())
                    child.expect([pexpect.TIMEOUT, 'ftp> '])
                    child.sendline('put ' + ftp_filename)
                    print((child.before).decode() + (child.after).decode())
                    child.expect([pexpect.TIMEOUT, 'ftp> '])
                    child.sendline('ls')
                    print((child.before).decode() + (child.after).decode())
                    child.expect([pexpect.TIMEOUT, 'ftp> '])
                    child.sendline('get ' + ftp_filename)
                    print((child.before).decode() + (child.after).decode())
                    child.expect([pexpect.TIMEOUT, 'ftp> '])
                    child.sendline('ls')
                    print((child.before).decode() + (child.after).decode())
                    child.expect([pexpect.TIMEOUT, 'ftp> '])
                    sleep(5)
                    child.sendline('disconnect')
                    swilog.info('disconnect')
                    child.sendline('exit')
                    swilog.info('exit')
                    sleep(1)

                    # Stop ppp0 link
                    command = 'sudo -S $LETP_TESTS/tools/Start_Stop_Dialup.sh 0 hl78xx'
                    swilog.info(command)
                    os.system('echo "%s" | ' % rootpassword + command)
                    sleep(5)

                    # Set back host network interface
                    command = 'sudo -S ifconfig %s up' % hostnetworkif
                    swilog.info(command)
                    os.system('echo "%s" | ' % rootpassword + command)
                    sleep(2)
                except AssertionError:
                    swilog.error("PPP test failure, continue to next test...")
                    VarGlobal.statOfItem = "NOK"

            count += 1


        # Capture swiheap dump
        collect_swiheap(target_cli, report_dir, HARD_INI + '_cmux_swiheap_data_' + datetime, note="cmux" + str(count))
        sleep(2)

    except Exception as err_msg:  # pylint: disable=broad-except
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
