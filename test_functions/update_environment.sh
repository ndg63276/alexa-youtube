#!/bin/bash

tag=$1
new_key=$2
new_val=$3
shift 3
regions=$@

gitroot=`git rev-parse --show-toplevel`

function update {
	arn=$1
	region=`echo $arn | cut -d: -f4`
	function_config=`aws lambda --region $region get-function-configuration --function-name $arn`
	old_environment=`echo "$function_config" | jq  ".Environment"`
	new_environment=`echo "$old_environment" | jq ".Variables.$new_key = \"$new_val\""`
	aws lambda --region $region update-function-configuration --function-name $arn --environment "$new_environment"
}

arns=`$gitroot/test_functions/list_lambda_functions.sh $tag $regions`
for arn in $arns; do
	update $arn
done

