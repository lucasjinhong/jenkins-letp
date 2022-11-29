import subprocess
import datetime
import os
import argparse
import paramiko

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--generate_report",
                    choices=["latest", "last", "none"],
                    help="Generate an HTML test report")
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
    flag = 0

    for line in iter(process.stdout.readline, ""):
        if line == 'END\n':
            break
        print(line, end='')

        #Error Handler
        if 'Error' in line:
            flag = 1

    #to catch the lines up to logout
    for line in iter(process.stdout.readline, ""): 
        print(line, end='')

    if flag == 1:
        raise Exception('Test Failed')

def main():
    os.chdir(SCRIPT_PATH)
    args = get_args()

    if len(args.Tests) < 1:
        raise ValueError('Test not found')

    cmd_letp = 'letp_wrap -y'
    cmd_ssh =  'sshpass -p vagrant ssh -tt vagrant@'

    if args.generate_report == 'latest':
        cmd_letp += ' -r latest'
    elif args.generate_report == 'last':
        cmd_letp += ' -r last'

    for i in args.Tests:
        cmd_letp = cmd_letp + ' ' + i

    testbed_ip = get_testbed_ip(args.Testbed_ID)
    cmd_ssh = cmd_ssh + testbed_ip

    print('Test to run: ', args.Tests)
    print('Connect to Testbed: ', args.Testbed_ID)

    ssh_process = subprocess.Popen(cmd_ssh,
                                shell=True,
                                stdin=subprocess.PIPE, 
                                stdout=subprocess.PIPE,
                                universal_newlines=True,
                                bufsize=0)

    ssh_process.stdin.write('cd WorkDir/integration/letp_wrapper\n')
    ssh_process.stdin.write('source "$(pipenv --venv)/bin/activate"\n')
    ssh_process.stdin.write('source init_letp.sh\n')
    ssh_process.stdin.write(cmd_letp + '\n')
    ssh_process.stdin.write('echo Clear Pycache File\n')
    ssh_process.stdin.write('rm -rf ~/WorkDir/integration/letp/sanity/HL78xx/__pycache__ \n')
    ssh_process.stdin.write('ls ~/WorkDir/integration/letp/sanity/HL78xx/__pycache__ \n')
    ssh_process.stdin.write('echo END\n')
    ssh_process.stdin.write('logout\n')
    ssh_process.stdin.close()

    print_result(ssh_process)
    
if __name__ == '__main__':
    main()