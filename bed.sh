#!/bin/bash

usage() {
cat <<EOM
Usage: $0 -n <bench*> [-q] or
       $0 -b <bed*> [-q] or
       $0 -e <bed>
       $0 -r <bed> [-u <url>]
  -q : show name only
  -n : list bench VM or sites
  -b : list bed VM
  -e : enter bed VM
  -r : reboot bed VM
  -u : specify a farm URL

Examples:
 - List test beds and ssh into one
   $0 -d twtpe_5*
   ansible-playbook pb_bed.yml -l twtpe_50a6f_001a0
   $0 -ed twtpe_50a6f_001a0

 1. List sites
    $0 -n .
    $0 -n all
 2. List bench(es) info
    $0 -n twtpe
    $0 -n twtpe_1a743
    $0 -n loc
 3. List bed(s) info
    $0 -b twtpe
    $0 -b twtpe_1a*
    $0 -b twtpe_1a743_00140
 4. SSH to a bed
    $0 -e twtpe_1a743_08000
 5. SSH to a metal
    $0 -e twtpe_1a743
 6. Reboot or switch a bed to URL
    $0 -r twtpe_1a743_05000
    $0 -r twtpe_1a743_05000 -u "https://jenkins.legato/"

EOM
}

while getopts ":n:b:e:r:qh" o; do
  case "${o}" in
    q)
      name_only=1
      ;;
    n)
      bench=${OPTARG}
      if [ "$bench" = "loc" ]; then
        bench=$(nslookup gerrit.legato | grep '^Name:' | tail | awk '{print $2}' | cut -d. -f1)*
      elif [[ "$bench" =~ ^[a-z]{5}$ ]]; then
        bench=$bench*
      fi
      ;;
    b)
      bed=${OPTARG}
      if [[ "$bed" =~ ^[a-z]{5}$ || "$bed" =~ ^[a-z]{5}_[0-9a-f]{5}$ ]]; then
        bed=$bed*
      fi
      ;;
    e)
      enter=1
      bed=${OPTARG}
      if [ $(echo $bed | tr -cd '_' | wc -c) -eq 1 ]; then
        bed=m_${bed}
      fi
      ;;
    r)
      reset=1
      bed=${OPTARG}
      if [ $(echo $bed | tr -cd '_' | wc -c) -le 1 ]; then
        usage >&2
        exit 1
      fi
      ;;
    u)
      url=${OPTARG}
      ;;
    h)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 1
      ;;
  esac
  last_o="${o}"
done
shift $((OPTIND-1))
if [ -z "$bench$bed" ]; then
  usage >&2
  exit 1
fi

#show="set -x"

if [[ "$bench" =~ ^\.|-|all$ ]]; then
# speical name only listing

  if [ "$bench" = "all" ]; then
    sites=(`ansible-inventory --list | jq -r ".all.children | .[]"`)
    sites="${sites[@]}"
    sites="${sites// /|}"
    $show; ansible-inventory --list | jq -r ". | to_entries[] | select(.key|test(\"^($sites)_\")) | .key"
  else
    $show; ansible-inventory --list | jq -r ".all.children | .[]"
  fi

else
# list details or perform bed operations

  prefix=0
  if [ -z "$bed" ]; then
    bed=m_$bench
  fi
  if [[ "$bed" =~ \*$ ]]; then
    bed="${bed:0:-1}"
    prefix=1
  fi
  q_host=$bed
  if [ "$reset" = "1" ]; then
    q_host=m_$(echo $bed | sed -rn 's/^([^_]+_[^_]+).*/\1/p')
  fi
  query="._meta.hostvars | to_entries[]"
  if [ $prefix -eq 1 ]; then
    query="$query | select(.key|startswith(\"$q_host\"))"
  else
    query="$query | select(.key == \"$q_host\")"
  fi
  if [[ "$enter" = "1" || "$reset" = "1" ]]; then
    $show; vars=(`ansible-inventory --list | jq -r "$query | [.value.ansible_user, .value.ansible_ssh_pass, .value.ansible_ssh_host, .key] | @tsv" | head -n1`)
    set +x
    if [ ${#vars[@]} -eq 4 ]; then
      if [ "$enter" = "1" ]; then
        echo Entering ${vars[3]} - ${vars[0]}@${vars[2]} for ssh
        if [[ "$bed" =~ ^m_ ]]; then
          exec ssh ${vars[0]}@${vars[2]}
        else
          exec sshpass -p ${vars[1]} ssh ${vars[0]}@${vars[2]}
        fi
      else
        echo Entering ${vars[3]} - ${vars[0]}@${vars[2]} to reset
        VM_NAME=$(grep -B1 "^$q_host ansible" /etc/ansible/hosts | sed -rn 's/# (\S+).*/\1/p')-pci${bed##*_}
        exec ssh ${vars[0]}@${vars[2]} bash -c \
         "echo -n '{ \"name\": \"jenkins\", \"jenkins_url\": \"${url:-https://jenkins.legato/}\" }' | etcdctl set \"/testbench/testbeds/$VM_NAME/user\""
      fi
    fi
    echo "Invalid bed=$bed" >&2
  else
    if [ "$name_only" = "1" ]; then
      filter=".key"
    else
      filter="[.key, .value.ansible_ssh_host] | @tsv"
    fi
    $show; ansible-inventory --list | jq -r "$query | $filter"
  fi

fi
set +x
