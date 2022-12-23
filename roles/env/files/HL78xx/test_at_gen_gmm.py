"""
General AT commands test cases :: GMM.

originated from A_HL_Common_GEN_GMM_0001.PY validation test script.
"""

import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


def A_HL_INT_GEN_GMM_0000(target_at, read_config, non_network_tests_setup_teardown):
    """Check GMM AT Command. Nominal/Valid use case."""
    print("\nA_HL_INT_GEN_GMM_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")

    # Variable Init
    Hard_INI = read_config.findtext("autotest/HARD_INI")
    # 2016-02-24 RHu Modification to fit product type
    Hard_INI = Hard_INI.split("_")[0]

    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    test_nb = ""
    test_ID = "A_HL_INT_GEN_GMM_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # AT+GMM=?
        target_at.run_at_cmd("AT+GMM=?", timeout, ["OK"])

        # AT+GMM
        target_at.run_at_cmd("AT+GMM", timeout, [Hard_INI, "OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
