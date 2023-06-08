
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

from pydop.fm_result import decl_errors__c, reason_tree__c, eval_result__c
from pydop.fm_constraint import _expbool__c, Var, Lit
from pydop.fm_configuration import configuration__c

from pydop.utils import _empty__, _path_from_str__


def _manage_parameter__(param):
  if(isinstance(param, str)):
    return Var(param)
  elif(isinstance(param, bool)):
    return Lit(param)
  else:
    return param




################################################################################
# path lookup class
################################################################################

class _lookup__c(object):
  __slots__ = ("m_content")
  def __init__(self):
    self.m_content = {}

  def insert(self, obj, path, errors):
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

  def get(self, path, errors, default=None):
    name = path[-1]
    decls = self.m_content.get(name)
    if(decls is None):
      errors.add_unbound(name)
    else:
      refs = tuple(filter((lambda data: _lookup__c._path_includes__(data[1], path)), decls))
      length = len(refs)
      if(length == 0):
        errors.add_unbound(name, path[:-1])
      elif(length > 1):
        errors.add_ambiguous(name, path[:-1], tuple(data[1] for data in refs))
      else:
        return refs[0][0]
    return default

  def get_with_path(self, path, suffix, errors, default=None):
    path = path + _path_from_str__(suffix)
    return self.get(path, errors, default)

  def resolve(self, key, errors, default=None):
    try:
      key_path = _path_from_str__(key)
      return self.get(key_path, errors, default)
    except ValueError:
      return default


  @staticmethod
  def _path_includes__(p, p_included):
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
        # print("  => False")
        return False
    # print("  => True")
    return True


################################################################################
# feature model evaluation result
################################################################################

class _eval_result_fd__c(eval_result__c):
  __slots__ = ("m_nvalue", "m_snodes")
  def __init__(self, value, reason, nvalue, snodes):
    eval_result__c.__init__(self, value, reason)
    self.m_nvalue = nvalue  # the value of the current feature, used for propagation within a FD
    self.m_snodes = snodes  # the list of sub nodes that are True

  def __bool__(self): return (self.value() and self.m_nvalue)


################################################################################
# Attribute Specification
################################################################################

##########################################
# 1. domains

# domains are either a single interval or a list of intervals
# an interval is a pair of integer/float/None values (None state infinite bound)
# e.g., (None, None) is a domain, as well as [(None, -1), (3, 5), (5, None)]

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

##########################################
# 2. attribute specifications

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


##########################################
# 1. core implementation

class _fd__c(object):
  __slots__ = (
    "m_norm",       # the product normalization function
    "m_name",       # the optional name of the feature (anonym nodes are possible)
    "m_content",    # the childrens of the current feature
    "m_ctcs",       # the cross-tree constraints at this feature level
    "m_attributes", # the attribute of the feature
    # the following fields are generated only at the root feature of a FD
    "m_lookup",     # mapping {name: [(feature_obj, path)]}: the keys are all the feature/attributes names in the current tree, and the list are all the elements having that name, with their relative path (in tuple format)
    "m_dom",        # mapping {feature_obj -> path}: lists all the features/attributes in the current, and give their path (in string format)
    # the following field is only used at the root feature of a FD during its evaluation
    "m_errors"      # a reason_tree__c object listing all the errors encountered during the evaluation of the FD
  )

  ##########################################
  # constructor API

  def __init__(self, *args, **kwargs):
  # def __init__(self, name, content, ctcs, attributes):
    global _default_product_normalization
    name, content, ctcs, attributes = _fd__c._manage_constructor_args__(*args, **kwargs)
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
      if(isinstance(el, _fd__c)):
        content.append(el)
      # elif(isinstance(el, _expbool__c)):
        # ctcs.append(el)
      else:
        ctcs.append(_manage_parameter__(el))
        # raise Exception(f"ERROR: unexpected FD subtree (found type \"{el.__class__.__name__}\")")
    return name, content, ctcs, attributes

  ##########################################
  # base API

  @property
  def name(self):
    return self.m_name
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
    self.m_dom    = None
    self.m_errors = None

  def check(self):
    return self.generate_lookup()

  def generate_lookup(self):
    if(self.m_lookup is None):
      self.m_errors = decl_errors__c()
      self.m_lookup = _lookup__c()
      self.m_dom    = {}
      self._generate_lookup_rec__([], 0, self.m_lookup, self.m_dom, self.m_errors)
    return self.m_errors

  def link_constraint(self, c):
    if(self.m_lookup is None):
      raise ValueError(f"ERROR: a non-root feature cannot link a constraint (detected feature \"{self}\").\nDid you forget to call \"generate_lookup\"?")
    errors = decl_errors__c()
    c = _expbool__c._manage_parameter__(c)
    res = c._link__(self.m_dom[self], self.m_lookup, errors)
    return (res, errors)

  def link_configuration(self, conf):
    if(self.m_lookup is None):
      raise ValueError(f"ERROR: a non-root feature cannot link a configuration (detected feature \"{self}\").\nDid you forget to call \"generate_lookup\"?")
    errors = decl_errors__c()
    res = self._link_configuration__(conf, errors)
    return (res, errors)

  def close_configuration(self, *confs):
    if(self.m_lookup is None):
      raise ValueError(f"ERROR: a non-root feature cannot close a configuration (detected feature \"{self}\").\nDid you forget to call \"generate_lookup\"?")
    errors = decl_errors__c()
    is_true_d = {}
    names = {}
    for i, conf in enumerate(confs):
      conf = self._link_configuration__(conf, errors)
      conf_dict = conf.m_dict
      for k, v in conf_dict.items():
        is_true_d[k] = (v, i)
        names[k] = conf.m_names.get(k, k)
    self._close_configuration_1__(is_true_d)
    # print("=====================================")
    # print("is_true_d")
    # print(is_true_d)
    # print("=====================================")
    res = {}
    v_local = is_true_d.get(self, _empty__)
    if(v_local is _empty__): self._close_configuration_2__(False, is_true_d, res)
    else: self._close_configuration_2__(v_local[0], is_true_d, res)
    return (configuration__c(res, self.m_lookup.resolve, names), errors)

  ##########################################
  # call API

  def __call__(self, conf, expected=True):
    if(self.m_dom is None):
      raise ValueError("ERROR: evaluating a non well-formed Feature Model (call 'check()' on it before)")
    res = self._eval_generic__(conf, _fd__c._f_get_deep__, expected)
    reason = res.m_reason
    if(reason):
      reason.update_ref(self._updater__)
      pass
    return res

  def _eval_generic__(self, conf, f_get, expected=True):
    # print(f"_eval_generic__([{self.__class__.__name__}]{self.m_name}, {conf}, {f_get}, {expected})")
    expected_att = (_empty__ if(expected is False) else expected)

    results_content = tuple(f_get(el, conf, self._get_expected__(el, i, expected)) for i, el in enumerate(self.m_content))
    result_att = tuple(self._manage_attribute__(el, conf, i, self._get_expected__(el, i, expected)) for i, el in enumerate(self.m_attributes))
    result_ctc = tuple(el(conf, i, self._get_expected__(el, i, expected)) for i, el in enumerate(self.m_ctcs))

    nvalue_subs  = tuple(itertools.chain((el.m_nvalue for el in results_content), (el.m_value for resu in (result_att, result_ctc) for el in resu)))
    nvalue_local = None
    nvalue_sub = self._compute__(nvalue_subs, nvalue_local)
    value_subs = all(el.m_value for el in results_content)
    snodes = tuple(v for el in results_content for v in el.m_snodes)

    # check consistency with name
    reason = None
    if(self.m_name is not None):
      nvalue_local = conf.get(self, _empty__)
      if(nvalue_local is _empty__): # should never occur
        reason = reason_tree__c(self, 0)
        reason.add_reason_value_none(self)
      elif((not nvalue_local) and snodes):
        reason = reason_tree__c(self, 0)
        reason.add_reason_dependencies(self, snodes)
      elif(nvalue_local and (not nvalue_sub)):
        reason = reason_tree__c(self, 0)
        reason.add_reason_value_mismatch(self, True, False)
      elif(nvalue_local):
        snodes = snodes + (self,)
    else:
      nvalue_local = nvalue_sub

    value = value_subs and (reason is None)

    if((nvalue_local != expected) or (not value)):
      if(reason is None): reason = reason_tree__c(self, 0)
      if((nvalue_local != expected)):
        reason.add_reason_value_mismatch(self, nvalue_local, expected)
      for el in itertools.chain(results_content, result_att, result_ctc):
        reason.add_reason_sub(el)

    return _eval_result_fd__c(value, reason, nvalue_local, snodes)

  def _f_get_shallow__(self, conf, expected=True):
    if(self.m_name is None):
      return self._eval_generic__(conf, _fd__c._f_get_shallow__, expected)
    else:
      nvalue = conf.get(self, _empty__)
      if(v is _empty__):
        reason = reason_tree__c(self, 0)
        reason.add_reason_value_none(self)
        value = False
        nvalue = False
        return _eval_result_fd__c(value, reason, nvalue, ())
      else:
        return _eval_result_fd__c(True, None, nvalue, ())

  def _f_get_deep__(self, conf, expected=True):
    return self._eval_generic__(conf, _fd__c._f_get_deep__, expected)

  def _manage_attribute__(self, att, conf, idx, expected):
    name, spec = att
    value = conf.get(att, _empty__)
    if(value is _empty__):
      if(expected):
        reason = reason_tree__c(self, 0)
        reason.add_reason_value_none(att)
        return eval_result__c(False, reason)
      else:
        return eval_result__c(False, None)
    else:
      res = spec(value)
      if(expected == res):
        return eval_result__c(res, None)
      else:
        reason = reason_tree__c(self, 0)
        reason.add_reason_value_mismatch(att, res, expected)
        return eval_result__c(res, reason)

  ##########################################
  # internal: lookup generation

  def _generate_lookup_rec__(self, path_to_self, idx, lookup, dom, errors):
    # print(f"_generate_lookup_rec__([{self.__class__.__name__}]{self.m_name}, {idx}, {path_to_self}, {lookup}, {errors})")
    # 1. if local names, add it to the table, and check no duplicates
    path_to_self.append(str(idx) if(self.m_name is None) else self.m_name)
    local_path = list(path_to_self)
    if(self.m_name is not None):
      lookup.insert(self, local_path, errors)
      # _fd__c._check_duplicate__(self, self.m_name, local_path, lookup, errors)
      dom[self] = local_path
    # 2. add subs
    for i, sub in enumerate(self.m_content):
      sub._generate_lookup_rec__(path_to_self, i, lookup, dom, errors)
    # 3. add attributes
    for att_def in self.m_attributes:
      att_path = [*local_path, att_def[0]]
      lookup.insert(att_def, att_path, errors)
      # _fd__c._check_duplicate__(att_def, att_def[0], local_path, lookup, errors)
      dom[att_def] = att_path
    # 4. check ctcs
    self.m_ctcs = tuple(ctc._link__(local_path, lookup, errors) for ctc in self.m_ctcs)
    # 5. reset path_to_self
    path_to_self.pop()

  ##########################################
  # internal: configuration nf API

  def _link_configuration__(self, conf, errors):
    if(isinstance(conf, configuration__c)):
      if(conf.m_resolver is self.m_lookup):
        return conf # already linked
      conf = conf.unlink().m_dict
    if(self.m_norm is not None):
      conf = self.m_norm(self, conf)
    linked = {}
    names = {}
    for key, val in conf.items():
      if(isinstance(key, str)):
        key_resolved = self.m_lookup.get(_path_from_str__(key), errors, None)
        if(key_resolved is not None):
          names[key_resolved] = key
          key = key_resolved
      linked[key] = val
    return configuration__c(linked, self.m_lookup.resolve, names)

  def _close_configuration_1__(self, is_true_d):
    idx, v_local, v_subs = self._infer_sv__(is_true_d)
    self._make_product_update__(is_true_d, idx, v_local, v_subs)
    for sub in self.m_content:
      sub._close_configuration_1__(is_true_d)
    idx, v_local, v_subs = self._infer_sv__(is_true_d)
    self._make_product_update__(is_true_d, idx, v_local, v_subs)

  def _make_product_update__(self, is_true_d, idx, v_local, v_subs):
    if(v_local is not _empty__):
      is_true_d[self] = (v_local, idx)
    for sub, v_sub in zip(self.m_content, v_subs):
      if(v_sub is not _empty__):
        is_true_d[sub] = (v_sub, idx)

  def _close_configuration_2__(self, v_local, is_true_d, res):
    _, _, v_subs = self._infer_sv__(is_true_d)
    res[self] = v_local
    for sub, v_sub in zip(self.m_content, v_subs):
      if(v_sub is _empty__):
        sub._close_configuration_2__(False, is_true_d, res)
      else:
        sub._close_configuration_2__(v_sub, is_true_d, res)
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

  def _updater__(self, ref):
    return self.m_dom.get(ref, ref)

##########################################
# 2. FD groups

class FDAnd(_fd__c):
  def __init__(self, *args, **kwargs):
    _fd__c.__init__(self, *args, **kwargs)
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

class FDAny(_fd__c):
  def __init__(self, *args, **kwargs):
    _fd__c.__init__(self, *args, **kwargs)
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

class FDOr(_fd__c):
  def __init__(self, *args, **kwargs):
    _fd__c.__init__(self, *args, **kwargs)
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

class FDXor(_fd__c):
  def __init__(self, *args, **kwargs):
    _fd__c.__init__(self, *args, **kwargs)
  def _compute__(self, values, nvalue):
    res = False
    for element in values:
      if(element):
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

##########################################
# 3. FD aliases

class FD(FDAnd): pass
class FDMandatory(FDAnd): pass
class FDOptional(FDAny): pass
class FDAlternative(FDXor): pass

