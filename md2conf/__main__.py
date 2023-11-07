import argparse
import logging
import os.path
import sys
import typing
from typing import Optional

import requests

from .api import ConfluenceAPI
from .application import Application
from .converter import ConfluenceDocumentOptions


class Arguments(argparse.Namespace):
    mdpath: str
    domain: str
    path: str
    username: str
    apikey: str
    space: str
    loglevel: str
    ignore_invalid_url: bool
    generated_by: Optional[str]


parser = argparse.ArgumentParser()
parser.prog = os.path.basename(os.path.dirname(__file__))
parser.add_argument(
    "mdpath", help="Path to Markdown file or directory to convert and publish."
)
parser.add_argument("-d", "--domain", help="Confluence organization domain.")
parser.add_argument("-p", "--path", help="Base path for Confluece wiki.")
parser.add_argument("-u", "--username", help="Confluence user name.")
parser.add_argument(
    "-a",
    "--apikey",
    help="Confluence API key. Refer to documentation how to obtain one.",
)
parser.add_argument(
    "-s",
    "--space",
    help="Confluence space key for pages to be published. If omitted, will default to user space.",
)
parser.add_argument(
    "-l",
    "--loglevel",
    choices=[
        typing.cast(str, logging.getLevelName(level)).lower()
        for level in (
            logging.DEBUG,
            logging.INFO,
            logging.WARN,
            logging.ERROR,
            logging.CRITICAL,
        )
    ],
    default=logging.getLevelName(logging.INFO),
    help="Use this option to set the log verbosity.",
)
parser.add_argument(
    "--generated-by",
    default="This page has been generated with a tool.",
    help="Add prompt to pages (default: 'This page has been generated with a tool.').",
)
parser.add_argument(
    "--no-generated-by",
    dest="generated_by",
    action="store_const",
    const=None,
    help="Do not add 'generated by a tool' prompt to pages.",
)
parser.add_argument(
    "--ignore-invalid-url",
    action="store_true",
    default=False,
    help="Emit a warning but otherwise ignore relative URLs that point to ill-specified locations.",
)

args = Arguments()
parser.parse_args(namespace=args)

logging.basicConfig(
    level=getattr(logging, args.loglevel.upper(), logging.INFO),
    format="%(asctime)s - %(levelname)s - %(funcName)s [%(lineno)d] - %(message)s",
)

try:
    with ConfluenceAPI(
        args.domain, args.path, args.username, args.apikey, args.space
    ) as api:
        Application(
            api,
            ConfluenceDocumentOptions(
                ignore_invalid_url=args.ignore_invalid_url,
                generated_by=args.generated_by,
            ),
        ).synchronize(args.mdpath)
except requests.exceptions.HTTPError as err:
    logging.error(err)

    # print details for a response with JSON body
    if err.response is not None:
        try:
            logging.error(err.response.json())
        except requests.exceptions.JSONDecodeError:
            pass

    sys.exit(1)
