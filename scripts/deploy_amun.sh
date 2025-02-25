#!/bin/bash

URL=$1
DEPLOY=$2
ARCH=$3
SERVER=$(echo ${URL} | awk -F/ '{print $3}')
VERSION=1.8
TAGS=""

echo 'Creating docker-compose.yml...'
cat << EOF > ./docker-compose.yml
version: '2'
services:
    amun:
        image: stingar/amun${ARCH}:${VERSION}
        restart: always
        volumes:
            - ./amun.sysconfig:/etc/default/amun:z
            - ./amun:/etc/amun:z
        ports:
            - "445:445"
EOF
echo 'Done!'
echo 'Creating amun.sysconfig...'
cat << EOF > amun.sysconfig
# This file is read from /etc/default/amun
#
# This can be modified to change the default setup of the unattended installation

DEBUG=false

# IP Address of the honeypot
# Leaving this blank will default to the docker container IP
IP_ADDRESS=

# CHN Server api to register to
CHN_SERVER="${URL}"

# Server to stream data to
FEEDS_SERVER="${SERVER}"
FEEDS_SERVER_PORT=10000

# Deploy key from the FEEDS_SERVER administrator
# This is a REQUIRED value
DEPLOY_KEY=${DEPLOY}

# Registration information file
# If running in a container, this needs to persist
AMUN_JSON="/etc/amun/amun.json"

# Comma separated tags for honeypot
TAGS="${TAGS}"
EOF
echo 'Done!'
echo ''
echo ''
echo 'Type "docker-compose ps" to confirm your honeypot is running'
echo 'You may type "docker-compose logs" to get any error or informational logs from your honeypot'
