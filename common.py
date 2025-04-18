from datetime import datetime
import gzip
import os
import re
import shutil
import sys
import time
# import zstandard as zstd


def print_file_info(file_path):

    # Get file stats
    file_stats = os.stat(file_path)

    # Get creation time and convert it to a human-readable format
    creation_time = time.ctime(file_stats.st_ctime)

    # Get file size in bytes
    file_size = file_stats.st_size  # Size in bytes

    # Print the results
    p(f"File: {file_path}")
    p(f"Creation Date: {creation_time}")
    p(f"Size: {file_size} bytes")


def p(msg, should_exit=False):
    if should_exit:
        msg += "\n.Quitting"
    print(f"{datetime.now().time()} {msg}", file=sys.stderr)
    if should_exit:
        sys.exit(-1)


def keep_file(filename):
    dst_file = None
    if os.path.exists(filename):
        path = os.path.dirname(filename)
        prev_dir = os.path.join(path, "prev")
        if not os.path.exists(prev_dir):
            os.mkdir(prev_dir)
        ver = 0
        filename_basename = os.path.basename(filename)
        while True and ver < 1000:
            if filename_basename.endswith(".csv"):
                dst_file = f"{filename_basename[0:-4]}.{ver:03}.csv"
            else:
                dst_file = f"{filename_basename}.{ver:03}"
            dst_file = os.path.join(prev_dir, dst_file)
            if not os.path.exists(dst_file):
                break
            ver += 1

        if ver == 1000:
            p(f"Cannot keep {filename}, please delete previous file", True)
        p(f"Moving {filename} to {dst_file}")
        shutil.move(filename, dst_file)
    return dst_file


def round59(num_in):
    rv = num_in
    if num_in is not None:
        if num_in < -1 or num_in > 1:
            rv = round(num_in, 5)
        else:
            rv = round(num_in, 9)
    return rv


def get_date_from_str(s):
    pattern = r'(\d{8})'
    results = re.findall(pattern, str(s))
    rv = results[0] if len(results) else None
    return rv


def log_args(args_to_print):
    out = "args: "
    for key in sorted(args_to_print.__dict__):
        out += "{}= {} ,".format(key, args_to_print.__dict__[key])
    p(f'{out[0:-1]}')


def print_final_msg(start_time):
    end_datetime = datetime.now()
    exec_time = (end_datetime - start_time).total_seconds()
    final_msg = f"Ended successfully on {end_datetime} after {round(exec_time, 2)} seconds"
    if exec_time > 60:
        exec_time_minutes = exec_time / 60
        final_msg += f", which are {round(exec_time_minutes, 2)} minutes"
        if exec_time_minutes > 60:
            exec_time_hours = exec_time_minutes / 60
            final_msg += f", which are {round(exec_time_hours, 2)} hours"

    p(f"{final_msg}")


# Avoid adding .gz extension i.e. assume filename ends with .gz for zipped files.
def get_file_handler(filename):
    file_handler = None
    if os.path.exists(filename):
        if filename.endswith('.gz'):
            file_handler = gzip.open(filename, 'rt')
        elif filename.endswith('.zst'):
            file_handler = zstd.open(filename, 'r')
        else:
            file_handler = open(filename)
    else:
        p(f'Can NOT find file {filename} .Quitting', True)
    return file_handler


def market_data_reader_time_to_secs_since_midnight(market_data_reader_time):
    hh, mm, ssmmm = market_data_reader_time.split(':')
    rv = int(hh) * 3600 + int(mm) * 60 + float(ssmmm)
    return rv
