
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

from pydop.fm_core import eval


import enum



################################################################################
# Boolean constraints
################################################################################


class _expbool__c(object): pass

class Lt(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    self.m_content = (left, right,)
  def __call__(self, product):
    return (eval(self.m_content[0], product) < eval(self.m_content[1], product))

class Eq(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    self.m_content = (left, right,)
  def __call__(self, product):
    return (eval(self.m_content[0], product) == eval(self.m_content[1], product))

class Leq(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    self.m_content = (left, right,)
  def __call__(self, product):
    return (eval(self.m_content[0], product) <= eval(self.m_content[1], product))

class And(_expbool__c):
  __slots__ = ()
  def __init__(self, *args):
    self.m_content = tuple(args)
  def __call__(self, product):
    for element in self.m_content:
      if(not eval(element, product)): return False
    return True

class Or(_expbool__c):
  __slots__ = ()
  def __init__(self, *args):
    self.m_content = tuple(args)
  def __call__(self, product):
    for element in self.m_content:
      if(eval(element, product)): return True
    return False

class Not(_expbool__c):
  __slots__ = ()
  def __init__(self, args):
    self.m_content = args
  def __call__(self, product):
    return not (eval(self.m_content, product))

class Xor(_expbool__c):
  __slots__ = ()
  def __init__(self, *args):
    self.m_content = tuple(args)
  def __call__(self, product):
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
  def __call__(self, product):
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
  def __call__(self, product):
    left = eval(self.m_content[0], product)
    right = eval(self.m_content[1], product)
    return ((not left) or (right))

class Iff(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    self.m_content = (left, right,)
  def __call__(self, product):
    left = eval(self.m_content[0], product)
    right = eval(self.m_content[1], product)
    return (left == right)



################################################################################
# Attribute Specification
################################################################################

_NoneType = type(None)

def _is_valid_bound(v):
  return isinstance(v, (int, float, _NoneType))

def _add_domain_spec(l, spec):
    if((len(spec) == 2) and _is_valid_bound(spec[0]) and _is_valid_bound(spec[1])):
      spec = (spec,)

    for arg in spec:
      if(not isinstance(arg, (float, int))):
        if((not isinstance(arg, tuple)) or (len(arg) != 2) or (not (_is_valid_bound(arg[0]) and _is_valid_bound(arg[1])))):
          raise ValueError(f"ERROR: expected domain specification (found {arg})")
        else:
          l.append(arg)
      else:
        l.append((arg, arg))

def _check_interval(interval, value):
  if((interval[0] is not None) and (value < interval[0])):
    return False
  if((interval[1] is not None) and (value > interval[1])):
    return False
  return True

def _check_domain(domain, value):
  if(domain):
    for i in domain:
      if(_check_interval(i, value)): return True
    return False
  else:
    return True



class _fdattribute_c(object): pass


class Class(_fdattribute_c):
  __slots__ = ("m_class")
  def __init__(self, domain):
    self.m_class = domain
  def __call__(self, value):
    return isinstance(value, self.m_class)


class Bool(Class):
  __slots__ = ()
  def __init__(self): Class.__init__(self, bool)


class String(Class):
  __slots__ = ()
  def __init__(self):  Class.__init__(self, str)


class Enum(Class):
  __slots__ = ()
  def __init__(self, domain):
    if(issubclass(domain, enum.Enum)):
       Class.__init__(self, domain)
    else:
      raise ValueError(f"ERROR: expected an enum class (found {domain})")


class Int(Class):
  __slots__ = ("m_domain",)
  def __init__(self, *args):
    Class.__init__(self, int)
    self.m_domain = []
    _add_domain_spec(self.m_domain, args)

  def __call__(self, value):
    if(Class.__call__(self, value)):
      return _check_domain(self.m_domain, value)
    else:
      return False


class Float(Class):
  __slots__ = ("m_domain",)
  def __init__(self, *args):
    Class.__init__(self, float)
    self.m_domain = []
    _add_domain_spec(self.m_domain, args)

  def __call__(self, value):
    if(Class.__call__(self, value)):
      return _check_domain(self.m_domain, value)
    else:
      return False



################################################################################
# Feature Groups
################################################################################

class _fdgroup__c(object):
  __slots__ = ("m_content",)
  def _eval__(self, product):
    res = self._start__()
    for element in self.m_content:
      val = self.get(element, product)
      res = self._combine__(res, val)
    return self._conclude__(res)
  def _ensure_false__(self, name_parent, product):
    for element in self.m_content:
      if(self.get_shallow(element)):
        raise ValueError(f"ERROR: the feature {self.get_name(element)} is activated while the parent feature {name_parent} is not")

  @staticmethod
  def get(element, product):
    if(isinstance(element, FD)): return element._eval__(product)
    elif(isinstance(element, str)): return product[element]
    else: return element
  @staticmethod
  def get_shallow(element, product):
    if(isinstance(element, FD)): return element._eval_shallow__(product)
    elif(isinstance(element, str)): return product[element]
    else: return element
  @staticmethod
  def get_name(element):
    if(isinstance(element, FD)): return element.get_name()
    elif(isinstance(element, str)): return element
    else: return element

  def _remove_subtree_from_product__(self, product):
    for element in self.m_content:
      element._remove_subtree_from_product__(product)

  def combine_product(self, default, update, res):
    for element in self.m_content:
      element.combine_product(default, update, res)


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



################################################################################
# Feature diagrams
################################################################################

class FD(object):
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
      if(isinstance(variable_name, str) and isinstance(spec, _fdattribute_c)):
        self.m_attributes.append((variable_name, spec,))
      elif(not isinstance(variable_name, str)):
        raise Exception(f"FD attribute name must be a str (type \"{variable_name.__class__.__name__}\" found)")
      else:
        raise Exception(f"FD attribute specification only accept expbool or str (type \"{spec.__class__.__name__}\" found)")


  def get_name(self):
    return self.m_name

  def _eval_shallow__(self, product):
    return product[self.m_name]

  def _eval__(self, product):
    decl = self._eval_shallow__(product)

    # 1. check consistency of subtree
    for i, group in enumerate(self.m_groups):
        tmp = group._eval__(product)
        if(decl):
          if(not tmp):
            raise ValueError(f"ERROR: group {i} of feature {self.get_name()} should be True (due to {self.get_name()} being True)")
        else:
          group._ensure_false__(self.get_name(), product)

    # 2. check consistency of cross tree constraints
    if(decl):
      ctc = self.m_ctcs(product)
      if(not ctc):
        raise ValueError(f"ERROR: cross tree constraints of feature {self.get_name()} should be valid (due to {self.get_name()} being activated)")

    if(decl):
      for att, spec in self.m_attributes:
        tmp = spec(product[att])
        if(not tmp):
          raise ValueError(f"ERROR: the value of {att} (in feature {self.get_name()}) does not validate its specification")
    else:
      for att, spec in self.m_attributes:
        tmp = (att not in product)
        if(not tmp):
          raise ValueError(f"ERROR: the attribute {att} (in feature {self.get_name()}) should not be in the product (due to {self.get_name()} not being activated)")


    return decl


  # def _eval__(self, product):
  #   decl = product[self.m_name]
  #   ctc = self.m_ctcs(product)
  #   # print(f"self.m_name = {self.m_name}, ctc = {ctc}")

  #   consistency = True
  #   res = True
  #   for i, group in enumerate(self.m_groups):
  #     tmp = group._eval__(product)
  #     consistency = consistency and tmp[0]
  #     res = res and tmp[1]
  #     for n in group._get_subname__():
  #       tmp = (decl or (not product[n]))
  #       consistency = consistency and tmp
  #       if(not tmp):
  #         raise ValueError(f"ERROR: the feature {n} is activated while the parent feature {self.m_name} is not")

  #   consistency = consistency and (res == decl) and (ctc or not decl)

  #   if(decl):
  #     for att, spec in self.m_attributes:
  #       tmp = spec(product[att])
  #       consistency = consistency and tmp
  #   else:
  #     for att, spec in self.m_attributes:
  #       tmp = (att not in product)
  #       consistency = consistency and tmp


  #   if not consistency:
  #     raise ValueError(f"SPL configuration error self.m_name : {self.m_name}")

  #   return (consistency, decl)

  def _remove_subtree_from_product__(self, product):
    if(product[self.m_name]):
      product[self.m_name] = False
    for att, spec in self.m_attributes:
      # product[att] = None
      product.pop(att)
    for group in self.m_groups:
      group._remove_subtree_from_product__(product)

  def __call__(self, product):
    tmp = self._eval__(product)
    return tmp
    # return tmp[0] and tmp[1]

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

