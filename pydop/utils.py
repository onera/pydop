
# This file is part of the pydop library.
# Copyright (c) 2021 ONERA.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program. If not, see
# <http://www.gnu.org/licenses/>.
#

# Author: Michael Lienhardt
# Maintainer: Michael Lienhardt
# email: michael.lienhardt@onera.fr


##########################################
# the empty object, for get API

class _empty_c__(object):
  __slots__ = ()
  def __str__(self): return "_empty__"
  def __repr__(self): return "_empty__"

_empty__ = _empty_c__()


##########################################
# path manipulation

def _path_from_str__(s):
  if(isinstance(s, str)):
    return s.split('/')
  elif(isinstance(s, (tuple, list))):
    if(all(map((lambda e: isinstance(e, str)), s))):
      return s
  raise ValueError(f"ERROR: unexpected path type (expected str, tuple[str] or list[str], found {type(s)})")

def _path_to_str__(path):
  if(isinstance(path, str)):
    return path
  elif(isinstance(path, (tuple, list))):
    if(all(map((lambda e: isinstance(e, str)), path))):
      return "/".join(path)
  elif(isinstance(path, type(None))):
    return "None"
  raise ValueError(f"ERROR: unexpected path type (expected str, tuple or list, found {type(path)})")

