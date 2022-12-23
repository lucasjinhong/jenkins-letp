"""
General AT commands test cases :: CGSN.

originated from A_HL_Common_GEN_CGSN_0001.PY validation test script.
"""

import re
import swilog
import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT, format_at_response
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


def A_HL_INT_GEN_CGSN_0000(target_at, non_network_tests_setup_teardown):
    """Check CGSN AT Command. Nominal/Valid use case."""
    print("\nA_HL_INT_GEN_CGSN_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    test_nb = ""
    test_ID = "A_HL_INT_GEN_CGSN_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        target_at.run_at_cmd("AT+CGSN=?", timeout, ["OK"])

        target_at.run_at_cmd("AT+CGSN", timeout, ["OK"])

        result = format_at_response(target_at.run_at_cmd("AT+CGSN", timeout, ["OK"]))

        if not re.match("^[0-9]+$", result[0]):
            swilog.error("the <IMEI> is NOT all digits")
            VarGlobal.statOfItem = "NOK"
        if len(result[0]) != 15:
            swilog.error("the length of <IMEI> is NOT 15")
            VarGlobal.statOfItem = "NOK"

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
