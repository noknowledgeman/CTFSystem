#!/bin/bash

SUBMISSION_ID=$1

curl -X POST http://localhost:8080/admin/review/${SUBMISSION_ID} \
    -H "Content-Type: application/json" \
    -d '{"decision": "approve", "notes": "This was manually approved"}'