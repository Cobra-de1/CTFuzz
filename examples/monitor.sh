#!/bin/bash
#readelf
x=0
while [ $x -eq 0 ]
do 
    a=$(grep "execs_done[^\d]*: 2....." /home/ctfuzz/Desktop/test/aflplusplus/readelf/2/out/default/fuzzer_stats 2> /dev/null)
    if [ ! -z "$a" ]; then
        cp /home/ctfuzz/Desktop/test/aflplusplus/readelf/2/out/default/fuzzer_stats /home/ctfuzz/Desktop/test/aflplusplus/readelf/2/out/default/fuzzer_stats_200000
        x=1
    fi
done
sleep 20

#strings
x=0
while [ $x -eq 0 ]
do 
    a=$(grep "execs_done[^\d]*: 2....." /home/ctfuzz/Desktop/test/aflplusplus/strings/2/out/default/fuzzer_stats 2> /dev/null)
    if [ ! -z "$a" ]; then
        cp /home/ctfuzz/Desktop/test/aflplusplus/strings/2/out/default/fuzzer_stats /home/ctfuzz/Desktop/test/aflplusplus/strings/2/out/default/fuzzer_stats_200000
        x=1
    fi
done
sleep 20

#size
x=0
while [ $x -eq 0 ]
do 
    a=$(grep "execs_done[^\d]*: 2....." /home/ctfuzz/Desktop/test/aflplusplus/size/2/out/default/fuzzer_stats 2> /dev/null)
    if [ ! -z "$a" ]; then
        cp /home/ctfuzz/Desktop/test/aflplusplus/size/2/out/default/fuzzer_stats /home/ctfuzz/Desktop/test/aflplusplus/size/2/out/default/fuzzer_stats_200000
        x=1
    fi
done
sleep 20

#objdump
x=0
while [ $x -eq 0 ]
do 
    a=$(grep "execs_done[^\d]*: 2....." /home/ctfuzz/Desktop/test/aflplusplus/objdump/2/out/default/fuzzer_stats 2> /dev/null)
    if [ ! -z "$a" ]; then
        cp /home/ctfuzz/Desktop/test/aflplusplus/objdump/2/out/default/fuzzer_stats /home/ctfuzz/Desktop/test/aflplusplus/objdump/2/out/default/fuzzer_stats_200000
        x=1
    fi
done
sleep 20

#nm
x=0
while [ $x -eq 0 ]
do 
    a=$(grep "execs_done[^\d]*: 2....." /home/ctfuzz/Desktop/test/aflplusplus/nm/2/out/default/fuzzer_stats 2> /dev/null)
    if [ ! -z "$a" ]; then
        cp /home/ctfuzz/Desktop/test/aflplusplus/nm/2/out/default/fuzzer_stats /home/ctfuzz/Desktop/test/aflplusplus/nm/2/out/default/fuzzer_stats_200000
        x=1
    fi
done
sleep 20

#pdfinfo
x=0
while [ $x -eq 0 ]
do 
    a=$(grep "execs_done[^\d]*: 2....." /home/ctfuzz/Desktop/test/aflplusplus/pdfinfo/2/out/default/fuzzer_stats 2> /dev/null)
    if [ ! -z "$a" ]; then
        cp /home/ctfuzz/Desktop/test/aflplusplus/pdfinfo/2/out/default/fuzzer_stats /home/ctfuzz/Desktop/test/aflplusplus/pdfinfo/2/out/default/fuzzer_stats_200000
        x=1
    fi
done
sleep 20

#pdfimages
x=0
while [ $x -eq 0 ]
do 
    a=$(grep "execs_done[^\d]*: 2....." /home/ctfuzz/Desktop/test/aflplusplus/pdfimages/2/out/default/fuzzer_stats 2> /dev/null)
    if [ ! -z "$a" ]; then
        cp /home/ctfuzz/Desktop/test/aflplusplus/pdfimages/2/out/default/fuzzer_stats /home/ctfuzz/Desktop/test/aflplusplus/pdfimages/2/out/default/fuzzer_stats_200000
        x=1
    fi
done
sleep 20

#pdfdetach
x=0
while [ $x -eq 0 ]
do 
    a=$(grep "execs_done[^\d]*: 2....." /home/ctfuzz/Desktop/test/aflplusplus/pdfdetach/2/out/default/fuzzer_stats 2> /dev/null)
    if [ ! -z "$a" ]; then
        cp /home/ctfuzz/Desktop/test/aflplusplus/pdfdetach/2/out/default/fuzzer_stats /home/ctfuzz/Desktop/test/aflplusplus/pdfdetach/2/out/default/fuzzer_stats_200000
        x=1
    fi
done
sleep 20

#pdftotext
x=0
while [ $x -eq 0 ]
do 
    a=$(grep "execs_done[^\d]*: 2....." /home/ctfuzz/Desktop/test/aflplusplus/pdftotext/2/out/default/fuzzer_stats 2> /dev/null)
    if [ ! -z "$a" ]; then
        cp /home/ctfuzz/Desktop/test/aflplusplus/pdftotext/2/out/default/fuzzer_stats /home/ctfuzz/Desktop/test/aflplusplus/pdftotext/2/out/default/fuzzer_stats_200000
        x=1
    fi
done
sleep 20

#pdftohtml
x=0
while [ $x -eq 0 ]
do 
    a=$(grep "execs_done[^\d]*: 2....." /home/ctfuzz/Desktop/test/aflplusplus/pdftohtml/2/out/default/fuzzer_stats 2> /dev/null)
    if [ ! -z "$a" ]; then
        cp /home/ctfuzz/Desktop/test/aflplusplus/pdftohtml/2/out/default/fuzzer_stats /home/ctfuzz/Desktop/test/aflplusplus/pdftohtml/2/out/default/fuzzer_stats_200000
        x=1
    fi
done
sleep 20

#pdftoppm
x=0
while [ $x -eq 0 ]
do 
    a=$(grep "execs_done[^\d]*: 2....." /home/ctfuzz/Desktop/test/aflplusplus/pdftoppm/2/out/default/fuzzer_stats 2> /dev/null)
    if [ ! -z "$a" ]; then
        cp /home/ctfuzz/Desktop/test/aflplusplus/pdftoppm/2/out/default/fuzzer_stats /home/ctfuzz/Desktop/test/aflplusplus/pdftoppm/2/out/default/fuzzer_stats_200000
        x=1
    fi
done
# sleep 20