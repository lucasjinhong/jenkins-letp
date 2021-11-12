Bed control
================================

  * List/Enter desired testbench and testbed-VMS easily
  * Provide an ansible enviroment to check and troubleshoot issues
  * ansible (by Redhat) is simple and flexible, written in python, w/ yaml & jinja2 and excellent online doc

Installation
---------------

  * install python3
  * upgrade install pip with: pip3 install --upgrade pip
  * run ./setup.sh, this
    - installs the required python tools
    - create ansible inventory and config under /etc/ansible/ directory

Usage
---------------

  1. Refer to ./bed.sh -h
     1. List sites
        ```
        ./bed.sh -n .
        ./bed.sh -n all
        ```
     2. List bench(es) info
        ```
        ./bed.sh -n twtpe
        ./bed.sh -n twtpe_1a743
        ./bed.sh -n loc
        ```
     3. List bed(s) info
        ```
        ./bed.sh -b twtpe
        ./bed.sh -b twtpe_1a*
        ./bed.sh -b twtpe_1a743_00140
        ```
     4. SSH to a bed
        ```
        ./bed.sh -e twtpe_1a743_08000
        ```
     5. SSH to a metal
        ```
        ./bed.sh -e twtpe_1a743
        ```
     6. Reboot or switch a bed to URL
        ```
        ./bed.sh -r twtpe_1a743_05000
        ./bed.sh -r twtpe_1a743_05000 -u "https://jenkins.legato/"
        ```
  2. Running ansible ad-hoc commands
     - e.g. run uptime on beds of 3 benches
     ```
     ansible -a uptime twtpe_1a743:twtpe_50a6f:twtpe_79a53
     ```
  3. Update environment - for twtpe
     - refer to roles/env/tasks/env_install.yml
     ```
     ansible-playbook pb_env.yml -l twtpe_79a53
     ```
  4. Show USB status of test beds
     - refer to roles/bed/tasks/bed_status.yml
     ```
     ansible-playbook pb_bed.yml -l twtpe_50a6f
     ```
  5. Run some basic AT (ATI3, AT+CGSN, AT+CCID) on the test beds
     - refer to roles/bed/tasks/bed_check_hl78.yml
     ```
     ansible-playbook pb_bed.yml -e main=check_hl78 -l 'twtpe_50a6f_001d0:twtpe_50a6f_0[34]000'
     ```
