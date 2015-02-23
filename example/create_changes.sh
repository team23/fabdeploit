#!/bin/bash

NUM_COMMITS=$[ $[ $RANDOM % 9 ] + 1 ]
COMMIT_COUNT=1

if [ ! -d test_repo ]
then
    git init test_repo
    echo 'Django' > test_repo/REQUIREMENTS
fi

cd test_repo || exit 1

while [ $COMMIT_COUNT -lt $NUM_COMMITS ]
do
    FILES_UPDATED=0
    # do about 15 updates per commit
    while [ $FILES_UPDATED -lt 15 ]
    do
        # max 30 files
        FILENAME=$[ $RANDOM % 50 ]
        if [ $[ $RANDOM % 5 ] -eq 0 ]
        then
            echo $RANDOM > $FILENAME
        else
            echo $RANDOM >> $FILENAME
        fi
        FILES_UPDATED=$[ $FILES_UPDATED + 1 ]
    done
    git add [0-9]* REQUIREMENTS
    git commit -m "`date +%s`.$COMMIT_COUNT"
    sleep 1
    COMMIT_COUNT=$[ $COMMIT_COUNT + 1 ]
done
