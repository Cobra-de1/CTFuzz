#!/bin/bash
#readelf
command_line="afl-fuzz -O -i /home/ctfuzz/Desktop/input_binary/in/elf/ -o /home/ctfuzz/Desktop/test/aflplusplus/readelf/1/out -- /home/ctfuzz/Desktop/input_binary/binary/binutils/readelf -a @@"
$command_line &
pid=$!
sleep 21603
kill -INT $pid
sleep 10

#strings
command_line="afl-fuzz -O -i /home/ctfuzz/Desktop/input_binary/in/elf/ -o /home/ctfuzz/Desktop/test/aflplusplus/strings/1/out -- /home/ctfuzz/Desktop/input_binary/binary/binutils/strings -a @@"
$command_line &
pid=$!
sleep 21603
kill -INT $pid
sleep 10

#size
command_line="afl-fuzz -O -i /home/ctfuzz/Desktop/input_binary/in/elf/ -o /home/ctfuzz/Desktop/test/aflplusplus/size/1/out -- /home/ctfuzz/Desktop/input_binary/binary/binutils/size -A -x -t @@"
$command_line &
pid=$!
sleep 21603
kill -INT $pid
sleep 10

# objdump
command_line="afl-fuzz -O -i /home/ctfuzz/Desktop/input_binary/in/elf/ -o /home/ctfuzz/Desktop/test/aflplusplus/objdump/1/out -- /home/ctfuzz/Desktop/input_binary/binary/binutils/objdump -a -f -x -d @@"
$command_line &
pid=$!
sleep 21603
kill -INT $pid
sleep 10

#nm
command_line="afl-fuzz -O -i /home/ctfuzz/Desktop/input_binary/in/elf/ -o /home/ctfuzz/Desktop/test/aflplusplus/nm/1/out -- /home/ctfuzz/Desktop/input_binary/binary/binutils/nm -C @@"
$command_line &
pid=$!
sleep 21603
kill -INT $pid
sleep 10


#pdfinfo
command_line="afl-fuzz -O -i /home/ctfuzz/Desktop/input_binary/in/pdf/ -o /home/ctfuzz/Desktop/test/aflplusplus/pdfinfo/1/out -- /home/ctfuzz/Desktop/input_binary/binary/poppler/pdfinfo -box @@"
$command_line &
pid=$!
sleep 21603
kill -INT $pid
sleep 10

#pdfimages
command_line="afl-fuzz -O -i /home/ctfuzz/Desktop/input_binary/in/pdf/ -o /home/ctfuzz/Desktop/test/aflplusplus/pdfimages/1/out -- /home/ctfuzz/Desktop/input_binary/binary/poppler/pdfimages -list -j @@"
$command_line &
pid=$!
sleep 21603
kill -INT $pid
sleep 10

#pdfdetach
command_line="afl-fuzz -O -i /home/ctfuzz/Desktop/input_binary/in/pdf/ -o /home/ctfuzz/Desktop/test/aflplusplus/pdfdetach/1/out -- /home/ctfuzz/Desktop/input_binary/binary/poppler/pdfdetach -list @@"
$command_line &
pid=$!
sleep 21603
kill -INT $pid
sleep 10

#pdftotext
command_line="afl-fuzz -O -i /home/ctfuzz/Desktop/input_binary/in/pdf/ -o /home/ctfuzz/Desktop/test/aflplusplus/pdftotext/1/out -- /home/ctfuzz/Desktop/input_binary/binary/poppler/pdftotext -htmlmeta @@"
$command_line &
pid=$!
sleep 21603
kill -INT $pid
sleep 10

#pdftohtml
command_line="afl-fuzz -O -i /home/ctfuzz/Desktop/input_binary/in/pdf/ -o /home/ctfuzz/Desktop/test/aflplusplus/pdftohtml/1/out -- /home/ctfuzz/Desktop/input_binary/binary/poppler/pdftohtml -stdout @@"
$command_line &
pid=$!
sleep 21603
kill -INT $pid
sleep 10

#pdftoppm
command_line="afl-fuzz -O -i /home/ctfuzz/Desktop/input_binary/in/pdf/ -o /home/ctfuzz/Desktop/test/aflplusplus/pdftoppm/1/out -- /home/ctfuzz/Desktop/input_binary/binary/poppler/pdftoppm -mono @@"
$command_line &
pid=$!
sleep 21603
kill -INT $pid