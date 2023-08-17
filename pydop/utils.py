
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
import bisect

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
    return "/" + "/".join(map(str, self))
  def __getitem__(self, key):
    if(isinstance(key, int)): return tuple.__getitem__(self, key)
    else: return path__c(tuple.__getitem__(self, key))

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
  __slots__ = ("m_content",)
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
      errors.add_unbound(name, path[:-1])
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



################################################################################
# intervals and domains
################################################################################

float_inf_minus = float("-inf")
float_inf_plus  = float("inf")

def is_valid_bound(v):
  """is_valid_bound(object) -> bool
returns if the object in parameter is a valid bound (either int or a float)
  """
  return isinstance(v, (int, float,))

def is_valid_bound_ext(v):
  """is_valid_bound_ext(object) -> bool
returns if the object in parameter is a valid extended bound (either int, float or None for infinity)
  """
  return ((v is None) or is_valid_bound(v))


def _nf_of_bound_(b, is_min):
  if(b is None):
    if(is_min): return float_inf_minus
    else: return float_inf_plus
  else:
    return b


def _interval_error_(obj): return ValueError(f"ERROR: an interval must be a pair (a,b) with a<b (found {obj})")

class interval__c(tuple):
  __slots__ = ()
  def __new__(cls, v_min, v_max):
    v_min = _nf_of_bound_(v_min, True)
    v_max = _nf_of_bound_(v_max, False)
    if(is_valid_bound(v_min) and  is_valid_bound(v_max) and (v_min <= v_max)):
      return tuple.__new__(interval__c, (v_min, v_max))
    else: raise _interval_error_((v_min, v_max))

  def contains(self, value):
    return ((self[0] <= value) and (value < self[1]))
  def __str__(self):
    if(self[0] == float_inf_minus): return f"]{self[0]}, {self[1]}["
    else: return f"[{self[0]}, {self[1]}["

def interval_min(v): return v[0]
def interval_max(v): return v[1]

def interval_of_obj(obj):
  if(isinstance(obj, interval__c)): return obj
  elif(isinstance(obj, int)): return interval__c(obj, obj+1)
  elif(isinstance(obj, (list, tuple)) and (len(obj) == 2)):
    return interval__c(obj[0], obj[1])
  else:
    raise _interval_error_(obj)

def _extend_dlist_interval_(dlist, v):
  v_min, v_max = v
  idx_min = bisect.bisect(dlist, v_min, key=interval_min)
  idx_max = bisect.bisect(dlist, v_max, key=interval_max)
  if(idx_min == 0):
    if(idx_max == len(dlist)): return [v]
    else:
      v_next = dlist[idx_max]
      if(v_next[0] <= v_max):
        return [interval__c(v_min, v_next[1]), *dlist[idx_max+1:]]
      else:
        return  [v, *dlist[idx_max:]]
  else:
    v_prev = dlist[idx_min-1]
    if(v_min <= v_prev[1]):
      idx_min -= 1
      v_min = v_prev[0]
    if(idx_max == len(dlist)): return [*dlist[:idx_min], interval__c(v_min, v_max)]
    else:
      v_next = dlist[idx_max]
      if(v_next[0] <= v_max):
        if(idx_min < 0): return [interval__c(v_min, v_next[1]), *dlist[idx_max+1:]]
        else: return [*dlist[:idx_min], interval__c(v_min, v_next[1]), *dlist[idx_max+1:]]
      else:
        if(idx_min < 0): return [interval__c(v_min, v_max), *dlist[idx_max:]]
        return [*dlist[:idx_min], interval__c(v_min, v_max), *dlist[idx_max:]]

class domain__c(tuple):
  __slots__ = ()
  def __new__(cls, *args):
    if((len(args) == 2) and (is_valid_bound_ext(args[0])) and (is_valid_bound_ext(args[1]))):
      args = (interval__c(args[0], args[1]),)
    elif((len(args) == 1) and isinstance(args[0], int)):
      args = (interval__c(args[0], args[0]+1),)
    res = []
    for arg in args:
      res = _extend_dlist_interval_(res, interval_of_obj(arg))
    return tuple.__new__(domain__c, res)
  def contains(self, value):
    if(bool(self)):
      idx = bisect.bisect(self, value, key=interval_min)
      return (0 < idx) and (value < self[idx-1][1])
    else: return True
  def __str__(self):
    if(bool(self)):
      return " ∪ ".join(map(str, self))
    else:
      return "]-inf, inf["



################################################################################
# for CNF DIMACS translation
################################################################################

def anot(value):
  """
  Util function that implements the negation of a boolean value or a dimacs atom (i.e., integer)
  """
  if(value is True): return False
  elif(value is False): return True
  else:
    assert (isinstance(value, int))
    return - value

class dimacs__c(object):
  """Represents a dimacs-encoded SAT problem.
Includes a registry for automatic conversion from variable name to dimacs representation (i.e., integers)
  """
  __slots__ = ("m_vreg", "m_clauses", "m_counter", "has_true_clause", "has_false_clause", "m_nb_clause",)
  def __init__(self):
    self.m_vreg = {}
    self.m_clauses = []
    self.m_counter = 1
    self.has_true_clause = False
    self.has_false_clause = False
    self.m_nb_clause = 0

  def get(self, v):
    """"get(object) -> integer
Returns the id of the variable name in parameter
    """
    res = self.m_vreg.get(v)
    if(res is None):
      res = self.m_counter
      self.m_counter += 1
      self.m_vreg[v] = res
    return res

  def add_clause(self, clause):
    """add_clause(tuple[int | bool]) -> NoneType
add_clause(list[int] | bool) -> NoneType
Adds a clause to the CNF problem
    """
    # 1. ensure clause consistency
    assert (isinstance(clause, (tuple, list)))
    clause = tuple(map(self._add_clause_el_, clause))
    # 2. register clause
    self.m_clauses.append(clause)
    self.m_nb_clause += 1

  def _add_clause_el_(self, el):
    if(el is True):
      self.has_true_clause = True
      return self.get(el)
    elif(el is False):
      self.has_false_clause = True
      return self.get(el)
    else:
      assert (isinstance(el, int) and (-self.m_counter < el) and (el < self.m_counter))
      return el

  def add_comment(self, comment):
    """add_comment(str) -> NoneType
Adds a comment to the clause list (useful for documenting the generated CNF file)
    """
    assert (isinstance(comment, str))
    self.m_clauses.append(comment)

  def get_mapping(self):
    """get_mapping() -> dict[object, int]
Returns the dict mapping every variable to its dimacs integer
    """
    return self.m_vreg
  def get_clauses(self):
    """get_clauses() -> list[tuple[int]]
Returns the list of clause of this CNF problem
    """
    return self.m_clauses

  def to_string(self, dom=None):
    """to_string() -> str
to_string(iterable[object]) -> str
to_string(iterable[pair[object, str]]) -> str
Returns the textual representation of this CNF problem, using the dimacs format.
The optional parameter is used to identify which variable must be documented in the header of the file,
 i.e., for each variable object `v` in `dom`, a comment is added at the start of the file of the form
```c id variable_name```
where `id` is the dimacs integer corresponding to `v`, and `variable_name` is either `v` or the string associated to `v` in `dom`
    """
    if(dom is None):
      dom = ()
    res = ""
    # 1. print variable name
    for el in dom:
      if(isinstance(el, (tuple, list)) and (len(el) == 2)):
        key, name = el
      else:
        key = el
        name = el
      res += f"c {self.m_vreg[key]} {name}\n"
    nb_clause = self.m_nb_clause
    if(self.has_true_clause): nb_clause += 1
    if(self.has_false_clause): nb_clause += 1
    res += f"p cnf {self.m_counter - 1} {nb_clause}\n"
    for c in self.m_clauses:
      if(isinstance(c, str)):
        res += f"c {c}\n"
      else:
        res += f"{' '.join(map(str, c))} 0\n"
    if(self.has_true_clause): res += f"{self.get(True)} 0\n"
    if(self.has_false_clause): res += f"{-self.get(False)} 0\n"
    return res

  def __str__(self):
    return self.to_string()


################################################################################
# for debugging
################################################################################

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
