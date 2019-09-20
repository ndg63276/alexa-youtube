#!/bin/bash

gitroot=`git rev-parse --show-toplevel`

name=$1
region=$2

if [[ $region == "" ]]; then
	echo "Need name and region"
	exit
fi

DEVELOPER_KEY=`$gitroot/test_functions/get_developer_key.sh`
ROLE="arn:aws:iam::175548706300:role/lambda_basic_execution"

aws lambda --region $region create-function --function-name $name --runtime python2.7 --role $ROLE --handler lambda_function.lambda_handler --zip-file fileb://$gitroot/lambda_function.zip --timeout 10 --memory-size 512 --environment Variables={DEVELOPER_KEY=$DEVELOPER_KEY}

aws lambda --region $region add-permission --function-name $name --statement-id 1 --action "lambda:InvokeFunction" --principal "alexa-appkit.amazon.com"
