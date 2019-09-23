#!/bin/bash

gitroot=`git rev-parse --show-toplevel`

name=$1
region=$2
patreonamount=$3
patreon="$4 $5 $6"

if [[ $patreon == "  " ]]; then
	echo "Need name, region, patreon amount and patreon name"
	exit
fi

DEVELOPER_KEY=`$gitroot/test_functions/get_developer_key.sh`
ROLE="arn:aws:iam::175548706300:role/lambda_basic_execution"

environment="{ \"Variables\":{\"DEVELOPER_KEY\":\"$DEVELOPER_KEY\" } }"
tags="{\"PatreonAmount\":\"$patreonamount\",\"Patreon\":\"$patreon\" }"

aws lambda --region $region create-function --function-name $name --runtime python2.7 --role $ROLE --handler lambda_function.lambda_handler --zip-file fileb://$gitroot/lambda_function.zip --timeout 10 --memory-size 512 --environment "$environment" --tags "$tags"

aws lambda --region $region add-permission --function-name $name --statement-id 1 --action "lambda:InvokeFunction" --principal "alexa-appkit.amazon.com"
