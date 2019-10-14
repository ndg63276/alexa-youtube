#!/bin/bash

arn="arn:aws:lambda:eu-west-1:175548706300:function:YouTubeTest"
region=`echo $arn | cut -d: -f4`

function_config=`aws lambda --region $region get-function-configuration --function-name $arn`
env_vars=`echo "$function_config" | jq -r ".Environment.Variables"`

echo $env_vars
