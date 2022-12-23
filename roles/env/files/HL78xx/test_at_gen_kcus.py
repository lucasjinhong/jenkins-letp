"""
General AT commands test cases :: KCUS.

originated from A_HL_Common_GEN_KCUS_0001.PY validation test script.
"""
import pytest
import swilog
import VarGlobal
from autotest import *

timeout = 15
swilog.info("\n----- Program start -----\n")

@pytest.fixture()
def kcus_setup_teardown(non_network_tests_setup_teardown, target_at, read_config):
    """Test case setup and teardown."""
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    # Start Test
    print("\n------------Test's preambule Start------------")

    # initial configure
    module = read_config.findtext("autotest/HARD_INI")
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)
    initial_kcus = True

    if Soft_Version <= "04.00.00.00":
        initial_kcus = False

    if module in ["HL7800-M"]:
        setHL7800MParams(target_at, initial_kcus)
    elif module in ["HL7800", "HL7802", "HL7810", "HL7812", "HL7845"]:
        target_at.run_at_cmd("AT+KCUS=0", timeout, ["OK"])
    else:
        VarGlobal.statOfItem = "NOK"
        swilog.error("KCUS test does not support Module Type...")

    test_nb = ""
    test_ID = "A_HL_INT_GEN_KCUS_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test Case Start------------")

    yield test_ID, initial_kcus

    print("\n----- KCUS TearDown -----\n")

    # restore after finishing or for exception
    if module in ["HL7800-M"]:
        setHL7800MParams(target_at, initial_kcus)
    else:
        target_at.run_at_cmd('AT%SETACFG="Identification.Model.ModelNumber","' + module + '"', timeout, ["OK"])
        target_at.run_at_cmd('AT%GETACFG="Identification.Model.ModelNumber"', timeout, [module, "OK"])
        target_at.run_at_cmd("AT+KCUS=0", timeout, ["OK"])

def setOtherParams(target_at, initial_kcus):
    """Set KCUS AT command."""
    target_at.run_at_cmd('AT+KCUS=1,"HL7800T"', timeout, ["OK"])

    target_at.run_at_cmd('AT+KCUS=2,"swiserver.Identification.Model","HL7800-T"', timeout, ["OK"])

    target_at.run_at_cmd('AT+KCUS=2,"swiserver.Identification.ProductName","HL7800-T"', timeout, ["OK"])

    target_at.run_at_cmd('AT%SETACFG="Identification.Model.ModelNumber","HL7800-T"', timeout, ["OK"])

    # Manually Apply to keep AT+KCUS? initial result
    if initial_kcus:
        target_at.run_at_cmd("AT+KCUS=3", timeout, ["OK"])

    # Check if Set Correctly
    target_at.run_at_cmd("AT+KCUS?", timeout, [r"\+KCUS: HL7800T", \
                                            r"\+KCUS: swiserver.Identification.Model,HL7800-T", \
                                            r"\+KCUS: swiserver.Identification.ProductName,HL7800-T", \
                                            "OK"])

    target_at.run_at_cmd('AT%GETACFG="Identification.Model.ModelNumber"', timeout, ["HL7800-T", "OK"])

def setHL7800MParams(target_at, initial_kcus):
    # Set KCUS to Correct HL7800M values
    target_at.run_at_cmd('AT+KCUS=1,"HL7800M"', timeout, ["OK"])

    target_at.run_at_cmd('AT+KCUS=2,"swiserver.Identification.Model","HL7800-M"', timeout, ["OK"])

    target_at.run_at_cmd('AT+KCUS=2,"swiserver.Identification.ProductName","HL7800-M"', timeout, ["OK"])

    target_at.run_at_cmd('AT%SETACFG="Identification.Model.ModelNumber","HL7800-M"', timeout, ["OK"])

    target_at.run_at_cmd('AT+KCUS=2,"swiserver.Kbndcfg.Lock_NB1","1"', timeout, ["OK"])

    target_at.run_at_cmd('AT+KCUS=2,"swiserver.Kbndcfg.Lock_GSM","1"', timeout, ["OK"])

    # Manually Apply to keep AT+KCUS? initial result
    if initial_kcus:
        target_at.run_at_cmd("AT+KCUS=3", timeout, ["OK"])

    # Check if Set Correctly
    target_at.run_at_cmd("AT+KCUS?", timeout, [r"\+KCUS: HL7800M", \
                                            r"\+KCUS: swiserver.Identification.Model,HL7800-M", \
                                            r"\+KCUS: swiserver.Identification.ProductName,HL7800-M", \
                                            r"\+KCUS: swiserver.Kbndcfg.Lock_NB1,1", \
                                            r"\+KCUS: swiserver.Kbndcfg.Lock_GSM,1", \
                                            "OK"])

    target_at.run_at_cmd('AT%GETACFG="Identification.Model.ModelNumber"', timeout, ["HL7800-M", "OK"])

# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_GEN_KCUS_0000(target_at, read_config, kcus_setup_teardown):
    """Check KCUS AT commands. Nominal/Valid use case."""
    print("\nA_HL_GEN_KCUS_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")

    # variable init
    module = read_config.findtext("autotest/HARD_INI")
    test_ID = kcus_setup_teardown[0]
    initial_kcus = kcus_setup_teardown[1]

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # Check NV Mode Status : automatic or manual
        # In case automatic mode is enabled, a restore backup will be performed
        # That's why, we should set NV mode to manual instead
        result = format_at_response(target_at.run_at_cmd("AT+NVBU=NVfeatureMode,status", timeout, ["OK"]))
        nv_status = result[0]

        if nv_status == "manual":
            setOtherParams(target_at, initial_kcus)

        elif nv_status == "automatic":
            # Set nv_status manual
            target_at.run_at_cmd("AT+NVBU=NVfeatureMode,manual", timeout, ["OK"])

            setOtherParams(target_at, initial_kcus)

            # Re-set nv_status automatic
            target_at.run_at_cmd("AT+NVBU=NVfeatureMode,automatic", timeout, ["OK"])

        else:
            raise Exception("ERROR: unknown nv_status")

        # restore
        if module in ["HL7800-M"]:
            setHL7800MParams(target_at, initial_kcus)
        else:
            target_at.run_at_cmd('AT%SETACFG="Identification.Model.ModelNumber","' + module + '"', timeout, ["OK"])
            target_at.run_at_cmd('AT%GETACFG="Identification.Model.ModelNumber"', timeout, [module, "OK"])
            target_at.run_at_cmd("AT+KCUS=0", timeout, ["OK"])

    except Exception as err_msg:
        # reset to initial status for exceptions
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)


swilog.info("\n----- Program End -----\n")
