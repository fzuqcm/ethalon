#!/bin/bash

cd test_outputs
for file in $(find . -regextype posix-extended -regex '.*put_[0-9]{1}.txt')
do
	mv $file $(echo $file | sed 's/\(.*\)_/\1_0000/')
done
