#!/bin/bash

python dqn_test.py 0 0 > /home/ctfuzz/Desktop/saved/CTFuzz/readelf/1/readelf_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 0 1 > /home/ctfuzz/Desktop/saved/CTFuzz/readelf/1/readelf_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 1 0 > /home/ctfuzz/Desktop/saved/CTFuzz/strings/1/strings_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 1 1 > /home/ctfuzz/Desktop/saved/CTFuzz/strings/1/strings_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 2 0 > /home/ctfuzz/Desktop/saved/CTFuzz/size/1/size_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 2 1 > /home/ctfuzz/Desktop/saved/CTFuzz/size/1/size_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 3 0 > /home/ctfuzz/Desktop/saved/CTFuzz/objdump/1/objdump_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 3 1 > /home/ctfuzz/Desktop/saved/CTFuzz/objdump/1/objdump_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 4 0 > /home/ctfuzz/Desktop/saved/CTFuzz/nm/1/nm_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 4 1 > /home/ctfuzz/Desktop/saved/CTFuzz/nm/1/nm_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 5 0 > /home/ctfuzz/Desktop/saved/CTFuzz/pdfinfo/1/pdfinfo_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 5 1 > /home/ctfuzz/Desktop/saved/CTFuzz/pdfinfo/1/pdfinfo_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 6 0 > /home/ctfuzz/Desktop/saved/CTFuzz/pdfimages/1/pdfimages_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 6 1 > /home/ctfuzz/Desktop/saved/CTFuzz/pdfimages/1/pdfimages_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 7 0 > /home/ctfuzz/Desktop/saved/CTFuzz/pdfdetach/1/pdfdetach_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 7 1 > /home/ctfuzz/Desktop/saved/CTFuzz/pdfdetach/1/pdfdetach_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 8 0 > /home/ctfuzz/Desktop/saved/CTFuzz/pdftotext/1/pdftotext_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 8 1 > /home/ctfuzz/Desktop/saved/CTFuzz/pdftotext/1/pdftotext_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 9 0 > /home/ctfuzz/Desktop/saved/CTFuzz/pdftohtml/1/pdftohtml_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 9 1 > /home/ctfuzz/Desktop/saved/CTFuzz/pdftohtml/1/pdftohtml_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 10 0 > /home/ctfuzz/Desktop/saved/CTFuzz/pdftoppm/1/pdftoppm_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python dqn_test.py 10 1 > /home/ctfuzz/Desktop/saved/CTFuzz/pdftoppm/1/pdftoppm_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10
