#!/bin/bash

cd examples
rm -rf checkpoint *.index *.data* *.png .afl-showmap* .ipynb_checkpoints *.pth
killall ex-frsv

