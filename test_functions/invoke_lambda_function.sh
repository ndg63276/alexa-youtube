#!/bin/bash

gitroot=`git rev-parse --show-toplevel`

. config.cfg

function invoke {
  intent=$1
  local -n arr=$2
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
  invoke $intent config1
  invoke $intent config2
  invoke $intent config3
  invoke $intent config4
  invoke $intent config5
  invoke $intent config6
  invoke $intent config7
  invoke $intent config8
  invoke $intent config9
  invoke $intent config10
done
