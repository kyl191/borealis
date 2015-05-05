from __future__ import print_function
import os, time, sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from borealis import Borealis

class Handler(FileSystemEventHandler):
  app = Borealis("config.json")

  def __init__(self, dest_dir = "/", remove_base=None):
    FileSystemEventHandler.__init__(self)
    self.dest_dir = dest_dir
    self.remove_base = remove_base

  # Copying a file into a watched file only generates a created event
  def on_created(self, event):
    print(event.src_path, event.event_type)
    if not event.is_directory:
      self.app.upload_file(event.src_path, dest_dir=self.dest_dir, remove_base=self.remove_base)
    else:
      for (root, dirs, files) in os.walk(event.src_path, topdown=False):
        for file in files:
          self.app.upload_file(os.path.join(root, file), dest_dir=self.dest_dir, remove_base=self.remove_base)
        if not os.listdir(root):
          os.rmdir(root)

if __name__ == '__main__':
  args = sys.argv[1:]
  path = args[0] if args else "/var/lib/transmission-daemon/downloads/"
  observer = Observer()
  observer.schedule(Handler(dest_dir = "/downloads", remove_base=path), path=path)
  observer.start()

  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    observer.stop()

  observer.join()
