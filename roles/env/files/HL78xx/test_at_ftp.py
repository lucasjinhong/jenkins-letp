import string
import random
import pytest
import time
import swilog
import pexpect
import VarGlobal
import ast
from autotest import *

swilog.info( "\n----- Program start -----\n")

def ftp_cleanup_func(target_at):
    print("\n===================================================")
    print("Performing ftp connection cleanup START...")
    print("===================================================\n")
    rsp = target_at.run_at_cmd("AT+KFTPCFG?", 20, ["OK"])
    for cfg in rsp.split('\r\n'):
        if "KFTPCFG:" in cfg:
            _ = cfg.split(',')
            cfg_num = _[0].replace('+KFTPCFG: ', '')
            if _[-2] == '1':
                target_at.run_at_cmd("AT+KFTPCLOSE=%s" % cfg_num, 20, ["OK"])
            else:
                target_at.run_at_cmd("AT+KFTPCFGDEL=%s" % cfg_num, 20, ["OK"])
    print("\n===================================================")
    print("Performing ftp connection cleanup END...")
    print("===================================================\n")

@pytest.fixture
def ftp_cleanup(target_at):
    ftp_cleanup_func(target_at)
    yield
    ftp_cleanup_func(target_at)

def string_generator(size):
    """
    Function to generate a random string of characters of size input
    """
    chars = string.ascii_uppercase + string.ascii_lowercase
    return ''.join(random.choice(chars) for _ in range(size))

# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_FTP_0000(target_at, read_config, network_tests_setup_teardown, ftp_cleanup):
    """
    Check FTP AT Commands. Nominal/Valid use case
    """
    print("\nA_HL_INT_FTP_0000 TC Start:\n")
    test_environment_ready = "Ready"
    print("\n------------Test's preambule Start------------")

    phase = int(read_config.findtext("autotest/Features_PHASE"))
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)
    if phase < 2:
        pytest.skip("Phase < 2 : No AT+KFTPxxx commands")

    # Variable Init
    timeout = 15
    IMSI = read_config.findtext("autotest/SIM_IMSI")
    Network = read_config.findtext("autotest/Network")
    #if "sierra" in str.lower(Network) or "telus" in str.lower(Network):
    #    ftp_filename = "files/kftp/test_" + IMSI + ".txt"
    #else:
    #    ftp_filename = "test_" + IMSI + ".txt"
    #Modify for TPE FTP server
    if "sierra" in str.lower(Network) or "telus" in str.lower(Network):
        ftp_filename = "files/kftp/test_" + IMSI + ".txt"
    else:
        ftp_filename = "files/test_" + IMSI + ".txt"
    ftp_server = read_config.findtext("autotest/IntegrationVMServer")
    ftp_username = read_config.findtext("autotest/ftp_username")
    ftp_passwd = read_config.findtext("autotest/ftp_passwd")
    if not ftp_server or not ftp_username or not ftp_passwd:
        raise Exception("---->Problem: Enter your FTP SERVER configs in autotest.xml")

    SIM_GPRS_APN = ast.literal_eval(read_config.findtext("autotest/Network_APN"))[0]
    SIM_GPRS_LOGIN = ast.literal_eval(read_config.findtext("autotest/Network_APN_login"))[0]
    SIM_GPRS_PASSWORD = ast.literal_eval(read_config.findtext("autotest/Network_APN_password"))[0]
    PARAM_GPRS_PDP = ast.literal_eval(read_config.findtext("autotest/Network_PDP_type"))[0]
    Config_Name = read_config.findtext("autotest/Network_Config/Config_Name")

    # Module Init
    target_at.run_at_cmd("ate0", timeout,["OK"])
    target_at.run_at_cmd("AT&K3\r\n", timeout,["OK\r\n"])
    target_at.run_at_cmd("AT+CMEE=1", timeout, ["OK"])
    target_at.run_at_cmd("AT+CGMR", timeout, ["OK"])
    target_at.run_at_cmd("AT+CREG=2", timeout, ["OK"])
    target_at.run_at_cmd("AT+CEREG=2", timeout, ["OK"])

    test_nb = ""
    test_ID = "A_HL_INT_FTP_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        swilog.info( "\n----- Testing Start -----\n")

        # Check FTP AT Test Commands
        #For HL780x & HL781x
        target_at.run_at_cmd("AT+KFTPCFG=?", timeout, [r"\+KFTPCFG:\s\(1-2\),<remote-name\/ip>,\(0-64\),\(0-64\),\(1-65535\),\(0-1\),\(0-1\),\(0-1\)", "OK"])
        target_at.run_at_cmd("AT+KFTPCNX=?", timeout, [r"\+KFTPCNX:\s\(1-6\)","OK"])
        if Soft_Version < "05.00.00.00":
            target_at.run_at_cmd("AT+KFTPRCV=?", timeout, [r"\+KFTPRCV:\s\(1-2\),<local_uri>,<server_path>,<file_name>,\(0\),\(0-4294967295\),\(0-4294967295\)", "OK"])
        else:
            target_at.run_at_cmd("AT+KFTPRCV=?", timeout, [r"\+KFTPRCV:\s\(1-6\),<local_uri>,<server_path>,<file_name>,\(0\),\(0-4294967295\),\(0-4294967295\)", "OK"])
        if Soft_Version < "05.00.00.00":
            target_at.run_at_cmd("AT+KFTPSND=?", timeout, [r"\+KFTPSND:\s\(1-2\),<local_uri>,<server_path>,<file_name>,\(0\),\(0-1\),\(0-4294967295\),\(0-4294967295\)", "OK"])
        else:
            target_at.run_at_cmd("AT+KFTPSND=?", timeout, [r"\+KFTPSND:\s\(1-6\),<local_uri>,<server_path>,<file_name>,\(0\),\(0-1\),\(0-4294967295\),\(0-4294967295\)", "OK"])
        target_at.run_at_cmd("AT+KFTPCLOSE=?", timeout, [r"\+KFTPCLOSE:\s\(1-6\),\(0-1\)", "OK"])
        target_at.run_at_cmd("AT+KFTPDEL=?", timeout, [r"\+KFTPDEL:\s\(1-6\),<server_path>,<file_name>,\(0\)", "OK"])
        target_at.run_at_cmd("AT+KFTPCFGDEL=?", timeout, [r"\+KFTPCFGDEL:\s\(1-6\)", "OK"])
        target_at.run_at_cmd("AT+KFTPLS=?", timeout, [r"\+KFTPLS:\s\(1-6\),<server_path>,<file_name>,\(0\)", "OK"])

        # Add FTP CFG
        target_at.run_at_cmd("AT+CGDCONT=1,\"%s\",\"%s\"" % (PARAM_GPRS_PDP, SIM_GPRS_APN), timeout, ["OK"])
        target_at.run_at_cmd("AT+KCNXCFG=1,\"GPRS\",\"%s\",\"%s\",\"%s\"" % (SIM_GPRS_APN, SIM_GPRS_LOGIN, SIM_GPRS_PASSWORD), timeout, ["OK"])
        target_at.run_at_cmd("AT+KFTPCFG=1,\"%s\",\"%s\",\"%s\",,1,0,0" %(ftp_server,ftp_username,ftp_passwd), timeout, [r"\+KFTPCFG:\s1", "OK\r\n"])
        target_at.run_at_cmd("AT+KFTPCFG?", timeout, [r"\+KFTPCFG:\s1,1,\"%s\",\"%s\",\"\",21,1,0,0" %(ftp_server,ftp_username), "OK\r\n"])

        # Setup FTP Connection
        target_at.run_at_cmd("AT+KFTPCNX=1", timeout, ["OK", r"\+KCNX_IND:\s1,1,0", r"\+KFTP_IND:\s1,1"])
        target_at.run_at_cmd("AT+KFTPCFG?", timeout, [r"\+KFTPCFG:\s1,1,\"%s\",\"%s\",\"\",21,1,1,0" %(ftp_server,ftp_username), "OK\r\n"])

        # Check File Existence on FTP Server
        #rsp = target_at.run_at_cmd("AT+KFTPLS=1,,\"%s\"\r" %ftp_filename, timeout, ["OK|KFTP_ERROR"])
        rsp = target_at.run_at_cmd("AT+KFTPLS=1,,\"%s\"\r" %ftp_filename, timeout, ["OK|KFTP_ERROR"])

        if "+KFTPLS: %s" %ftp_filename in rsp:
            target_at.run_at_cmd("AT+KFTPDEL=1,,\"%s\"" %ftp_filename, timeout, ["OK", r"\+KFTP_IND:\s1,2"])
            target_at.run_at_cmd("AT+KFTPLS=1,,\"%s\"" %ftp_filename, timeout, [r"\+KFTP_ERROR:\s1,*"])

        # Send File to FTP Server
        _ = target_at.run_at_cmd("AT+KPATTERN?",timeout,["OK"])
        pattern_string = re.findall(r'\+KPATTERN: "(.*?)"',_)

        # List of different data sizes to test FTP send/receive
        if Soft_Version < "04.00.00.00":
            ftp_data = [string_generator(10)]
        #Modify for HL780x.4.6.9.x
        elif Soft_Version < "05.00.00.00":
            ftp_data = [string_generator(10), string_generator(100), string_generator(500)]
        else:
            ftp_data = [string_generator(10), string_generator(100), string_generator(1000)]

        for content in ftp_data:

            try:
                swilog.info("FTP Data Size: %i" % len(content))
                target_at.run_at_cmd("AT+KFTPSND=1,,,\"%s\"" %ftp_filename, timeout, ["\r\nCONNECT\r\n"])
                target_at.run_at_cmd("%s%s" %(content, pattern_string[0]), timeout * 2, ["OK\r\n", r"\+KFTP_IND:\s1,2,%d\r\n" %len(content)])
                time.sleep(10) # Need delay until file is ready on remote FTP server.

                # List File Size from FTP Server
                target_at.run_at_cmd("AT+KFTPLS=1,,\"%s\"" %ftp_filename, timeout, [r"\+KFTPLS:\s%s\s%d\r\n" %(ftp_filename, len(content))])

                # Receive File from FTP Server
                target_at.run_at_cmd("AT+KFTPRCV=1,,,\"%s\"" %ftp_filename, timeout, ["CONNECT", content, "OK\r\n", r"\+KFTP_IND:\s1,2,%d\r\n" %len(content)])

                #Delete File from FTP Server
                target_at.run_at_cmd("AT+KFTPDEL=1,,\"%s\"" %ftp_filename, timeout, ["OK", r"\+KFTP_IND:\s1,2"])
                target_at.run_at_cmd("AT+KFTPLS=1,,\"%s\"" %ftp_filename, timeout, [r"\+KFTP_ERROR:\s1,*"])
                time.sleep(2)
            except:
                swilog.error("Module failed to FTP transfer data size: %i" % len(content))
                VarGlobal.statOfItem = "NOK"

        # Disconect FTP Connection
        target_at.run_at_cmd("AT+KFTPCLOSE=1,1", timeout, ["OK"])
        target_at.run_at_cmd("AT+KFTPCFG?", timeout, [r"\+KFTPCFG:\s1,1,\"%s\",\"%s\",\"\",21,1,0,0" %(ftp_server,ftp_username), "OK"])

        # Delete FTP CFG
        target_at.run_at_cmd("AT+KFTPCFGDEL=1", timeout, ["OK"])
        target_at.run_at_cmd("AT+KFTPCFG?", timeout, ["OK"])

        swilog.info( "\n----- Testing End -----\n")

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

swilog.info( "\n----- Program End -----\n")
