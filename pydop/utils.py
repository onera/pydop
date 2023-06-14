
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


import itertools

##########################################
# the empty object, for get API

class _empty_c__(object):
  """Class for the object corresponding to the empty value (in case None can be a value)"""
  __slots__ = ()
  def __str__(self): return "_empty__"
  def __repr__(self): return "_empty__"

"""The empty object"""
_empty__ = _empty_c__()


################################################################################
# path manipulation
################################################################################

def _is_str_(s):
  """_is_str_(object) -> bool
Returns if the object in parameter is a string
  """
  return isinstance(s, str)


def _path_from_str__(s):
  """convert a string, tuple or list into a path"""
  if(_is_str_(s)):
    return s.split('/')
  elif(isinstance(s, (tuple, list))):
    return s
  raise ValueError(f"ERROR: unexpected path type (expected str, tuple or list, found {type(s)})")

def _path_to_str__(path):
  if(_is_str_(path)):
    return path
  elif(isinstance(path, (tuple, list))):
    if(all(map((lambda e: isinstance(e, str)), path))):
      return "/".join(path)
  elif(isinstance(path, type(None))):
    return "None"
  raise ValueError(f"ERROR: unexpected path type (expected str, tuple or list, found {type(path)})")


class path__c(tuple):
  __slots__ = ()
  def __new__(cls, content=()):
    return tuple.__new__(path__c, path__c._manage_parameter_(content))
  def __add__(self, suffix):
    return path__c(itertools.chain(self, path__c._manage_parameter_(suffix)))
  def __str__(self):
    return "/".join(map(str, self))

  @staticmethod
  def _manage_parameter_(param):
    if(isinstance(param, str)):
      param = param.split('/')
    return param




################################################################################
# path lookup class
################################################################################

class lookup__c(object):
  """Class for variable lookup"""
  __slots__ = ("m_content")
  def __init__(self):
    self.m_content = {}

  def insert(self, obj, path, errors):
    """insert(object, path, decl_errors__c)
States that `obj` is uniquely identified with `path`.
Can store a duplication error in the `errors` object in case it is not the case
    """
    name = path[-1]
    decls = self.m_content.get(name)
    if(decls is None):
      self.m_content[name] = [ (obj, path) ]
    else:
      other = None
      for obj_other, path_other in decls:
        if(path == path_other):
          other = obj_other
          break
      if(other is not None):
        errors.add_duplicate(path, obj, other)
      decls.append( (obj, path) )

  def get(self, path, location, errors, default=None):
    """get(path, object, decl_errors__c) -> object
get(path, object, decl_errors__c, object) -> object
Gets the object corresponding to the path in parameter.
The `location` parameter states where `path` is being requested
If the path does not correspond to any object, adds an unbound error to `errors` and returns `default`.
If the path corresponds to multiple objects, adds an abiguous error to `errors` and returns `default`.
    """
    name = path[-1]
    decls = self.m_content.get(name)
    if(decls is None):
      errors.add_unbound(name)
    else:
      refs = tuple(filter((lambda data: lookup__c._path_includes__(data[1], path)), decls))
      length = len(refs)
      if(length == 0):
        errors.add_unbound(name, path[:-1])
      elif(length > 1):
        errors.add_ambiguous(name, path[:-1], tuple(data[1] for data in refs))
      else:
        return refs[0][0]
    return default

  # def get_with_path(self, path, suffix, errors, default=None):
  #   path = path + _path_from_str__(suffix)
  #   return self.get(path, errors, default)


  def resolve(self, key, location, errors, default=None):
    """resolve(object, object, errors) -> object
resolve(object, object, errors, object) -> object
Wrapper around the `get` method, where the path is not yet formated
    """
    try:
      key_path = path__c(key)
      return self.get(key_path, location, errors, default)
    except ValueError:
      return default


  @staticmethod
  def _path_includes__(p, p_included):
    """_path_includes__(path, path) -> bool
Returns if `p_included` is included in `p`
    """
    # print(f"_path_includes__({p}, {p_included})")
    idx_p = 0
    idx_included = 0
    len_p = len(p)
    len_included = len(p_included)
    while(idx_included < len_included):
      if(idx_p < len_p):
        if(p[idx_p] == p_included[idx_included]):
          idx_included += 1
        idx_p += 1
      else:
        return False
    return True

  def __iter__(self):
    for v in self.m_content.values():
      for obj, path in v:
        yield path

class lookup_wrapper__c(object):
  __slots__ = ("m_root", "m_prefix",)
  def __init__(self, root, prefix):
    self.m_root = root
    self.m_prefix = prefix

  def get(self, path, location, errors, default=None):
    return self.m_root.get(self.m_prefix + path, location, errors, default)

  def resolve(self, key, location, errors, default=None):
    return self.m_root.resolve(self.m_prefix + key, location, errors, default)





##########################################
# for debug
indent_counter = 0

def wrap_start_end(f):
  def res(*args, **kwargs):
    global indent_counter
    print((" " * indent_counter) + f"starting {f.__name__}({args[0].name}, {args[1:]}, {kwargs})")
    indent_counter += 1
    res = f(*args, **kwargs)
    indent_counter -= 1
    print((" " * indent_counter) + f"ending {f.__name__}")
    return res
  return res
