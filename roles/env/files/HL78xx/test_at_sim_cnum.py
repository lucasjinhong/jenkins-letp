"""
SIM AT commands test cases :: CNUM.

originated from A_HL_Common_NS_CNUM_0001.PY validation test script.
"""
import pytest
import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT, C_TIMER_LOW
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


def A_HL_INT_SIM_CNUM_0000(target_at, read_config, non_network_tests_setup_teardown):
    """Check CNUM AT Command. Nominal/Valid use case."""
    print("\nA_HL_INT_SIM_CNUM_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    # Variable Init
    SIM_Pin1 = read_config.findtext("autotest/PIN1_CODE")

    if not SIM_Pin1:
        pytest.skip("PIN1_CODE is blank")

    test_nb = ""
    test_ID = "A_HL_INT_SIM_CNUM_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # AT+CNUM
        target_at.run_at_cmd("AT+CNUM", timeout, ["OK"])

        # AT+CNUM=?
        target_at.run_at_cmd("AT+CNUM=?", timeout, ["OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
