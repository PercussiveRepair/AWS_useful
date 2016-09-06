#!/bin/bash
# Script to create IAM creds either from user input or cli option

set -e

function usage()
{
    msg 'iam_create.sh [hupl]'
    msg ''
    msg '    Creates IAM creds for the given users in the given account with the given access level'
    msg
    msg '    options:'
    msg '      -h this help'
    msg '      -u list of space separated users to create creds for in the form firstname.lastname'
    msg '      -p list of space separated AWS credentials profile names to use'
    msg '      -l level of access to grant (AdministratorAccess or ReadOnlyAccess)'
    msg '      -g GPG key to encrypt for'
}

# read any command line options
while getopts hu:p:l: opt; do
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

# if no cli options then ask for the
if [[ $OPTIND -eq 1 ]]; then
  PROFILE_LIST=`cat ~/.aws/credentials | grep "\[" | tr '\n' ' '`
  GPG_KEYS=`gpg --list-keys | grep uid | cut -d"<" -f 2 | cut -d">" -f 1`

  echo "Usernames, space separated"
  read USERS

  echo "AWS account profiles, space separated"
  echo $PROFILE_LIST
  read PROFILES

  echo "Access level - 1) AdministratorAccess or 2) ReadOnlyAccess"
  read LEVEL

  echo "GPG encrypt? y/N"
  read GPGYN

  if [[ $GPGYN = "y" ]]; then
    echo "Which user?"
    echo $GPG_KEYS
    read GPG
  fi
fi

if [[ $LEVEL == '1' ]]; then
  LEVEL='AdministratorAccess'
elif [[ $LEVEL == '2' ]]; then
  LEVEL='ReadOnlyAccess'
fi

for i in $USERS; do
  for p in $PROFILES; do
    echo "Username: $i" | tee -a $i.$p.creds
    CREATE=`aws --profile $p iam create-user --user-name $i`
    POLICY=`aws --profile $p iam attach-user-policy --policy-arn arn:aws:iam::aws:policy/$LEVEL --user-name $i`
    KEYS=`aws --profile $p iam create-access-key --user-name $i`
    PWD=`openssl rand -base64 12`
    PASS=`aws --profile $p iam create-login-profile --user-name $i --no-password-reset-required --password $PWD`
    ID=`echo $KEYS | cut -d "\"" -f 22`
    KEY=`echo $KEYS | cut -d "\"" -f 18`
    echo "Password: $PWD" | tee -a $i.creds
    echo "AWS_ID: $ID" | tee -a $i.creds
    echo "AWS_SECRET: $KEY" | tee -a $i.creds
    echo "URL: https://$p.signin.aws.amazon.com/console" | tee -a $i.$p.creds
    if [[ $GPGYN = "y" ]]; then
      gpg -e --trust-model always -r $GPG -o $i.$p.creds.gpg $i.creds
      rm $i.$p.creds
      echo "GPG encrypted to $i.$p.creds.gpg"
    fi
  done
done
