"""
General AT commands test cases :: CGMM.

originated from A_HL_Common_GEN_CGMM_0001.PY validation test script.
"""
import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT, format_at_response
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


def A_HL_INT_GEN_CGMM_0000(target_at, read_config, non_network_tests_setup_teardown):
    """Check CGMM AT Command. Nominal/Valid use case."""
    print("\nA_HL_INT_GEN_CGMM_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    test_nb = ""
    test_ID = "A_HL_INT_GEN_CGMM_0000"
    PRINT_START_FUNC(test_nb + test_ID)
    VarGlobal.statOfItem = "OK"

    # Variable Init
    Hard_INI = read_config.findtext("autotest/HARD_INI")
    # 2016-02-24 RHu Modification to fit product type
    Hard_INI = Hard_INI.split("_")[0]

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    # AT+CMEE?
    result = format_at_response(target_at.run_at_cmd("AT+CMEE?", timeout, ["OK"]))

    # default cmee
    cmee = "1"
    for r in result:
        if r.find("+CMEE: ") != -1:
            cmee = r.split(": ")[1]
            print("\nDefault cmee is: " + cmee)

    # ATE0+CMEE=1
    target_at.run_at_cmd("ATE0", timeout, ["OK"])

    target_at.run_at_cmd("AT+CMEE=1", timeout, ["OK"])

    try:
        # AT+CGMM=?
        target_at.run_at_cmd("AT+CMEE=?", timeout, ["OK"])

        # AT+CGMM
        target_at.run_at_cmd("AT+CGMM", timeout, [Hard_INI, "OK"])

        # Restore default cmee
        target_at.run_at_cmd("AT+CMEE=" + cmee, timeout, ["OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
