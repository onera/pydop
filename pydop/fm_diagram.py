
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


import enum


class _empty_c__(object):
  __slots__ = ()
  def __str__(self): return "_empty__"
  def __repr__(self): return "_empty__"

_empty__ = _empty_c__()




################################################################################
# Predicate evaluation and error reporting
################################################################################

## change the API to have the reasons in the paramter of the function, not in the output

class _unbound__c(object):
  __slots__ = ("m_name", "m_path",)
  def __init__(self, name, path=None):
    self.m_name = name
    self.m_path = path
  def __str__(self):
    if(self.m_path is None):
      return f"ERROR: variable \"{self.m_name}\" not declared"
    else:
      return f"ERROR: variable \"{self.m_name}\" not declared in path \"{_path_to_str__(self.m_path)}\""

class _ambiguous__c(object):
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


class _decl_errors__c(object):
  __slots__ = ("m_unbounds", "m_ambiguities",)
  def __init__(self):
    self.m_unbounds = []
    self.m_ambiguities = []

  def add_unbound(self, name, path=None):
    self.m_unbounds.append(_unbound__c(name, path))
  def add_ambiguous(self, name, path, paths):
    self.m_unbounds.append(_ambiguous__c(name, path, paths))

  @property
  def unbounds(self): return self.m_unbounds
  @property
  def ambiguities(self): return self.m_ambiguities

  def has_unbounds(self): return bool(self.m_unbounds)
  def has_ambiguities(self): return bool(self.m_ambiguities)

  def __bool__(self):
    return bool(self.m_unbounds) or bool(self.m_ambiguities)
  def __str__(self):
    return "\n".join(str(el) for l in (self.m_unbounds, self.m_ambiguities) for el in l)


###############################

class _reason_tree__c(object):
  __slots__ = (
    "m_name",   # The identifier of the node where the reasons where found
    "m_content" # The list of reasons
  )
  def __init__(self, name, idx, content):
    self.m_name = f"[{idx}]" if(name is None) else name
    self.m_content = content 

  def _tostring__(self, indent):
    if(isinstance(self.m_content, (tuple, list, set))):
      res = f"{indent}{self.m_name}: (\n"
      indent_more = f"{indent} "
      for r in self.m_content:
        if(isinstance(r, _reason_tree__c)):
          res += r._tostring__(indent_more)
        else:
          res += f"{indent_more}{r}\n"
      res += f"{indent})\n"
      return res
    else:
      return f"{indent}{self.m_name}: {self.m_content}\n"

  def __str__(self): return self._tostring__("")


class _eval_result__c(object):
  __slots__ = ("m_value", "m_reason", "m_snodes")
  def __init__(self, value=None, reason=None):
    self.m_value  = value   # the result of the evaluation
    self.m_reason = reason  # reason for which a False value cannot be fixed

  def value(self): return self.m_value
  # def __bool__(self): return (self.m_reason is None)
  def __bool__(self): return self.value()

class _eval_result_fd__c(_eval_result__c):
  __slots__ = ("m_nvalue", "m_snodes")
  def __init__(self, value=None, reason=None, nvalue=None, snodes=None):
    _eval_result__c.__init__(self, value, reason)
    self.m_nvalue = nvalue # the value of the subnode, used for propagation within a FD
    self.m_snodes = snodes  # the list of sub nodes that are True


def _get_value__(res):
  if(isinstance(res, _eval_result__c)):
    return res.m_value
  else:
    return res


################################################################################
# Paths and partial paths manipulation
################################################################################

def _path_includes__(p, p_included):
  # print(f"CHECKING INCLUSION: {p} include {p_included}")
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
      # print("  => False")
      return False
  # print("  => True")
  return True

def _path_to_str__(path): return ("None" if(path is None) else "/".join(path))
def _path_from_str__(s): return s.split('/')


def _path_check_exists__(path_s, mapping, errors, additional_path=()):
  path = _path_from_str__(path_s)
  name = path[-1]
  path = (additional_path + tuple(path[0:-1]))
  decls = mapping.get(name)
  if(decls is None):
    errors.add_unbound(name)
  else:
    refs = []
    length = 0
    for el in decls:
      # if(_path_includes__(el[1], path + (path,))):
      if(_path_includes__(el[1], path)):
          refs.append(el)
          length += 1
    if(length == 0):
      errors.add_unbound(path_s, additional_path)
    elif(length > 1):
      # print(f"AMBIGIUTY: {path_s} => {length} | {refs}")
      errors.add_ambiguous(path_s, None, tuple(el[1] for el in refs))
    else:
      path = refs[0][0]
  return path



################################################################################
# Boolean constraints
################################################################################


class _expbool__c(object):
  __slots__ = ("m_content","m_vars")
  def __init__(self, content):
    self.m_content = content
    # self.m_vars = tuple(el for sub in content for el in (
    #   sub.m_vars if(isinstance(sub, _expbool__c)) else ((sub,) if(isinstance(sub, str)) else ())))

  def get_name(self): return self.__class__.__name__

  def __call__(self, product, idx=None, expected=True):
    # print(f"{self.__class__.__name__}.__call__({product}, {idx}, {expected})")
    # results = tuple(my_eval(el, product, i, self._get_expected__(el, i, expected)) for i, el in enumerate(self.m_content))
    results = tuple(_expbool__c._eval_generic__(el, product, i, self._get_expected__(el, i, expected)) for i, el in enumerate(self.m_content))
    values = tuple(_get_value__(el) for el in results)
    # print(f"  => values  = {values}")
    res = self._compute__(values)
    if(res == expected):
      reason = None
    else:
      tmp1 = zip(self.m_content, values)
      message = " vs ".join(f"[{el[0]} = {el[1]}]" for el in tmp1)
      tmp2 = filter((lambda x: isinstance(x, _eval_result__c) and (x.m_reason is not None)), results)
      sub_reasons = tuple(el.m_reason for el in tmp2)
      reason = self._get_reason__(idx, (message,) + sub_reasons) if(sub_reasons) else self._get_reason__(idx, message)
    return _eval_result__c(res, reason)
 
  def __str__(self): return f"{self.get_name()}({', '.join(str(el) for el in self.m_content)})"

  @staticmethod
  def _eval_generic__(el, product, i, expected):
    if(isinstance(el, _expbool__c)):
      return el(product, i, expected)
    else:
      return product.get(el, el)

  def _get_reason__(self, idx, content): return _reason_tree__c(self.get_name(), idx, content)
  def _check_declarations__(self, path, mapping, errors):
    self.m_content = tuple(map((lambda sub: _expbool__c._check_declarations_sub__(sub, path, mapping, errors)), self.m_content))
    return self

  @staticmethod
  def _check_declarations_sub__(sub, path, mapping, errors):
    if(isinstance(sub, _expbool__c)):
      return sub._check_declarations__(path, mapping, errors)
    elif(isinstance(sub, str)):
      return _path_check_exists__(sub, mapping, errors, path)
    else:
      return sub


class Lt(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (values[0] < values[1])
  def _get_expected__(self, el, idx, expected): return None
      
class Leq(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (values[0] <= values[1])
  def _get_expected__(self, el, idx, expected): return None

class Eq(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (values[0] == values[1])
  def _get_expected__(self, el, idx, expected): return None

class Geq(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (values[0] >= values[1])
  def _get_expected__(self, el, idx, expected): return None

class Gt(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (values[0] > values[1])
  def _get_expected__(self, el, idx, expected): return None


class And(_expbool__c):
  __slots__ = ()
  def __init__(self, *args):
    _expbool__c.__init__(self, args)
  def _compute__(self, values):
    return all(values)
  def _get_expected__(self, el, idx, expected):
    if(expected is True): return True
    else: return None

class Or(_expbool__c):
  __slots__ = ()
  def __init__(self, *args):
    _expbool__c.__init__(self, args)
  def _compute__(self, values):
    return any(values)
  def _get_expected__(self, el, idx, expected):
    if(expected is not False): return None
    else: return False

class Not(_expbool__c):
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
  __slots__ = ()
  def __init__(self, *args):
    _expbool__c.__init__(self, args)
  def _compute__(self, values):
    res = False
    for element in values:
      if(_get_value__(element)):
        if(res): return False
        else: res = True
    return res
  def _get_expected__(self, el, idx, expected):
    return None

class Conflict(_expbool__c):
  __slots__ = ()
  def __init__(self, *args):
    _expbool__c.__init__(self, args)
  def _compute__(self, values):
    res = False
    for element in values:
      if(_get_value__(element)):
        if(res): return False
        else: res = True
    return True
  def _get_expected__(self, el, idx, expected):
    return None


class Implies(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return ((not _get_value__(values[0])) or _get_value__(values[1]))
  def _get_expected__(self, el, idx, expected):
    return None

class Iff(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (_get_value__(values[0]) == _get_value__(values[1]))
  def _get_expected__(self, el, idx, expected):
    return None



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
        l.append((arg, arg+1))

def _check_interval(interval, value):
  if((interval[0] is not None) and (value < interval[0])):
    return False
  if((interval[1] is not None) and (value >= interval[1])):
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

  def description(self):
    return f'{self.m_domain[0][0]} <= x < {self.m_domain[0][1]}'

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

class List(Class):
  __slots__ = ("m_size", "m_kind",)
  def __init__(self, size=None, spec=None):
    Class.__init__(self, (list, tuple))
    self.m_size = []
    if(size is not None):
      _add_domain_spec(self.m_size, size)
    self.m_kind = spec

  def __call__(self, value):
    if(Class.__call__(self, value)):
      # print(f"_check_domain({self.m_size}, {len(value)}) = {_check_domain(self.m_size, len(value))}")
      if(_check_domain(self.m_size, len(value))):
        if(self.m_kind is None):
          return True
        else:
          for el in value:
            if(not self.m_kind(el)):
              return False
          return True
    return False



################################################################################
# Feature Diagrams, Generalized as Groups
################################################################################

_default_product_normalization = None

def set_default_product_normalization(f):
  global _default_product_normalization
  _default_product_normalization = f


class _fdgroup__c(object):
  __slots__ = ("m_norm", "m_name", "m_content", "m_ctcs", "m_attributes", "m_lookup", "m_path", "m_errors")

  ##########################################
  # constructor API

  def __init__(self, *args, **kwargs):
  # def __init__(self, name, content, ctcs, attributes):
    global _default_product_normalization
    name, content, ctcs, attributes = _fdgroup__c._manage_constructor_args__(*args, **kwargs)
    self.m_norm = _default_product_normalization
    self.m_name = name
    self.m_content = content
    self.m_ctcs = ctcs
    self.m_attributes = attributes
    self.clean()

  def set_product_normalization(self, f):
    self.m_norm = f

  @staticmethod
  def _manage_constructor_args__(*args, **kwargs):
    # print(f"_manage_constructor_args__({args}, {kwargs})")
    if(bool(args) and isinstance(args[0], str)):
      name = args[0]
      args = args[1:]
    else:
      name = None
    attributes = tuple((key, spec) for key, spec in kwargs.items())
    content = []
    ctcs = []
    for el in args:
      if(isinstance(el, _fdgroup__c)):
        content.append(el)
      elif(isinstance(el, _expbool__c)):
        ctcs.append(el)
      else:
        raise Exception(f"ERROR: unexpected FD subtree (found type \"{el.__class__.__name__}\")")
    return name, content, ctcs, attributes

  ##########################################
  # base API

  @property
  def name(self):
    return self.m_name
  @property
  def path(self):
    return self.m_path
  @property
  def children(self):
    return self.m_content
  @property
  def cross_tree_constraints(self):
    return self.m_ctcs
  @property
  def attributes(self):
    return self.m_attributes
  def has_attributes(self):
    return len(self.attributes) != 0
  def is_leaf(self):
    return len(self.children) == 0

  ##########################################
  # generate_lookup API

  def clean(self):
    self.m_lookup = None
    self.m_path = None
    self.m_errors = None

  def check(self):
    return self.generate_lookup()

  def generate_lookup(self):
    if(self.m_lookup is None):
      self.m_errors = _decl_errors__c()
      self.m_lookup = {}
      self._generate_lookup__rec([], 0, self.m_lookup, self.m_errors)
    return self.m_errors

  def nf_constraint(self, c):
    errors = _decl_errors__c()
    if(not isinstance(c, _expbool__c)):
      c = And(c)
    res = c._check_declarations__(self.m_path, self.m_lookup, errors)
    return (res, errors)

  def nf_product(self, *args): # TODO: need to add inconsistency checking (with error list, like always, filled by _infer_sv__)
    # print(f"nf_product({args})")
    errors = _decl_errors__c()
    is_true_d = {}
    for i, p in enumerate(args):
      for k, v in self._normalize_product__(p, errors).items():
        is_true_d[k] = (v, i)
    self._make_product_rec_1(is_true_d)
    # print("=====================================")
    # print("is_true_d")
    # print(is_true_d)
    # print("=====================================")
    res = {}
    v_local = is_true_d.get(self, _empty__)
    if(v_local is _empty__):
      self._make_product_rec_2(False, is_true_d, res)
    else:
      self._make_product_rec_2(v_local[0], is_true_d, res)
    # print(f" => {res}")
    return (res, errors)


  def _generate_lookup__rec(self, path_to_self, idx, res, errors):
    # print(f"_generate_lookup__rec({self.m_name}, {idx}, {path_to_self}, {res}, {errors})")
    # 1. if local names, add it to the table, and check no duplicates
    path_to_self.append(str(idx) if(self.m_name is None) else self.m_name)
    local_path = tuple(path_to_self)
    self.m_path = local_path
    if(self.m_name is not None):
      _fdgroup__c._check_duplicate__(self, self.m_name, local_path, res, errors)
    # 2. add subs
    for i, sub in enumerate(self.m_content):
      sub._generate_lookup__rec(path_to_self, i, res, errors)
    # 3. add attributes
    for att_def in self.m_attributes:
      _fdgroup__c._check_duplicate__(att_def, att_def[0], local_path, res, errors)
    # 4. check ctcs
    # print(self.m_ctcs)
    self.m_ctcs = tuple(ctc._check_declarations__(local_path, res, errors) for ctc in self.m_ctcs)
    path_to_self.pop()
    # 5. reset path_to_self

  @staticmethod
  def _check_duplicate__(el, name, path, res, errors):
    # print(f"_check_duplicate__({el}, {name}, {path}, {res})")
    tmp = res.get(name)
    if(tmp is not None):
      others = []
      for el in tmp:
        if(_path_includes__(path, el[1])):
          others.append(el[1])
      if(bool(others)):
        errors.add_ambiguous(name, path, others)
        # raise Exception(f"ERROR: ambiguous declaration of feature \"{_path_to_str__(path)}\" (found \"{_path_to_str__(other)}\")")
      tmp.append( (el, (path),) )
    else:
      res[name] = [(el, (path),)]

  ##########################################
  # call API

  def __call__(self, product, expected=True):
    return self._eval_generic__(product, _fdgroup__c._f_get_deep__, expected)

  def _eval_generic__(self, product, f_get, expected=True):
    # print(f"_eval_generic__([{self.__class__.__name__}]{self.m_path}, {product}, {f_get}, {expected})")
    # print(f"_eval_generic__([{self.__class__.__name__}]{_path_to_str__(self.m_path)})")
    # print(f"_eval_generic__({_path_to_str__(self.m_path)})")
    expected_att = (_empty__ if(expected is False) else expected)

    results_content = tuple(f_get(el, product, self._get_expected__(el, i, expected)) for i, el in enumerate(self.m_content))
    # print(f" => computed results_content: {results_content}")
    # print(f"   reasons = {', '.join(str(el.m_reason) for el in results_content)}")
    result_att = tuple(self._manage_attribute__(el, product, i, self._get_expected__(el, i, expected)) for i, el in enumerate(self.m_attributes))
    # print(f" => computed result_att: {result_att}")
    # print(f"   reasons = {', '.join(str(el.m_reason) for el in result_att)}")
    result_ctc = tuple(_expbool__c._eval_generic__(el, product, i, self._get_expected__(el, i, expected)) for i, el in enumerate(self.m_ctcs))
    # print(f" => computed result_ctc: {result_ctc}")
    # print(f"   reasons = {', '.join(str(el.m_reason) for el in result_ctc)}")


    nvalue_subs  = tuple(itertools.chain((el.m_nvalue for el in results_content), (el.m_value for resu in (result_att, result_ctc) for el in resu)))
    # nvalue_local = product.get(self, _empty__)
    nvalue_local = None
    # print(f"  => compute {nvalue_subs}, {nvalue_local}")
    nvalue_sub = self._compute__(nvalue_subs, nvalue_local)
    # print(f"  => nvalue_sub = {nvalue_sub}")
    value_subs = all(el.m_value for el in results_content)
    snodes = tuple(v for el in results_content for v in el.m_snodes)

    # print(f" => computed res: {res}")

    # check consistency with name
    reason = None
    if(self.m_name is not None):
      nvalue_local = product.get(self, _empty__)
      if(nvalue_local is _empty__):
        reason = f"Feature {_path_to_str__(self.m_path)} has no value in the input product"
      elif((not nvalue_local) and snodes):
        tmp = ', '.join(f"\"{_path_to_str__(el.m_path)}\"" for el in snodes)
        reason = f"Feature {_path_to_str__(self.m_path)} should be set to True due to validated subfeatures (found: {tmp})"
      elif(nvalue_local and (not nvalue_sub)):
        reason = f"Feature {_path_to_str__(self.m_path)} is selected while its content is False"
      elif(nvalue_local):
        snodes = snodes + (self,)
    else:
      nvalue_local = nvalue_sub

    value = value_subs and (reason is None)
    # print(f"  => nvalue_local = {nvalue_local}")
    # print(f"  => value = {value}")

    reasons = None
    if((nvalue_local != expected) or (not value)):
      reasons = []
      if(reason is not None): reasons.append(reason)
      if((nvalue_local != expected)):
        if(expected is None):
          reasons.append(f"Feature {_path_to_str__(self.m_path)} has value {nvalue_local}")
        else:
          reasons.append(f"Feature {_path_to_str__(self.m_path)} has value {nvalue_local} (expected {expected})")
      for el in (el for resu in (results_content, result_att, result_ctc) for el in resu):
        if(el.m_reason is not None): reasons.append(el.m_reason)
      reasons = _reason_tree__c(self.__class__.__name__, self.m_path, reasons)

    return _eval_result_fd__c(value, reasons, nvalue_local, snodes)

  def _f_get_shallow__(self, product, expected=True):
    if(self.m_name is None):
      return self._eval_generic__(product, _fdgroup__c._f_get_shallow__, expected)
    else:
      nvalue = product.get(self, _empty__)
      if(v is _empty__):
        value = False
        nvalue = False
        reasons = [f"Feature {_path_to_str__(self.m_path)} has no value in the input product"]
        return _eval_result_fd__c(value, _reason_tree__c(self.__class__.__name__, self.m_path, reasons), nvalue, ())
      else:
        return _eval_result_fd__c(True, None, nvalue, ())

  def _f_get_deep__(self, product, expected=True):
    return self._eval_generic__(product, _fdgroup__c._f_get_deep__, expected)

  def _manage_attribute__(self, att, product, idx, expected):
    name, spec = att
    value = product.get(att, _empty__)
    reason = None
    if(value is _empty__):
      if(expected):
        return _eval_result__c(False, _reason_tree__c(name, idx, "Attribute has no value in the input product"))
      else:
        return _eval_result__c(False)
    else:
      res = spec(value)
      if(expected == res):
        return _eval_result__c(res)
      else:
        return _eval_result__c(res, _reason_tree__c(name, idx, f"Attribute has erroneous value \"{value}\" => specification returns {res}"))

  ##########################################
  # product inner API

  def _normalize_product__(self, product, errors):
    res = {}
    if(self.m_norm is not None):
      product = self.m_norm(self, product)
    for key, val in product.items():
      if(isinstance(key, str)):
        res[_path_check_exists__(key, self.m_lookup, errors)] = val
      else:
        res[key] = val
    return res

  def _make_product_rec_1(self, is_true_d):
    idx, v_local, v_subs = self._infer_sv__(is_true_d)
    self._make_product_update__(is_true_d, idx, v_local, v_subs)
    for sub in self.m_content:
      sub._make_product_rec_1(is_true_d)
    idx, v_local, v_subs = self._infer_sv__(is_true_d)
    self._make_product_update__(is_true_d, idx, v_local, v_subs)

  def _make_product_update__(self, is_true_d, idx, v_local, v_subs):
    if(v_local is not _empty__):
      is_true_d[self] = (v_local, idx)
    for sub, v_sub in zip(self.m_content, v_subs):
      if(v_sub is not _empty__):
        is_true_d[sub] = (v_sub, idx)

  def _make_product_rec_2(self, v_local, is_true_d, res):
    # _, _, v_subs = self._make_product_extract__(is_true_d)
    # print(f"  {self} :subs[0] => {v_subs}")
    _, _, v_subs = self._infer_sv__(is_true_d)
    # print(f"  {self} :subs[1] => {v_subs}")
    res[self] = v_local
    for sub, v_sub in zip(self.m_content, v_subs):
      if(v_sub is _empty__):
        sub._make_product_rec_2(False, is_true_d, res)
      else:
        sub._make_product_rec_2(v_sub, is_true_d, res)
    # if feature selected, need to include the attribute 
    if(v_local):
      for att_def in self.m_attributes:
        v = is_true_d.get(att_def, _empty__)
        if(v is not _empty__):
          res[att_def] = v[0]

  @staticmethod
  def _make_product_extract_utils__(is_true_d, domain, expected=True):
    idx = -1
    if(expected is None):
      value = _empty__
      def f(val):
        nonlocal idx
        nonlocal value
        if(val is _empty__): 
          return val
        else:
          if(val[1] > idx):
            idx = val[1]
            value = val[0]
          return val[0]
      for sub in domain:
        f(is_true_d.get(sub, _empty__))
      return idx, value
    else:      
      def f(val):
        nonlocal idx
        if(val is _empty__): 
          return val
        else:
          if((val[0] == expected) and (val[1] > idx)):
            idx = val[1]
          return val[0]
      v_subs = tuple(f(is_true_d.get(sub, _empty__)) for sub in domain)
      return idx, v_subs



  ##########################################
  # print for error report

  def __str__(self):
    if(self.m_path is None):
      return object.__str__(self)
    else:
      return _path_to_str__(self.m_path)

  def __repr__(self): return str(self)
  




class FDAnd(_fdgroup__c):
  def __init__(self, *args, **kwargs):
    _fdgroup__c.__init__(self, *args, **kwargs)
  def _compute__(self, values, nvalue):
    return all(values)
  def _get_expected__(self, el, i, expected):
    return (True if(expected) else None)
  def _infer_sv__(self, is_true_d):
    idx, value = self._make_product_extract_utils__(is_true_d, itertools.chain((self,), self.m_content), expected=None)
    def get_default(el):
      val = is_true_d.get(el, _empty__)
      if((val is _empty__) or (val[1] < idx)):
        return value
      else:
        return val[0]
    v_local = get_default(self)
    return idx, v_local, tuple(get_default(sub) for sub in self.m_content)


class FDAny(_fdgroup__c):
  def __init__(self, *args, **kwargs):
    _fdgroup__c.__init__(self, *args, **kwargs)
  def _compute__(self, values, nvalue):
    return True
  def _get_expected__(self, el, i, expected):
    return None
  def _infer_sv__(self, is_true_d):
    # tuple((is_true_d.get(sub, (_empty__, -1))[0]) for sub in self.m_content)
    idx_subs, v_subs = self._make_product_extract_utils__(is_true_d, self.m_content)
    v_local, idx_local = is_true_d.get(self, (False, -1))
    if(idx_subs > idx_local):
      idx_local = idx_subs
      v_local = True
    return idx_local, v_local, v_subs


class FDOr(_fdgroup__c):
  def __init__(self, *args, **kwargs):
    _fdgroup__c.__init__(self, *args, **kwargs)
  def _compute__(self, values, nvalue):
    return any(values)
  def _get_expected__(self, el, i, expected):
    return (False if(not expected) else None)
  def _infer_sv__(self, is_true_d):
    # tuple((is_true_d.get(sub, (_empty__, -1))[0]) for sub in self.m_content)
    idx_subs, v_subs = self._make_product_extract_utils__(is_true_d, self.m_content)
    v_local, idx_local = is_true_d.get(self, (False, -1))
    if(idx_subs > idx_local):
      idx_local = idx_subs
      v_local = True
    return idx_local, v_local, v_subs

class FDXor(_fdgroup__c):
  def __init__(self, *args, **kwargs):
    _fdgroup__c.__init__(self, *args, **kwargs)
  def _compute__(self, values, nvalue):
    res = False
    for element in values:
      if(_get_value__(element)):
        if(res): return False
        else: res = True
    return res
  def _get_expected__(self, el, i, expected):
    return None
  def _infer_sv__(self, is_true_d):
    idx_subs, v_subs = self._make_product_extract_utils__(is_true_d, self.m_content)
    v_local, idx_local = is_true_d.get(self, (False, -1))
    if(idx_subs > idx_local):
      idx_local = idx_subs
      v_local = True
    if(idx_subs > -1):
      v_subs = tuple((is_true_d.get(sub, (False, -1)) == (True, idx_subs)) for sub in self.m_content)
    return idx_local, v_local, v_subs


class FD(FDAnd): pass

