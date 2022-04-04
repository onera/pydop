
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

from pydop.fm_core import fm_class, eval


class _expbool__c(fm_class): pass

class Lt(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    self.m_content = (left, right,)
  def eval(self, product):
    return (eval(self.m_content[0], product) < eval(self.m_content[1], product))

class Eq(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    self.m_content = (left, right,)
  def eval(self, product):
    return (eval(self.m_content[0], product) == eval(self.m_content[1], product))

class Leq(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    self.m_content = (left, right,)
  def eval(self, product):
    return (eval(self.m_content[0], product) <= eval(self.m_content[1], product))

class And(_expbool__c):
  __slots__ = ()
  def __init__(self, *args):
    self.m_content = tuple(args)
  def eval(self, product):
    for element in self.m_content:
      if(not eval(element, product)): return False
    return True

class Or(_expbool__c):
  __slots__ = ()
  def __init__(self, *args):
    self.m_content = tuple(args)
  def eval(self, product):
    for element in self.m_content:
      if(eval(element, product)): return True
    return False

class Not(_expbool__c):
  __slots__ = ()
  def __init__(self, args):
    self.m_content = args
  def eval(self, product):
    return not (eval(self.m_content, product))

class Xor(_expbool__c):
  __slots__ = ()
  def __init__(self, *args):
    self.m_content = tuple(args)
  def eval(self, product):
    res = False
    for element in self.m_content:
      if(eval(element, product)):
        if(res): return False
        else: res = True
    return res

class Conflict(_expbool__c):
  __slots__ = ()
  def __init__(self, *args):
    self.m_content = tuple(args)
  def eval(self, product):
    res = False
    for element in self.m_content:
      if(eval(element, product)):
        if(res): return False
        else: res = True
    return True

class Implies(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    self.m_content = (left, right,)
  def eval(self, product):
    left = eval(self.m_content[0], product)
    right = eval(self.m_content[1], product)
    return ((not left) or (right))

class Iff(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    self.m_content = (left, right,)
  def eval(self, product):
    left = eval(self.m_content[0], product)
    right = eval(self.m_content[1], product)
    return (left == right)


# 2. feature model
# ================
class _fdgroup__c(object):
  __slots__ = ("m_content",)
  def _eval__(self, product):
    consistency = True
    res = self._start__()
    for element in self.m_content:
      element = self.get(element, product)
      consistency = consistency and element[0]
      res = self._combine__(res, element[1])
    return (consistency, self._conclude__(res))
  def _get_subname__(self):
    for fd in self.m_content:
      if(isinstance(fd, str)):
        yield fd
      else:
        yield fd.m_name
  @staticmethod
  def get(element, product):
    if(isinstance(element, FD)): return element._eval__(product)
    elif(isinstance(element, str)): return (True, product[element])
    else: return element

  def _remove_subtree_from_product__(self, product):
    for element in self.m_content:
      element._remove_subtree_from_product__(product)

  def combine_product(self, default, update, res):
    for element in self.m_content:
      element.combine_product(default, update, res)



# ---------------------------------------------------------------------
class FDAnd(_fdgroup__c):
  def __init__(self, *args):
    self.m_content = tuple(args)
  @staticmethod
  def _start__(): return True
  @staticmethod
  def _combine__(left, right): return left and right
  @staticmethod
  def _conclude__(value): return value
class FDAny(_fdgroup__c):
  def __init__(self, *args):
    self.m_content = tuple(args)
  @staticmethod
  def _start__(): return True
  @staticmethod
  def _combine__(left, right): return True
  @staticmethod
  def _conclude__(value): return value
class FDOr(_fdgroup__c):
  def __init__(self, *args):
    self.m_content = tuple(args)
  @staticmethod
  def _start__(): return False
  @staticmethod
  def _combine__(left, right): return left or right
  @staticmethod
  def _conclude__(value): return value
class FDXor(_fdgroup__c):
  def __init__(self, *args):
    self.m_content = tuple(args)
  @staticmethod
  def _start__(): return 0
  @staticmethod
  def _combine__(left, right):
    if(right): return left + 1
    else: return left
  @staticmethod
  def _conclude__(value): return (value == 1)

  def combine_product(self, default, update, res):
    has_update = False
    has_add = False
    for element in self.m_content:
      val = update.get(element.m_name)
      if(val is not None): has_update = True
      if(val == True): has_add = True
    if(has_update):
      if(has_add):
        def _manage_el__(element):
          if(update.get(element.m_name, False)):
            element.combine_product(default, update, res)
      else:
        def _manage_el__(element):
          if(default[element.m_name] and update.get(element.m_name, True)):
            element.combine_product(default, update, res)
      for element in self.m_content:
        _manage_el__(element)
    else:
      _fdgroup__c.combine_product(self, default, update, res)

# ---------------------------------------------------------------------
class FD(fm_class):
  __slots__ = ("m_name", "m_groups", "m_ctcs", "m_attributes")

  def __init__(self, decl, *args, **kwargs):
    if(isinstance(decl, str)): self.m_name = decl
    else:
      raise Exception(f"FD constructor only accepts str as name (type \"{decl.__class__.__name__}\" found)")

    self.m_groups =[]
    self.m_ctcs =[]

    for sub in args:
      if(isinstance(sub, _fdgroup__c)):
        self.m_groups.append(sub)
      elif(isinstance(sub, (bool, _expbool__c, str))):
        self.m_ctcs.append(sub)
      else:
        raise Exception(f"FD constructor only accepts fdgroup, bool, expbool or str as content (type \"{sub.__class__.__name__}\" found)")

    self.m_groups = tuple(self.m_groups)
    self.m_ctcs = And(*self.m_ctcs)

    self.m_attributes = []
    for variable_name, spec in kwargs.items():
      if(isinstance(variable_name, str) and isinstance(spec, (_expbool__c, str))):
        self.m_attributes.append((variable_name, spec,))
      elif(not isinstance(variable_name, str)):
        raise Exception(f"FD attribute name must be a str (type \"{variable_name.__class__.__name__}\" found)")
      else:
        raise Exception(f"FD attribute specification only accept expbool or str (type \"{spec.__class__.__name__}\" found)")

  def _eval__(self, product):
    decl = product[self.m_name]
    ctc = self.m_ctcs.eval(product)
    # print(f"self.m_name = {self.m_name}, ctc = {ctc}")

    consistency = True
    res = True
    for group in self.m_groups:
      tmp = group._eval__(product)
      consistency = consistency and tmp[0]
      res = res and tmp[1]
      for n in group._get_subname__():
        consistency = consistency and (decl or (not product[n]))

    consistency = consistency and (res == decl) and (ctc or not decl)

    for att, spec in self.m_attributes:
      res = eval(spec, product)
      consistency = consistency and (res or not decl)

    if not consistency:
      raise ValueError(f"SPL configuration error self.m_name : {self.m_name}")

    return (consistency, decl)

  def _remove_subtree_from_product__(self, product):
    if(product[self.m_name]):
      product[self.m_name] = False
    for att, spec in self.m_attributes:
      product[att] = None
    for group in self.m_groups:
      group._remove_subtree_from_product__(product)

  def eval(self, product):
    tmp = self._eval__(product)
    return tmp[0] and tmp[1]

  def combine_product(self, default, update, res=None):
    if(res is None):
      res = {}
    val = update.get(self.m_name, default[self.m_name])
    res[self.m_name] = val
    if(val): # the subtree needs to be included in res
      for att, spec in self.m_attributes:
        res[att] = update.get(att, default[att])
      for group in self.m_groups:
        group.combine_product(default, update, res)
    return res

