#!/bin/bash

gitroot=`git rev-parse --show-toplevel`

regions="us-east-1
eu-west-1
us-west-2
ap-northeast-1
"

intents=`ls $gitroot/test_intents/`

for intent in $intents; do
  for region in $regions; do
    arn="arn:aws:lambda:$region:175548706300:function:YouTube"
    echo $arn $intent $region
    aws lambda --region $region invoke --function-name $arn --payload fileb://$gitroot/test_intents/$intent /dev/null | grep StatusCode
  done
done
