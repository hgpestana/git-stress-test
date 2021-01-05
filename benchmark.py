#!/usr/bin/env python

import concurrent.futures
import logging
import os
import random
import subprocess
import tempfile
import timeit
import time

_NUM_COMMITS = 5
_NUM_USERS = 10
_NUM_FILES = 5

_TARGET_PROJECT = 'git@git.pst.asseco.com:testing/stress-testing.git'
_TARGET_DIRECTORY = 'c:\\Users\\10000102\\dev\\asseco\\git-stress-test\\tests'


def random_file(directory):
    try:
        files = [os.path.join(path, filename)
                 for path, dirs, files in os.walk(directory)
                 for filename in files
                 if '.git' not in path]

        return random.choice(files)
    except IndexError:
        return None


def run_commits(git_user):
    logging.info("Waiting %s seconds to start", git_user)
    time.sleep(git_user)

    user_directory = '{}\\user_{}'.format(_TARGET_DIRECTORY, git_user)
    logging.info("Thread %s: starting", user_directory)

    logging.info("Creating the user directory for %s", user_directory)
    subprocess.run('mkdir {}'.format(user_directory), shell=True)

    logging.info("Cloning the project for %s", user_directory)
    subprocess.run('git clone {} {}'.format(_TARGET_PROJECT, user_directory), shell=True)

    logging.info("Creating commits for %s", user_directory)

    for commit in range(_NUM_COMMITS):
        logging.info("Clearing unsubmitted previous commit files")

        subprocess.run('git reset --hard', shell=True)
        subprocess.run('git pull', shell=True)

        logging.info("Starting commit %s for %s", commit, user_directory)

        # Queue tasks to do.
        tasks = list()

        logging.info("Generating tasks for commit %s of %s", commit, user_directory)
        for i in range(_NUM_FILES):
            r_file = random_file(user_directory)

            if not r_file or i < (_NUM_FILES / 2):
                temp = tempfile.NamedTemporaryFile(dir=user_directory, delete=False)
                tasks.append(('CREATED', temp.name))
            else:
                tasks.append(('DELETED', r_file))

        logging.info("Executing tasks for commit %s of %s", commit, user_directory)
        # Execute tasks
        for task in tasks:
            if 'CREATED' == task[0]:
                logging.info("Creating file %s for %s", task[1], user_directory)

                # write lines into the file
                with open(task[1], 'wb') as file:
                    file.write(os.urandom(1024))
                    file.close()
                logging.info("Entering the directory %s", user_directory)
                os.chdir(user_directory)

                subprocess.Popen('git add {}'.format(task[1]), shell=True).wait()
            elif 'DELETED' == task[0]:
                logging.info("Deleting file %s for %s", task[1], user_directory)
                subprocess.run('rm {}'.format(task[1]), shell=True)

        logging.info("Commiting %s for %s", commit, user_directory)
        start_commit = timeit.timeit()

        logging.info("Entering the directory %s", user_directory)
        os.chdir(user_directory)

        subprocess.run('git commit --quiet --all --message="Commit number {}."'.format(commit), shell=True)
        logging.info("Finished commit %s for %s", commit, user_directory)

        logging.info("Pushing commit %s for %s", commit, user_directory)
        subprocess.run('git pull', shell=True)
        subprocess.run('git push', shell=True)
        logging.info("Finished push for commit %s for %s", commit, user_directory)

        end_commit = timeit.timeit()
        logging.info("Commit & push for commit %s of %s took %s seconds", commit, user_directory, end_commit - start_commit)


subprocess.run('rm -rf {}'.format(_TARGET_DIRECTORY), shell=True)
subprocess.run('mkdir {}'.format(_TARGET_DIRECTORY), shell=True)

os.chdir(_TARGET_DIRECTORY)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

with concurrent.futures.ThreadPoolExecutor(max_workers=_NUM_USERS) as executor:
    results = executor.map(run_commits, range(_NUM_USERS))
    for result in list(results):
        logging.info("Finished thread %s", result)
