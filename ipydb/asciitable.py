# -*- coding: utf-8 -*-
from future.standard_library import install_aliases
install_aliases()

"""Draw ascii tables."""
import itertools
import sys

from future.utils import string_types

from .utils import termsize


class FakedResult(object):
    """Utility for making an iterable look like an sqlalchemy ResultProxy."""

    def __init__(self, items, headings):
        self.items = items
        self.headings = headings

    def __iter__(self):
        return iter(self.items)

    def keys(self):
        return self.headings


class PivotResultSet(object):
    """Pivot a result set into an iterable of (fieldname, value)."""

    def __init__(self, rs):
        self.rs = rs

    def __iter__(self):
        # Note: here we 'ovewrite' ambiguous / duplicate keys
        # is this a bad thing? probably not?
        # r.items() throws exceptions from SA if there are ambiguous
        # columns in the select statement.
        return (zip(r.keys(), r.values()) for r in self.rs)

    def keys(self):
        return ['Field', 'Value']


def isublists(l, n):
    return itertools.zip_longest(*[iter(l)] * n)


def draw(cursor, out=sys.stdout, paginate=True, max_fieldsize=100):
    """Render an result set as an ascii-table.

    Renders an SQL result set to `out`, some file-like object.
    Assumes that we can determine the current terminal height and
    width via the termsize module.

    Args:
        cursor: An iterable of rows. Each row is a list or tuple
                with index access to each cell. The cursor
                has a list/tuple of headings via cursor.keys().
        out: File-like object.
    """

    def heading_line(sizes):
        for size in sizes:
            out.write(b'+' + b'-' * (size + 2))
        out.write(b'+\n')

    def draw_headings(headings, sizes):
        heading_line(sizes)
        for idx, size in enumerate(sizes):
            fmt = '| %%-%is ' % size
            out.write((fmt % headings[idx]).encode('utf8'))
        out.write(b'|\n')
        heading_line(sizes)

    cols, lines = termsize()
    headings = cursor.keys()
    sizes = list(map(lambda x: len(x), headings))
    if paginate:
        cursor = isublists(cursor, lines - 4)
        # else we assume cursor arrive here pre-paginated
    for screenrows in cursor:
        for row in screenrows:
            if row is None:
                break
            for idx, value in enumerate(row):
                if not isinstance(value, string_types):
                    value = str(value)
                size = max(sizes[idx], len(value))
                sizes[idx] = min(size, max_fieldsize)
        draw_headings(headings, sizes)
        for rw in screenrows:
            if rw is None:
                break  # from isublists impl
            for idx, size in enumerate(sizes):
                fmt = '| %%-%is ' % size
                value = rw[idx]
                if not isinstance(value, string_types):
                    value = str(value)
                if len(value) > max_fieldsize:
                    value = value[:max_fieldsize - 5] + '[...]'
                value = value.replace('\n', '^')
                value = value.replace('\r', '^').replace('\t', ' ')
                try:
                    value = fmt % value
                except UnicodeDecodeError:
                    value = fmt % value.decode('utf8')
                out.write(value.encode('utf8'))
            out.write(b'|\n')
        if not paginate:
            heading_line(sizes)
            out.write(b'\n')
