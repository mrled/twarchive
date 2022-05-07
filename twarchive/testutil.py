"""Code used exclusively for testing"""

import os
import shutil
import tempfile

from twarchive import hugo


class TemporaryHugoSite:
    """A context manager that creates a temporary Hugo site

    Creates the required (empty) directories for a hugo.HugoSite to exist
    """

    def __init__(self):
        self.site = hugo.HugoSite(tempfile.mkdtemp())
        os.mkdir(self.site.content)
        os.mkdir(self.site.content_twarchive)
        os.mkdir(self.site.data)
        os.mkdir(self.site.data_twarchive)

    def __enter__(self):
        return self.site

    def __exit__(self, exc_type, exc_value, exc_tb):
        shutil.rmtree(self.site.base)
