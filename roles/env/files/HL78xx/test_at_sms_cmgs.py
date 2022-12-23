"""
SMS AT commands test cases :: CMGS
originated from A_HL_Common_G_SMS_CMGS_0008.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import configparser
from autotest import *

# Build PDU
#-----------------------------------------------------------------------
def buildPduSCA(number,TypeOfAddress):
    s = list(number.lstrip('+'))
    a = len(s)//2
    if len(s)%2 != 0:
        a = a+1
    a = a+1
    if a<10:
        temp = '0' + chr(48 + a) + TypeOfAddress
    else:
        temp = '0' + chr(65 + a - 10) + TypeOfAddress
    n = len(s)
    if n%2 == 0:
        i=1
        while(i < n):
            temp += s[i] + s[i-1]
            i += 2
    else:
        i=1
        while(i < n-1):
            temp += s[i] + s[i-1]
            i += 2
        temp += 'F' + s[n-1]
    return temp
#-----------------------------------------------------------------------

def buildPduDa(number,TypeOfAddress):
    #First PDU Byte: Length of phone number
    #Second PDU Byte: Type of Address: '91' (international) / '81' (national)
    #Validation Autotest: temp = '0B91'
    #Amarisoft: temp = '0381'
    s = list(number.lstrip('+'))

    if len(s) > 9:
        n = len(s)
        n_hex = hex(n).strip("0x").capitalize()
        temp = '0%s'%n_hex + TypeOfAddress
    else:
        n = len(s)
        temp = '0%s'%n + TypeOfAddress

    if n%2 == 0:
        i=1
        while(i < n):
            temp += s[i] + s[i-1]
            i += 2
    else:
        i=1
        while(i < n-1):
            temp += s[i] + s[i-1]
            i += 2
        temp += 'F' + s[n-1]
    return temp


def  A_HL_INT_SMS_CMGS_0000(target_at, read_config, network_tests_setup_teardown):
    """
    Check CMGS AT Command. Nominal/Valid use case. Check SMS Text & PDU can be sent when GPRS attached and bearer is activiated.
    """

    print("\nA_HL_INT_SMS_CMGS_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    VoiceNumber = read_config.findtext("autotest/Voice_Number")
    SmsMessageStorage = read_config.findtext("autotest/SmsMessageStorage")
    ServiceCenterNumberTx = read_config.findtext("autotest/ServiceCenterNumberTx")
    ServiceCenterNumberRx = read_config.findtext("autotest/ServiceCenterNumberRx")
    VoiceNumberPdu = buildPduDa(VoiceNumber,"81")
    ServiceCenterNumberTxPdu = buildPduSCA(ServiceCenterNumberTx,"81")
    ServiceCenterNumberRxPdu = buildPduSCA(ServiceCenterNumberRx,"81")

    # Requires Amarisoft SIM Card for the test case
    Network = read_config.findtext("autotest/Network")
    if ("amarisoft") not in str.lower(Network):
        raise Exception("Problem: Amarisoft SIM and Config should be used.")

    test_nb = ""
    test_ID = "A_HL_INT_SMS_CMGS_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        #AT+CMGF?
        SagSendAT(target_at, "AT+CMGF?\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], C_TIMER_LOW)
        result = SagMatchResp(answer, ["\r\n+CMGF: ?\r\n"])
        # default cmgf
        if result:
            cmgf = answer.split("\r\n")[1].split(": ")[1]
            print("\nDefault cmgf is: "+cmgf)
        else:
            cmgf = "0"

        # +CSCA information to enter
        SagSendAT(target_at, 'AT+CSCA="'+ ServiceCenterNumberTx + '"\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        # AT+CSCA?
        SagSendAT(target_at, "AT+CSCA?\r")
        resp1 = '\r\n+CSCA: "' +ServiceCenterNumberTx+ '",129\r\n\r\nOK\r\n'
        SagWaitnMatchResp(target_at, [resp1], C_TIMER_LOW)

        SagSendAT(target_at, "AT+CNMI=1,1\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        SagSendAT(target_at, 'AT+CPMS="SM","SM","SM"\r')
        SagWaitnMatchResp(target_at, ['\r\n+CPMS: *,'+SmsMessageStorage+',*,'+SmsMessageStorage+',*,'+SmsMessageStorage+'\r\n\r\nOK\r\n'], C_TIMER_LOW)

        SagSendAT(target_at, "AT+CMGD=1,4\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 1200000)

        # Send SMS in Text format
        SagSendAT(target_at, "AT+CMGF=1\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        SagSendAT(target_at, 'AT+CMGS="' + VoiceNumber + '"\r')

        SagWaitnMatchResp(target_at, ['\r\n>'], 2000)
        SagSendAT(target_at, 'Test SMS\x1A')
        SagWaitnMatchResp(target_at, ['\r\n+CMGS: *\r\n\r\nOK\r\n'], 10000)
        SagWaitnMatchResp(target_at, ['\r\n+CMTI: "SM",1\r\n'], 30000)

        SagSendAT(target_at, 'AT+CMGR=1\r')
        resp1 = '\r\n+CMGR: "REC UNREAD","'+VoiceNumber+'",,"??/??/??,??:??:?????"\r\nTest SMS\r\n\r\nOK\r\n'

        SagWaitnMatchResp(target_at, [resp1], 8000)

        # Send SMS in PDU format
        SagSendAT(target_at, "AT+CMGF=0\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        SagSendAT(target_at, "AT+CMGF?\r")
        SagWaitnMatchResp(target_at, ["\r\n+CMGF: 0\r\n\r\nOK\r\n"], C_TIMER_LOW)

        if len(VoiceNumber) == 3:
            SagSendAT(target_at, 'AT+CMGS=17\r')
            SagWaitnMatchResp(target_at, ['\r\n>'], 2000)
            SagSendAT(target_at, ''+ServiceCenterNumberTxPdu+'1100'+VoiceNumberPdu+'0000AA08D4F29C0E9A36A7\x1A')

        elif len(VoiceNumber) == 10:
            SagSendAT(target_at, 'AT+CMGS=20\r')
            SagWaitnMatchResp(target_at, ['\r\n>'], 2000)
            SagSendAT(target_at, '001100'+VoiceNumberPdu+'0000AA08D4F29C0E9A36A7\x1A')

        else:
            swilog.error("Please check Voice_Number in autotest.xml - length of number is not 3 or 10")
            assert False

        SagWaitnMatchResp(target_at, ['\r\n+CMGS: *\r\n\r\nOK\r\n'], 10000)
        SagWaitnMatchResp(target_at, ['\r\n+CMTI: "SM",2\r\n'], 30000)

        # Read the SMS in text mode to avoid decoding Service Center Address information in PDU Mode
        SagSendAT(target_at, "AT+CMGF=1\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        SagSendAT(target_at, 'AT+CMGR=2\r')
        resp1 = '\r\n+CMGR: "REC UNREAD","'+VoiceNumber+'",,"??/??/??,??:??:?????"\r\nTest SMS\r\n\r\nOK\r\n'
        SagWaitnMatchResp(target_at, [resp1], 8000)

        print("*********************************************************")

        # Send SMS from storage in Text format
        SagSendAT(target_at, "AT+CMGF=1\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        SagSendAT(target_at, 'AT+CMGW="' + VoiceNumber + '"\r')
        SagWaitnMatchResp(target_at, ['\r\n> '], 2000)
        SagSendAT(target_at, 'TEST SMS\x1A')
        answer = SagWaitResp(target_at, ["\r\n+CMGW: *\r\n"], 3000)
        result = SagMatchResp(answer, ["\r\n+CMGW: *\r\n"])
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        if result:
            idx = answer.split("\r\n")[1].split(": ")[1]
            SagSendAT(target_at, "AT+CMSS=" + idx + "\r")
            idx = str(int(idx) + 1)
            SagWaitnMatchResp(target_at, ["\r\n+CMSS: *\r\n\r\nOK\r\n"], C_TIMER_MEDIUM)
            SagWaitnMatchResp(target_at, ['\r\n+CMTI: "SM",' + idx + '\r\n'], 30000)
        else:
            VarGlobal.statOfItem = "NOK"

        # TPE’s Amarisoft SIM has only 5 SMS storage in total. So we need to delete a storage before the next test step.
        SagSendAT(target_at, "AT+CMGD=" + idx + ",0\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        # Send SMS from storage in PDU format
        SagSendAT(target_at, "AT+CMGF=0\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        SagSendAT(target_at, "AT+CMGF?\r")
        SagWaitnMatchResp(target_at, ["\r\n+CMGF: 0\r\n\r\nOK\r\n"], C_TIMER_LOW)

        if len(VoiceNumber) == 3:
            SagSendAT(target_at, 'AT+CMGW=17\r')
            SagWaitnMatchResp(target_at, ['\r\n> '], 2000)
            SagSendAT(target_at, ''+ServiceCenterNumberTxPdu+'1100'+VoiceNumberPdu+'0000AA08D4F29C0E9A36A7\x1A')

        elif len(VoiceNumber) == 10:
            SagSendAT(target_at, 'AT+CMGW=20\r')
            SagWaitnMatchResp(target_at, ['\r\n>'], 2000)
            SagSendAT(target_at, '001100'+VoiceNumberPdu+'0000AA08D4F29C0E9A36A7\x1A')

        answer = SagWaitResp(target_at, ["\r\n+CMGW: *\r\n"], 3000)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        idx = answer.split("\r\n")[1].split(": ")[1]
        SagSendAT(target_at, "AT+CMSS=" + idx + "\r")
        idx = str(int(idx) + 1)
        SagWaitnMatchResp(target_at, ["\r\n+CMSS: *\r\n\r\nOK\r\n"], C_TIMER_MEDIUM)
        SagWaitnMatchResp(target_at, ['\r\n+CMTI: "SM",' + idx + '\r\n'], 30000)

        print("*********************************************************")

        SagSendAT(target_at, "AT+CGEREP=0\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        # Restore default cmgf
        SagSendAT(target_at, "AT+CMGF=" + cmgf + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)
