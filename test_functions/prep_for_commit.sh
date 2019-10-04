#!/bin/bash

gitroot=`git rev-parse --show-toplevel`
rm $gitroot/lambda_function.zip 2>/dev/null
today=`date +"%d %b %Y"`
sed -i "/Last update/c\__Last update: ${today}__" $gitroot/README.md


GLOBIGNORE="*"
command="cd $gitroot; zip -r lambda_function.zip * -x \".git*\" -x \"test_functions*\" -x \"test_intents*\" -x \"InteractionModel*\""
for line in `cat $gitroot/.gitignore`; do
    command+=" -x \"$line\""
done
echo $command
#$command 
