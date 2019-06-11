#!/bin/bash

gitroot=`git rev-parse --show-toplevel`

aws lambda --region eu-west-1 update-function-code --function-name arn:aws:lambda:eu-west-1:175548706300:function:YouTube --zip-file fileb://$gitroot/lambda_function.zip
aws lambda --region ap-northeast-1 update-function-code --function-name arn:aws:lambda:ap-northeast-1:175548706300:function:YouTube --zip-file fileb://$gitroot/lambda_function.zip
aws lambda --region us-east-1 update-function-code --function-name arn:aws:lambda:us-east-1:175548706300:function:YouTube --zip-file fileb://$gitroot/lambda_function.zip
aws lambda --region us-west-2 update-function-code --function-name arn:aws:lambda:us-west-2:175548706300:function:YouTube --zip-file fileb://$gitroot/lambda_function.zip
