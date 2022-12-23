"""
test cases :: test_template
originated from test_template.py validation test script.
"""

import os
import pytest
import VarGlobal
from autotest import *

timeout = 15

def A_HL_INT_Function_Name_0000():
    """
    Test case description
    """
    print("\nA_HL_INT_Function_Name_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")

    test_nb = ""
    test_ID = "A_HL_INT_Function_Name_0000"
    PRINT_START_FUNC(test_nb + test_ID)
    VarGlobal.statOfItem = "OK"

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        """
        Test something....

        """

        if not (AT_percent_CCID or AT_CCID):
            VarGlobal.statOfItem = "NOK"

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
