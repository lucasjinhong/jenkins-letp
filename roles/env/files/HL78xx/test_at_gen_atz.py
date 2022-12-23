"""
General AT commands test cases :: ATZ.

originated from A_HL_Common_GEN_ATZ_0001.PY validation test script.
"""
import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


def A_HL_INT_GEN_ATZ_0000(target_at, read_config, non_network_tests_setup_teardown):
    """Check ATZ AT Command. Nominal/Valid use case."""
    print("\nA_HL_INT_GEN_ATZ_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")

    test_nb = ""
    test_ID = "A_HL_INT_CEL_ATZ_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    target_at.run_at_cmd("ATE0", timeout, ["OK"])

    try:
        # ATZ
        target_at.run_at_cmd("ATZ", timeout, ["OK"])

        # ATZ0
        target_at.run_at_cmd("ATZ0", timeout, ["OK"])

        # ATZ1
        if "HL78" in HARD_INI:
            target_at.run_at_cmd("ATZ1", timeout, ["OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
