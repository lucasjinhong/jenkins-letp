"""
General AT commands test cases :: GMI.

originated from A_HL_Common_GEN_GMI_0001.PY validation test script.
"""

import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


def A_HL_INT_GEN_GMI_0000(target_at, read_config, non_network_tests_setup_teardown):
    """Check GMI AT Command. Nominal/Valid use case."""

    print("\nA_HL_INT_GEN_GMI_0000 TC Start:\n")

    print("\n------------Test's preambule Start------------")

    state = non_network_tests_setup_teardown

    if state == "OK":
        print("General Test Setup Success")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")

    test_nb = ""
    test_ID = "A_HL_INT_GEN_GMI_0000"
    PRINT_START_FUNC(test_nb + test_ID)
    VarGlobal.statOfItem = "OK"

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # AT+GMI=?
        target_at.run_at_cmd("AT+GMI=?", timeout, ["OK"])

        # AT+GMI
        if "HL78" in HARD_INI:
            target_at.run_at_cmd("AT+GMI", timeout, ["Sierra Wireless", "OK"])
        elif "RC51" in HARD_INI:
            target_at.run_at_cmd("AT+GMI", timeout, ["Sierra Wireless, Incorporated", "OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
