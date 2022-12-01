import subprocess
import datetime
import os
import argparse
import paramiko
from re import findall

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--generate_report',
                    choices=['latest', 'last', 'none'],
                    help='Generate an HTML test report')
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

def get_test_report(ip_addr, time, remote_path, version_name):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=ip_addr, username='vagrant', password='vagrant')
    ftp_client=ssh_client.open_sftp()

    dir_name = remote_path.split('/')[0]
    remote_path = '/home/vagrant/WorkDir/integration/' + remote_path
    local_path = '/home/lkoh/TestBed_Control/bed-control/Testing/' + version_name + '/'

    # check if local directory exits
    try:
        os.mkdir(local_path)        # Create version directory
    except:
        pass

    try:
        local_path = local_path + time  + '/'
        os.mkdir(local_path)        # Create Time directory
    except:
        pass
    
    # Create Log or Report files directory
    local_path = local_path + dir_name + '/'
    os.mkdir(local_path)

    remote_files = ftp_client.listdir(remote_path)
    print('moving', remote_path, 'to', local_path)

    # move file from remote to local
    for file in remote_files:
        remote_file_path = remote_path + file
        local_file_path = local_path + file
        ftp_client.get(remote_file_path,local_file_path)
    ftp_client.close()
    
    # for upload file to jasmine2
    local_path = '/'.join(local_path.split('/')[:-1]) + '/'

    return local_path

def publish_test_report(version_name, local_path):
    jasmine2_path = '//jasmine2/Projects-1/Engineering/Firmware/Releases/Internal/HL78XX/integration/Jenkins_Local_Test/'
    time = local_path.split('/')[-3]
    jasmine2_dir_name = local_path.split('/')[-2]

    print('publish', local_path, 'to', jasmine2_path)
    subprocess.run(['smbclient', jasmine2_path, '-c', 'prompt OFF'
                    + '; mkdir ' + version_name + '; cd ' + version_name 
                    + '; mkdir ' + time + '; cd ' + time
                    + '; mkdir ' + jasmine2_dir_name + '; cd ' + jasmine2_dir_name 
                    + '; lcd ' + local_path 
                    + '; mput *', '-Ulkoh', '-W SIERRAWIRELESS', 'Jinhong253'
                    ])
    return

def print_result(process):
    flag = 0
    log_path = ''
    report_path = ''

    for line in iter(process.stdout.readline, ''):
        if line == 'END\n':
            break
        print(line, end='')

        # Error Handler
        if 'Error' in line:
            flag = 1

        # get path of logs and reports
        if 'letp_wrapper_logs' in line:
            log_path = line
        elif 'letp_wrapper_reports' in line:
            report_path = line

    if flag == 1:
        raise

    log_path = ''.join(x for x in findall(r'[\w+.+]+/', log_path)[-4:])
    report_path = ''.join(x for x in findall(r'[\w+.+]+/', report_path)[-2:])

    return log_path, report_path

def main():
    os.chdir(SCRIPT_PATH)
    args = get_args()
    time = str(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    local_path = []

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

    print('\nTest to run: ', args.Tests)
    print('Connect to Testbed: ', args.Testbed_ID, '\n')

    ssh_process = subprocess.Popen(cmd_ssh,
                                shell=True,
                                stdin=subprocess.PIPE, 
                                stdout=subprocess.PIPE,
                                universal_newlines=True,
                                bufsize=0)

    print('Test START\n')
    # Call letp_wrap command
    ssh_process.stdin.write('cd WorkDir/integration/letp_wrapper\n')
    ssh_process.stdin.write('source "$(pipenv --venv)/bin/activate"\n')
    ssh_process.stdin.write('source init_letp.sh\n')
    ssh_process.stdin.write(cmd_letp + '\n')

    # Clear Pycache File
    ssh_process.stdin.write('rm -rf ~/WorkDir/integration/letp/sanity/HL78xx/__pycache__ \n')
    ssh_process.stdin.write('ls ~/WorkDir/integration/letp/sanity/HL78xx/__pycache__ \n')

    ssh_process.stdin.write('logout\n\n')
    ssh_process.stdin.close()

    # Take path of log and report and print_result of test
    log_path, report_path = print_result(ssh_process)
    print('\nTest END')

    version_name = log_path.split('/')[2]

    # Getting remote directory to local
    print('\nStart Getting Logs and Reports directory')
    for path in [log_path, report_path]:
        if len(path) > 0:
            local_path.append(get_test_report(testbed_ip, time, path, version_name))

    print('\nStart Publishing Logs and reports to Jasmine2')
    for path in local_path:
        print('\nPublishing: ' + path.split('/')[-2])
        publish_test_report(version_name, path)

    print('\nDONE')
    
if __name__ == '__main__':
    main()