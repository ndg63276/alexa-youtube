#!/bin/bash

gitroot=`git rev-parse --show-toplevel`

. config.cfg

function invoke {
  intent=$1
  eval "declare -A arr="${2#*=}
  if [[ ${arr[type]} == 'live' ]]; then
    region=${arr[region]}
    arn_no=${arr[arn]}
    name=${arr[name]}
    arn=arn:aws:lambda:$region:$arn_no:function:$name
    echo $arn $intent $region
    aws lambda --region $region invoke --function-name $arn --payload fileb://$gitroot/test_intents/$intent /dev/null | grep StatusCode
  fi
}

intents=`ls $gitroot/test_intents/`

for intent in $intents; do
  if [[ ${config1[type]} != "" ]]; then invoke $intent "$(declare -p config1)"; fi
  if [[ ${config2[type]} != "" ]]; then invoke $intent "$(declare -p config2)"; fi
  if [[ ${config3[type]} != "" ]]; then invoke $intent "$(declare -p config3)"; fi
  if [[ ${config4[type]} != "" ]]; then invoke $intent "$(declare -p config4)"; fi
  if [[ ${config5[type]} != "" ]]; then invoke $intent "$(declare -p config5)"; fi
  if [[ ${config6[type]} != "" ]]; then invoke $intent "$(declare -p config6)"; fi
  if [[ ${config7[type]} != "" ]]; then invoke $intent "$(declare -p config7)"; fi
  if [[ ${config8[type]} != "" ]]; then invoke $intent "$(declare -p config8)"; fi
  if [[ ${config9[type]} != "" ]]; then invoke $intent "$(declare -p config9)"; fi
  if [[ ${config10[type]} != "" ]]; then invoke $intent "$(declare -p config10)"; fi
done
