/*
   american fuzzy lop++ - map display utility
   ------------------------------------------

   Originally written by Michal Zalewski

   Forkserver design by Jann Horn <jannhorn@googlemail.com>

   Now maintained by Marc Heuse <mh@mh-sec.de>,
                        Heiko Eißfeldt <heiko.eissfeldt@hexco.de> and
                        Andrea Fioraldi <andreafioraldi@gmail.com> and
                        Dominik Maier <mail@dmnk.co>

   Copyright 2016, 2017 Google Inc. All rights reserved.
   Copyright 2019-2023 AFLplusplus Project. All rights reserved.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at:

     https://www.apache.org/licenses/LICENSE-2.0

   A very simple tool that runs the targeted binary and displays
   the contents of the trace bitmap in a human-readable form. Useful in
   scripts to eliminate redundant inputs and perform other checks.

   Exit code is 2 if the target program crashes; 1 if it times out or
   there is a problem executing it; or 0 if execution is successful.

 */

#define AFL_MAIN

#include "config.h"
#include "types.h"
#include "debug.h"
#include "alloc-inl.h"
#include "hash.h"
#include "sharedmem.h"
#include "forkserver.h"
#include "common.h"
#include "hash.h"

#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include <signal.h>
#include <dirent.h>
#include <fcntl.h>
#include <limits.h>

#include <semaphore.h>

#include <dirent.h>
#include <sys/wait.h>
#include <sys/time.h>
#include <sys/shm.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/resource.h>

#define SHARED_MEM_SIZE 65541
#define SHARED_MEM_NAME "/shared_mem"
#define SEM_INPUT_NAME "/sem_input"
#define SEM_OUTPUT_NAME "/sem_output"

static char *shared_mem;
static sem_t *sem_input, *sem_output;

static char *stdin_file;               /* stdin file                        */

static u8 *in_dir = NULL,              /* input folder                      */
    *out_file = NULL, *at_file = NULL;        /* Substitution string for @@ */

static u8 outfile[PATH_MAX];

static u8 *in_data,                    /* Input data                        */
    *coverage_map;                     /* Coverage map                      */

static u64 total;                      /* tuple content information         */
static u32 tcnt, highest;              /* tuple content information         */

static u32 in_len;                     /* Input data length                 */

static u32 map_size = MAP_SIZE, timed_out = 0;

static bool quiet_mode,                /* Hide non-essential messages?      */
    edges_only,                        /* Ignore hit counts?                */
    raw_instr_output,                  /* Do not apply AFL filters          */
    cmin_mode,                         /* Generate output in afl-cmin mode? */
    binary_mode,                       /* Write output as a binary map      */
    keep_cores,                        /* Allow coredumps?                  */
    remove_shm = true,                 /* remove shmem?                     */
    collect_coverage,                  /* collect coverage                  */
    have_coverage,                     /* have coverage?                    */
    no_classify,                       /* do not classify counts            */
    debug,                             /* debug mode                        */
    print_filenames,                   /* print the current filename        */
    wait_for_gdb;

static volatile u8 stop_soon,          /* Ctrl-C pressed?                   */
    child_crashed;                     /* Child crashed?                    */

static sharedmem_t       shm;
static afl_forkserver_t *fsrv;
static sharedmem_t      *shm_fuzz;

/* Classify tuple counts. Instead of mapping to individual bits, as in
   afl-fuzz.c, we map to more user-friendly numbers between 1 and 8. */

static const u8 count_class_human[256] = {

    [0] = 0, [1] = 1,  [2] = 2,  [3] = 3,  [4] = 4,
    [8] = 5, [16] = 6, [32] = 7, [128] = 8

};

static const u8 count_class_binary[256] = {

    [0] = 0,
    [1] = 1,
    [2] = 2,
    [3] = 4,
    [4 ... 7] = 8,
    [8 ... 15] = 16,
    [16 ... 31] = 32,
    [32 ... 127] = 64,
    [128 ... 255] = 128

};

static void init_sem_shm() {
  // Create the shared memory
  int shared_fd = shm_open(SHARED_MEM_NAME, O_CREAT | O_RDWR, 0660);
  if (shared_fd == -1) {
      perror("Error creating shared memory");
      exit(1);
  }
  if (ftruncate(shared_fd, SHARED_MEM_SIZE) == -1) {
      perror("Error setting size of shared memory");
      exit(1);
  }
  shared_mem = mmap(NULL, SHARED_MEM_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, shared_fd, 0);
  if (shared_mem == MAP_FAILED) {
      perror("Error mapping shared memory");
      exit(1);
  }

  memset(shared_mem, 0, SHARED_MEM_SIZE);

  // Create the input semaphore
  sem_input = sem_open(SEM_INPUT_NAME, O_CREAT, 0660, 0);
  if (sem_input == SEM_FAILED) {
      perror("Error creating input semaphore");
      exit(1);
  }

  // Create the output semaphore
  sem_output = sem_open(SEM_OUTPUT_NAME, O_CREAT, 0660, 0);
  if (sem_output == SEM_FAILED) {
      perror("Error creating output semaphore");
      exit(1);
  }

  // Create array for input data
  in_data = malloc(SHARED_MEM_SIZE);
}

static void deinit_sem_shm() {
    sem_post(sem_input);

    munmap(shared_mem, SHARED_MEM_SIZE);

    // Unlink shared memory and smeaphores
    shm_unlink(SHARED_MEM_NAME);
    sem_unlink(SEM_INPUT_NAME);
    sem_unlink(SEM_OUTPUT_NAME);

    // free in_data
    free(in_data);
}

static void kill_child() {

  timed_out = 1;
  if (fsrv->child_pid > 0) {

    kill(fsrv->child_pid, fsrv->child_kill_signal);
    fsrv->child_pid = -1;

  }

}

static void classify_counts(afl_forkserver_t *fsrv) {

  u8       *mem = fsrv->trace_bits;
  const u8 *map = binary_mode ? count_class_binary : count_class_human;

  u32 i = map_size;

  if (edges_only) {

    while (i--) {

      if (*mem) { *mem = 1; }
      mem++;

    }

  } else if (!raw_instr_output) {

    while (i--) {

      *mem = map[*mem];
      mem++;

    }

  }

}

static sharedmem_t *deinit_shmem(afl_forkserver_t *fsrv,
                                 sharedmem_t      *shm_fuzz) {

  afl_shm_deinit(shm_fuzz);
  fsrv->support_shmem_fuzz = 0;
  fsrv->shmem_fuzz_len = NULL;
  fsrv->shmem_fuzz = NULL;
  ck_free(shm_fuzz);
  return NULL;

}

/* Get rid of temp files (atexit handler). */

static void at_exit_handler(void) {

  if (stdin_file) { unlink(stdin_file); }

  if (remove_shm) {

    if (shm.map) afl_shm_deinit(&shm);
    if (fsrv->use_shmem_fuzz) deinit_shmem(fsrv, shm_fuzz);

  }

  afl_fsrv_killall();

}

/* Analyze results. */

static void analyze_results(afl_forkserver_t *fsrv) {

  u32 i;
  for (i = 0; i < map_size; i++) {

    if (fsrv->trace_bits[i]) {

      total += fsrv->trace_bits[i];
      if (fsrv->trace_bits[i] > highest) highest = fsrv->trace_bits[i];
      if (!coverage_map[i]) { coverage_map[i] = 1; }

    }

  }

}

/* Execute target application. */

static void showmap_run_target_forkserver(afl_forkserver_t *fsrv, u8 *mem,
                                          u32 len) {

  afl_fsrv_write_to_testcase(fsrv, mem, len);

  if (!quiet_mode) { SAYF("-- Program output begins --\n" cRST); }

  if (afl_fsrv_run_target(fsrv, fsrv->exec_tmout, &stop_soon) ==
      FSRV_RUN_ERROR) {

    FATAL("Error running target");

  }

  if (fsrv->trace_bits[0] == 1) {

    fsrv->trace_bits[0] = 0;
    have_coverage = true;

  } else {

    have_coverage = false;

  }

  if (!no_classify) { classify_counts(fsrv); }

  if (!quiet_mode) { SAYF(cRST "-- Program output ends --\n"); }

  if (!fsrv->last_run_timed_out && !stop_soon &&
      WIFSIGNALED(fsrv->child_status)) {

    child_crashed = true;

  } else {

    child_crashed = false;

  }

  if (!quiet_mode) {

    if (timed_out || fsrv->last_run_timed_out) {

      SAYF(cLRD "\n+++ Program timed off +++\n" cRST);
      timed_out = 0;

    } else if (stop_soon) {

      SAYF(cLRD "\n+++ Program aborted by user +++\n" cRST);

    } else if (child_crashed) {

      SAYF(cLRD "\n+++ Program killed by signal %u +++\n" cRST,
           WTERMSIG(fsrv->child_status));

    }

  }

  if (stop_soon) {

    SAYF(cRST cLRD "\n+++ afl-showmap folder mode aborted by user +++\n" cRST);
    exit(1);

  }

}

/* Handle Ctrl-C and the like. */

static void handle_stop_sig(int sig) {

  (void)sig;
  stop_soon = true;
  afl_fsrv_killall();
  deinit_sem_shm();

}

/* Do basic preparations - persistent fds, filenames, etc. */

static void set_up_environment(afl_forkserver_t *fsrv, char **argv) {

  char *afl_preload;
  char *frida_afl_preload = NULL;

  setenv("ASAN_OPTIONS",
         "abort_on_error=1:"
         "detect_leaks=0:"
         "allocator_may_return_null=1:"
         "symbolize=0:"
         "detect_odr_violation=0:"
         "handle_segv=0:"
         "handle_sigbus=0:"
         "handle_abort=0:"
         "handle_sigfpe=0:"
         "handle_sigill=0",
         0);
  setenv("LSAN_OPTIONS",
         "exitcode=" STRINGIFY(LSAN_ERROR) ":"
         "fast_unwind_on_malloc=0:"
         "symbolize=0:"
         "print_suppressions=0",
          0);
  setenv("UBSAN_OPTIONS",
         "halt_on_error=1:"
         "abort_on_error=1:"
         "malloc_context_size=0:"
         "allocator_may_return_null=1:"
         "symbolize=0:"
         "handle_segv=0:"
         "handle_sigbus=0:"
         "handle_abort=0:"
         "handle_sigfpe=0:"
         "handle_sigill=0",
         0);
  setenv("MSAN_OPTIONS", "exit_code=" STRINGIFY(MSAN_ERROR) ":"
                         "abort_on_error=1:"
                         "msan_track_origins=0"
                         "allocator_may_return_null=1:"
                         "symbolize=0:"
                         "handle_segv=0:"
                         "handle_sigbus=0:"
                         "handle_abort=0:"
                         "handle_sigfpe=0:"
                         "handle_sigill=0", 0);

  if (get_afl_env("AFL_PRELOAD")) {

    if (fsrv->qemu_mode) {

      /* afl-qemu-trace takes care of converting AFL_PRELOAD. */

    } else if (fsrv->frida_mode) {

      afl_preload = getenv("AFL_PRELOAD");
      u8 *frida_binary = find_afl_binary(argv[0], "afl-frida-trace.so");
      if (afl_preload) {

        frida_afl_preload = alloc_printf("%s:%s", afl_preload, frida_binary);

      } else {

        frida_afl_preload = alloc_printf("%s", frida_binary);

      }

      ck_free(frida_binary);

      setenv("LD_PRELOAD", frida_afl_preload, 1);
      setenv("DYLD_INSERT_LIBRARIES", frida_afl_preload, 1);

    } else {

      /* CoreSight mode uses the default behavior. */

      setenv("LD_PRELOAD", getenv("AFL_PRELOAD"), 1);
      setenv("DYLD_INSERT_LIBRARIES", getenv("AFL_PRELOAD"), 1);

    }

  } else if (fsrv->frida_mode) {

    u8 *frida_binary = find_afl_binary(argv[0], "afl-frida-trace.so");
    setenv("LD_PRELOAD", frida_binary, 1);
    setenv("DYLD_INSERT_LIBRARIES", frida_binary, 1);
    ck_free(frida_binary);

  }

  if (frida_afl_preload) { ck_free(frida_afl_preload); }

}

/* Setup signal handlers, duh. */

static void setup_signal_handlers(void) {

  struct sigaction sa;

  sa.sa_handler = NULL;
#ifdef SA_RESTART
  sa.sa_flags = SA_RESTART;
#else
  sa.sa_flags = 0;
#endif
  sa.sa_sigaction = NULL;

  sigemptyset(&sa.sa_mask);

  /* Various ways of saying "stop". */

  sa.sa_handler = handle_stop_sig;
  sigaction(SIGHUP, &sa, NULL);
  sigaction(SIGINT, &sa, NULL);
  sigaction(SIGTERM, &sa, NULL);

}

u32 run() {
  init_sem_shm();

  while (true) {

    // Wait for input to be available
    if (sem_wait(sem_input) == -1) {
        perror("Error waiting for input semaphore");
        exit(1);
    }

    // Read the input from shared memory
    u8* input = shared_mem;
    // Process the input here (for example, reverse it)
    in_len = 0;
    for (int i = 0; i < 4; i++) {
      in_len = in_len * 256 + input[i];
    }
    
    memset(in_data, 0, SHARED_MEM_SIZE);
    memcpy(in_data, input + 4, in_len);    
    memset(coverage_map, 0, 65536);
    
    clock_t begin = clock();

    showmap_run_target_forkserver(fsrv, in_data, in_len);

    clock_t end = clock();

    analyze_results(fsrv);

    // Write the output to shared memory
    u8* output = shared_mem;
    memset(output, 0, SHARED_MEM_SIZE);
    memcpy(output + 5, coverage_map, SHARED_MEM_SIZE - 5);

    u32 ret = child_crashed * 2 + fsrv->last_run_timed_out;

    output[0] = ret;

    long long time_spent = end - begin;

    output[1] = (time_spent >> 24) & 0xFF;
    output[2] = (time_spent >> 16) & 0xFF;
    output[3] = (time_spent >> 8) & 0xFF;
    output[4] = time_spent & 0xFF;

    // Signal that the output is ready
    if (sem_post(sem_output) == -1) {
        perror("Error signaling output semaphore");
        exit(1);
    }
                                                       /* not tracked */
  
  }

  return 0;  

}

/* Show banner. */

static void show_banner(void) {

  SAYF(cCYA "afl-showmap" VERSION cRST " by Michal Zalewski\n");

}

/* Display usage hints. */

static void usage(u8 *argv0) {

  show_banner();

  SAYF(
      "\n%s [ options ] -- /path/to/target_app [ ... ]\n\n"

      "Required parameters:\n"
      "  -o file    - file to write the trace data to\n\n"

      "Execution control settings:\n"
      "  -t msec    - timeout for each run (default: 1000ms)\n"
      "  -m megs    - memory limit for child process (default: none)\n"
#if defined(__linux__) && defined(__aarch64__)
      "  -A         - use binary-only instrumentation (ARM CoreSight mode)\n"
#endif
      "  -O         - use binary-only instrumentation (FRIDA mode)\n"
#if defined(__linux__)
      "  -Q         - use binary-only instrumentation (QEMU mode)\n"
      "  -U         - use Unicorn-based instrumentation (Unicorn mode)\n"
      "  -W         - use qemu-based instrumentation with Wine (Wine mode)\n"
      "               (Not necessary, here for consistency with other afl-* "
      "tools)\n"
      "  -X         - use Nyx mode\n"
#endif
      "\n"
      "Other settings:\n"
      "  -i dir     - process all files below this directory, must be combined "
      "with -o.\n"
      "               With -C, -o is a file, without -C it must be a "
      "directory\n"
      "               and each bitmap will be written there individually.\n"
      "  -C         - collect coverage, writes all edges to -o and gives a "
      "summary\n"
      "               Must be combined with -i.\n"
      "  -q         - sink program's output and don't show messages\n"
      "  -e         - show edge coverage only, ignore hit counts\n"
      "  -r         - show real tuple values instead of AFL filter values\n"
      "  -s         - do not classify the map\n"
      "  -c         - allow core dumps\n\n"

      "This tool displays raw tuple data captured by AFL instrumentation.\n"
      "For additional help, consult %s/README.md.\n\n"

      "Environment variables used:\n"
      "LD_BIND_LAZY: do not set LD_BIND_NOW env var for target\n"
      "AFL_CMIN_CRASHES_ONLY: (cmin_mode) only write tuples for crashing "
      "inputs\n"
      "AFL_CMIN_ALLOW_ANY: (cmin_mode) write tuples for crashing inputs also\n"
      "AFL_CRASH_EXITCODE: optional child exit code to be interpreted as "
      "crash\n"
      "AFL_DEBUG: enable extra developer output\n"
      "AFL_FORKSRV_INIT_TMOUT: time spent waiting for forkserver during "
      "startup (in milliseconds)\n"
      "AFL_KILL_SIGNAL: Signal ID delivered to child processes on timeout, "
      "etc.\n"
      "                 (default: SIGKILL)\n"
      "AFL_FORK_SERVER_KILL_SIGNAL: Kill signal for the fork server on "
      "termination\n"
      "                             (default: SIGTERM). If unset and "
      "AFL_KILL_SIGNAL is\n"
      "                             set, that value will be used.\n"
      "AFL_MAP_SIZE: the shared memory size for that target. must be >= the "
      "size the\n"
      "              target was compiled for\n"
      "AFL_PRELOAD: LD_PRELOAD / DYLD_INSERT_LIBRARIES settings for target\n"
      "AFL_PRINT_FILENAMES: Print the queue entry currently processed will to "
      "stdout\n"
      "AFL_QUIET: do not print extra informational output\n"
      "AFL_NO_FORKSRV: run target via execve instead of using the forkserver\n",
      argv0, doc_path);

  exit(1);

}

/* Main entry point */

int main(int argc, char **argv_orig, char **envp) {

  // TODO: u64 mem_limit = MEM_LIMIT;                  /* Memory limit (MB) */

  s32  opt, i;
  bool mem_limit_given = false, timeout_given = false, unicorn_mode = false,
       use_wine = false;
  char **use_argv;

  char **argv = argv_cpy_dup(argc, argv_orig);

  afl_forkserver_t fsrv_var = {0};
  if (getenv("AFL_DEBUG")) { debug = true; }
  if (get_afl_env("AFL_PRINT_FILENAMES")) { print_filenames = true; }

  fsrv = &fsrv_var;
  afl_fsrv_init(fsrv);
  map_size = get_map_size();
  fsrv->map_size = map_size;

  doc_path = access(DOC_PATH, F_OK) ? "docs" : DOC_PATH;

  quiet_mode = true;
  collect_coverage = true;

  if (getenv("AFL_QUIET") != NULL) { be_quiet = true; }

  while ((opt = getopt(argc, argv, "+i:o:f:m:t:AeqCZOH:QUWbcrshXY")) > 0) {

    switch (opt) {

      case 's':
        no_classify = true;
        break;

      case 'C':
        collect_coverage = true;
        quiet_mode = true;
        break;

      case 'i':
        if (in_dir) { FATAL("Multiple -i options not supported"); }
        in_dir = optarg;
        break;

      case 'o':

        if (out_file) { FATAL("Multiple -o options not supported"); }
        out_file = optarg;
        break;

      case 'm': {

        u8 suffix = 'M';

        if (mem_limit_given) { FATAL("Multiple -m options not supported"); }
        mem_limit_given = true;

        if (!optarg) { FATAL("Wrong usage of -m"); }

        if (!strcmp(optarg, "none")) {

          fsrv->mem_limit = 0;
          break;

        }

        if (sscanf(optarg, "%llu%c", &fsrv->mem_limit, &suffix) < 1 ||
            optarg[0] == '-') {

          FATAL("Bad syntax used for -m");

        }

        switch (suffix) {

          case 'T':
            fsrv->mem_limit *= 1024 * 1024;
            break;
          case 'G':
            fsrv->mem_limit *= 1024;
            break;
          case 'k':
            fsrv->mem_limit /= 1024;
            break;
          case 'M':
            break;

          default:
            FATAL("Unsupported suffix or bad syntax for -m");

        }

        if (fsrv->mem_limit < 5) { FATAL("Dangerously low value of -m"); }

        if (sizeof(rlim_t) == 4 && fsrv->mem_limit > 2000) {

          FATAL("Value of -m out of range on 32-bit systems");

        }

      }

      break;

      case 'f':  // only in here to avoid a compiler warning for use_stdin

        FATAL("Option -f is not supported in afl-showmap");
        // currently not reached:
        fsrv->use_stdin = 0;
        fsrv->out_file = strdup(optarg);

        break;

      case 't':

        if (timeout_given) { FATAL("Multiple -t options not supported"); }
        timeout_given = true;

        if (!optarg) { FATAL("Wrong usage of -t"); }

        if (strcmp(optarg, "none")) {

          fsrv->exec_tmout = atoi(optarg);

          if (fsrv->exec_tmout < 20 || optarg[0] == '-') {

            FATAL("Dangerously low value of -t");

          }

        } else {

          // The forkserver code does not have a way to completely
          // disable the timeout, so we'll use a very, very long
          // timeout instead.
          WARNF(
              "Setting an execution timeout of 120 seconds ('none' is not "
              "allowed).");
          fsrv->exec_tmout = 120 * 1000;

        }

        break;

      case 'e':

        if (edges_only) { FATAL("Multiple -e options not supported"); }
        if (raw_instr_output) { FATAL("-e and -r are mutually exclusive"); }
        edges_only = true;
        break;

      case 'q':

        quiet_mode = true;
        break;

      case 'Z':

        /* This is an undocumented option to write data in the syntax expected
           by afl-cmin. Nobody else should have any use for this. */

        cmin_mode = true;
        quiet_mode = true;
        break;

      case 'H':
        /* Another afl-cmin specific feature. */
        at_file = optarg;
        break;

      case 'O':                                               /* FRIDA mode */

        if (fsrv->frida_mode) { FATAL("Multiple -O options not supported"); }

        fsrv->frida_mode = true;
        setenv("AFL_FRIDA_INST_SEED", "1", 1);

        break;

      /* FIXME: We want to use -P for consistency, but it is already unsed for
       * undocumenetd feature "Another afl-cmin specific feature." */
      case 'A':                                           /* CoreSight mode */

#if !defined(__aarch64__) || !defined(__linux__)
        FATAL("-A option is not supported on this platform");
#endif

        if (fsrv->cs_mode) { FATAL("Multiple -A options not supported"); }

        fsrv->cs_mode = true;
        break;

      case 'Q':

        if (fsrv->qemu_mode) { FATAL("Multiple -Q options not supported"); }

        fsrv->qemu_mode = true;
        break;

      case 'U':

        if (unicorn_mode) { FATAL("Multiple -U options not supported"); }

        unicorn_mode = true;
        break;

      case 'W':                                           /* Wine+QEMU mode */

        if (use_wine) { FATAL("Multiple -W options not supported"); }
        fsrv->qemu_mode = true;
        use_wine = true;

        break;

      case 'Y':  // fallthough
#ifdef __linux__
      case 'X':                                                 /* NYX mode */

        if (fsrv->nyx_mode) { FATAL("Multiple -X options not supported"); }

        fsrv->nyx_mode = 1;
        fsrv->nyx_parent = true;
        fsrv->nyx_standalone = true;

        break;
#else
      case 'X':
        FATAL("Nyx mode is only availabe on linux...");
        break;
#endif

      case 'b':

        /* Secret undocumented mode. Writes output in raw binary format
           similar to that dumped by afl-fuzz in <out_dir/queue/fuzz_bitmap. */

        binary_mode = true;
        break;

      case 'c':

        if (keep_cores) { FATAL("Multiple -c options not supported"); }
        keep_cores = true;
        break;

      case 'r':

        if (raw_instr_output) { FATAL("Multiple -r options not supported"); }
        if (edges_only) { FATAL("-e and -r are mutually exclusive"); }
        raw_instr_output = true;
        break;

      case 'h':
        usage(argv[0]);
        return -1;
        break;

      default:
        usage(argv[0]);

    }

  }

  if (optind == argc || !out_file) { usage(argv[0]); }

  if (in_dir) {

    if (!out_file && !collect_coverage)
      FATAL("for -i you need to specify either -C and/or -o");

  }

  if (fsrv->qemu_mode && !mem_limit_given) { fsrv->mem_limit = MEM_LIMIT_QEMU; }
  if (unicorn_mode && !mem_limit_given) { fsrv->mem_limit = MEM_LIMIT_UNICORN; }

  check_environment_vars(envp);

  if (getenv("AFL_NO_FORKSRV")) {             /* if set, use the fauxserver */
    fsrv->use_fauxsrv = true;

  }

  if (getenv("AFL_DEBUG")) {

    DEBUGF("");
    for (i = 0; i < argc; i++)
      SAYF(" %s", argv[i]);
    SAYF("\n");

  }

  //  if (afl->shmem_testcase_mode) { setup_testcase_shmem(afl); }

  setenv("AFL_NO_AUTODICT", "1", 1);

  /* initialize cmplog_mode */
  shm.cmplog_mode = 0;
  setup_signal_handlers();

  set_up_environment(fsrv, argv);

#ifdef __linux__
  if (!fsrv->nyx_mode) {

    fsrv->target_path = find_binary(argv[optind]);

  } else {

    fsrv->target_path = ck_strdup(argv[optind]);

  }

#else
  fsrv->target_path = find_binary(argv[optind]);
#endif

  fsrv->trace_bits = afl_shm_init(&shm, map_size, 0);

  if (!quiet_mode) {

    show_banner();
    ACTF("Executing '%s'...", fsrv->target_path);

  }

  if (in_dir) {

    /* If we don't have a file name chosen yet, use a safe default. */
    u8 *use_dir = ".";

    if (access(use_dir, R_OK | W_OK | X_OK)) {

      use_dir = get_afl_env("TMPDIR");
      if (!use_dir) { use_dir = "/tmp"; }

    }

    stdin_file = at_file ? strdup(at_file)
                         : (char *)alloc_printf("%s/.afl-showmap-temp-%u",
                                                use_dir, (u32)getpid());
    unlink(stdin_file);

    // If @@ are in the target args, replace them and also set use_stdin=false.
    detect_file_args(argv + optind, stdin_file, &fsrv->use_stdin);

  } else {

    // If @@ are in the target args, replace them and also set use_stdin=false.
    detect_file_args(argv + optind, at_file, &fsrv->use_stdin);

  }
  

    use_argv = argv + optind;

  if (getenv("AFL_FORKSRV_INIT_TMOUT")) {

    s32 forksrv_init_tmout = atoi(getenv("AFL_FORKSRV_INIT_TMOUT"));
    if (forksrv_init_tmout < 1) {

      FATAL("Bad value specified for AFL_FORKSRV_INIT_TMOUT");

    }

    fsrv->init_tmout = (u32)forksrv_init_tmout;

  }

  if (getenv("AFL_CRASH_EXITCODE")) {

    long exitcode = strtol(getenv("AFL_CRASH_EXITCODE"), NULL, 10);
    if ((!exitcode && (errno == EINVAL || errno == ERANGE)) ||
        exitcode < -127 || exitcode > 128) {

      FATAL("Invalid crash exitcode, expected -127 to 128, but got %s",
            getenv("AFL_CRASH_EXITCODE"));

    }

    fsrv->uses_crash_exitcode = true;
    // WEXITSTATUS is 8 bit unsigned
    fsrv->crash_exitcode = (u8)exitcode;

  }

  shm_fuzz = ck_alloc(sizeof(sharedmem_t));

  /* initialize cmplog_mode */
  shm_fuzz->cmplog_mode = 0;
  u8 *map = afl_shm_init(shm_fuzz, MAX_FILE + sizeof(u32), 1);
  shm_fuzz->shmemfuzz_mode = true;
  if (!map) { FATAL("BUG: Zero return from afl_shm_init."); }
#ifdef USEMMAP
  setenv(SHM_FUZZ_ENV_VAR, shm_fuzz->g_shm_file_path, 1);
#else
  u8 *shm_str = alloc_printf("%d", shm_fuzz->shm_id);
  setenv(SHM_FUZZ_ENV_VAR, shm_str, 1);
  ck_free(shm_str);
#endif
  fsrv->support_shmem_fuzz = true;
  fsrv->shmem_fuzz_len = (u32 *)map;
  fsrv->shmem_fuzz = map + sizeof(u32);

  configure_afl_kill_signals(fsrv, NULL, NULL,
                             (fsrv->qemu_mode || unicorn_mode
#ifdef __linux__
                              || fsrv->nyx_mode
#endif
                              )
                                 ? SIGKILL
                                 : SIGTERM);

  if (!fsrv->cs_mode && !fsrv->qemu_mode && !unicorn_mode) {

    u32 save_be_quiet = be_quiet;
    be_quiet = !debug;
    if (map_size > 4194304) {

      fsrv->map_size = map_size;

    } else {

      fsrv->map_size = 4194304;  // dummy temporary value

    }

    u32 new_map_size =
        afl_fsrv_get_mapsize(fsrv, use_argv, &stop_soon,
                             (get_afl_env("AFL_DEBUG_CHILD") ||
                              get_afl_env("AFL_DEBUG_CHILD_OUTPUT"))
                                 ? 1
                                 : 0);
    be_quiet = save_be_quiet;

    if (new_map_size) {

      // only reinitialize when it makes sense
      if (map_size < new_map_size ||
          (new_map_size > map_size && new_map_size - map_size > MAP_SIZE)) {

        if (!be_quiet)
          ACTF("Acquired new map size for target: %u bytes\n", new_map_size);

        afl_shm_deinit(&shm);
        afl_fsrv_kill(fsrv);
        fsrv->map_size = new_map_size;
        fsrv->trace_bits = afl_shm_init(&shm, new_map_size, 0);

      }

      map_size = new_map_size;

    }

    fsrv->map_size = map_size;

  }

  if (in_dir) {

    DIR *dir_in, *dir_out = NULL;

    if (getenv("AFL_DEBUG_GDB")) wait_for_gdb = true;

    fsrv->dev_null_fd = open("/dev/null", O_RDWR);
    if (fsrv->dev_null_fd < 0) { PFATAL("Unable to open /dev/null"); }

    // if a queue subdirectory exists switch to that
    u8 *dn = alloc_printf("%s/queue", in_dir);
    if ((dir_in = opendir(dn)) != NULL) {

      closedir(dir_in);
      in_dir = dn;

    } else

      ck_free(dn);
    if (!be_quiet) ACTF("Reading from directory '%s'...", in_dir);

    if (!collect_coverage) {

      if (!(dir_out = opendir(out_file))) {

        if (mkdir(out_file, 0700)) {

          PFATAL("cannot create output directory %s", out_file);

        }

      }

    } else {

      if ((coverage_map = (u8 *)malloc(map_size + 64)) == NULL)
        FATAL("coult not grab memory");
      edges_only = false;
      raw_instr_output = true;

    }

    atexit(at_exit_handler);
    fsrv->out_file = stdin_file;
    fsrv->out_fd =
        open(stdin_file, O_RDWR | O_CREAT | O_EXCL, DEFAULT_PERMISSION);
    if (fsrv->out_fd < 0) { PFATAL("Unable to create '%s'", out_file); }

    

    afl_fsrv_start(fsrv, use_argv, &stop_soon,
                   (get_afl_env("AFL_DEBUG_CHILD") ||
                    get_afl_env("AFL_DEBUG_CHILD_OUTPUT"))
                       ? 1
                       : 0);

    map_size = fsrv->map_size;

    if (fsrv->support_shmem_fuzz && !fsrv->use_shmem_fuzz)
      shm_fuzz = deinit_shmem(fsrv, shm_fuzz);

    run();

    if (!quiet_mode) { OKF("Processed %llu input files.", fsrv->total_execs); }

    if (dir_out) { closedir(dir_out); }

    if (collect_coverage) {

      memcpy(fsrv->trace_bits, coverage_map, map_size);

    }

  }

  if (!quiet_mode || collect_coverage) {

    if (!tcnt && !have_coverage) { FATAL("No instrumentation detected" cRST); }
    OKF("Captured %u tuples (map size %u, highest value %u, total values %llu) "
        "in '%s'." cRST,
        tcnt, fsrv->real_map_size, highest, total, out_file);
    if (collect_coverage)
      OKF("A coverage of %u edges were achieved out of %u existing (%.02f%%) "
          "with %llu input files.",
          tcnt, map_size, ((float)tcnt * 100) / (float)map_size,
          fsrv->total_execs);

  }

  if (stdin_file) {

    unlink(stdin_file);
    ck_free(stdin_file);
    stdin_file = NULL;

  }

  remove_shm = 0;
  afl_shm_deinit(&shm);
  if (fsrv->use_shmem_fuzz) shm_fuzz = deinit_shmem(fsrv, shm_fuzz);

  u32 ret;

  if (cmin_mode && !!getenv("AFL_CMIN_CRASHES_ONLY")) {

    ret = fsrv->last_run_timed_out;

  } else {

    ret = child_crashed * 2 + fsrv->last_run_timed_out;

  }

  if (fsrv->target_path) { ck_free(fsrv->target_path); }

  afl_fsrv_deinit(fsrv);

  if (stdin_file) { ck_free(stdin_file); }
  if (collect_coverage) { free(coverage_map); }

  argv_cpy_free(argv);
  if (fsrv->qemu_mode) { free(use_argv[2]); }

  deinit_sem_shm();

  exit(ret);

}
