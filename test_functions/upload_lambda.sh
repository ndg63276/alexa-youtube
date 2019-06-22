#!/bin/bash

gitroot=`git rev-parse --show-toplevel`

. config.cfg

function upload {
  local -n arr=$1
  if [[ ${arr[type]} == 'live' ]]; then
    region=${arr[region]}
    arn_no=${arr[arn]}
    name=${arr[name]}
    arn=arn:aws:lambda:$region:$arn_no:function:$name
    aws lambda --region $region update-function-code --function-name $arn --zip-file fileb://$gitroot/lambda_function.zip
  fi
}

upload config1
upload config2
upload config3
upload config4
upload config5
upload config6
upload config7
upload config8
upload config9
upload config10
