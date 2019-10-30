#!/bin/bash

gitroot=`git rev-parse --show-toplevel`
rm $gitroot/lambda_function.zip 2>/dev/null
find . -type f -name *~ -exec rm -rf {} \;
find . -type d -name __pycache__ -exec rm -rf {} \;
find . -type f -name *.py[cod] -exec rm -rf {} \;
find . -type f -name *\$py.class -exec rm -rf {} \;
today=`date +"%d %b %Y"`
sed -i "/Last update/c\__Last update: ${today}__" $gitroot/README.md


GLOBIGNORE="*"
command="cd $gitroot; zip -r lambda_function.zip * -x \".git*\" -x \"test_functions*\" -x \"test_intents*\" -x \"InteractionModel*\""
echo $command
