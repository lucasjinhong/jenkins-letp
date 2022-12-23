"""
DEV AT commands test cases :: SECUREBOOT.

Originated from A_HL_DEV_SECUREBOOT_0000.PY validation test script.
"""
import pytest
import swilog
import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT, format_at_response
from autotest import pytestmark  # noqa # pylint: disable=unused-import

swilog.info("\n----- Program start -----\n")

timeout = 15


# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_DEV_SECBOOT_0000(target_at, read_config, non_network_tests_setup_teardown):
    """Check Secure boot identification (ATI9) AT commands. Nominal/Valid use case."""
    print("\nA_HL_DEV_SECUREBOOT_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")

    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase < 2:
        pytest.skip("Phase < 1 : Secure boot mode is not supported")

    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    test_nb = ""
    test_ID = "A_HL_DEV_SECUREBOOT_0000"
    PRINT_START_FUNC(test_nb + test_ID)
    print("\n------------Test's preambule End------------")
    print("\n------------Test Case Start------------")

    try:
        # Check Secure boot AT Test Command
        result = format_at_response(target_at.run_at_cmd("ATI9", timeout, ["OK"]))
        strSBUB = result[11].split()[1]
        strSBFW = result[12].split()[1]
        rPukLen = len(result[13])
        fPukLen = len(result[14])

        if strSBUB == "0":
            if (strSBFW != "0") | (rPukLen != 1) | (fPukLen != 1):
                VarGlobal.statOfItem = "NOK"
            else:
                print("Secure boot mode successfully disabled")
        else:
            # RPuk anf FPUk shall be checked as RPuK = 42BA7F7D, FPuK = 4A14BD70 or FPuK = E3340DE5
            # RnD key is unique.
            # These hard coded CRC32 values are depending of PUB Keys.
            rPuk = result[13].split()[1]
            fPuk = result[14].split()[1]
            if (strSBFW == "0") | (rPuk != "42BA7F7D") | ((fPuk != "4A14BD70") & (fPuk != "E3340DE5")):
                VarGlobal.statOfItem = "NOK"
            else:
                print("Secure boot mode successfully enabled")
    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)


swilog.info("\n----- Program End -----\n")
