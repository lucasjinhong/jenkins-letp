import os
import stat
from serial import Serial, SerialException
from serial.tools.list_ports import comports
from integration_libs.hl78_errors import CME_Error, CMS_Error
from time import sleep
import re
import logging

log = logging.getLogger("hl78_uart")
log.setLevel(logging.DEBUG)
c_handler = logging.StreamHandler()
c_handler.setFormatter(
        logging.Formatter("[%(name)s][%(levelname)s]: %(message)s"))
log.addHandler(c_handler)

# Define default ports depending on OS
if os.name == 'posix':
    default_at = '/dev/ttyUSB0'
    default_cli = '/dev/ttyUSB1'
    # default_relay = '/dev/ttyACM0'
    default_relay = '/dev/hidraw0'
    default_console = '/dev/ttyUSB2'
    usb_regex = 'USB'
    relay_regex = 'ACM'
elif os.name == 'nt':
    default_at = 'COM1'
    default_cli = 'COM2'
    default_relay = 'COM3'
    default_console = 'COM4'
    usb_regex = 'COM'
    relay_regex = 'COM'

def cme_error_get_info(response):
    def get_error(line):
        try:
            err = int(get_at_return_value(line))
            err = CME_Error(err).name
            return '%s (%s)' % (line, err)
        except ValueError:
            return line

    return list(map(get_error, response))

def cms_error_get_info(response):
    def get_error(line):
        try:
            err = int(get_at_return_value(line))
            err = CMS_Error(err).name
            return '%s (%s)' % (line, err)
        except ValueError:
            return line

    return list(map(get_error, response))


def send_cli_command(uart_cli, command, prompt='\r\n>', strip_prompt=True):
    uart_cli.write(('%s\r\n' % command.strip()).encode())
    uart_cli.readline()

    response = uart_cli.read_until(prompt).decode('utf-8')

    if strip_prompt:
        response = '\r\n'.join(response.split('\r\n')[:-1])
    return response


def parse_ati9(stripped_response):
    # First 3 lines are not annotated
    ati9 = {
        'modem_sw': stripped_response[0],
        'fw_version': stripped_response[1],
        'build_date': stripped_response[2],
        }
    for line in stripped_response[3:]:
        value = get_at_return_value(line)
        key = line.split(':')[0]
        ati9[key] = value

    # Maintain backwards compatibility with old key names
    for key, _ in list(ati9.items()):
        if key == "IMEI-SV":
            ati9["imei_sv"] = ati9.pop(key)
        elif key == "Legato RTOS":
            ati9["legato_version"] = ati9.pop(key)

    return ati9

def is_secboot(ser_at):
    """Checks if a module has secureboot enabled

    Arguments:
    ser_at: Serial object attached to AT port

    Returns: bool
    """
    ati9 = get_ati9(ser_at)
    try:
        if 'HL78xx' in ati9['fw_version']:
            SBUB = ati9["SBUB"]
            if SBUB == "0":
                return None
            elif ati9["RPuK"] == "42BA7F7D" and (ati9["FPuK"] == "4A14BD70" or ati9["FPuK"] == "E3340DE5"):
                # RnD signed key
                return "SIGNED_RND"
            elif ati9["RPuK"] == "53F7A48A" and ati9["FPuK"] == "139A8E70":
                # Sierra signed key
                return "SIGNED_SIERRA"
            else:
                log.error(ati9)
                raise ValueError("Could not determine if module was signed from response")

        elif 'SWIX55C' in ati9['fw_version'] or 'SWIX65C' in ati9['fw_version'] or 'EM' in ati9['model']:
            log.info("Unlocking module and sending AT!SECBOOTCFG?")
            unlock_resp = set_at_unlock(ser_at)
            if 'ERROR' in unlock_resp:
                raise ValueError("AT!UNLOCK ERROR - cannot unlock module to check secure boot status")
            ser_at.write(b'AT!SECBOOTCFG?\r\n')
            ser_at.readline()
            sleep(4)

            response = strip_at_response(
                    ser_at.read_all().decode('utf-8').split('\r\n'))
            log.info(response)

            if response[0].split(",")[1] == '1':
                return "SIGNED_SIERRA"

        else:
            raise ValueError("Secure boot check not supported on this module!")

    except KeyError:
        # old Firmware version before 3.5.0.0 which does not have "SBUB" value
        return False

def get_ati9(ser_at):
    """Gets the information returned by ATI9 as a dict

    Arguments:
    ser_at: Serial object attached to AT port

    Returns: a dict containing the ATI9 information
    """
    log.info("Sending ATI9")
    ser_at.write(b'ATI9\r\n')
    ser_at.readline()
    ser_at.readline()
    sleep(4)

    response = strip_at_response(
            ser_at.read_all().decode('utf-8').split('\r\n'))
    log.debug(response)

    if 'OK' in response[-1]:
        log.debug("Valid response received")
        response = parse_ati9(response)
        return response
    else:
        raise ValueError(
                "Invalid response received from module: %s"
                % cme_error_get_info(response))

def get_ati3(ser_at):
    log.info("Sending ATI3")
    ser_at.write(b'ATI3\r\n')
    sleep(2)
    ser_at.readline()
    ser_at.readline()

    response = strip_at_response(
            ser_at.read_all().decode('utf-8').split('\r\n'))
    log.debug(response)

    if 'OK' in response[-1] and len(response) == 2:
        log.debug("HL78 valid response received")
        response = response[0]
        return response
    elif 'OK' in response[-1] and len(response) == 7:
        log.debug("Qualcomm valid response received")
        response = response[1].split(" ")[1]
        return response
    else:
        raise ValueError(
                "Invalid response received from module: %s"
                % cme_error_get_info(response))

def set_at_unlock(ser_at):
    log.info("Sending AT!UNLOCK=\"A710\"")
    ser_at.write(b'AT!UNLOCK="A710"\r\n')
    sleep(2)
    ser_at.readline()

    response = strip_at_response(
            ser_at.read_all().decode('utf-8').split('\r\n'))
    log.debug(response)

    if 'OK' in response[-1] and len(response) == 1:
        log.debug("Valid response received, some AT commands are now unlocked")
        response = response[0]
    elif 'ERROR' in response[-1]:
        sleep(5)
        log.info("Sending AT!UNLOCK=\"A710A710\"")
        ser_at.write(b'AT!UNLOCK="A710A710"\r\n')
        sleep(2)
        ser_at.readline()

        response = strip_at_response(
                ser_at.read_all().decode('utf-8').split('\r\n'))
        log.debug(response)

        if 'OK' in response[-1] and len(response) == 1:
            log.debug("Valid response received, some AT commands are now unlocked")
            response = response[0]
    else:
        log.debug("Firmware does not support AT command access control")
    return response


def strip_at_response(response):
    try:
        response = list(map(lambda line: line.decode("utf-8"), response))
    except:
        pass
    response = list(map(lambda line: line.strip(), response))
    response = list(filter(lambda line: len(line), response))
    response = list(filter(lambda line: '+CREG: ' not in line, response))
    response = list(filter(lambda line: '+CEREG: ' not in line, response))
    response = list(filter(lambda line: '+WDSI: ' not in line, response))
    response = list(filter(lambda line: '+CEER: ' not in line, response))
    response = list(filter(lambda line: 'QCSRVCINFO : 7 ,1' not in line, response))
    return response


def get_at_return_value(line):
    line = line.split(':')
    if len(line) < 2:
        return None
    else:
        return ':'.join(line[1:]).strip()


def get_uart(uart, at=True):

    ser = Serial()
    ser.baudrate = 115200
    ser.port = uart
    ser.timeout = 1
    ser.writeTimeout=3
    try:
        ser.open()
    except SerialException as e:
        ser.close()
        log.debug("ser.open() assert")
        log.debug(e)
        return None

    if ser.is_open:
        # Clear out anything in the buffer
        while ser.read_all():
            pass

        if at:
            ser.write(b'ATE1\r\n')
            ser.read_until('OK\r\n')
        ser.read_all()
        return ser

    log.warning("Couldn't open %s" % uart)
    return None


def is_valid_cli(uart_cli):
    try:
        log.debug("Checking if %s is a valid CLI port" % uart_cli)
        ser = get_uart(uart_cli, at=False)
        if not ser:
            return False

        # cp command exists in both uboot and cli
        ser.write(b'cp\r\n')
        sleep(2)
        ser.readline()
        response = ser.read_all().decode("utf-8").split('\r\n')
        log.debug(response)

        if response[-1].startswith('#'):
            log.info("UBOOT detected, resetting...")
            ser.write(b'reset\r\n')
            log.info("Waiting 15 seconds for reset")
            ser.close()
            sleep(15)
            return is_valid_cli(uart_cli)

        ser.close()
        if response[-1].endswith('>'):
            return True
        else:
            return False
    except:
        return False


def is_valid_at(uart_at):

    try:
        if "mhitty" in uart_at and stat.S_ISCHR(os.lstat(uart_at)[stat.ST_MODE]):
            os.system("sudo chmod 666 %s" %uart_at)
            sleep(3)
    except:
        pass

    try:
        log.debug("Checking if %s is a valid AT port" % uart_at)
        ser = get_uart(uart_at)
        if not ser:
            return False

        ser.write(b'ATI\r\n')
        sleep(2)
        ser.readline()
        ser.readline()

        response = strip_at_response(ser.read_all().decode("utf-8").split('\r\n'))
        log.debug(response)
        ser.close()
        if 'OK' in response[-1]:
            return True
        else:
            return False
    except:
        return False

def is_valid_relay(uart_relay):

    try:
        if uart_relay:
            log.debug("Checking if %s is a valid relay port" % uart_relay)
            ser = get_uart(uart_relay, at=False)
            if not ser:
                return False

        ser.write(b'relay read\r\n')
        sleep(2)
        ser.readline()

        response = strip_at_response(ser.read_all().decode("utf-8").split('\r\n'))
        log.debug(response)
        ser.close()
        if '>' in response:
            return True
        else:
            return False
    except:
        return False

def is_valid_console(uart_console):

    try:
        if uart_console:
            log.debug("Checking if %s is a valid console port" % uart_console)
            ser = get_uart(uart_console, at=False)
            if not ser:
                return False

        ser.write(b'cd ~\r\n')
        sleep(2)
        ser.readline()

        response = strip_at_response(ser.read_all().decode("utf-8").split('\r\n'))
        log.debug(response)
        ser.close()
        expected_resp = ['sdxlemur login:', 'swi-sdx55 login:', 'Password:', '~ #', 'root@swi-sdx55:~#']
        match = set(expected_resp).intersection(response)
        if match:
            return True
        else:
            return False
    except:
        return False

def check_uart(uart1, uart2):

    if is_valid_cli(uart1) and is_valid_at(uart2):
        log.info("Found CLI port:%s AT port:%s" %(uart1,uart2))
        out = {
                'uart_at': uart2,
                'uart_cli': uart1
            }
        return out
    elif is_valid_cli(uart2) and is_valid_at(uart1):
        log.info("Found CLI port:%s AT port:%s" %(uart2,uart1))
        out = {
                'uart_at': uart1,
                'uart_cli': uart2
            }
        return out

    return None

def find_uart(uart_cli=default_cli, uart_at=default_at):

    log.info("Checking for UART cli at %s" % uart_cli)
    log.info("Checking for UART at at %s" % uart_at)

    out = check_uart(uart_cli,uart_at)
    if out:
        return out

    log.info(("UART settings appear to be invalid, "
              "attempting to find correct ports"))
    ports = comports(include_links=True)

    avail_ports = [ f for f in ports if usb_regex in f.device ]

    log.info("Found ports: %s" % [ f.device for f in avail_ports ])
    log.info("Checking if these ports are correct...")

    valid_at = None
    valid_cli = None
    for f in avail_ports:
        if is_valid_cli(f.device):
            valid_cli = f.device
        elif is_valid_at(f.device):
            valid_at = f.device

        if valid_at and valid_cli:
            out = {
                    'uart_at': valid_at,
                    'uart_cli': valid_cli
                }
            return out

    return None

def find_at(uart_at=default_at):

    for _ in range(6):
        log.info("Checking for UART AT port at %s" % uart_at)

        if is_valid_at(uart_at):
            log.info("Port appears to be valid.")
            out = {
                    'uart_at': uart_at,
                }
            return out

        log.info(("UART AT settings appear to be invalid, "
                "attempting to find correct port"))

        ports = comports(include_links=True)

        avail_ports = [ f for f in ports if usb_regex in f.device ]
        log.info("Found ports: %s" % [ f.device for f in avail_ports ])

        log.info("Checking if these ports are correct...")
        for f in avail_ports:
            log.info("Found ports: %s" % f.device)
            if is_valid_at(f.device):
                log.info("Port appears to be valid.")
                return {'uart_at': f.device,}

        if is_valid_at("/dev/mhitty1"):
            log.info("Port appears to be valid.")
            return {'uart_at': "/dev/mhitty1",}

        sleep(5)

    log.warning("Couldn't find valid UART AT port")
    return None

def find_cli(uart_cli=default_cli):

    for _ in range(6):
        log.info("Checking for UART CLI port at %s" % uart_cli)

        if is_valid_cli(uart_cli):
            log.info("Port appears to be valid.")
            out = {
                    'uart_cli': uart_cli,
                }
            return out


        log.info(("UART CLI settings appear to be invalid, "
                "attempting to find correct port"))

        ports = comports(include_links=True)

        avail_ports = [ f for f in ports if usb_regex in f.device ]
        log.info("Found ports: %s" % [ f.device for f in avail_ports ])
        log.info("Checking if these ports are correct...")
        for f in avail_ports:
            log.info("Found ports: %s" % f.device)
            if is_valid_cli(f.device):
                log.info("Port appears to be valid.")
                return {'uart_cli': f.device,}
        sleep(5)

    log.warning("Couldn't find valid UART CLI port")
    return None

def find_relay(uart_relay=default_relay):

    for _ in range(2):
        log.info("Checking for UART relay port at %s" % uart_relay)

        if is_valid_relay(uart_relay):
            log.info("Port appears to be valid.")
            out = {
                    'uart_relay': uart_relay,
                }
            return out

        log.info(("UART relay settings appear to be invalid, "
                "attempting to find correct port"))

        ports = comports(include_links=True)
        avail_ports = [ f for f in ports if relay_regex in f.device ]
        log.info("Found ports: %s" % [ f.device for f in avail_ports ])

        log.info("Checking if these ports are correct...")
        for f in avail_ports:
            log.info("Found ports: %s" % f.device)
            if is_valid_relay(f.device):
                log.info("Port appears to be valid.")
                return {'uart_relay': f.device,}

        sleep(5)

    log.warning("Couldn't find valid UART relay port")
    return None

def find_console(uart_console=default_console):

    for _ in range(2):
        log.info("Checking for UART console port at %s" % uart_console)

        if is_valid_console(uart_console):
            log.info("Port appears to be valid.")
            out = {
                    'uart_console': uart_console,
                }
            return out

        log.info(("UART console settings appear to be invalid, "
                "attempting to find correct port"))

        ports = comports(include_links=True)

        avail_ports = [ f for f in ports if usb_regex in f.device ]
        log.info("Found ports: %s" % [ f.device for f in avail_ports ])

        log.info("Checking if these ports are correct...")
        for f in avail_ports:
            log.info("Found ports: %s" % f.device)
            if is_valid_console(f.device):
                log.info("Port appears to be valid.")
                return {'uart_console': f.device,}

        sleep(5)

    log.warning("Couldn't find valid UART console port")
    return None

def init_console(uart_console=default_console, username='root', password=''):

        log.debug("Initialize %s Console port" % uart_console)
        ser = get_uart(uart_console, at=False)
        if not ser:
            return False

        # Check if console is ready
        ser.write(b'\r\n')
        sleep(2)
        ser.readline()
        response = ser.read_all().decode("utf-8").split('\r\n')
        log.debug(response)
        if '~ # ' in response or 'root@swi-sdx55:~# ' in response:
            log.info("Console port ready")
            return True

        # Clear the buffer until login prompt
        for _ in range(5):
            ser.write(b'\r\n')
            sleep(2)
            ser.readline()
            response = ser.read_all().decode("utf-8").split('\r\n')
            log.debug(response)
            if 'sdxlemur login: ' in response or 'swi-sdx55 login: ' in response:
                break

        # Login to console
        log.info("Attempting to login to console...")
        ser.write(b'%s\r\n' % username.encode())
        sleep(2)
        ser.readline()

        # Return if password is not required
        response = ser.read_all().decode("utf-8").split('\r\n')
        log.debug(response)
        if '~ # ' in response or 'root@swi-sdx55:~# ' in response:
            log.info("Console port ready")
            return True

        # Re-enter password again if unsuccessful
        for _ in range(2):
            ser.write(b'%s\r\n' % password.encode())
            sleep(2)
            ser.readline()
            response = ser.read_all().decode("utf-8").split('\r\n')
            log.debug(response)

            if '~ # ' in response or 'root@swi-sdx55:~# ' in response:
                log.info("Console port ready")
                return True

        log.warning("Unable to login to console!")
        return False
