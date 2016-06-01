#!/bin/sh -e

# send file to s3 via curl

s3Key=""
s3Secret=""
file="FILE"
awsPath="/path/"
bucket="bucket_name"
contentType="text/plain"

resource="/${bucket}${awsPath}${file}"
date=$(TZ=UTC date "+%a, %d %b %Y %T %z")
echo $date

string="PUT\n\n${contentType}\n${date}\n${resource}"
signature=$(echo -en ${string} | openssl sha1 -hmac ${s3Secret} -binary | base64)

echo "Sending file"
echo "content" > FILE
echo " file: "
cat FILE
curl -v -L -X PUT -T "${file}" \
        -H "Host: ${bucket}.s3.amazonaws.com" \
        -H "Date: ${date}" \
        -H "Content-Type: ${contentType}" \
        -H "Authorization: AWS ${s3Key}:${signature}" \
        https://${bucket}.s3.amazonaws.com${awsPath}${file}

echo "file sent to s3"
