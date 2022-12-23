"""
AV AT commands test cases :: WAMS
originated from A_HL_Common_AVMS_LWM2M_CNT_0003.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import ast
from autotest import *


def A_HL_INT_AV_WAMS_0000(target_at, read_config, non_network_tests_setup_teardown):
    """
    Check WAMS AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_AV_WAMS_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    test_nb = ""
    test_ID = "A_HL_INT_AV_WAMS_0000"
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

    print("\n------------Test Case Start------------")

    try:
        # Check firmware public key
        key = "308201080282010100B225CCFB87A49A4DDFF4D8F86B06FBACA6707493F77E0F32A98DB223F357403083738F8B74F577A0394F7056962D323C13C39F6C1B2073F9B4CDA7ECF4AAB6CEF0709CEA7F2202320B2FF2DE35553F17D286DE95C8C6DC33A27072583A4139AE6B78DD4A1C6AC4DEADB7F8DCAECC203D202104045125BFF519E3980703B9002B54FBEC915DB36D177912E0F25055213F04E4AFB2755AFD3C2CB09FBC460C57C9E025D96CD3F63B312C3965A014442C6E38A937ED84CC9EF8D0D39715B2B3E2C2FAF2EBB89A15BA6993C11CEE9B81A56B17AE8E2D3642C67919BB05DD2B9240953CE5F241AD454B1AE5021055D84BB7AAB60BEA7DEA58FEF99E8DECAAA8714749020103"
        wrongKey = "0123456789ABCDEF"
        keyNotStored = "123456789000"

        print("Check wrong firmware public key")

        SagSendAT(target_at, 'AT+WAMS=0,9,'+str(len(wrongKey)//2)+',1,0\r')
        SagWaitnMatchResp(target_at, ['\r\n>'], 5000)
        SagSendAT(target_at, '%s\x1A'%(wrongKey))
        SagWaitnMatchResp(target_at, ['*\r\n+WAMS: 2\r\nOK\r\n'], 30000)

        print("Check good firmware public key")

        SagSendAT(target_at, 'AT+WAMS=0,9,'+str(len(key)//2)+',1,0\r')
        SagWaitnMatchResp(target_at, ['\r\n>'], 5000)
        SagSendAT(target_at, '%s\x1A'%(key))
        SagWaitnMatchResp(target_at, ['*\r\n+WAMS: 0\r\nOK\r\n'], 30000)

        if "RC51" in HARD_INI:

            print("Check wrong firmware public key")

            SagSendAT(target_at, 'AT+WAMS=0,10,10\r')
            SagWaitnMatchResp(target_at, ['\r\n>'], 5000)
            SagSendAT(target_at, '%s\x1A'%(keyNotStored))
            SagWaitnMatchResp(target_at, ['*\r\n+WAMS: 2\r\nOK\r\n'], 30000)

            print("Check firmware public key not stored")

            SagSendAT(target_at, 'AT+WAMS=1,10,10\r')
            SagWaitnMatchResp(target_at, ['\r\n>'], 5000)
            SagSendAT(target_at, '%s\x1A'%(keyNotStored))
            SagWaitnMatchResp(target_at, ['*\r\n+WAMS: 1\r\nOK\r\n'], 30000)

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
