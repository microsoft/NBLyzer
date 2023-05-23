# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from azure.storage.blob import (
    BlobServiceClient,
    BlobClient,
    ContainerClient,
    StorageStreamDownloader,
)
from os.path import dirname, abspath, exists
from json import loads, load

class ResourceManager:
    """
    Resource manager and caching mechanism for resource fetching both from azure storage accounts and local files.
    If access.txt is not provided remote capabilities will be disabled.
    """

    def __init__(self) -> None:
        self.remote_cache = dict()
        self.local_cache = dict()
        self.remote_capable = True
        
        ACCESS_PATH = dirname(abspath(__file__)) + "\\access.txt"

        if not exists(ACCESS_PATH):
            self.remote_capable = False
            return

        with open(ACCESS_PATH, "r") as access:
            lines: list[str] = access.readlines()

        try:
            CONNECTION_STRING, CONTAINER_NAME = lines[0], lines[1]

        except:
            raise Exception("Invalid access file format.")

        if CONNECTION_STRING[-1] == "\n":
            CONNECTION_STRING = CONNECTION_STRING[0:-1]

        if CONTAINER_NAME[-1] == "\n":
            CONTAINER_NAME = CONTAINER_NAME[0:-1]

        try:
            self.blob_service_client: BlobServiceClient = (
                BlobServiceClient.from_connection_string(CONNECTION_STRING)
            )
            self.container_client: ContainerClient = (
                self.blob_service_client.get_container_client(CONTAINER_NAME)
            )

        except:
            self.blob_service_client.close()
            raise Exception("Connection chaining storage->container failed.")

    def __del__(self):
        self.remote_cache.clear()
        self.local_cache.clear()

        if self.remote_capable:
            self.blob_service_client.close()

    def _fetch_remote(self, nb_name: str):
        """
        Helper function that fetches blob by name from fixed storage account and container.
        """
        try:
            blob_client: BlobClient = self.container_client.get_blob_client(nb_name)
            stream_downloader: StorageStreamDownloader = blob_client.download_blob()

        except:
            self.blob_service_client.close()
            raise Exception(f"Connection to blob client named {nb_name} failed.")

        return loads(stream_downloader.readall())

    def _open_local_json(self, nb_path: str):
        """
        Helper function that opens a file from a provided local path.
        """
        with open(nb_path, "rb") as f:
            return load(f)

    def _open_local_file(self, nb_path: str):
        """
        Helper function that opens a file from a provided local path.
        """
        with open(nb_path, "r") as f:
            return f.read()

    def grab_remote(self, file_name: str):
        """
        Returns remote resource (blob) requested by name. Performs fetching from storage account
        if blob is not present in cache.

        Parameters
        ----------
        file_name: str
            Name of the blob to be grabbed

        Returns
        ----------
            Byte representation of a resource matching the requested blob name.
        """
        if not self.remote_capable:
            raise Exception('Unconfigured remote connection.')

        if file_name not in self.remote_cache:
            self.remote_cache[file_name] = self._fetch_remote(file_name)

        return self.remote_cache[file_name]

    def grab_local_json(self, path_name: str):
        """
        Returns local resource requested by FULL PATH name. Performs file opening
        if path is not present in cache.

        Parameters
        ----------
        path_name: str
            Name of the file to be grabbed

        Returns
        ----------
            File representation of a file matching the requested blob name.
        """

        if path_name not in self.local_cache:
            self.local_cache[path_name] = self._open_local_json(path_name)
        
        return self.local_cache[path_name]

    def grab_local_file(self, path_name: str):
        """
        Returns local resource requested by FULL PATH name. Performs file opening
        if path is not present in cache. Does not decode json

        Parameters
        ----------
        path_name: str
            Name of the file to be grabbed

        Returns
        ----------
            File representation of a file matching the requested blob name.
        """

        if path_name not in self.local_cache:
            self.local_cache[path_name] = self._open_local_file(path_name)
        
        return self.local_cache[path_name]


mngr: ResourceManager = ResourceManager()
