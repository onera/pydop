
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

"""
This file contains all the classes used for error reporting,
and a wrapper class `eval_result__c` around `bool` that stores a tree of errors hinting to why the bool is False
"""


import itertools

# from pydop.utils import _path_to_str__

################################################################################
# error reporting
################################################################################

##########################################
# 1. feature model naming consistency

class _unbound__c(object):
  """This class states that a used variable name is not declared"""
  __slots__ = ("m_name",)
  def __init__(self, name):
    """_unbound__c(name) -> _unbound__c
States that `name` does not correspond to a declared variable
    """
    self.m_name = name
  def __str__(self):
    return f"variable \"{self.m_name}\" not declared"

class _ambiguous__c(object):
  """This class states that a used variable name is ambiguous (it corresponds to multiple variables)"""
  __slots__ = ("m_name", "m_variables",)
  def __init__(self, name, variables):
    """_ambiguous__c(name, variables) -> _ambiguous__c
States that `name` corresponds to the given set of variables
    """
    self.m_name  = name
    self.m_variables = variables
  def __str__(self):
    tmp = ", ".join(f"\"{p}\"" for p in self.m_variables)
    return f"reference \"{self.m_name}\" is ambiguous (corresponds to variables: {tmp})"

class _duplicate__c(object):
  """This class states that an exact path is ambiguous (it corresponds to multiple variables)"""
  __slots__ = ("m_variables",)
  def __init__(self, variables):
    """_duplicate__c(variables) -> _duplicate__c
States that variables in parameters have the same identifier
    """
    self.m_variables = set(variables)
  def add(self, *variables):
    self.m_variables.update(variables)
  def __len__(self): return len(self.m_variables)
  def __str__(self):
    tmp = ", ".join(f"\"{obj}\"" for obj in self.m_variables)
    return f"this path corresponds to more than one object (found {tmp})"


## main class

class decl_errors__c(object):
  """This is a global class managing all naming errors during analysis."""
  __slots__ = ("m_content",)
  def __init__(self):
    """decl_errors__c() -> decl_errors__c"""
    self.m_content = {}

  def add_unbound(self, name, location):
    """add_unbound(str, path__c) -> None
Adds the error that `name` does not correspond to any variable in `location`
    """
    tmp = self._ensure_(location)
    tmp[0].append(_unbound__c(name))
    return self
  def add_ambiguous(self, name, location, variables):
    """add_ambiguous(str, path__c, set[object]) -> None
Adds the error that `name` corresponds to several variables in `location`
    """
    tmp = self._ensure_(location)
    tmp[0].append(_ambiguous__c(name, variables))
    return self
  def add_duplicate(self, location, obj_main, obj_other):
    """add_duplicate(str, path__c, object, object) -> None
Adds the error that `location/name` is the unique path of the two variables `obj_main`  and `obj_other`
    """
    tmp = self._ensure_(location)
    tmp[1].add(obj_main, obj_other)
    return self

  def _ensure_(self, location):
    res = self.m_content.get(location)
    if(res is None):
      res = ([], _duplicate__c(set()))
      self.m_content[location] = res
    return res

  def __bool__(self):
    return bool(self.m_content)
  def __iter__(self):
    for loc, el in self.m_content.items():
      for sub in el[0]:
        yield (loc, sub)
      if(len(el[1]) > 1): yield (loc, el[1])
  def __str__(self):
    return "\n".join(f"In {loc}:\n" + decl_errors__c._str_from_el_(el) for loc, el in self.m_content.items())

  @staticmethod
  def _str_from_el_(el):
    res = "\n".join(f"  {error}" for error in el[0])
    if(len(el[1]) > 1):
      if(bool(res)): res += f"\n  {el[1]}"
      else: res = f"  {el[1]}"
    return res



##########################################
# 2. constraint and fm evaluation

class _reason_value_mismatch__c(object):
  __slots__ = ("m_name", "m_ref", "m_val", "m_expected",)
  def __init__(self, ref, val, expected=None):
    self.m_ref = ref
    self.m_val = val
    self.m_expected = expected
  def update_ref(self, updater): self.m_ref = updater(self.m_ref)
  def __str__(self):
    if(self.m_expected is None):
      return f"{self.m_ref} is {self.m_val}"
    else:
      return f"{self.m_ref} is {self.m_val} (expected: {self.m_expected})"

class _reason_value_none__c(object):
  __slots__ = ("m_ref",)
  def __init__(self, ref):
    self.m_ref = ref
  def update_ref(self, updater): self.m_ref = updater(self.m_ref)
  def __str__(self):
    return f"{self.m_ref} has no value in the input configuration"

class _reason_dependencies__c(object):
  __slots__ = ("m_ref", "m_deps",)
  def __init__(self, ref, deps):
    self.m_ref = ref
    self.m_deps = deps
  def update_ref(self, updater):
    self.m_ref = updater(self.m_ref)
    self.m_deps = tuple(updater(el) for el in self.m_deps)
  def __str__(self):
    tmp = ', '.join(f"\"{el}\"" for el in self.m_deps)
    return f"{self.m_ref} should be True due to dependencies (found: {tmp})"

class _reason_value_none__c(object):
  __slots__ = ("m_ref",)
  def __init__(self, ref):
    self.m_ref = ref
  def update_ref(self, updater): self.m_ref = updater(self.m_ref)
  def __str__(self):
    return f"{self.m_ref} has no value in the input configuration"

class _reason_dependencies__c(object):
  __slots__ = ("m_ref", "m_deps",)
  def __init__(self, ref, deps):
    self.m_ref = ref
    self.m_deps = deps
  def update_ref(self, updater):
    self.m_ref = updater(self.m_ref)
    self.m_deps = tuple(updater(el) for el in self.m_deps)
  def __str__(self):
    tmp = ', '.join(f"\"{el}\"" for el in self.m_deps)
    return f"{self.m_ref} should be True due to dependencies (found: {tmp})"


## main class

class reason_tree__c(object):
  __slots__ = ("m_ref", "m_local", "m_subs", "m_count",)
  def __init__(self, name, idx):
    self.m_ref = f"[{idx}]" if(name is None) else name
    self.m_local = []
    self.m_subs = []
    self.m_count = 0

  def add_reason_value_mismatch(self, ref, val, expected=None):
    # print(f"add_reason_value_mismatch({ref.name}, {val}, {expected})")
    self.m_local.append(_reason_value_mismatch__c(ref, val, expected))
    self.m_count += 1
    return self
  def add_reason_value_none(self, ref):
    # print(f"add_reason_value_none({ref})")
    self.m_local.append(_reason_value_none__c(ref))
    self.m_count += 1
    return self
  def add_reason_dependencies(self, ref, deps):
    # print(f"add_reason_dependencies({ref}, {deps})")
    self.m_local.append(_reason_dependencies__c(ref, deps))
    self.m_count += 1  
    return self
  def add_reason_sub(self, sub):
    # print(f"add_reason_sub({sub})")
    if((isinstance(sub, eval_result__c)) and (sub.m_reason is not None) and (bool(sub.m_reason))):
      self.m_subs.append(sub.m_reason)
      self.m_count += 1
    return self

  def update_ref(self, updater):
    self.m_ref = updater(self.m_ref)
    for el in itertools.chain(self.m_local, self.m_subs):
      el.update_ref(updater)

  def _tostring__(self, indent):
    if(self.m_count == 0):
      return ""
    elif(self.m_count == 1):
      if(self.m_local):
        return f"{indent}{self.m_ref}: {self.m_local[0]}"
      else:
        return f"{indent}{self.m_ref}: {self.m_subs[0]._tostring__(indent)}"
    else:
      res = f"{indent}{self.m_ref}: (\n"
      indent_more = f"{indent} "
      for e in self.m_local:
        res += f"{indent_more}{e}\n"
      for s in self.m_subs:
        res += s._tostring__(indent_more) + "\n"
      res += f"{indent})"
      return res

  def __len__(self): return self.m_count
  def __iter__(self): return itertools.chain(iter(self.m_local), iter(self.m_subs))
  def __bool__(self): return (self.m_count != 0)
  def __str__(self): return self._tostring__("")


################################################################################
# evaluation result
################################################################################

class eval_result__c(object):
  __slots__ = ("m_value", "m_reason",)
  def __init__(self, value, reason):
    self.m_value  = value   # the result of the evaluation
    self.m_reason = reason  # reason for which the result is not what was expected

  def value(self): return self.m_value
  def __bool__(self): return self.value()
