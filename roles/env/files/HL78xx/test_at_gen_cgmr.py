"""
General AT commands test cases :: CGMR.

originated from A_HL_Common_GEN_CGMR_0001.PY validation test script.
"""
import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


def A_HL_INT_GEN_CGMR_0000(target_at, read_config, non_network_tests_setup_teardown):
    """Check CGMR AT Command. Nominal/Valid use case."""
    print("\nA_HL_INT_GEN_CGMR_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    test_nb = ""
    test_ID = "A_HL_INT_GEN_CGMR_0000"
    PRINT_START_FUNC(test_nb + test_ID)
    VarGlobal.statOfItem = "OK"

    # Variable Init
    SOFT_INI = read_config.findtext("autotest/SOFT_INI_Soft_Version")

    test_nb = ""
    test_ID = "A_HL_INT_GEN_CGMR_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # AT+CGMR=?
        target_at.run_at_cmd("AT+CGMR=?", timeout, ["OK"])

        # AT+CGMR
        target_at.run_at_cmd("AT+CGMR", timeout, [SOFT_INI, "OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
