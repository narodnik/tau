#!/usr/bin/python

# seperate file called simulate
# import data structures from tau
# generate fake events with legit info
# start, pause, stop

import argparse
import datetime
import os
import logging
import tau
import random

titles = [
    "generate fake tasks",
    "AMM script",
    "bonding curve script",
    "write T letter",
    "share tokeneconomics",
    "net hooks",
    "rename map",
    "document CRV tokeneconomics",
    "document network code",
    "refactor tau",
    "darkfi bull thesis",
    "book flights",
    "finish DAO spec",
    "gui library",
    "incremental merkle tree",
    "reply to amy",
    "make vector a mutex hashmap",
    "agorism intro",
    "write tutorial",
    "cashier spec",
    "design note enc scheme",
    ]

descriptions = [
    "create a script called simulator that creates fake tasks with legit info",
    "write a simple AMM in python",
    "write a simple bonding curve in python",
    "send journal to T",
    "finish token document and share with team",
    "write /net hooks for map",
    "think of a better name for map",
    "explain why CRV tokeneconomics is superior",
    "write top level documentation for /net module",
    "refactor tau to enable merge strategies",
    "write darkfi bull thesis for egirl capital",
    "book trip to US and back",
    "code specification for anonymous DAOs",
    "initial spec for gui library",
    "study incremental merkle trees",
    "write email to amy",
    "refactor map to use hashmaps instead of vectors",
    "write introduction to agorism journal",
    "darkfi testnet tutorial",
    "write trustless cashier specification",
    "create encryption scheme for note",
    ]

assignee = [
        "roz",
        "nar",
        "xesan",
        "parazyd",
        "mylta",
        "genjix",
        "pythia",
        "armor",
        "dunklezfr",
        "dasman"
        ]

projects = [
        "tau",
        "df.token",
        "df.token",
        "phil",
        "df.token",
        "df.net",
        "df.map",
        "df.defi",
        "df.net",
        "tau",
        "phil",
        "admin",
        "df.dao",
        "df.gui",
        "df.crypto",
        "phil",
        "df.map",
        "phil",
        "df.v0",
        "df.v1",
        "df.crypto"
        ]

years = [
        "2020",
        "2021",
        "2022"
        ]

def random_date():
    day, month = random_number(), random_number()
    year = int(random.choice(years))
    date = datetime.date(year, month, day)
    return date

def random_number():
    return random.randrange(1, 12)

def create_task(ref_id, id, title, desc, assign, project,
        due, rank, created_at, settings):
    task_info = tau.TaskInfo(ref_id, id, title, desc, assign,
            project, due, rank, created_at, settings)
    task_info.save()
    task_info.activate()
    logging.info(f"{task_info}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='simulator',
        usage='%(prog)s [commands]',
        description="simulate fake tasks"
    )
    parser.add_argument('integer', metavar='N', type=int, nargs='?',
            help='define the number of fake tasks')
    parser.add_argument("-v", "--verbose",
            action="store_const",
            dest="loglevel", const=logging.DEBUG, default=logging.WARNING,
            help="increase output verbosity"),
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    try:
        config_path = os.environ["TAU_CONFIG_PATH"]
    except KeyError:
        config_path = os.path.expanduser("~/.config/tau/")
    
    config = tau.Config(config_path)
    config.load()
    
    n_tasks = int(args.integer)
    for i in range(n_tasks):
        ref_id = tau.random_hex_string()
        id = random_number()
        title = random.choice(titles)
        index = titles.index(title)
        desc = descriptions[index]
        assign = random.choice(assignee)
        project = random.choice(projects)
        due = random_date()
        rank = random_number()
        # TODO: fix this
        created_at = datetime.datetime.now()
        settings = tau.Settings(config)
        create_task(ref_id, id, title, desc, assign, project,
            due, rank, created_at, settings)

