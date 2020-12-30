"""Common functions."""

from pathlib import Path
from typing import Iterable, Union

from hidsltools.functions import chroot, exe
from hidsltools.logging import LOGGER
from hidsltools.types import Filesystem, Partition


__all__ = ['MountContext']


MOUNT = '/usr/bin/mount'
UMOUNT = '/usr/bin/umount'


def mount(device: Union[Path, str], mountpoint: Path, *,
          fstype: Filesystem = None, verbose: bool = False, **options):
    """Mounts a partition."""

    command = [MOUNT]

    if fstype:
        command += ['-t', str(fstype)]

    if options:
        command += ['-o', ','.join(f'{k}={v}' for k, v in options.items())]

    command += [str(device), str(mountpoint)]
    exe(command, verbose=verbose)


def umount(mountpoint_or_device: Path, *, verbose: bool = False):
    """Umounts a mountpoint."""

    exe([UMOUNT, str(mountpoint_or_device)], verbose=verbose)


class MountContext:
    """Context manager for mounts."""

    def __init__(self, partitions: Iterable[Partition], *,
                 root: Union[Path, str] = '/',
                 verbose: bool = False,
                 **options):
        """Sets the partitions."""
        self.partitions = partitions
        self.root = Path(root)
        self.verbose = verbose
        self.options = options

    def __enter__(self):
        self.mount()
        return self.root

    def __exit__(self, *_):
        self.umount()

    def sorted_partitions(self, reverse: bool = False) -> Iterable[Partition]:
        """Returns the partitions sorted by mount point."""
        return sorted(self.partitions, key=lambda part: part.mountpoint,
                      reverse=reverse)

    def mount(self):
        """Mounts all partitions to the mountpoint."""
        for partition in self.sorted_partitions():
            mountpoint = chroot(self.root, partition.mountpoint)
            mountpoint.mkdir(mode=0o755, parents=True, exist_ok=True)
            LOGGER.debug('Mounting %s to %s.', partition.device, mountpoint)
            mount(partition.device, mountpoint, fstype=partition.filesystem,
                  verbose=self.verbose, **self.options)

    def umount(self):
        """Mounts all partitions to the mountpoint."""
        for partition in self.sorted_partitions(reverse=True):
            mountpoint = chroot(self.root, partition.mountpoint)
            LOGGER.debug('Umounting %s.', mountpoint)
            umount(mountpoint, verbose=self.verbose)
