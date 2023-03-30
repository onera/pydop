
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

################################################################################
# error reporting
################################################################################

##########################################
# 1. feature model naming consistency

class _unbound__c(object):
  # when a name is not declared
  __slots__ = ("m_name", "m_path",)
  def __init__(self, name, path=None):
    self.m_name = name
    self.m_path = path
  def __str__(self):
    if(self.m_path is None):
      return f"ERROR: variable \"{self.m_name}\" not declared"
    else:
      return f"ERROR: variable \"{self.m_name}\" not declared in (partial) path \"{_path_to_str__(self.m_path)}\""

class _ambiguous__c(object):
  # when a partial path corresponds to several possibilities
  __slots__ = ("m_name", "m_path", "m_paths",)
  def __init__(self, name, path, paths):
    self.m_name  = name
    self.m_path  = path
    self.m_paths = paths
  def __str__(self):
    tmp = ", ".join(f"\"{_path_to_str__(p)}\"" for p in self.m_paths)
    if(self.m_path is None):
      return f"ERROR: reference \"{self.m_name}\" is ambiguous (corresponds to paths: {tmp})"
    else:
      return f"ERROR: reference \"{_path_to_str__(self.m_path)}[{self.m_name}]\" is ambiguous (corresponds to paths: {tmp})"

class _duplicate__c(object):
  # when the same path correspond to the same object
  __slots__ = ("m_path", "m_objs",)
  def __init__(self, path, obj_main, obj_other):
    self.m_path = path
    self.m_objs = [obj_main, obj_other]
  def add(self, obj):
    self.m_objs.append(objs)
  def __str__(self):
    tmp = ", ".join(f"\"{type(obj)}\"" for obj in self.m_objs)
    return f"ERROR: path \"{_path_to_str__(self.m_path)}\" correspond to more than one object (found types {tmp})"


## main class

class decl_errors__c(object):
  __slots__ = ("m_unbounds", "m_ambiguities", "m_duplicates",)
  def __init__(self):
    self.m_unbounds = []
    self.m_ambiguities = []
    self.m_duplicates = {}

  def add_unbound(self, name, path=None):
    self.m_unbounds.append(_unbound__c(name, path))
  def add_ambiguous(self, name, path, paths):
    self.m_unbounds.append(_ambiguous__c(name, path, paths))
  def add_duplicate(self, path, obj_main, obj_other):
    ref = self.m_duplicates.get(path)
    if(ref is None):
      self.m_duplicates[path] = _duplicate__c(path, obj_main, obj_other)
    else:
      ref.add(obj_main)

  def __bool__(self):
    return bool(self.m_unbounds) or bool(self.m_ambiguities) or bool(self.m_duplicates)
  def __str__(self):
    return "\n".join(str(el) for el in itertools.chain(self.m_unbounds, self.m_ambiguities, self.m_duplicates.values()))

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
    if(expected is None):
      return f"{self.m_ref} vs {self.m_val}"
    else:
      return f"{self.m_ref} vs {self.m_val} (expected: {self.m_expected})"

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

class _reason_value_mismatch__c(object):
  __slots__ = ("m_name", "m_ref", "m_val", "m_expected",)
  def __init__(self, ref, val, expected=None):
    self.m_ref = ref
    self.m_val = val
    self.m_expected = expected
  def update_ref(self, updater): self.m_ref = updater(self.m_ref)
  def __str__(self):
    if(self.m_expected is None):
      return f"{self.m_ref} vs {self.m_val}"
    else:
      return f"{self.m_ref} vs {self.m_val} (expected: {self.m_expected})"

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
    self.m_local.append(_reason_value_mismatch__c(ref, val, expected))
    self.m_count += 1
  def add_reason_value_none(self, ref):
    self.m_local.append(_reason_value_none__c(ref))
    self.m_count += 1
  def add_reason_dependencies(self, ref, deps):
    self.m_local.append(_reason_dependencies__c(ref, deps))
    self.m_count += 1  
  def add_reason_sub(self, sub):
    if((isinstance(sub, eval_result__c)) and (sub.m_reason is not None) and (bool(sub.m_reason))):
      self.m_subs.append(sub.m_reason)
      self.m_count += 1

  def update_ref(self, updater):
    self.m_ref = updater(self.m_ref)
    for el in itertools.chain(self.m_local, self.m_subs):
      el.update_ref(updater)

  def _tostring__(self, indent):
    if(self.m_count == 0):
      return ""
    elif(self.m_count == 1):
      if(self.m_local):
        return f"{indent}{self.m_ref}: {self.m_local[0]}\n"
      else:
        return f"{indent}{self.m_ref}: {self.m_subs[0]._tostring__(indent)}\n"
    else:
      res = f"{indent}{self.m_ref}: (\n"
      indent_more = f"{indent} "
      for e in self.m_local:
        res += f"{indent_more}{e}\n"
      for s in self.m_subs:
        res += s._tostring__(indent_more)
      res += f"{indent})\n"
      return res

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
