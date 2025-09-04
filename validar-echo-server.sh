#!/bin/bash

SERVER_PORT=$(grep -i 'SERVER_PORT' ./server/config.ini | head -n1 | cut -d'=' -f2 | tr -d ' ')

RESPONSE=$(timeout 5 docker run --rm --network=tp0_testing_net alpine sh -c "\
  apk add --no-cache netcat-openbsd && \
  echo 'ping' | nc -w 2 server $SERVER_PORT" | tail -n 1)

if [ "$RESPONSE" = "ping" ]; then
  echo "action: test_echo_server | result: success"
else
  echo "action: test_echo_server | result: fail"
fi
