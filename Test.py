import subprocess
import os
import argparse

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('Testbed_ID', 
                        help='List the Tesbed_ID to run the tests')
    parser.add_argument('Tests', nargs='*',
                        help='List of test/campaigns to run')
    return parser.parse_args()

def get_testbed_ip(id):
    try:
        ip_addr = subprocess.check_output(['./bed.sh', '-b', id])
        ip_addr = ip_addr.decode('ascii').split('\t')[1]
    except:
        raise ValueError('Testbed_ID not found')

    return ip_addr

def print_result(process):
    for line in process.stdout:
        if line == 'END\n':
            break

        print(line, end='')

        #Error Handler
        if 'Error' in line:
            raise line

    #to catch the lines up to logout
    for line in process.stdout: 
        print(line, end='')

def main():
    os.chdir(SCRIPT_PATH)
    args = get_args()

    cmd_letp = 'letp_wrap -y'
    cmd_ssh =  'sshpass -p vagrant ssh -tt vagrant@'

    for i in args.Tests:
        cmd_letp = cmd_letp + ' ' + i

    cmd_ssh = cmd_ssh+ get_testbed_ip(args.Testbed_ID)

    print('Test to run: ', args.Tests)
    print('Connect to Testbed: ', args.Testbed_ID)

    sshProcess = subprocess.Popen(cmd_ssh,
                                shell=True,
                                stdin=subprocess.PIPE, 
                                stdout=subprocess.PIPE,
                                universal_newlines=True,
                                bufsize=0)

    sshProcess.stdin.write('cd WorkDir/integration/letp_wrapper\n')
    sshProcess.stdin.write('source "$(pipenv --venv)/bin/activate"\n')
    sshProcess.stdin.write('source init_letp.sh\n')
    sshProcess.stdin.write(cmd_letp + '\n')
    sshProcess.stdin.write('echo END\n')
    sshProcess.stdin.write('logout\n')
    sshProcess.stdin.close()

    print_result(sshProcess)
    
if __name__ == '__main__':
    main()