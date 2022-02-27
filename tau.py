#!/usr/bin/python

import os
import argparse
import datetime
import pprint
import requests
import json
import sys
from decimal import Decimal as Real

def error(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(-1)

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
    due_date = datetime.date(year, month, day)

    return due_date

class TaskInfo:

    def __init__(self, assign, project, due, rank):
        self.assign = assign
        self.project = project
        self.due = due
        self.rank = rank

    def __repr__(self):
        return (
            f"TaskInfo {{\n"
            f"  assign: {self.assign},\n"
            f"  project: {self.project},\n"
            f"  due: {self.due},\n"
            f"  rank: {self.rank},\n"
            f"}}"
        )

def cmd_add(args, settings):
    if not validate_due_date(args.due):
        error(f"due date {args.due} is not valid")
    due = convert_due_date(args.due)

    # TODO: created_at attribute

    task_info = TaskInfo(args.assign, args.project, due, args.rank)
    print(f"{task_info}")

def arg_parser(client):
    parser = argparse.ArgumentParser(prog='tx',
        usage='%(prog)s [commands]',
        description="Collective task management cli"
    )

    subparsers = parser.add_subparsers()

    # add [-a/--assign USER] [-p/--project zk] [-d/--due DDMM] [-r/--rank 4.87]
    #   [-c/--custom CUSTOM_KEY:CUSTOM_VALUE]...
    # if assigned USER is empty, then task is unassigned
    # custom adds additional custom attributes
    # rank is arbitrary Decimal precision
    #
    # $ tx add -a nar -p zk
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
        "-c", "--custom",
        default=None,
        help="custom_key:custom_value attribute")
    parser_add.set_defaults(func=cmd_add)

    #parser.add_argument("-k", "--key", action='store_true', help="Generate a new keypair")
    #parser.add_argument("-i", "--info", action='store_true', help="Request info from daemon")
    #parser.add_argument("-s", "--stop", action='store_true', help="Send a stop signal to the daemon")
    #parser.add_argument("-hi", "--hello", action='store_true', help="Say hello")
    args = parser.parse_args()

    # TODO: load config, only steps until #2 for now. Do #3 onwards later
    # weaker priority than command line args
    # ~/.config/tx/tx.toml
    # [settings]
    # custom_editor="nvim"
    #
    # 1. Read environment variable TX_CONFIG_PATH=...
    #    default is not set is ~/.config/tx/
    # 2. make directory if it doesn't already exist
    # 3. Load {config_path}/tx.toml
    #    has a settings section
    #       [settings]
    #       custom_editor="nvim"    # Forget this for now
    # 4. Load config into Settings class
    settings = None

    try:
        config_path = os.environ["TX_CONFIG_PATH"]
    except KeyError:
        config_path = os.path.expanduser("~/.config/tx/")

    try:
        os.makedirs(config_path)
    except FileExistsError:
        pass

    args.func(args, settings)

    #if args.key:
    #    try:
    #        print("Attemping to generate a new key pair...")
    #        client.key_gen(client.payload)
    #    except Exception:
    #        raise

    #if args.info:
    #    try:
    #        print("Info was entered")
    #        client.get_info(client.payload)
    #        print("Requesting daemon info...")
    #    except Exception:
    #        raise

    #if args.stop:
    #    try:
    #        print("Stop was entered")
    #        client.stop(client.payload)
    #        print("Sending a stop signal...")
    #    except Exception:
    #        raise

    #if args.hello:
    #    try:
    #        print("Hello was entered")
    #        client.say_hello(client.payload)
    #    except Exception:
    #        raise


class DarkClient:
    # TODO: generate random ID (4 byte unsigned int) (rand range 0 - max size
    # uint32
    def __init__(self):
        self.url = "http://localhost:8000/"
        self.payload = {
            "method": [],
            "params": [],
            "jsonrpc": [],
            "id": [],
        }

    def key_gen(self, payload):
        payload['method'] = "key_gen"
        payload['jsonrpc'] = "2.0"
        payload['id'] = "0"
        key = self.__request(payload)
        print(key)

    def get_info(self, payload):
        payload['method'] = "get_info"
        payload['jsonrpc'] = "2.0"
        payload['id'] = "0"
        info = self.__request(payload)
        print(info)

    def stop(self, payload):
        payload['method'] = "stop"
        payload['jsonrpc'] = "2.0"
        payload['id'] = "0"
        stop = self.__request(payload)
        print(stop)

    def say_hello(self, payload):
        payload['method'] = "say_hello"
        payload['jsonrpc'] = "2.0"
        payload['id'] = "0"
        hello = self.__request(payload)
        print(hello)

    def __request(self, payload):
        response = requests.post(self.url, json=payload).json()
        # print something better
        # parse into data structure 
        print(response)
        assert response["jsonrpc"]

    
if __name__ == "__main__":
    client = DarkClient()
    arg_parser(client)
    sys.exit(0)

    #rpc()
    ## Example echo method
    #payload = {
    #    #"method:": args,
    #    #"method": "stop",
    #    "method": "get_info",
    #    #"method": "say_hello",
    #    #"params": [],
    #    "jsonrpc": "2.0",
    #    "id": 0,
    #}
    #response = requests.post(url, json=payload).json()

    #print(response)
    #assert response["result"] == "Hello World!"
    #assert response["jsonrpc"]

