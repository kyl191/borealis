#!/usr/bin/env python
from __future__ import print_function
from borealis import Borealis

watch_path = "/new"
dest_dir = "/var/lib/transmission-daemon/watch"
app = Borealis("config.json")

try:
  while True:
    app.wait_for_activity(watch_path)
    # download new files
    app.get_folder_content(watch_path, dest_dir, remove_base=watch_path)
except KeyboardInterrupt:
  print("Stopping watch on %s in linked Dropbox account" % watch_path)
