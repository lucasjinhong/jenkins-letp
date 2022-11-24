#!/bin/bash

# Set up ansible for accessing test beds VM
#
# Usage: ./ans_cfg.sh [<output>] [<filter>]
#
#  When <output> is empty,
#   1. Call farm cli to get a list of test beds
#   2. Install ansible, and patch python2.7 to avoid some deprecated warnings
#   3. Create an ansible inventory INI file for access
#   4. Run some ansible ad-hoc commands as an example
#
#  When <output> is non-empty,
#   Retrieve all test beds
#
# Examples:
#
#   1. Update/Install the ansible configurations, for all test beds
#      ./ans_cfg.sh
#
#   2. Create an inventory INI file only
#      ./ans_cfg.sh myinv.txt
#

output=$1
filter=${2:-.}

if [ ! -d farmctrl ]; then
  git clone git://gerrit.legato/farm-control.git farmctrl
  (cd farmctrl/cli; sudo -u admin pip3 install -r requirements.txt)
else
  (cd farmctrl; git pull origin master)
fi

farm_cli=$PWD/farmctrl/cli/farm
tb_list=$(basename "$0")
tb_list=/tmp/${tb_list%.*}_${RANDOM}

# get the list from farm cli
while true; do
  timeout 5 bash -c "$farm_cli host list --name *-er-lxtb* | tail -n +3 > $tb_list.tmp " && break
  echo Retry $farm_cli host list >&2
  sleep 30
done

cat $tb_list.tmp | \
 sed -rn 's/^(([^-]+)-er-lxtb[0-9a-f]+([0-9a-f]{5})-pci(\S+)) +vm +.* (([0-9]+\.){3}[0-9]+).*/\1 \2 \3 \4 \5/p' > $tb_list.txt
cat $tb_list.tmp | \
 sed -rn 's/^(([^-]+)-er-lxtb[0-9a-f]+([0-9a-f]{5})) +metal +.* (([0-9]+\.){3}[0-9]+).*/\1 \2 \3 x \4/p' >> $tb_list.txt

# create INI inventory file
create_ansible_inventory() {

lst_gp_site=()
lst_gp_tb=()
is_metal=0
while read -r line ; do
  vars=($line)

  site_name="gp_site_${vars[1]}"
  check="echo \${#$site_name[@]}"
  if [ `eval $check` -eq 0 ]; then
    echo
    lst_gp_site+=($site_name)
  fi

  if [ "${vars[3]}" = "x" ]; then
    if [ $is_metal -eq 0 ]; then
      echo
      is_metal=1
    fi
    cat <<EOM
# ${vars[0]}
m_${vars[1]}_${vars[2]} ansible_ssh_host=${vars[4]}
EOM
  else
    tb_name="gp_tb_${vars[1]}_${vars[2]}"
    check="echo \${#$tb_name[@]}"
    if [ `eval $check` -eq 0 ]; then
      eval "$site_name+=(${vars[1]}_${vars[2]})"
      echo
      lst_gp_tb+=($tb_name)
    fi
    eval "$tb_name+=(${vars[1]}_${vars[2]}_${vars[3]})"

    cat <<EOM
# ${vars[0]}
${vars[1]}_${vars[2]}_${vars[3]} ansible_ssh_host=${vars[4]}
EOM
  fi
done < <(cat $tb_list.txt | grep $filter)
rm -f $tb_list.txt $tb_list.tmp

for i in ${lst_gp_tb[@]}; do
  check="echo \${$i[@]}"
  cat <<EOM

[${i#gp_tb_}]
`for g in $(eval $check); do
echo $g
done;`
EOM
done

for i in ${lst_gp_site[@]}; do
  check="echo \${$i[@]}"
  cat <<EOM

[${i#gp_site_}:children]
`for g in $(eval $check); do
echo $g
done;`
EOM
done

for i in ${lst_gp_site[@]}; do
  check="echo \${$i[@]}"
  cat <<EOM

[m_${i#gp_site_}]
`for g in $(eval $check); do
echo m_$g
done;`
EOM
done

cat <<EOM

[m_all:children]
`for i in ${lst_gp_site[@]}; do
echo m_${i#gp_site_}
done;`

[m_all:vars]
ansible_user=core
ansible_become_pass=core
ansible_ssh_common_args=''

[all:children]
`for i in ${lst_gp_site[@]}; do
echo ${i#gp_site_}
done;`

[all:vars]
ansible_user=vagrant
ansible_ssh_pass=vagrant
ansible_become_pass=vagrant
ansible_ssh_common_args='-F /dev/null'
ansible_python_interpreter=/usr/bin/python3

EOM

}

if [ -n "$output" ]; then
  # just create output inventory file
  create_ansible_inventory > $output
else
  # configure ansible and install the inventory file

  #install required packages
  python3 -c "import ansible" || {
    sudo -u admin pip3 install 'ansible<v2.10' mitogen
    # ensure python3 is used
    sudo -u admin sed -i '1s@/usr/bin/python$@/usr/bin/python3@' /usr/local/bin/ansible
  }

  config_line="# farm-control configured - 21-11-11"
  if [ ! -f /etc/ansible/ansible.cfg ] || ! grep -q -- "^$config_line" /etc/ansible/ansible.cfg ; then
    sudo -u admin mkdir -p /etc/ansible
    { cat <<EOM
[defaults]
inventory = /etc/ansible/hosts
interpreter_python = auto_silent
host_key_checking = False

strategy_plugins = /var/jenkins_home/.local/lib/python3.9/site-packages/ansible_mitogen/plugins/strategy
strategy = mitogen_linear

callback_whitelist = profile_tasks
stdout_callback = yaml

$config_line
EOM
    } | sudo -u admin tee /etc/ansible/ansible.cfg
  fi

  # install the inventory file
  create_ansible_inventory | sudo -u admin tee /etc/ansible/hosts >/dev/null

  if false; then
    site=$(nslookup gerrit.legato | grep '^Name:' | tail | awk '{print $2}' | cut -d. -f1)
    # run some test as a demo
    set -x
    first_kid=$(ansible-inventory --list | jq -r ".${site}.children[0]")
    #ansible-inventory --list --yaml
    #ansible-inventory --graph
    ansible-inventory --list | jq -r ".${site}.children"
    ansible-inventory --list | jq -r ".${first_kid}.hosts"
    #ansible-inventory --list | jq -r "._meta.hostvars.twtpe_1a743_08000"
    ansible-inventory --list | jq -r "._meta.hostvars | to_entries[] | select(.key|startswith(\"${first_kid}\")) | [.key, .value.ansible_ssh_host]"
    ansible ${first_kid} -a uptime
    #ansible ${first_kid} -a "bash -c 'lsusb || true'"
    set +x
  fi
fi
