#!/usr/bin/env python
from pyconfigmanager.config import Config

if __name__ == "__main__":
    config = Config(schema={"a": 12, "b": 12})
    parser = config.argument_parser()
    args = parser.parse_args()
