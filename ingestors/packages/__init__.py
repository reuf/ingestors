import logging
import shutil
import gzip
import bz2
import rarfile
import zipfile
import tarfile

from ingestors.base import Ingestor
from ingestors.support.shell import ShellSupport
from ingestors.support.package import PackageSupport
from ingestors.util import join_path

log = logging.getLogger(__name__)


class RARIngestor(PackageSupport, Ingestor):
    MIME_TYPES = [
        'application/x-rar'
    ]
    EXTENSIONS = ['rar']
    SCORE = 4

    def unpack(self, file_path, temp_dir):
        # FIXME: need to figure out how to unpack multi-part files.
        with rarfile.RarFile(file_path) as rf:
            self.unpack_members(rf, temp_dir)

    @classmethod
    def match(cls, file_path, mime_type=None):
        if rarfile.is_rarfile(file_path):
            return cls.SCORE
        return super(RARIngestor, cls).match(file_path, mime_type=mime_type)


class ZipIngestor(PackageSupport, Ingestor):
    MIME_TYPES = [
        'application/zip'
    ]
    EXTENSIONS = ['zip']
    SCORE = 3

    def unpack(self, file_path, temp_dir):
        with zipfile.ZipFile(file_path) as zf:
            self.unpack_members(zf, temp_dir)

    @classmethod
    def match(cls, file_path, mime_type=None):
        if zipfile.is_zipfile(file_path):
            return cls.SCORE
        return super(ZipIngestor, cls).match(file_path, mime_type=mime_type)


class TarIngestor(PackageSupport, Ingestor):
    MIME_TYPES = [
        'application/x-tar'
    ]
    EXTENSIONS = ['tar']
    SCORE = 4

    def unpack(self, file_path, temp_dir):
        with tarfile.open(name=file_path, mode='r:*') as tf:
            tf.extractall(temp_dir)

    @classmethod
    def match(cls, file_path, mime_type=None):
        if tarfile.is_tarfile(file_path):
            return cls.SCORE
        return super(TarIngestor, cls).match(file_path, mime_type=mime_type)


class SevenZipIngestor(PackageSupport, Ingestor, ShellSupport):
    MIME_TYPES = ['application/x-7z-compressed']
    EXTENSIONS = ['7z', '7zip']
    SCORE = 4

    def unpack(self, file_path, temp_dir):
        self.exec_command('7z',
                          'x', file_path,
                          '-y',
                          '-r',
                          '-bb0',
                          '-bd',
                          '-oc:%s' % temp_dir)


class SingleFilePackageIngestor(PackageSupport, Ingestor):
    SCORE = 2

    def unpack(self, file_path, temp_dir):
        file_name = self.result.file_name
        for ext in self.EXTENSIONS:
            ext = '.' + ext
            if file_name.endswith(ext):
                file_name = file_name[:len(file_name) - len(ext)]
        temp_file = join_path(temp_dir, file_name)
        self.unpack_file(file_path, temp_file)

    @classmethod
    def match(cls, file_path, mime_type=None):
        if tarfile.is_tarfile(file_path):
            return -1
        return super(SingleFilePackageIngestor, cls).match(file_path,
                                                           mime_type=mime_type)


class GzipIngestor(SingleFilePackageIngestor):
    MIME_TYPES = ['application/x-gzip', 'multipart/x-gzip']
    EXTENSIONS = ['gz', 'tgz']

    def unpack_file(self, file_path, temp_file):
        with gzip.GzipFile(file_path) as src:
            with open(temp_file, 'wb') as dst:
                shutil.copyfileobj(src, dst)


class BZ2Ingestor(SingleFilePackageIngestor):
    MIME_TYPES = ['application/x-bzip', 'application/x-bzip2',
                  'multipart/x-bzip', 'multipart/x-bzip2']
    EXTENSIONS = ['bz', 'tbz', 'bz2', 'tbz2']

    def unpack_file(self, file_path, temp_file):
        with bz2.BZ2File(file_path) as src:
            with open(temp_file, 'wb') as dst:
                shutil.copyfileobj(src, dst)
