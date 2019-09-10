#!/bin/bash

gitroot=`git rev-parse --show-toplevel`

if [[ $# == 0 ]]; then
  echo "No cfg file specified"
  exit
fi

. $1

have_downloaded=false

function download {
  eval "declare -A arr="${1#*=}
  if [[ ${arr[type]} == 'dev' ]]; then
    region=${arr[region]}
    arn_no=${arr[arn]}
    name=${arr[name]}
    arn=arn:aws:lambda:$region:$arn_no:function:$name
    url=$(aws lambda --region $region get-function --function-name $arn | grep Location |  cut -d'"' -f4)
    wget -O /tmp/aws.zip "$url"
    unzip -o /tmp/aws.zip lambda_function.py -d $gitroot
    rm /tmp/aws.zip
    have_downloaded=true
  else
    echo 1
  fi
}

if [[ $have_downloaded == false && ${config1[type]} != "" ]]; then download "$(declare -p config1)"; fi
if [[ $have_downloaded == false && ${config2[type]} != "" ]]; then download "$(declare -p config2)"; fi
if [[ $have_downloaded == false && ${config3[type]} != "" ]]; then download "$(declare -p config3)"; fi
if [[ $have_downloaded == false && ${config4[type]} != "" ]]; then download "$(declare -p config4)"; fi
if [[ $have_downloaded == false && ${config5[type]} != "" ]]; then download "$(declare -p config5)"; fi
if [[ $have_downloaded == false && ${config6[type]} != "" ]]; then download "$(declare -p config6)"; fi
if [[ $have_downloaded == false && ${config7[type]} != "" ]]; then download "$(declare -p config7)"; fi
if [[ $have_downloaded == false && ${config8[type]} != "" ]]; then download "$(declare -p config8)"; fi
if [[ $have_downloaded == false && ${config9[type]} != "" ]]; then download "$(declare -p config9)"; fi
if [[ $have_downloaded == false && ${config10[type]} != "" ]]; then download "$(declare -p config10)"; fi



