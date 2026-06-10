#!/bin/bash
docker build -t django-challenge .
docker run -d --name django-challenge -p 8000:8000 django-challenge
