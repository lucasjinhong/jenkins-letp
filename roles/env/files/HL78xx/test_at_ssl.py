import os
import pytest
import swilog
import VarGlobal
from autotest import *

swilog.info("\n----- Program start -----\n")

timeout = 15

@pytest.fixture
def datamode_cleanup(target_cli, target_at, read_config):

    HARD_INI = read_config.findtext("autotest/HARD_INI")
    EOF = "--EOF--Pattern--"

    yield

    if "HL78" in HARD_INI:
        print("\n===========================================================================")
        print("\nPerforming script cleanup... Verify the module exits from data session:\n")
        print("===========================================================================")
        try:
            target_at.run_at_cmd(EOF, timeout, ["ERROR"])
        except:
            print("\nRebooting module...")
            SagSendAT(target_cli, 'reset\r')
            SagSleep(Booting_Duration)
            # Unlock module
            SagSendAT(target_at, "AT!UNLOCK=\"A710\"\r")
            SagWaitnMatchResp(target_at, ["OK|ERROR"], 5000)

# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_SSL_0000(datamode_cleanup, target_at, read_config, non_network_tests_setup_teardown):
    """
    Check SSL AT Commands. Nominal/Valid use case
    """
    print("\nA_HL_INT_SSL_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)
    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase < 2:
        pytest.skip("Phase < 2 : No AT+KSSLxxx commands")

    if "HL78" in HARD_INI and Soft_Version <= "04.00.00.00":
        default_auth = "0"
        rsa_key_size = "3000"
    else:
        default_auth = "1"
        rsa_key_size = "4096"

    # Modify for HL78xx newly version
    # if "HL78" in HARD_INI and "04.06.00.00" <= Soft_Version < "05.05.00.00":
    if "HL78" in HARD_INI and "04.06.00.00" <= Soft_Version:
        profile_ids = 8
        default_root_cert_idx = "0"
        root_cert_idx_range = 4
    else:
        profile_ids = 16

    cert = os.path.expandvars("$LETP_TESTS/config/cert/cert")
    privkey = os.path.expandvars("$LETP_TESTS/config/key/key")
    tls_ver = 1.2
    invalid = "123456789"
    EOF = "--EOF--Pattern--\r\n"

    if "HL78" in HARD_INI and "04.05.00.00" <= Soft_Version < "04.06.00.00":
        supported_cipher_suites = {
            'TLS-RSA-WITH-AES-128-CCM'                  :    ['1','1','16','0','4','1','0'],
            'TLS-RSA-WITH-AES-256-GCM-SHA384'           :    ['1','1','16384','8','4','1','0'],
            'TLS-RSA-WITH-AES-128-CCM-8'                :    ['1','1','256','0','4','1','0'],
            'TLS-RSA-WITH-AES-256-CCM'                  :    ['1','1','32','0','4','1','0'],
            'TLS-RSA-WITH-AES-256-CCM-8'                :    ['1','1','512','0','4','1','0'],
            'TLS-RSA-WITH-AES-128-GCM-SHA256'           :    ['1','1','8192','4','4','1','0'],
            'TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA256'     :    ['8','1','64','4','4','1','0'],
            'TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256'     :    ['8','1','8192','4','4','1','0'],
            'TLS-ECDHE-ECDSA-WITH-AES-128-CCM'          :    ['8','2','16','0','4','1','0'],
            'TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384'   :    ['8','2','16384','8','4','1','0'],
            'TLS-ECDHE-ECDSA-WITH-AES-128-CCM-8'        :    ['8','2','256','0','4','1','0'],
            'TLS-ECDHE-ECDSA-WITH-AES-256-CCM'          :    ['8','2','32','0','4','1','0'],
            'TLS-ECDHE-ECDSA-WITH-AES-256-CCM-8'        :    ['8','2','512','0','4','1','0'],
            'TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA256'   :    ['8','2','64','4','4','1','0'],
            'TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256'   :    ['8','2','8192','4','4','1','0']
        }
    # Modify for HL78xx newly version
    # elif "HL78" in HARD_INI and "04.06.00.00" <= Soft_Version < "05.05.00.00":
    elif "HL78" in HARD_INI and "04.06.00.00" <= Soft_Version:
        supported_cipher_suites = {
            'TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256'     :    ['8','1','8192','4','4','1'],
            'TLS-ECDHE-ECDSA-WITH-AES-128-CCM'          :    ['8','2','16','0','4','1'],
            'TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384'   :    ['8','2','16384','8','4','1'],
            'TLS-ECDHE-ECDSA-WITH-AES-128-CCM-8'        :    ['8','2','256','0','4','1'],
            'TLS-ECDHE-ECDSA-WITH-AES-256-CCM'          :    ['8','2','32','0','4','1'],
            'TLS-ECDHE-ECDSA-WITH-AES-256-CCM-8'        :    ['8','2','512','0','4','1'],
            'TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256'   :    ['8','2','8192','4','4','1']
        }
    else:
        supported_cipher_suites = {
            'TLS-RSA-WITH-AES-128-CCM'                  :    ['1','1','16','0','4','1'],
            'TLS-RSA-WITH-AES-256-GCM-SHA384'           :    ['1','1','16384','8','4','1'],
            'TLS-RSA-WITH-AES-128-CCM-8'                :    ['1','1','256','0','4','1'],
            'TLS-RSA-WITH-AES-256-CCM'                  :    ['1','1','32','0','4','1'],
            'TLS-RSA-WITH-AES-256-CCM-8'                :    ['1','1','512','0','4','1'],
            'TLS-RSA-WITH-AES-128-GCM-SHA256'           :    ['1','1','8192','4','4','1'],
            'TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA256'     :    ['8','1','64','4','4','1'],
            'TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256'     :    ['8','1','8192','4','4','1'],
            'TLS-ECDHE-ECDSA-WITH-AES-128-CCM'          :    ['8','2','16','0','4','1'],
            'TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384'   :    ['8','2','16384','8','4','1'],
            'TLS-ECDHE-ECDSA-WITH-AES-128-CCM-8'        :    ['8','2','256','0','4','1'],
            'TLS-ECDHE-ECDSA-WITH-AES-256-CCM'          :    ['8','2','32','0','4','1'],
            'TLS-ECDHE-ECDSA-WITH-AES-256-CCM-8'        :    ['8','2','512','0','4','1'],
            'TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA256'   :    ['8','2','64','4','4','1'],
            'TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256'   :    ['8','2','8192','4','4','1']
        }

    if "HL78" in HARD_INI and "04.05.00.00" <= Soft_Version < "04.06.00.00":
        default_cipher_suites = {
            'TLS-RSA-WITH-AES-128-CCM'                  :    '1,1,1,16,0,4,1,0',
            'TLS-ECDHE-ECDSA-WITH-AES-256-CCM'          :    '10,8,2,32,0,4,1,0',
            'TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA256'   :    '11,8,2,64,4,4,1,0',
            'TLS-ECDHE-ECDSA-WITH-AES-128-CCM-8'        :    '12,8,2,256,0,4,1,0',
            'TLS-ECDHE-ECDSA-WITH-AES-256-CCM-8'        :    '13,8,2,512,0,4,1,0',
            'TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256'   :    '14,8,2,8192,4,4,1,0',
            'TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384'   :    '15,8,2,16384,8,4,1,0',
            'TLS-RSA-WITH-AES-256-CCM'                  :    '2,1,1,32,0,4,1,0',
            'TLS-RSA-WITH-AES-128-CCM-8'                :    '3,1,1,256,0,4,1,0',
            'TLS-RSA-WITH-AES-256-CCM-8'                :    '4,1,1,512,0,4,1,0',
            'TLS-RSA-WITH-AES-128-GCM-SHA256'           :    '5,1,1,8192,4,4,1,0',
            'TLS-RSA-WITH-AES-256-GCM-SHA384'           :    '6,1,1,16384,8,4,1,0',
            'TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA256'     :    '7,8,1,64,4,4,1,0',
            'TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256'     :    '8,8,1,8192,4,4,1,0',
            'TLS-ECDHE-ECDSA-WITH-AES-128-CCM'          :    '9,8,2,16,0,4,1,0'
        }
    # Modify for HL78xx newly version
    #elif "HL78" in HARD_INI and "04.06.00.00" <= Soft_Version < "05.05.00.00":
    elif "HL78" in HARD_INI and "04.06.00.00" <= Soft_Version:
        default_cipher_suites = {
            'TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256'     :    '1,8,1,8192,4,4,1,0',
            'TLS-ECDHE-ECDSA-WITH-AES-128-CCM'          :    '2,8,2,16,0,4,1,0',
            'TLS-ECDHE-ECDSA-WITH-AES-256-CCM'          :    '3,8,2,32,0,4,1,0',
            'TLS-ECDHE-ECDSA-WITH-AES-128-CCM-8'        :    '4,8,2,256,0,4,1,0',
            'TLS-ECDHE-ECDSA-WITH-AES-256-CCM-8'        :    '5,8,2,512,0,4,1,0',
            'TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256'   :    '6,8,2,8192,4,4,1,0',
            'TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384'   :    '7,8,2,16384,8,4,1,0'
        }
    else:
        default_cipher_suites = {
            'TLS-RSA-WITH-AES-128-CCM'                  :    '1,1,1,16,0,4,1',
            'TLS-ECDHE-ECDSA-WITH-AES-256-CCM'          :    '10,8,2,32,0,4,1',
            'TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA256'   :    '11,8,2,64,4,4,1',
            'TLS-ECDHE-ECDSA-WITH-AES-128-CCM-8'        :    '12,8,2,256,0,4,1',
            'TLS-ECDHE-ECDSA-WITH-AES-256-CCM-8'        :    '13,8,2,512,0,4,1',
            'TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256'   :    '14,8,2,8192,4,4,1',
            'TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384'   :    '15,8,2,16384,8,4,1',
            'TLS-RSA-WITH-AES-256-CCM'                  :    '2,1,1,32,0,4,1',
            'TLS-RSA-WITH-AES-128-CCM-8'                :    '3,1,1,256,0,4,1',
            'TLS-RSA-WITH-AES-256-CCM-8'                :    '4,1,1,512,0,4,1',
            'TLS-RSA-WITH-AES-128-GCM-SHA256'           :    '5,1,1,8192,4,4,1',
            'TLS-RSA-WITH-AES-256-GCM-SHA384'           :    '6,1,1,16384,8,4,1',
            'TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA256'     :    '7,8,1,64,4,4,1',
            'TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256'     :    '8,8,1,8192,4,4,1',
            'TLS-ECDHE-ECDSA-WITH-AES-128-CCM'          :    '9,8,2,16,0,4,1'
        }

    # Module Init
    target_at.run_at_cmd("ATE1", timeout, ["OK"])
    target_at.run_at_cmd("AT+CMEE=1", timeout, ["OK"])

    test_nb = ""
    test_ID = "A_HL_INT_SSL_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        swilog.info("\n----- Testing Start -----\n")
        #------------ Verify AT+KSSLCRYPTO Test, Read, and Write Commands ------------
        print("\n------------ Verify AT+KSSLCRYPTO Test, Read, and Write Commands ------------\n")
        # Modify for HL78xx newly version
        # if "HL78" in HARD_INI and "04.06.00.00" <= Soft_Version < "05.05.00.00":
        if "HL78" in HARD_INI and "04.06.00.00" <= Soft_Version:
            target_at.run_at_cmd("AT+KSSLCRYPTO=?", timeout, [r"\+KSSLCRYPTO:\s<profile_id>,<mkey_Algo>,<auth_algo>,<enc_algo>,<mac_algo>,<tls_ver>,<auth>","<root_cert_idx>","OK"])
        else:
            target_at.run_at_cmd("AT+KSSLCRYPTO=?", timeout, [r"\+KSSLCRYPTO:\s<profile_id>,<mkey_Algo>,<auth_algo>,<enc_algo>,<mac_algo>,<tls_ver>,<auth>", "OK"])

        # Modify for HL78xx newly version
        # if "HL78" in HARD_INI and "04.06.01.00" <= Soft_Version < "05.05.00.00":
        if "HL78" in HARD_INI and "04.06.01.00" <= Soft_Version:
            target_at.run_at_cmd("AT+KSSLCRYPTO?", timeout, [r"\+KSSLCRYPTO:\s0,8,3,25392,12,4," + default_auth + "," + default_root_cert_idx, \
                                                          r"\+KSSLCRYPTO:\s1,8,1,8192,4,4," + default_auth + "," + default_root_cert_idx, \
                                                          r"\+KSSLCRYPTO:\s2,8,2,16,0,4," + default_auth + "," + default_root_cert_idx, \
                                                          r"\+KSSLCRYPTO:\s3,8,2,32,0,4," + default_auth + "," + default_root_cert_idx, \
                                                          r"\+KSSLCRYPTO:\s4,8,2,256,0,4," + default_auth + "," + default_root_cert_idx, \
                                                          r"\+KSSLCRYPTO:\s5,8,2,512,0,4," + default_auth + "," + default_root_cert_idx, \
                                                          r"\+KSSLCRYPTO:\s6,8,2,8192,4,4," + default_auth + "," + default_root_cert_idx, \
                                                          r"\+KSSLCRYPTO:\s7,8,2,16384,8,4," + default_auth + "," + default_root_cert_idx, "OK"])
        elif "HL78" in HARD_INI and "04.06.00.00" == Soft_Version:
            target_at.run_at_cmd("AT+KSSLCRYPTO?", timeout, [r"\+KSSLCRYPTO:\s0,8,3,25456,12,4," + default_auth + "," + default_root_cert_idx, \
                                                          r"\+KSSLCRYPTO:\s1,8,1,8192,4,4," + default_auth + "," + default_root_cert_idx, \
                                                          r"\+KSSLCRYPTO:\s2,8,2,16,0,4," + default_auth + "," + default_root_cert_idx, \
                                                          r"\+KSSLCRYPTO:\s3,8,2,32,0,4," + default_auth + "," + default_root_cert_idx, \
                                                          r"\+KSSLCRYPTO:\s4,8,2,256,0,4," + default_auth + "," + default_root_cert_idx, \
                                                          r"\+KSSLCRYPTO:\s5,8,2,512,0,4," + default_auth + "," + default_root_cert_idx, \
                                                          r"\+KSSLCRYPTO:\s6,8,2,8192,4,4," + default_auth + "," + default_root_cert_idx, \
                                                          r"\+KSSLCRYPTO:\s7,8,2,16384,8,4," + default_auth + ","  + default_root_cert_idx, "OK"])
        else:
            target_at.run_at_cmd("AT+KSSLCRYPTO?", timeout, [r"\+KSSLCRYPTO:\s0,9,3,25456,12,4," + default_auth,\
                                                          r"\+KSSLCRYPTO:\s1,1,1,16,0,4," + default_auth, \
                                                          r"\+KSSLCRYPTO:\s2,1,1,32,0,4," + default_auth, \
                                                          r"\+KSSLCRYPTO:\s3,1,1,256,0,4," + default_auth, \
                                                          r"\+KSSLCRYPTO:\s4,1,1,512,0,4," + default_auth, \
                                                          r"\+KSSLCRYPTO:\s5,1,1,8192,4,4," + default_auth, \
                                                          r"\+KSSLCRYPTO:\s6,1,1,16384,8,4," + default_auth, \
                                                          r"\+KSSLCRYPTO:\s7,8,1,64,4,4," + default_auth, \
                                                          r"\+KSSLCRYPTO:\s8,8,1,8192,4,4," + default_auth, \
                                                          r"\+KSSLCRYPTO:\s9,8,2,16,0,4," + default_auth,\
                                                          r"\+KSSLCRYPTO:\s10,8,2,32,0,4," + default_auth, \
                                                          r"\+KSSLCRYPTO:\s11,8,2,64,4,4," + default_auth, \
                                                          r"\+KSSLCRYPTO:\s12,8,2,256,0,4," + default_auth, \
                                                          r"\+KSSLCRYPTO:\s13,8,2,512,0,4," + default_auth, \
                                                          r"\+KSSLCRYPTO:\s14,8,2,8192,4,4," + default_auth, \
                                                          r"\+KSSLCRYPTO:\s15,8,2,16384,8,4," + default_auth, "OK"])
        # Verify Write command for all of the Supported Ciphor Suites - test on all profile_ids
        for profile_id in range(1, profile_ids):
            print("\n\n--- Testing on profile_id: %i ---\n" % profile_id)
            for i in sorted(supported_cipher_suites.values()):
                cipher_suite = ""
                for j in i:
                    cipher_suite+=','+j
                # Modify for HL78xx newly version
                # if "HL78" in HARD_INI and "04.06.00.00" <= Soft_Version < "05.05.00.00":
                if "HL78" in HARD_INI and "04.06.00.00" <= Soft_Version:
                    for root_cert_idx in range(1,root_cert_idx_range):
                        target_at.run_at_cmd("AT+KSSLCRYPTO="+str(profile_id)+cipher_suite+','+str(root_cert_idx), timeout, ["OK|ERROR"])
                else:
                    target_at.run_at_cmd("AT+KSSLCRYPTO="+str(profile_id)+cipher_suite, timeout, ["OK|ERROR"])
            time.sleep(1)
        print("\n\n-- Set all profile_id's to default --\n")
        # Set all profile_id's back to default values
        for i in sorted(default_cipher_suites.values()):
            target_at.run_at_cmd("AT+KSSLCRYPTO="+i, timeout, ["OK|ERROR"])

        #------------ Verify AT+KSSLCFG Test, Read, and Write Commands ------------
        print("\n------------ Verify AT+KSSLCFG Test, Read, and Write Commands ------------\n")
        target_at.run_at_cmd("AT+KSSLCFG=?", timeout, [r"\+KSSLCFG:\s<option\sid>,<option>", "OK"])
        target_at.run_at_cmd("AT+KSSLCFG?", timeout, [r"\+KSSLCFG:\s0,3", r"\+KSSLCFG:\s2,0", "OK"])

        # Set TLS version to be highest possible
        target_at.run_at_cmd("AT+KSSLCFG=0,0", timeout, ["OK"])
        if tls_ver > 1.2:
            # Update when higher version available
            target_at.run_at_cmd("AT+KSSLCFG?", timeout, [r"\+KSSLCFG:\s0,??", "OK"])
        else:
            target_at.run_at_cmd("AT+KSSLCFG?", timeout, [r"\+KSSLCFG:\s0,3", "OK"])

        target_at.run_at_cmd("AT+KSSLCFG=0,3", timeout, ["OK"])
        target_at.run_at_cmd("AT+KSSLCFG?", timeout, [r"\+KSSLCFG:\s0,3", "OK"])
        target_at.run_at_cmd("AT+KSSLCFG=1,\"string\"", timeout, ["OK"])
        target_at.run_at_cmd("AT+KSSLCFG?", timeout, [r"\+KSSLCFG:\s0,3", r"\+KSSLCFG:\s2,0", "OK"])
        target_at.run_at_cmd("AT+KSSLCFG=2,0", timeout, ["OK"])
        target_at.run_at_cmd("AT+KSSLCFG?", timeout, [r"\+KSSLCFG:\s2,0", "OK"])
        target_at.run_at_cmd("AT+KSSLCFG=2,1", timeout, [r"\+CME\sERROR:\s918"])

        #------------ Verify AT+KCERTSTORE Test, Read, and Write Commands ------------
        print("\n------------ Verify AT+KCERTSTORE Test, Read, and Write Commands ------------\n")
        # Clear existing certificates
        for i in range(2):
            target_at.run_at_cmd("AT+KCERTDELETE="+str(i), timeout, ["OK"])

        # Modify for HL78xx newly version
        # if "HL78" in HARD_INI and "04.05.00.00" <= Soft_Version < "05.05.00.00":
        if "HL78" in HARD_INI and "04.05.00.00" <= Soft_Version:
            target_at.run_at_cmd("AT+KCERTSTORE=?", timeout, [r"\+KCERTSTORE:\s\(0-1\),\(1-" + rsa_key_size + r"\),\(0-3\)", "OK"])
        else:
            target_at.run_at_cmd("AT+KCERTSTORE=?", timeout, [r"\+KCERTSTORE:\s\(0-1\),\(1-" + rsa_key_size + r"\),\(0-2\)", "OK"])
        target_at.run_at_cmd("AT+KCERTSTORE?", timeout, ["CONNECT", "root_cert,0,0", "local_cert,0,0", "local_cert,1,0", "local_cert,2,0", "OK"])

        # Read certificate contents
        try:
            with open(cert, "r") as f:
                cert_data = f.read()
        except:
            swilog.debug("certificate file %s cannot be read" % cert)
            raise

        # Verify storing the certificate as root certificate
        target_at.run_at_cmd("AT&K3", timeout, ["OK"])
        target_at.run_at_cmd("AT+KCERTSTORE=0,%d" % len(cert_data), timeout, ["CONNECT"])
        target_at.run_at_cmd(cert_data+EOF, timeout+10)
        target_at.run_at_cmd("AT+KCERTSTORE?", timeout, ["CONNECT", "root_cert,0,"+str(len(cert_data)), "local_cert,1,0", "local_cert,2,0", "OK"])
        # Verify storing the certificate as local certificate
        target_at.run_at_cmd("AT+KCERTSTORE=1,%d" % len(cert_data), timeout, ["CONNECT"])
        target_at.run_at_cmd(cert_data+EOF, timeout+10)
        target_at.run_at_cmd("AT+KCERTSTORE?", timeout, ["CONNECT", "root_cert,0,"+str(len(cert_data)), "local_cert,0,"+str(len(cert_data)), "local_cert,1,0", "local_cert,2,0", "OK"])

        # Verify storing an invalid certificate as a local and root certificate
        for i in range(2):
            # Certificate too short
            target_at.run_at_cmd("AT+KCERTSTORE=%i,%d" % (i, len(invalid)+1), timeout, ["CONNECT"])
            target_at.run_at_cmd(invalid, timeout, [r"\+CME\sERROR:\s930"])
            # Certificate invalid
            target_at.run_at_cmd("AT+KCERTSTORE=%i,%d" % (i, len(invalid)), timeout, ["CONNECT"])
            target_at.run_at_cmd(invalid, timeout, [r"\+CME\sERROR:\s931"])

        #------------ Verify AT+KPRIVKSTORE Test, Read, and Write Commands ------------
        # Clear existing keys
        for i in range(3):
            target_at.run_at_cmd("AT+KPRIVKDELETE="+str(i), timeout, ["OK"])

        print("\n------------ Verify AT+KPRIVKSTORE Test, Read, and Write Commands ------------\n")
        target_at.run_at_cmd("AT+KPRIVKSTORE=?", timeout, [r"\+KPRIVKSTORE:\s\(0-2\),\(1-" + rsa_key_size + r"\)", "OK"])
        target_at.run_at_cmd("AT+KPRIVKSTORE?", timeout, ["CONNECT", "private_key,0,0", "private_key,1,0", "private_key,2,0", "OK"])

        # Read private key contents
        try:
            with open(privkey, "r") as f:
                key = f.read()
        except:
            swilog.debug("private key file %s cannot be read" % privkey)
            raise

        # Verify storing the private key on index 0
        target_at.run_at_cmd("AT+KPRIVKSTORE=0,%d" % len(key), timeout, ["CONNECT"])
        target_at.run_at_cmd(key+EOF, timeout+10)
        target_at.run_at_cmd("AT+KPRIVKSTORE?", timeout, ["CONNECT", "private_key,0,"+str(len(key)), "private_key,1,0", "private_key,2,0", "OK"])

        # Verify storing the private key on the other indices
        target_at.run_at_cmd("AT+KPRIVKSTORE=1,%d" % len(key), timeout, ["CONNECT"])
        target_at.run_at_cmd(key+EOF, timeout+10)
        target_at.run_at_cmd("AT+KPRIVKSTORE?", timeout, ["CONNECT", "private_key,0,"+str(len(key)), "private_key,1,"+str(len(key)), "private_key,2,0", "OK"])
        target_at.run_at_cmd("AT+KPRIVKSTORE=2,%d" % len(key), timeout, ["CONNECT"])
        target_at.run_at_cmd(key+EOF, timeout+10)
        target_at.run_at_cmd("AT+KPRIVKSTORE?", timeout, ["CONNECT", "private_key,0,"+str(len(key)), "private_key,1,"+str(len(key)), "private_key,2,"+str(len(key)), "OK"])

        # Verify storing an invalid private key to all 3 indices
        for i in range(3):
            # Private key too short
            target_at.run_at_cmd("AT+KPRIVKSTORE=%i,%d" % (i, len(invalid)+1), timeout, ["CONNECT"])
            target_at.run_at_cmd(invalid, timeout, [r"\+CME\sERROR:\s930"])
            # Private key invalid
            target_at.run_at_cmd("AT+KPRIVKSTORE=%i,%d" % (i, len(invalid)), timeout, ["CONNECT"])
            target_at.run_at_cmd(invalid, timeout, [r"\+CME\sERROR:\s931"])

        #------------ Verify AT+KCERTDELETE Test, Read, and Write Commands ------------
        print("\n------------ Verify AT+KCERTDELETE Test, Read, and Write Commands ------------\n")
        # Modify for HL78xx newly version
        # if "HL78" in HARD_INI and "04.05.00.00" <= Soft_Version < "05.05.00.00":
        if "HL78" in HARD_INI and "04.05.00.00" <= Soft_Version:
            target_at.run_at_cmd("AT+KCERTDELETE=?", timeout, [r"\+KCERTDELETE:\s\(0-1\),\(0-3\)", "OK"])
        else:
            target_at.run_at_cmd("AT+KCERTDELETE=?", timeout, [r"\+KCERTDELETE:\s\(0-1\),\(0-2\)", "OK"])
        target_at.run_at_cmd("AT+KCERTDELETE?", timeout, [r"\+KCERTDELETE:", "OK"])
        target_at.run_at_cmd("AT+KCERTDELETE=0", timeout, ["OK"])
        target_at.run_at_cmd("AT+KCERTDELETE=1", timeout, ["OK"])
        #Verify certificate has been cleared from KCERTSTORE
        target_at.run_at_cmd("AT+KCERTSTORE?", timeout, ["CONNECT", "root_cert,0,0", "local_cert,0,0", "local_cert,1,0", "local_cert,2,0", "OK"])

        #------------ Verify AT+KPRIVKDELETE Test and Write Commands ------------
        print("\n------------ Verify AT+KPRIVKDELETE Test and Write Commands ------------\n")
        target_at.run_at_cmd("AT+KPRIVKDELETE=?", timeout, [r"\+KPRIVKDELETE:\s\(0-2\)", "OK"])
        target_at.run_at_cmd("AT+KPRIVKDELETE=0", timeout, ["OK"])
        target_at.run_at_cmd("AT+KPRIVKDELETE=1", timeout, ["OK"])
        target_at.run_at_cmd("AT+KPRIVKDELETE=2", timeout, ["OK"])
        #Verify key has been cleared from KPRIVKSTORE
        target_at.run_at_cmd("AT+KPRIVKSTORE?", timeout, ["CONNECT", "private_key,0,0", "private_key,1,0", "private_key,2,0", "OK"])

        swilog.info("\n----- Testing End -----\n")

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

swilog.info("\n----- Program End -----\n")
