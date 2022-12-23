"""
General AT commands test cases :: GMR.

originated from A_HL_Common_GEN_GMR_0001.PY validation test script.
"""
import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


def A_HL_INT_GEN_GMR_0000(target_at, read_config, non_network_tests_setup_teardown):
    """Check GMR AT Command. Nominal/Valid use case."""
    print("\nA_HL_INT_GEN_GMR_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    # Variable Init
    SOFT_INI = read_config.findtext("autotest/SOFT_INI_Soft_Version")

    test_nb = ""
    test_ID = "A_HL_INT_GEN_GMR_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        # AT+GMR=?
        target_at.run_at_cmd("AT+GMR=?", timeout, ["OK"])

        # AT+GMR
        target_at.run_at_cmd("AT+GMR", timeout, [SOFT_INI, "OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
