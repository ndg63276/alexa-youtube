#!/bin/bash

gitroot=`git rev-parse --show-toplevel`

tag=$1

if [[ $tag == "" ]]; then
	echo "No tag specified, eg dev"
	exit
fi

function upload {
  arn=$1
  region=`echo $arn | cut -d: -f4`
  aws lambda --region $region update-function-code --function-name $arn --zip-file fileb://$gitroot/lambda_function.zip
}


if [[ $1 == *cfg ]]; then
	. $1
	if [[ ${config1[type]} != "" ]]; then
		region=${config1[region]}
		arn_no=${config1[arn]}
		name=${config1[name]}
		arn=arn:aws:lambda:$region:$arn_no:function:$name
		upload $arn
	fi
else
	arns=`$gitroot/test_functions/list_lambda_functions.sh $tag`
	for arn in $arns; do
		upload $arn
	done
fi
