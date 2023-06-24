#!/bin/bash

python old_rlfuzz.py 0 0 > /home/ctfuzz/Desktop/oldrlfuzz/readelf/1/readelf_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 0 1 > /home/ctfuzz/Desktop/oldrlfuzz/readelf/1/readelf_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 1 0 > /home/ctfuzz/Desktop/oldrlfuzz/strings/1/strings_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 1 1 > /home/ctfuzz/Desktop/oldrlfuzz/strings/1/strings_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 2 0 > /home/ctfuzz/Desktop/oldrlfuzz/size/1/size_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 2 1 > /home/ctfuzz/Desktop/oldrlfuzz/size/1/size_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 3 0 > /home/ctfuzz/Desktop/oldrlfuzz/objdump/1/objdump_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 3 1 > /home/ctfuzz/Desktop/oldrlfuzz/objdump/1/objdump_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 4 0 > /home/ctfuzz/Desktop/oldrlfuzz/nm/1/nm_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 4 1 > /home/ctfuzz/Desktop/oldrlfuzz/nm/1/nm_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 5 0 > /home/ctfuzz/Desktop/oldrlfuzz/pdfinfo/1/pdfinfo_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 5 1 > /home/ctfuzz/Desktop/oldrlfuzz/pdfinfo/1/pdfinfo_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 6 0 > /home/ctfuzz/Desktop/oldrlfuzz/pdfimages/1/pdfimages_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 6 1 > /home/ctfuzz/Desktop/oldrlfuzz/pdfimages/1/pdfimages_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 7 0 > /home/ctfuzz/Desktop/oldrlfuzz/pdfdetach/1/pdfdetach_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 7 1 > /home/ctfuzz/Desktop/oldrlfuzz/pdfdetach/1/pdfdetach_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 8 0 > /home/ctfuzz/Desktop/oldrlfuzz/pdftotext/1/pdftotext_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 8 1 > /home/ctfuzz/Desktop/oldrlfuzz/pdftotext/1/pdftotext_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 9 0 > /home/ctfuzz/Desktop/oldrlfuzz/pdftohtml/1/pdftohtml_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 9 1 > /home/ctfuzz/Desktop/oldrlfuzz/pdftohtml/1/pdftohtml_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 10 0 > /home/ctfuzz/Desktop/oldrlfuzz/pdftoppm/1/pdftoppm_train.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10

python old_rlfuzz.py 10 1 > /home/ctfuzz/Desktop/oldrlfuzz/pdftoppm/1/pdftoppm_test.txt &
pid=$!
sleep 21610
#sleep 61
kill -INT $pid
./clear.sh
sleep 10
