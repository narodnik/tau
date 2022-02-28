#!/usr/bin/python

import os
import argparse
import datetime
import itertools
import json
import hashlib
import logging
import pprint
import pickle
import sys
import tempfile
import time
from decimal import Decimal as Real
from tabulate import tabulate

def error(message):
    logging.error(f"Error: {message}", file=sys.stderr)
    sys.exit(-1)

def make_path(config_path, subdirs=None):
    if subdirs is not None:
        assert isinstance(subdirs, str)
        config_path = os.path.join(config_path, subdirs)

    try:
        os.makedirs(config_path)
    except FileExistsError:
        pass

# Is this string an integer number
def is_integer(s):
    try:
        _ = int(s)
    except ValueError:
        return False
    return True

def validate_due_date(date):
    if date is None:
        return True
    
    assert(isinstance(date, str))
    if len(date) != 4:
        return False

    if not is_integer(date):
        return False

    try:
        due_date = convert_due_date(date)
    except ValueError:
        return False

    return True

# This function MUST be called after validate_due_date(date)
def convert_due_date(date):
    if date is None:
        return None

    assert(isinstance(date, str))
    assert(len(date) == 4)
    assert(is_integer(date))

    # We know the date is a 4 byte integer value.
    # Now evaluate the month and year
    # DDMM format
    day, month = int(date[:2]), int(date[2:])
    year = datetime.date.today().year
    #print(f"{day} {month} {year}")

    # !!!
    # This line can throw ValueError if month or day is invalid!
    # Should be caught by validate_due_date(date)
    due = datetime.date(year, month, day)

    # Keep incrementing year for due date until it's in the future
    now = datetime.datetime.now().date()
    while due < now:
        due = due.replace(year = due.year + 1)

    return due

class Config:

    def __init__(self, config_path):
        # Save the config path
        self.path = config_path

    def load(self):
        # Load the configuration from f
        try:
            with open(self.filename(), "rb") as f:
                self._load(f)
        except FileNotFoundError:
            # File doesn't exist
            # TODO: Create empty file
            pass

    def _load(self, f):
        pass

    def filename(self):
        return os.path.join(self.path, "tk.toml")

class Settings:

    def __init__(self, config):
        self.config = config
        self.editor = os.environ.get('EDITOR', 'nvim')

    def month_filename(self, date):
        month, year = date.month, date.year
        year = str(year)[2:]
        month = f"{month:02d}"
        filename = f"{month}{year}"
        path = os.path.join(self.config.path, f"month/{filename}")
        return path

class MonthTasks:

    def __init__(self, created_at, settings):
        self.created_at = created_at
        self.settings = settings

        self.task_tks = []

    def objects(self):
        tks = []
        for tk_hash in self.task_tks:
            tk = TaskInfo.load(tk_hash, self.settings)
            tks.append(tk)
        return tks

    def add(self, tk_hash):
        self.task_tks.append(tk_hash)

    def save(self):
        data = {
            "created_at": self.created_at.timestamp(),
            "tasks": self.task_tks
        }
        with open(self.settings.month_filename(self.created_at), "w") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def load(date, settings):
        with open(settings.month_filename(date), "r") as f:
            data = json.load(f)
        created_at = datetime.datetime.fromtimestamp(data["created_at"])
        self = MonthTasks(created_at, settings)
        self.task_tks = data["tasks"]
        return self

    @staticmethod
    def load_or_create(date, settings):
        try:
            return MonthTasks.load(date, settings)
        except FileNotFoundError:
            # File does not yet exist. Create a new one
            month_tks = MonthTasks(date, settings)
            # TODO: Auto roll over open tasks from month before
            # Open last month, copy open tasks to this object
            # Function to return open tasks from last month
            # Then assign to this month and save.
            month_tks.save()
            return month_tks

class TaskInfo:

    def __init__(self, id, title, desc, assign, project, due,
                 rank, created_at, settings):
        self.id = id
        self.title = title
        self.desc = desc

        self.assign = assign
        self.project = project
        self.due = due
        self.rank = rank
        self.created_at = created_at

        self.settings = settings

    def activate(self):
        # Open the task
        month_tks = MonthTasks.load_or_create(self.created_at, self.settings)
        month_tks.add(self.tk_hash())
        month_tks.save()

    @staticmethod
    def data_path(settings, tk_hash):
        path = os.path.join(settings.config.path,
                            f"task/{tk_hash}")
        return path

    def path(self):
        return TaskInfo.data_path(self.settings, self.tk_hash())

    def save(self):
        with open(self.path(), "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(tk_hash, settings):
        path = TaskInfo.data_path(settings, tk_hash)
        with open(path, "rb") as f:
            tk = pickle.load(f)
        # Settings should not be loaded normally
        tk.settings = settings
        return tk
    
    def tk_hash(self):
        rep = repr(self).encode('utf-8')
        result = hashlib.sha256(rep).hexdigest()
        return result

    def __repr__(self):
        return (
            f"TaskInfo {{\n"
            f"  id: {self.id},\n"
            f"  title: {self.title},\n"
            f"  desc: {self.desc},\n"
            f"  assign: {self.assign},\n"
            f"  project: {self.project},\n"
            f"  due: {self.due},\n"
            f"  rank: {self.rank},\n"
            f"}}"
        )

def read_description(settings):
    temp = tempfile.NamedTemporaryFile()
    temp.write(b"\n")
    temp.write(b"# Write task description above this line\n")
    temp.write(b"# These lines will be removed\n")
    temp.flush()
    os.system(f"{settings.editor} {temp.name}")
    desc = open(temp.name, "r").read()
    # Remove comments and empty lines from desc
    desc = "\n".join(line for line in desc.split("\n")
                     if line and line[0] != "#")
    return desc

def find_free_id(settings):
    now = datetime.datetime.now()
    month_tks = MonthTasks.load_or_create(now, settings)
    tks = month_tks.objects()
    tk_ids = [tk.id for tk in tks]
    for i in itertools.count():
        if i not in tk_ids:
            return i

def cmd_add(args, settings):
    if not validate_due_date(args.due):
        error(f"due date {args.due} is not valid")
    due = convert_due_date(args.due)

    id = find_free_id(settings)

    created_at = datetime.datetime.now()

    if args.title is None:
        title = input("Title: ")
    else:
        title = args.title

    if args.desc is None:
        desc = read_description(settings)
    else:
        desc = args.desc

    task_info = TaskInfo(id, title, desc, args.assign, args.project,
                         due, args.rank, created_at, settings)
    task_info.save()
    task_info.activate()
    logging.info(f"tk hash: {task_info.tk_hash()}")
    logging.info(f"{task_info}")

def cmd_list(args, settings):
    now = datetime.datetime.now()
    month_tks = MonthTasks.load_or_create(now, settings)
    tks = month_tks.objects()
    table = []
    for tk in tks:
        table.append((tk.id, tk.title, tk.project, tk.assign, tk.due, tk.rank))
    headers = ["ID", "Title", "Project", "Assigned", "Due", "Rank"]
    print(tabulate(table, headers=headers))

def cmd_show(args, settings):
    logging.debug("show command called")

def run_app():
    parser = argparse.ArgumentParser(prog='tau',
        usage='%(prog)s [commands]',
        description="Collective task management cli"
    )
    parser.add_argument("-v", "--verbose",
            action="store_const",
            dest="loglevel", const=logging.DEBUG, default=logging.WARNING,
            help="increase output verbosity"),
    subparsers = parser.add_subparsers()

    # add [-a/--assign USER] [-p/--project zk] [-d/--due DDMM] [-r/--rank 4.87]
    #   [-c/--custom CUSTOM_KEY:CUSTOM_VALUE]...
    # if assigned USER is empty, then task is unassigned
    # custom adds additional custom attributes
    # rank is arbitrary Decimal precision
    #
    # $ tau add -a nar -p zk
    # Title: "read paper on DARK compilers"
    # Description: _
    #
    # By default just prompt input, or you can set the program to open with
    # a custom editor
    parser_add = subparsers.add_parser("add", help="add a new task")
    parser_add.add_argument(
        "-a", "--assign", #action='store_true',
        default=None,
        help="assign task to user")
    parser_add.add_argument(
        "-p", "--project", #action='store_true',
        default=None,
        help="task project (can be hierarchical: crypto.zk")
    parser_add.add_argument(
        "-d", "--due", #action='store_true',
        default=None,
        help="due date: 0222")
    parser_add.add_argument(
        "-r", "--rank", #action='store_true',
        type=Real, default=None,
        help=("project rank, is an arbitrary precision"
              "decimal real value: 4.8761"))
    parser_add.add_argument(
        "-t", "--title",
        default=None,
        help="specify task title")
    parser_add.add_argument(
        "--desc",
        default=None,
        help="specify task description")
    parser_add.add_argument(
        "-c", "--custom",
        default=None,
        help="custom_key:custom_value attribute")
    parser_add.set_defaults(func=cmd_add)

    parser_list = subparsers.add_parser("list", help="list open tasks")
    parser_list.set_defaults(func=cmd_list)

    parser_show = subparsers.add_parser("show", help="show task by id")
    parser_show.set_defaults(func=cmd_show)
    parser_show.add_argument('-i', '--id', default=None, required=True, help='task id')

    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    # TODO: load config, only steps until #2 for now. Do #3 onwards later
    # weaker priority than command line args
    # ~/.config/tau/tau.toml
    # [settings]
    # custom_editor="nvim"
    #
    # 1. Read environment variable TX_CONFIG_PATH=...
    #    default is not set is ~/.config/tau/
    # 2. make directory if it doesn't already exist
    # 3. Load {config_path}/tau.toml
    #    has a settings section
    #       [settings]
    #       custom_editor="nvim"    # Forget this for now
    # 4. Load config into Settings class

    # Config file settings are not implemented yet.
    # Stub
    config = None

    try:
        config_path = os.environ["TAU_CONFIG_PATH"]
    except KeyError:
        config_path = os.path.expanduser("~/.config/tau/")

    make_path(config_path)
    make_path(config_path, "task")
    make_path(config_path, "month")

    config = Config(config_path)
    config.load()
    settings = Settings(config)

    try: 
        # Check the subcommand was actually specified
        args.func
    except AttributeError:
        # No subcommand specified, print the help and exit
        parser.print_help()
        return

    # Actually run the command
    args.func(args, settings)

if __name__ == "__main__":
    run_app()
    sys.exit(0)

