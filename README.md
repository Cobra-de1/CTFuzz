# CTFuzz: A coverage-guided fuzzing tools with reinforcement learning

## Workflow and architect of CTFuzz

CTFuzz is a coverage-guided fuzzing tools with reinforcement learning. The workflow and architect can see below.

![ctfuzz](https://github.com/Cobra-de1/CTFuzz/assets/57558487/fd278a78-d2f1-4009-b07b-5e63ff895254)

CTFuzz use coverage instrumentation method provide by [AFLplusplus](https://github.com/AFLplusplus/AFLplusplus) version 4.05c

## Install requiment

- OS: ubuntu 20.04

- Python: Python 3.8.10

- pip: pip 20.0.2

## Install afl

```bash
sudo apt-get install -y build-essential python3-dev automake cmake git flex bison libglib2.0-dev libpixman-1-dev python3-setuptools cargo libgtk-3-dev
sudo apt install -y gcc-multilib g++-multilib
sudo apt-get install -y gcc-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-plugin-dev libstdc++-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-dev
cd ctfuzz/afl/
unzip 4.05c.zip
cd AFLplusplus-4.05c
cp ../ex-frsv.c ../afl-fuzz-* src
cp ../afl-fuzz.h include
cp ../GNUmakefile .
cd frida_mode
make
cd ../
make all
sudo make install
```

## Install CTFuzz
```bash
pip install .
```

## Install reinforcement learning library
```bash
pip install -r requirements.txt
```
