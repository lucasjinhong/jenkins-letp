"""
General AT commands test cases :: CIMI.

originated from A_HL_Common_GEN_CIMI_0001.PY validation test script
"""

import time
import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


def A_HL_INT_GEN_CIMI_0000(target_at, read_config, non_network_tests_setup_teardown):
    """Check CIMI AT Command. Nominal/Valid use case."""
    print("\nA_HL_INT_GEN_CIMI_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    # Variable Init
    SIM_INI_IMSI = read_config.findtext("autotest/SIM_IMSI")
    Hard_INI = read_config.findtext("autotest/HARD_INI")

    test_nb = ""
    test_ID = "A_HL_INT_GEN_CIMI_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        target_at.run_at_cmd("AT", timeout, ["OK"])

        target_at.run_at_cmd("ATI", timeout, [Hard_INI, "OK"])

        target_at.run_at_cmd("AT", timeout, ["OK"])

        time.sleep(2)
        # AT+CIMI=?
        target_at.run_at_cmd("AT+CIMI=?", timeout, ["OK"])

        time.sleep(2)
        # AT+CIMI after at+cpin
        target_at.run_at_cmd("AT+CIMI", timeout, [SIM_INI_IMSI, "OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
