"""General AT commands test cases :: WIMEI."""

import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT, format_at_response
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


def A_HL_INT_GEN_WIMEI_0000(target_at, non_network_tests_setup_teardown):
    """Check WIMEI AT Command. Nominal/Valid use case."""
    print("\nA_HL_INT_GEN_WIMEI_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    test_nb = ""
    test_ID = "A_HL_INT_GEN_WIMEI_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        # WIMEI=?
        target_at.run_at_cmd("AT+WIMEI=?", timeout, ["OK"])

        # WIMEI? = CGSN
        result = format_at_response(target_at.run_at_cmd("AT+CGSN", timeout, ["OK"]))

        atResult = "\\+WIMEI: " + result[0]
        target_at.run_at_cmd("AT+WIMEI?", timeout, [atResult, "OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
