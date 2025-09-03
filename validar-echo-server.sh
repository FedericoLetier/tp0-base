#!/bin/bash

RESPONSE=$(timeout 5 docker run --rm --network=tp0_testing_net alpine sh -c "\
  apk add --no-cache netcat-openbsd && \
  echo 'ping' | nc -w 2 server 12345" | tail -n 1)

if [ "$RESPONSE" = "ping" ]; then
  echo "action: test_echo_server | result: success"
else
  echo "action: test_echo_server | result: fail"
fi
