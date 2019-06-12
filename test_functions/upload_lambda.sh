#!/bin/bash

gitroot=`git rev-parse --show-toplevel`

regions="us-east-1
eu-west-1
us-west-2
ap-northeast-1
"

for region in $regions; do
  arn="arn:aws:lambda:$region:175548706300:function:YouTube"
  aws lambda --region $region update-function-code --function-name $arn --zip-file fileb://$gitroot/lambda_function.zip
done
