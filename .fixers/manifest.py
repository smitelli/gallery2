#!/usr/bin/python2

"""
Rewrite all Gallery2 `MANIFEST` files based on the current content of all files.

Takes no arguments, does not care about the current working directory. Starts
in the parent directory and recursively walks through all files named MANIFEST,
rewriting them with the current file hashes.

NOTE: This does not discover new files; only files that already had entries are
considered.
"""

from __future__ import print_function
import fnmatch
import zlib
from os import path, walk


def main():
    for manifest in walk_manifests():
        print(manifest)

        with open(manifest, 'r') as fh:
            out = []
            for line in fh:
                line = line.strip()

                if not line.startswith('#') and not line.startswith('R\t'):
                    line = rewrite_manifest_entry(line)

                out.append(line)

        with open(manifest, 'w') as fh:
            fh.write('\n'.join(out))
            fh.write('\n')


def walk_manifests():
    root_path = path.realpath(path.join(path.dirname(__file__), '..'))
    for root, dirnames, filenames in walk(root_path):
        for filename in fnmatch.filter(filenames, 'MANIFEST'):
            yield path.join(root, filename)


def rewrite_manifest_entry(line):
    filename = line.split('\t')[0]

    with open(filename, 'rb') as fh:
        d = fh.read()

    if filename.endswith((
            'LICENSE', 'MANIFEST', 'README', 'GNUmakefile', 'shtool', '.LESSER',
            '.TXT', '.class', '.css', '.dtd', '.htaccess', '.html', '.inc',
            '.js', '.lib', '.php', '.php-template', '.pl', '.po', '.raw',
            '.sql', '.tpl', '.txt', '.xml')):
        d_unix = d.replace('\r\n', '\n')
        d_dos = d_unix.replace('\n', '\r\n')
    else:
        d_unix = d_dos = d

    return filename + '\t' + \
        str(zlib.crc32(d_unix) & 0xffffffff) + '\t' + \
        str(zlib.crc32(d_dos) & 0xffffffff) + '\t' + \
        str(len(d_unix)) + '\t' + \
        str(len(d_dos))


if __name__ == '__main__':
    main()
