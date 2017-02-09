#!/bin/bash
# Script to create IAM creds either from user input or cli option

function usage()
{
    echo 'iam_create.sh [huplg]'
    echo ''
    echo '    Creates IAM creds for the given users in the given account with the given access level'
    echo
    echo '    options:'
    echo '      -h this help'
    echo '      -u list of space separated users to create creds for in the form firstname.lastname'
    echo '      -p list of space separated AWS credential profile names to use'
    echo '      -l level of access to grant (AdministratorAccess or ReadOnlyAccess)'
    echo '      -g GPG key to encrypt for'
}

# read any command line options
while getopts hu:p:l:g opt; do
    case ${opt} in
        h) usage; exit 0;;
        u) USERS=${OPTARG};;
        p) PROFILES=${OPTARG};;
        l) LEVEL=${OPTARG};;
        g) GPG=${OPTARG};;
    esac
done

# shift away any command line options that
# have already been read
shift $((OPTIND-1))

# if no cli options then ask for them
if [[ $OPTIND -eq 1 ]]; then
  PROFILE_LIST=`cat ~/.aws/credentials | grep "\[" | sort -t[ -k2 | tr '\n' ' '`
  GPG_KEYS=`gpg --list-keys | grep uid | awk -F '[<>]' '{for (i=2; i<NF; i+=2) printf "<%s>%s", $i, OFS; print ""}' | sort -t'<' -k2 -f -u | tr '\n' ' '`

  echo "Usernames, space separated"
  read USERS

  echo "AWS account profiles, space separated"
  echo $PROFILE_LIST
  read PROFILES

  echo "Access level - 1) AdministratorAccess or 2) ReadOnlyAccess or type existing group name to join"
  read LEVEL

  echo "GPG encrypt? y/N"
  read GPGYN

  if [[ $GPGYN = "y" ]]; then
    echo "Which user?"
    echo $GPG_KEYS
    read GPG
  fi
fi

for i in $USERS; do
  for p in $PROFILES; do
    if echo $(aws --profile $p iam get-user --user-name $i) | grep $i; then
      echo "User exists!"
      exit 1
    fi
    echo "Username: $i" | tee -a $i.$p.creds
    CREATE=`aws --profile $p iam create-user --user-name $i`
    if [[ $LEVEL == '1' ]]; then
      POLICY=`aws --profile $p iam attach-user-policy --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --user-name $i`
    elif [[ $LEVEL == '2' ]]; then
      POLICY=`aws --profile $p iam attach-user-policy --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess --user-name $i`
    else
      GROUP=`aws --profile $p iam add-user-to-group --group-name $LEVEL --user-name $i`
    fi
   # POLICY=`aws --profile $p iam attach-user-policy --policy-arn arn:aws:iam::aws:policy/$LEVEL --user-name $i`
    KEYS=`aws --profile $p iam create-access-key --user-name $i`
    PWD=`openssl rand -base64 12`
    PASS=`aws --profile $p iam create-login-profile --user-name $i --no-password-reset-required --password $PWD`
    ID=`echo $KEYS | cut -d "\"" -f 22`
    KEY=`echo $KEYS | cut -d "\"" -f 18`
    echo "Password: $PWD" | tee -a $i.$p.creds
    echo "AWS_ID: $ID" | tee -a $i.$p.creds
    echo "AWS_SECRET: $KEY" | tee -a $i.$p.creds
    echo "URL: https://$p.signin.aws.amazon.com/console" | tee -a $i.$p.creds
    if [[ $GPGYN = "y" ]]; then
      gpg -e --trust-model always -r $GPG -o $i.$p.creds.gpg $i.$p.creds
      rm $i.$p.creds
      echo "GPG encrypted to $i.$p.creds.gpg"
    fi
  done
done
