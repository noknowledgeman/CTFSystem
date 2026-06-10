#!/bin/bash

SAMPLE="$1"

curl -X POST http://localhost:8080/submissions/upload \
    -F group_id=$SAMPLE -F archive="@./${SAMPLE}.zip"