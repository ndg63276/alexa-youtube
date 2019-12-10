#!/bin/bash

region=$1
if [[ $region == "" ]]; then
	region=eu-west-1
fi

arn="arn:aws:lambda:${region}:175548706300:function:YouTubeTest"

function_config=`aws lambda --region $region get-function-configuration --function-name $arn`
env_vars=`echo "$function_config" | jq -r ".Environment.Variables"`

echo $env_vars
