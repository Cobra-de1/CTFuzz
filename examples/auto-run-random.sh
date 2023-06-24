#!/bin/bash

python random_ctfuzz2.py 0 > /home/ctfuzz/Desktop/saved/random/readelf_2.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python random_ctfuzz2.py 1 > /home/ctfuzz/Desktop/saved/random/strings_2.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python random_ctfuzz2.py 2 > /home/ctfuzz/Desktop/saved/random/size_2.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python random_ctfuzz2.py 3 > /home/ctfuzz/Desktop/saved/random/objdump_2.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python random_ctfuzz2.py 4 > /home/ctfuzz/Desktop/saved/random/nm_2.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python random_ctfuzz2.py 5 > /home/ctfuzz/Desktop/saved/random/pdfinfo_2.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python random_ctfuzz2.py 6 > /home/ctfuzz/Desktop/saved/random/pdfimages_2.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python random_ctfuzz2.py 7 > /home/ctfuzz/Desktop/saved/random/pdfdetach_2.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python random_ctfuzz2.py 8 > /home/ctfuzz/Desktop/saved/random/pdftotext_2.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python random_ctfuzz2.py 9 > /home/ctfuzz/Desktop/saved/random/pdftohtml_2.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python random_ctfuzz2.py 10 > /home/ctfuzz/Desktop/saved/random/pdftoppm_2.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
