#!/bin/bash

gitroot=`git rev-parse --show-toplevel`

name=$1
region=$2
patreonamount=$3
patreon="$4 $5 $6"

if [[ ! "$region" =~ ^(us-east-1|us-west-2|eu-west-1|ap-northeast-1)$ ]]; then
	echo "Invalid region, must be one of us-east-1|us-west-2|eu-west-1|ap-northeast-1"
	exit
fi

if [[ $patreon == "  " ]]; then
	echo "Need name, region, patreon amount and patreon name"
	exit
fi

ENVIRONMENT_VARIABLES=`$gitroot/test_functions/get_environment_variables.sh $region`
ROLE="arn:aws:iam::175548706300:role/lambda_basic_execution"

environment="{ \"Variables\": $ENVIRONMENT_VARIABLES }"
tags="{\"PatreonAmount\":\"$patreonamount\",\"Patreon\":\"$patreon\" }"

aws lambda --region $region create-function --function-name $name --runtime python3.7 --role $ROLE --handler lambda_function.lambda_handler --zip-file fileb://$gitroot/lambda_function.zip --timeout 10 --memory-size 512 --environment "$environment" --tags "$tags"

aws lambda --region $region add-permission --function-name $name --statement-id 1 --action "lambda:InvokeFunction" --principal "alexa-appkit.amazon.com"
