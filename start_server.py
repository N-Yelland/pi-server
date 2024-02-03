#!/usr/bin/env python

"""
Starts a TCP website running on a specified port.
"""

from typing import Optional, Sequence

import asyncio
import argparse
import os

from api_requests import update_dns_record_ip_address, enter_development_mode
from server import run_server

HOSTNAME = "pi.nicyelland.com"
DEFAULT_PORT = 12233


def get_args(arg_list: Optional[Sequence[str]] = None):

    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__),
        description=__doc__,
        epilog="Created by Nicholas Yelland (c) 2024",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-d", "--dev-mode",
        action="store_true",
        help="run server in development mode, disabling Cloudflare cache"
    )

    parser.add_argument(
        "-p", "--port",
        action="store",
        type=int,
        default=DEFAULT_PORT,
        help="port on which to run the server"
    )
    parser.add_argument(
        "-u", "--update-ip",
        action="store_true",
        help="update Cloudflare DNS record with the current external IP, requested from ipify.com. Often necessary "
             "after some downtime; can be indicated by 522 errors"
    )

    return parser.parse_args(arg_list)


async def main():
    args = get_args()

    if args.dev_mode:
        print("Entering development mode...")
        await enter_development_mode()

    if args.update_ip:
        print("Updating IP address...")
        await update_dns_record_ip_address(HOSTNAME)

    await run_server(args.port)


if __name__ == "__main__":
    asyncio.run(main())