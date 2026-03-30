#!/bin/bash
echo "Cloning Smartsheet WireMock server..."
if [ ! -d "smartsheet-sdk-tests" ]; then
  git clone https://github.com/smartsheet/smartsheet-sdk-tests.git
fi
cd smartsheet-sdk-tests
echo "Starting WireMock on http://localhost:8082 ..."
docker compose up -d
echo "WireMock is running. Mappings loaded from ./mappings/"
echo "Test it: curl http://localhost:8082/2.0/sheets"
