import argparse
import collections
import datetime
import functools
import json
import os
import time

DATETIME_FMT = "%Y-%m-%dT%H:%M:%SZ"


def strptime(dt):
    return datetime.datetime.strptime(dt, DATETIME_FMT)


def strftime(dt):
    return dt.strftime(DATETIME_FMT)


def ratelimit(limit, every):
    # Limit on numbers of call in 'limit' time by sleeping for required time
    def limitdecorator(fn):
        times = collections.deque()

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if len(times) >= limit:
                t0 = times.pop()
                t = time.time()
                sleep_time = every - (t - t0)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            times.appendleft(time.time())
            return fn(*args, **kwargs)

        return wrapper

    return limitdecorator


def chunk(l, n):
    # Return provided list into chunk of size n
    for i in range(0, len(l), n):
        yield l[i:i + n]


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def load_schema(entity):
    return load_json(get_abs_path("schemas/{}.json".format(entity)))


def update_state(state, entity, dt):
    if dt is None:
        return

    if isinstance(dt, datetime.datetime):
        dt = strftime(dt)

    # Add entity in state if not found
    if entity not in state:
        state[entity] = dt

    # Update state if provided datetime is greater than existing one
    if dt >= state[entity]:
        state[entity] = dt


def parse_args(required_config_keys):
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='Config file', required=True)
    parser.add_argument('-s', '--state', help='State file')
    args = parser.parse_args()

    config = load_json(args.config)
    if "x_pendo_integration_key" not in config:
        env_key = os.getenv("X_PENDO_INTEGRATION_KEY")
        if env_key is not None:
            config["x_pendo_integration_key"] = env_key
    check_config(config, required_config_keys) # Check config for missing fields

    if args.state:
        state = load_json(args.state)
    else:
        state = {}

    return config, state


def check_config(config, required_keys):
    # Verify that all the required keys are present in config
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise Exception(
            "Config is missing required keys: {}".format(missing_keys))
