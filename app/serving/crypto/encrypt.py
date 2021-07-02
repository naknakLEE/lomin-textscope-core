import argparse
import re
import os

from crypto import Crypto
from utils import encrypt_dir, encrypt_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", type=str, required=True)
    parser.add_argument("-t", "--targets", nargs="+", type=str, default=[])
    parser.add_argument("--prefix", type=str, default="lo_")
    parser.add_argument("--key", type=str, default="")
    parser.add_argument("--remove", action="store_true")
    args = parser.parse_args()

    key = bytes(args.key.encode("utf-8")) if len(args.key) > 0 else Crypto().generate_key()
    print(f"Please copy & paste this key to your config : {key}")
    print(f"Used prefix : {args.prefix}")

    if os.path.isdir(args.path):
        if len(args.targets) > 0:
            target = r"[A-Za-z0-9_-]+\." + "(" + "|".join(args.targets) + ")" + "(?!.)"
            regex = re.compile(target)
        else:
            regex = None
       
        encrypt_dir(args.path, key=key, prefix=args.prefix, filter=regex, remove=args.remove)
    else:
        encrypt_file(args.path, key=key, prefix=args.prefix, remove=args.remove)
  