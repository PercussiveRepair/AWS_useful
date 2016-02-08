#!/bin/bash
# Script to create IAM creds either from user input or cli option using aws credentials file

function usage()
{
    msg 'iam_create.sh [hupl]'
    msg ''
    msg '    Creates IAM creds for the given users in the given account with the given access level'
    msg
    msg '    options:'
    msg '      -h this help'
    msg '      -u list of space separated users to create creds for in the form firstname.lastname'
    msg '      -p AWS credentials profile name to use (AdministratorAccess or ReadOnlyAccess)'
    msg '      -l level of access to grant'
}

# read any command line options
while getopts hu:p:l: opt; do
    case ${opt} in
        h) usage; exit 0;;
        u) USERS=${OPTARG};;
        p) PROFILE=${OPTARG};;
        l) LEVEL=${OPTARG};;
    esac
done

# shift away any command line options that
# have already been read
shift $((OPTIND-1))

# if no cli options then ask for the 
if [ $OPTIND -eq 1 ]; then
  PROFILES=`cat ~/.aws/credentials | grep "\[" | tr '\n' ' '`

  echo "Usernames, space separated"
  read USERS

  echo "AWS profile name from:" 
  echo $PROFILES
  read PROFILE

  echo "Access level - 1) AdministratorAccess or 2) ReadOnlyAccess"
  read LEVEL
fi

if [ $LEVEL == '1' ]; then
  LEVEL='AdministratorAccess'
elif [ $LEVEL == '2' ]; then
  LEVEL='ReadOnlyAccess'
fi

for i in $USERS
  do echo "Username: $i"
  CREATE=`aws --profile $PROFILE iam create-user --user-name $i` 
  POLICY=`aws --profile $PROFILE iam attach-user-policy --policy-arn arn:aws:iam::aws:policy/$LEVEL --user-name $i`
  KEYS=`aws --profile $PROFILE iam create-access-key --user-name $i` 
  PWD=`openssl rand -base64 12`
  PASS=`aws --profile $PROFILE iam create-login-profile --user-name $i --no-password-reset-required --password $PWD`
  ID=`echo $KEYS | cut -d "\"" -f 22`
  KEY=`echo $KEYS | cut -d "\"" -f 18` 
  echo "Password: $PWD"
  echo "AWS_ID: $ID"
  echo "AWS_SECRET: $KEY"
  echo "URL: https://$PROFILE.signin.aws.amazon.com/console"
  done
