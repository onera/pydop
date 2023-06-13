
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
This file contains the different classes for building boolean expressions over variables.
In particular, the class `_expbool__c` is an abstract super classes of all boolean classes and contains most functionalities of the boolean classes
"""

import itertools

from pydop.fm_result import decl_errors__c, reason_tree__c, eval_result__c
from pydop.fm_configuration import configuration__c
from pydop.utils import _empty__

################################################################################
# Boolean constraints
################################################################################

##########################################
# 1. main class (for all non leaf behavior)

class _expbool__c(object):
  __slots__ = ("m_content", "m_vars",)
  def __init__(self, content):
    self.m_content = tuple(_expbool__c._manage_parameter__(param) for param in content)
    self.m_vars = None

  def get_name(self): return self.__class__.__name__
  def __str__(self): return f"{self.get_name()}({', '.join(str(el) for el in self.m_content)})"

  ## constraint API

  def __call__(self, product, idx=None, expected=True):
    # print(f"{self.__class__.__name__}.__call__({product}, {idx}, {expected})")
    # results = tuple(_expbool__c._eval_generic__(el, product, i, self._get_expected__(el, i, expected)) for i, el in enumerate(self.m_content))
    results = tuple(el(product, i, self._get_expected__(el, i, expected)) for i, el in enumerate(self.m_content))
    values = tuple(el.value() for el in results)
    # print(f"  => values  = {values}")
    res = self._compute__(values)
    if(res == expected):
      reason = None
    else:
      reason = reason_tree__c(self.get_name(), idx)
      for i, el in enumerate(self.m_content):
        reason.add_reason_value_mismatch(el, results[i], self._get_expected__(el, i, expected))
      for r in results:
        reason.add_reason_sub(r)
    return eval_result__c(res, reason)
 
  @staticmethod
  def _manage_parameter__(param):
    if(isinstance(param, _expbool__c)):
      return param
    elif(isinstance(param, str)):
      return Var(param)
    else:
      return Lit(param)

  def _link__(self, path, mapping, errors):
    res = _expbool__c(tuple(map((lambda sub: sub._link__(path, mapping, errors)), self.m_content)))
    res.__class__ = self.__class__
    return res

  ## feature model API

  def check(self): return decl_errors__c()

  def link_constraint(self, c, strict=False):
    errors = decl_errors__c()
    if(strict):
      for v in (c.vars - self.vars): errors.add_unbound(v)
    else:
      c._vars_update(self.vars)
    return (c, errors)

  def link_configuration(self, conf):
    errors = decl_errors__c()
    for v in (set(conf.keys()) - self.vars): errors.add_unbound(v)
    return (conf, errors)

  def close_configuration(self, *confs):
    errors = decl_errors__c()
    conf = dict(itertools.chain(*map((lambda e: e.items()), confs)))
    return self.link_configuration(conf)

  ## free variables manipulations

  @property
  def vars(self):
    if(self.m_vars is None):
      self.m_vars = set()
      self._vars_update(self.m_vars)
    return self.m_vars

  def _vars_update(self, s):
    if(self.m_vars is None):
      for el in self.m_content:
        el._vars_update(s)
    else:
      s.update(self.m_vars)


##########################################
# 2. leafs

class Var(_expbool__c):
  """Class for variables (e.g., features and attributes)"""
  # overrides _expbool__c default tree behavior (Var is a leaf)
  __slots__ = ()
  def __init__(self, var):
    """Var(object) -> Var
The parameter is the id of the variable
    """
    self.m_content = var
  def __call__(self, product, idx=None, expected=True):
    global _empty__
    res = product.get(self.m_content, _empty__)
    if(res is _empty__):
      reason = reason_tree__c(self.get_name(), idx)
      reason.add_reason_value_none(self.m_content)
    else:
      reason = None
    return eval_result__c(res, reason)
  def __str__(self): return f"Var({self.m_content})"

  def _link__(self, path, resolver, errors):
    return Var(resolver.get_with_path(path, self.m_content, errors, self.m_content))

  def _vars_update(self, s):
    s.add(self.m_content)


class Lit(_expbool__c):
  """Class for literals (i.e., wraps python objects within a boolean expression)"""
  # overrides _expbool__c default tree behavior (Lit is a leaf)
  __slots__ = ()
  def __init__(self, var):
    """Lit(object) -> Lit
The parameter is the wrapped object
    """
    self.m_content = var
  def __call__(self, product, idx=None, expected=True):
    return eval_result__c(self.m_content, None)
  def __str__(self): return f"Lit({self.m_content})"

  def _link__(self, path, mapping, errors):
    return self

  def _vars_update(self, s): pass

##########################################
# 3. constraint over non-booleans

class Lt(_expbool__c):
  """Class for the < comparison"""
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (values[0] < values[1])
  def _get_expected__(self, el, idx, expected): return None
      
class Leq(_expbool__c):
  """Class for the <= comparison"""
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (values[0] <= values[1])
  def _get_expected__(self, el, idx, expected): return None

class Eq(_expbool__c):
  """Class for the == comparison"""
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (values[0] == values[1])
  def _get_expected__(self, el, idx, expected): return None

class Geq(_expbool__c):
  """Class for the >= comparison"""
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (values[0] >= values[1])
  def _get_expected__(self, el, idx, expected): return None

class Gt(_expbool__c):
  """Class for the > comparison"""
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    # print(f"Gt._compute__({values})")
    return (values[0] > values[1])
  def _get_expected__(self, el, idx, expected): return None

##########################################
# 4. boolean operators

class And(_expbool__c):
  """Class for the logical conjunction of booleans"""
  __slots__ = ()
  def __init__(self, *args):
    _expbool__c.__init__(self, args)
  def _compute__(self, values):
    return all(values)
  def _get_expected__(self, el, idx, expected):
    if(expected is True): return True
    else: return None

class Or(_expbool__c):
  """Class for the logical disjunction of booleans"""
  __slots__ = ()
  def __init__(self, *args):
    _expbool__c.__init__(self, args)
  def _compute__(self, values):
    return any(values)
  def _get_expected__(self, el, idx, expected):
    if(expected is not False): return None
    else: return False

class Not(_expbool__c):
  """Class for the logical negation of a boolean"""
  __slots__ = ()
  def __init__(self, arg):
    _expbool__c.__init__(self, (arg,))
  def _compute__(self, values):
    return not values[0]
  def _get_expected__(self, el, idx, expected):
    if(expected is True): return False
    elif(expected is False): return True
    else: return None

class Xor(_expbool__c):
  """Class for the logical alternative of booleans"""
  __slots__ = ()
  def __init__(self, *args):
    _expbool__c.__init__(self, args)
  def _compute__(self, values):
    res = False
    for element in values:
      if(element):
        if(res): return False
        else: res = True
    return res
  def _get_expected__(self, el, idx, expected):
    return None

class Conflict(_expbool__c):
  """Class for the logical NAND gate over multiple booleans"""
  __slots__ = ()
  def __init__(self, *args):
    _expbool__c.__init__(self, args)
  def _compute__(self, values):
    res = False
    for element in values:
      if(element):
        if(res): return False
        else: res = True
    return True
  def _get_expected__(self, el, idx, expected):
    return None

class Implies(_expbool__c):
  """Class for the logical implication of booleans"""
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return ((not values[0]) or values[1])
  def _get_expected__(self, el, idx, expected):
    return None

class Iff(_expbool__c):
  """Class for the logical equivalence of booleans (identical to Eq)"""
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (values[0] == values[1])
  def _get_expected__(self, el, idx, expected):
    return None

