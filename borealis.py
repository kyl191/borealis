#! /usr/bin/python
from __future__ import print_function
import dropbox, json, os, pprint

class Borealis:
  config = {}

  def __init__(self, config_file_path="config.json"):
    with open(config_file_path, 'r') as config_file:
      self.config = json.load(config_file)

    if not self.config.get('access_token'):
      # Get your app key and secret from the Dropbox developer website
      app_key = self.config.get("app_key")
      app_secret = self.config.get("app_secret")

      flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)

      # Have the user sign in and authorize this token
      authorize_url = flow.start()
      print(authorize_url)
      code = raw_input("Enter the authorization code here: ").strip()

      # This will fail if the user enters an invalid authorization code
      access_token, user_id = flow.finish(code)
      self.config['access_token'] = access_token
      with open(config_file_path, 'w') as outfile:
        json.dump(data, outfile)

    self.client = dropbox.client.DropboxClient(self.config.get("access_token"))
    print("linked account: %s" % self.client.account_info().get("email"))

  def upload_file(self, path, dest_dir="/",remove_base=None):
    dest = path
    if remove_base:
      dest = path.partition(remove_base)[2]
    dest = os.path.join(dest_dir, dest)
    size = os.path.getsize(path)
    f = open(path, "rb")
    print("Uploading %s to %s" % (path, dest))
    uploader = self.client.get_chunked_uploader(f, size)
    while uploader.offset < size:
      try:
        uploader.upload_chunked()
        uploader.finish(dest)
        print("Successfully uploaded %i bytes" % uploader.offset)
        if self.config.get("delete_local"):
          os.remove(path)
      except dropbox.rest.ErrorResponse as e:
        print(e)

  def get_folder_content(self, remote_dir="/", dest_dir=os.getcwd(), remove_base=None):
    """
    Downloads all content in the Dropbox folder 'remote_dir', mirroring the folder structure
    Also optionally deletes everything that is downloaded
    Doesn't attempt to do error checking
    """
    files = self.client.metadata(remote_dir)["contents"]
    for f in files:
      path = f.get("path")
      print("Considering %s" % f.get("path"))
      # If the file entry is a directory, recurse into it
      if f.get("is_dir"):
        get_files_in_folder(path, remove_base)
      else:
        # Dropbox path might have a base component we want to remove
        if remove_base:
          path = path.partition(remove_base)[2]
        # Get rid of the leading slash if present
        if path.startswith("/"):
          path = path[1:]
        # Build local destination path
        path = os.path.join(dest_dir, path)
        # Split the directory and filename
        directory, _ = os.path.split(path)
        # If the eventual destination directory doesn't exist, create it
        if not os.path.isdir(directory):
          os.makedirs(directory, 0755)
        # Download the file
        # Because we've manipulated path, go back to using f.get("path") for the dropbox access
        with open(path, 'wb') as dest, self.client.get_file(f.get("path")) as src:
          dest.write(src.read())
      # Regardless of whether it was a file or folder, delete it from Dropbox
      if self.config.get("delete_remote"):
        print("Deleting %s" % f.get("path"))
        self.client.file_delete(f.get("path"))

  def wait_for_activity(self, folder="/"):
    """
    This is meant to be a blocking call. The return value means nothing
    """
    d = self.client.delta(path_prefix=folder)
    while True:
      try:
        self.client.longpoll_delta(d['cursor'])
        break
      except dropbox.rest.ErrorResponse as e:
        print(e)
    return True
