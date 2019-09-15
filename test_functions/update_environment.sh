#!/bin/bash

if [[ $# == 0 ]]; then
  echo "Usage: $0 [cfg] [key] [val]"
  exit
fi

. $1
new_key=$2
new_val=$3

function update {
  eval "declare -A arr="${1#*=}
  region=${arr[region]}
  arn_no=${arr[arn]}
  name=${arr[name]}
  arn=arn:aws:lambda:$region:$arn_no:function:$name
  function_config=`aws lambda --region $region get-function-configuration --function-name $arn`
  old_environment=`echo "$function_config" | jq  ".Environment"`
  new_environment=`echo "$old_environment" | jq ".Variables.$new_key = \"$new_val\""`
  aws lambda --region $region update-function-configuration --function-name $arn --environment "$new_environment"
}

if [[ ${config1[type]} != "" ]]; then update "$(declare -p config1)"; fi
if [[ ${config2[type]} != "" ]]; then update "$(declare -p config2)"; fi
if [[ ${config3[type]} != "" ]]; then update "$(declare -p config3)"; fi
if [[ ${config4[type]} != "" ]]; then update "$(declare -p config4)"; fi
if [[ ${config5[type]} != "" ]]; then update "$(declare -p config5)"; fi
if [[ ${config6[type]} != "" ]]; then update "$(declare -p config6)"; fi
if [[ ${config7[type]} != "" ]]; then update "$(declare -p config7)"; fi
if [[ ${config8[type]} != "" ]]; then update "$(declare -p config8)"; fi
if [[ ${config9[type]} != "" ]]; then update "$(declare -p config9)"; fi
if [[ ${config10[type]} != "" ]]; then update "$(declare -p config10)"; fi

