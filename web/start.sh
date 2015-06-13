#!/bin/bash
# Set USERNAME and CONTROL_SERVICE env vars
PYTHONPATH=..:$PYTHONPATH twistd -noy server.tac
