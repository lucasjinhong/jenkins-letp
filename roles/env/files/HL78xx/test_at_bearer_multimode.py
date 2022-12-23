"""Bearer AT commands test cases :: Multi-Mode Feature
FWINT-451, EURY-1308 (ALT1250-3638, ALT1250-3773 and ALT1250-3983): Implement Multi Mode Integration Sanity Test Cases
"""

import time
import pytest
import VarGlobal
from autotest import *

timeout = 15

@pytest.fixture()
def multimode_setup_teardown(network_tests_setup_teardown, target_at, read_config):
    """Test case setup and teardown."""
    state = network_tests_setup_teardown
    if state == "OK":
        print("Test Setup Success")

    print("\nA_HL_INT_BEARER_MULTIMODE_0000 TC Start:\n")

    print("\n------------Test's preambule Start------------")

    # save default +KSREP
    result = format_at_response(target_at.run_at_cmd("AT+KSREP?", timeout, ["OK"]))
    ksrep = result[0].split(" ")[1].split(",")[0]
    if ksrep == "0":
        target_at.run_at_cmd("AT+KSREP=1", timeout, ["OK"])
        time.sleep(timeout)

    HARD_INI = read_config.findtext("autotest/HARD_INI")

    test_nb = ""
    test_ID = "A_HL_INT_BEARER_MULTIMODE_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test Case Start------------")
    yield test_ID
    print("\n------------Test Case Teardown------------")
    # Restore default KSELACQ
    target_at.run_at_cmd("AT+KSELACQ=0,0", timeout, ["OK"])

    # Restore default KSREP
    target_at.run_at_cmd("AT+KSREP=" + ksrep, timeout, ["OK"])
    time.sleep(timeout)

    SWI_Reset_Module(target_at, HARD_INI)

def A_HL_INT_BEARER_MULTIMODE_0000(target_at, read_config, multimode_setup_teardown):
    """Check KSELACQ AT Command. Nominal/Valid use case."""
    test_ID = multimode_setup_teardown

    # Firmware version check
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Firmware_Ver = two_digit_fw_version(SOFT_INI_Soft_Version)
    if Firmware_Ver < "04.05.02.00":
        pytest.skip("Firmware < 4.5.2: Multi-Mode feature is not supported")

    # Check if it is M module
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    if HARD_INI == "HL7800-M":
        pytest.skip("M model does not support switching KSRAT")

    # Variable Init
    AT_KSRAT = int(read_config.findtext("autotest/Features_AT_KSRAT"))
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)

    try:
        # Test Read and Query +KSLEACQ AT commands: to configure Preferred Radio Access Technology List (PRL)
        if (HARD_INI == "HL7800" or HARD_INI == "HL7810" or HARD_INI == "HL7845") and ("04.06.03.00" <= Firmware_Ver < "05.00.00.00" or Firmware_Ver >= "05.03.03.00"):
            target_at.run_at_cmd("AT+KSELACQ=?", timeout, [r"\+KSELACQ:\s\(0\),\(0-2\),\(1-2\)", "OK"])
        else:
            target_at.run_at_cmd("AT+KSELACQ=?", timeout, [r"\+KSELACQ:\s\(0\),\(0-3\),\(1-3\),\(1-3\)", "OK"])
        target_at.run_at_cmd("AT+KSELACQ?", timeout, [r"\+KSELACQ: 0", "OK"])

        # Test 1:
        # Set PRL to be RAT1=CAT-M, RAT2=NBIOT, RAT3=GSM, reset is required to make the setting to be effective
        # Switch RATs in PRL without reboot
        # Reset the module, RAT auto switches to the first preferred RAT
        print ("=====Test Scenario 1: Config PRL, Swith RATs without reboot=====")
        print ("--- Step1. Set PRL with RAT1=CAT-M, RAT2=NBIOT, RAT3=GSM, resetting module is required ---")
        if HARD_INI == "HL7800" or HARD_INI == "HL7810" or HARD_INI == "HL7845":
            target_at.run_at_cmd("AT+KSELACQ=0,1,2", timeout, ["OK"])
            SWI_Reset_Module(target_at, HARD_INI)
            target_at.run_at_cmd("AT+KSELACQ?", timeout, [r"\+KSELACQ: 1,2", "OK"])
        else:
            target_at.run_at_cmd("AT+KSELACQ=0,1,2,3", timeout, ["OK"])
            SWI_Reset_Module(target_at, HARD_INI)
            target_at.run_at_cmd("AT+KSELACQ?", timeout, [r"\+KSELACQ: 1,2,3", "OK"])
        target_at.run_at_cmd("at+ksrat?", timeout, [r"\+KSRAT: 0", "OK"])

        print ("--- Step2. Switch RATs in PRL without reboot, RAT switching is with OK response ---")
        target_at.run_at_cmd("at+ksrat=1", timeout, ["OK"])
        target_at.run_at_cmd("at+ksrat?", timeout, [r"\+KSRAT: 1", "OK"])
        if HARD_INI == "HL7802" or HARD_INI == "HL7812":
            target_at.run_at_cmd("at+ksrat=2", timeout, ["OK"])
            SagSleep(15000)
            target_at.run_at_cmd("at+ksrat?", timeout, [r"\+KSRAT: 2", "OK"])

        print ("--- Step3. Reset the  module, RAT auto switches to the first preference in PRL ---")
        SWI_Reset_Module(target_at, HARD_INI)
        target_at.run_at_cmd("at+ksrat?", timeout, [r"\+KSRAT: 0", "OK"])

        # Test 2:
        # Configure non-empty PRL
        # switch RAT to be not in the PRL without resetting module, the moudle does not switch to RAT that is not in PRL
        print ("=====Test Senario 2: Config PRL, swith RAT not in PRL, RAT does not switch to be the one not in PRL=====")
        print ("--- Step1. Configure non-empty PRL, resetting module is required ---")
        if HARD_INI == "HL7802" or HARD_INI == "HL7812":
            target_at.run_at_cmd("AT+KSELACQ=0,2,3", timeout, ["OK"])
            SWI_Reset_Module(target_at, HARD_INI)
            target_at.run_at_cmd("AT+KSELACQ?", timeout, [r"\+KSELACQ: 2,3", "OK"])
            target_at.run_at_cmd("at+ksrat?", timeout, [r"\+KSRAT: 1", "OK"])
            # Switch to the 2nd preferred RAT on HL7802/12
            target_at.run_at_cmd("at+ksrat=2", timeout, ["OK"])
            SagSleep(15000)
            target_at.run_at_cmd("at+ksrat?", timeout, [r"\+KSRAT: 2", "OK"])
        else:
            target_at.run_at_cmd("AT+KSELACQ=0,2", timeout, ["OK"])
            SWI_Reset_Module(target_at, HARD_INI)
            target_at.run_at_cmd("AT+KSELACQ?", timeout, [r"\+KSELACQ: 2", "OK"])
            target_at.run_at_cmd("at+ksrat?", timeout, [r"\+KSRAT: 1", "OK"])

        print ("--- Step2. switch RAT to be not in the PRL. RAT does not switch to be the one not in the PRL ---")
        target_at.run_at_cmd("at+ksrat=0", timeout, ["OK"])
        target_at.run_at_cmd("at+ksrat?", timeout, [r"\+KSRAT: 1", "OK"])

        # Test 3:
        # Set PRL list to be "None" (default)
        # Multiple switch RATs until module is with RAT=CAT-M
        # Config PRL with different RAT, module is with the first preference regardless the previous setting
        print ("=====Test 3: PRL is None (default), set RAT then change PRL, module is with the 1st preference in PRL=====")
        print ("--- Step1. PRL is set to be none (default), resetting module is required ---")
        target_at.run_at_cmd("AT+KSELACQ=0,0", timeout, ["OK"])
        SWI_Reset_Module(target_at, HARD_INI)

        print ("--- Step 2: Multiple switch RATs until module is with RAT=CAT-M, RAT switching is with OK response ---")
        target_at.run_at_cmd("AT+KSELACQ?", timeout, [r"\+KSELACQ: 0", "OK"])
        if HARD_INI == "HL7802" or HARD_INI == "HL7812":
            target_at.run_at_cmd("at+ksrat=2", timeout, ["OK"])
            SagSleep(15000)
            target_at.run_at_cmd("at+ksrat?", timeout, [r"\+KSRAT: 2", "OK"])
        target_at.run_at_cmd("at+ksrat=1", timeout, ["OK"])
        target_at.run_at_cmd("at+ksrat?", timeout, [r"\+KSRAT: 1", "OK"])
        target_at.run_at_cmd("at+ksrat=0", timeout, ["OK"])
        target_at.run_at_cmd("at+ksrat?", timeout, [r"\+KSRAT: 0", "OK"])

        print ("--- Step 3: Config PRL with non CAT-M, reset module, RAT is set by PRL regardless the setting when PRL is none ---")
        target_at.run_at_cmd("AT+KSELACQ=0,2,1", timeout, ["OK"])
        SWI_Reset_Module(target_at, HARD_INI)
        target_at.run_at_cmd("AT+KSELACQ?", timeout, [r"\+KSELACQ: 2,1", "OK"])
        target_at.run_at_cmd("at+ksrat?", timeout, [r"\+KSRAT: 1", "OK"])

        # Test 4:
        # Set non-empty PRL list
        # switch RAT with reboot (old KSRAT behavior) clears PRL to empty
        print ("=====Test 4: Set PRL, setting RAT with reboot clears PRL to be default =====")
        print ("--- Step1. Set non-empty PRL, resetting module is required ---")
        target_at.run_at_cmd("AT+KSELACQ=0,2", timeout, ["OK"])
        SWI_Reset_Module(target_at, HARD_INI)
        target_at.run_at_cmd("AT+KSELACQ?", timeout, [r"\+KSELACQ: 2", "OK"])
        target_at.run_at_cmd("at+ksrat?", timeout, [r"\+KSRAT: 1", "OK"])

        print ("--- Step2. Switch RAT with the 2nd para = 1 (reboot), PRL is cleared ---")
        target_at.run_at_cmd("at+ksrat=0,1", timeout, ["OK"])
        SagSleep(15000)
        target_at.run_at_cmd("at+ksrat?", timeout, [r"\+KSRAT: 0", "OK"])
        target_at.run_at_cmd("AT+KSELACQ?", timeout, [r"\+KSELACQ: 0", "OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)