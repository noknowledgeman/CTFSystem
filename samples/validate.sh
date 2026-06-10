#!/bin/bash

SUBMISSION_ID=$1

curl -X POST http://localhost:8080/validate/${SUBMISSION_ID} 