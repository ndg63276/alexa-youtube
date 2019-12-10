#!/bin/bash

tag=$1
shift
regions=$@
if [[ $regions == "" ]]; then
	regions="ap-northeast-1 eu-west-1 us-east-1 us-west-2"
fi

for region in $regions; do
	function_list=`aws lambda --region $region list-functions`
	arn_list=`echo $function_list | jq -r ".Functions[].FunctionArn"`

	for arn in $arn_list; do
		tag_list=`aws lambda --region $region list-tags --resource $arn`
		if jq -e ".Tags | has(\"$tag\")" >/dev/null <<< $tag_list; then
			echo $arn
		fi
	done
done

