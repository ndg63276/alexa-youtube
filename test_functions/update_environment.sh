#!/bin/bash

new_key=$1
new_val=$2

function update {
	region=$1
	arn=$2
	function_config=`aws lambda --region $region get-function-configuration --function-name $arn`
	old_environment=`echo "$function_config" | jq  ".Environment"`
	new_environment=`echo "$old_environment" | jq ".Variables.$new_key = \"$new_val\""`
	aws lambda --region $region update-function-configuration --function-name $arn --environment "$new_environment"
}


regions="ap-northeast-1 eu-west-1 us-east-1 us-west-2"
for region in $regions; do
	function_list=`aws lambda --region $region list-functions`
	arn_list=`echo $function_list | jq -r ".Functions[].FunctionArn"`

	for arn in $arn_list; do
		tag_list=`aws lambda --region $region list-tags --resource $arn`
		if jq -e '.Tags | has("Patreon")' >/dev/null <<< $tag_list; then
			update $region $arn
		fi
	done
done

