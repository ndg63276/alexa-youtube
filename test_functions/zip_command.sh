#!/bin/bash

gitroot=`git rev-parse --show-toplevel`
GLOBIGNORE="*"
rm $gitroot/lambda_function.zip 2>/dev/null
command="zip -r lambda_function.zip * -x \".git*\""
for line in `cat $gitroot/.gitignore`; do
    command+=" -x \"$line\""
done
echo $command
#$command 
