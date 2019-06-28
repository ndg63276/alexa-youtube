#!/bin/bash

gitroot=`git rev-parse --show-toplevel`

. config.cfg

function upload {
  eval "declare -A arr="${1#*=}
  if [[ ${arr[type]} == 'live' ]]; then
    region=${arr[region]}
    arn_no=${arr[arn]}
    name=${arr[name]}
    arn=arn:aws:lambda:$region:$arn_no:function:$name
    aws lambda --region $region update-function-code --function-name $arn --zip-file fileb://$gitroot/lambda_function.zip
  fi
}

if [[ ${config1[type]} != "" ]]; then upload "$(declare -p config1)"; fi
if [[ ${config2[type]} != "" ]]; then upload "$(declare -p config2)"; fi
if [[ ${config3[type]} != "" ]]; then upload "$(declare -p config3)"; fi
if [[ ${config4[type]} != "" ]]; then upload "$(declare -p config4)"; fi
if [[ ${config5[type]} != "" ]]; then upload "$(declare -p config5)"; fi
if [[ ${config6[type]} != "" ]]; then upload "$(declare -p config6)"; fi
if [[ ${config7[type]} != "" ]]; then upload "$(declare -p config7)"; fi
if [[ ${config8[type]} != "" ]]; then upload "$(declare -p config8)"; fi
if [[ ${config9[type]} != "" ]]; then upload "$(declare -p config9)"; fi
if [[ ${config10[type]} != "" ]]; then upload "$(declare -p config10)"; fi

