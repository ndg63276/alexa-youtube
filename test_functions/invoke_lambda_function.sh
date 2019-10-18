#!/bin/bash

gitroot=`git rev-parse --show-toplevel`

if [[ $# == 0 ]]; then
  echo "No cfg or arn file specified"
  exit
fi

function invoke {
	intent=$1
	arn=$2
	region=`echo $arn | cut -d: -f4`
	echo
	echo $intent
	aws lambda --region $region invoke --function-name $arn --payload fileb://$gitroot/test_intents/$intent /tmp/output.txt | grep StatusCode
	cat /tmp/output.txt
	echo
}

intents=`ls $gitroot/test_intents/`

for intent in $intents; do
	if [[ $1 == arn* ]]; then
		invoke $intent $1
	else
		. $1
		if [[ ${config1[type]} != "" ]]; then
			region=${config1[region]}
			arn_no=${config1[arn]}
			name=${config1[name]}
			arn=arn:aws:lambda:$region:$arn_no:function:$name
			invoke $intent $arn
		fi
	fi
done

rm /tmp/output.txt 2>/dev/null
