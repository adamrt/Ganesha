#!/usr/bin/env python3

import os
import sys

from ganesha.ui import MapViewer


def main():
    map_path = None
    if len(sys.argv) > 1:
        map_path = sys.argv[1]
        _, ext = os.path.splitext(map_path)
        if ext.lower() != ".gns":
            print("File type must be GSN")
            sys.exit()

    viewer = MapViewer()
    viewer.start(map_path)


if __name__ == "__main__":
    main()
