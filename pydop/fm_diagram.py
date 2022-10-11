
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

from pydop.fm_core import eval_predicate


import enum


################################################################################
# Predicate evaluation and error reporting
################################################################################

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
  def __init__(self, value=None, reason=None, snodes=None):
    self.m_value  = value   # the result of the evaluation, used for propagation within a FD
    self.m_reason = reason  # reason for which a False value cannot be fixed
    self.m_snodes = snodes  # the list of sub nodes that are True

  def value(self): return self.m_value
  def __bool__(self): return (self.m_reason is None)


def _get_result(res):
  if(isinstance(res, bool)):
    if(res): return _eval_result__c(value=res)
    else: return _eval_result__c(value=res, reason=_reason_tree__c(res, "False found"))
  else:
    return res




  # @staticmethod
  # def _manage_annex_list(annex_list, name, value):
  #   if((value is False) and bool(annex_list)): # the name is set to false while there are true features in the subtree
  #     return [f"Feature \"{name}\" must be True (due to [{', '.join(annex_list)}] being True)"]
  #   else:
  #     return []

  # @staticmethod
  # def _op_and(args, name=None, value=None):
  #   error_list = []
  #   annex = []
  #   for arg in args:
  #     if(isinstance(arg, bool)):
  #       if(not arg):
  #         error_list.append("False found")
  #     else:
  #       error_list.extend(arg.m_reasons_list)
  #       annex.extend(arg.m_annex)
  #       if(not arg.m_value):
  #         error_list.append("False found")
  #   error_list.extend(_eval_result__c._manage_annex_list(annex, name, value))
    
  #   error = _eval_result__c._reason_tree__c(name, error_list) if(error_list) else None
  #   if(value is True): annex.append(name)

  #   return _eval_result__c(error, annex)




# I have an issue where the value of a false feature is false (for the operator), while the feature diagram is true


################################################################################
# Boolean constraints
################################################################################



class _expbool__c(object):
  __slots__ = ("m_content","m_vars")
  def __init__(self, content):
    self.m_content = content
    self.m_vars = tuple(el for sub in content for el in (sub.m_vars if(isinstance(sub, _expbool__c)) else (sub,)))

  def get_name(self): return self.__class__.__name__
  def get_reason(self, idx, content): return _reason_tree__c(self.get_name(), idx, content)

  def __call__(self, product, idx=None, my_eval=eval_predicate):
    values = tuple(my_eval(el, product, i) for i, el in enumerate(self.m_content))
    res = self._compute__(values)
    if(res):
      reason = None
    else:
      tmp1 = zip(self.m_content, values)
      message = " vs ".join(f"[{el[0]} = {el[1].value() if(isinstance(el[1], _eval_result__c)) else el[1]}]" for el in tmp1)
      tmp2 = filter((lambda x: isinstance(x, _eval_result__c) and (x.m_reason is not None)), values)
      sub_reasons = tuple(el.m_reason for el in tmp2)
      reason = self.get_reason(idx, (message,) + sub_reasons) if(sub_reasons) else self.get_reason(idx, message)
    return _eval_result__c(res, reason)
 
  def __str__(self): return f"{self.get_name()}({', '.join(str(el) for el in self.m_content)})"


class Lt(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (values[0] < values[1])
      
class Leq(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (values[0] <= values[1])

class Eq(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (values[0] == values[1])

class Geq(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (values[0] >= values[1])

class Gt(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (values[0] > values[1])


class And(_expbool__c):
  __slots__ = ()
  def __init__(self, *args):
    _expbool__c.__init__(self, args)
  def _compute__(self, values):
    return all(bool(el) for el in values)
  # def __call__(self, product):
  #   for element in self.m_content:
  #     if(not eval(element, product)): return False
  #   return True

class Or(_expbool__c):
  __slots__ = ()
  def __init__(self, *args):
    _expbool__c.__init__(self, args)
  def _compute__(self, values):
    return any(bool(el) for el in values)
  # def __call__(self, product):
  #   for element in self.m_content:
  #     if(eval(element, product)): return True
  #   return False

class Not(_expbool__c):
  __slots__ = ()
  def __init__(self, arg):
    _expbool__c.__init__(self, (args,))
  def _compute__(self, values):
    return not bool(values[0])
  # def __call__(self, product):
  #   return not (eval(self.m_content, product))

class Xor(_expbool__c):
  __slots__ = ()
  def __init__(self, *args):
    _expbool__c.__init__(self, args)
  def _compute__(self, values):
    res = False
    for element in values:
      if(bool(element)):
        if(res): return False
        else: res = True
    return res
    # def __call__(self, product):
    #   res = False
    #   for element in self.m_content:
    #     if(eval(element, product)):
    #       if(res): return False
    #       else: res = True
    #   return res

class Conflict(_expbool__c):
  __slots__ = ()
  def __init__(self, *args):
    _expbool__c.__init__(self, args)
  def _compute__(self, values):
    res = False
    for element in values:
      if(bool(element)):
        if(res): return False
        else: res = True
    return True
  # def __call__(self, product):
  #   res = False
  #   for element in self.m_content:
  #     if(eval(element, product)):
  #       if(res): return False
  #       else: res = True
  #   return True

class Implies(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return ((not bool(values[0])) or bool(values[1]))
  # def __call__(self, product):
  #   left = eval(self.m_content[0], product)
  #   right = eval(self.m_content[1], product)
  #   return ((not left) or (right))

class Iff(_expbool__c):
  __slots__ = ()
  def __init__(self, left, right):
    _expbool__c.__init__(self, (left, right,))
  def _compute__(self, values):
    return (bool(values[0]) == bool(values[1]))
  # def __call__(self, product):
  #   left = eval(self.m_content[0], product)
  #   right = eval(self.m_content[1], product)
  #   return (left == right)



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


class List(_fdattribute_c):
  __slots__ = ("m_size", "m_content",)
  def __init__(self, size=None, kind=None):
    self.m_size = []
    if(size is not None):
      _add_domain_spec(self.m_size, *size)
    self.m_content = kind

  def __call__(self, value):
    if(isinstance(value, (tuple, list))):
      if(_check_domain(self.m_size, len(value))):
        if(self.m_kind is None):
          return True
        else:
          for el in value:
            if(not self.m_kind(el)): return False
          return True
    return False



################################################################################
# Feature Groups
################################################################################

# Ok, stuff are more complex than anticipated:
# we need to manage attributes, and error messages.
# Hence the return type is e

# class _fdgroup_res__c(object):
#   __slots__ = ("m_value", "m_enforced")
#   def __init__(self, value, enforced):
#     self.m_value = value
#     self.m_enforced = enforced

#   def __bool__(self): return self.m_value

#   @staticmethod
#   def monad(content, operator):
#     value = operator(map((lambda x: x.m_value if(isinstance(x, _fdgroup_res__c)) else x), content))
#     enforced = any(map((lambda x: x.m_enforced if(isinstance(x, _fdgroup_res__c)) else False), content))
#     return _fdgroup_res__c(value, enforced)

# need to have a lookup also for ctc!

def _path_includes(p, p_included):
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

# API:
# function that generates the lookup on demand, going down,
# with _generate_lookup__rec(self, path_to_self, res), res beeing the lookup table being generated
# !! need to consider also attributes that have the same possibility of name clash with features

# also, something that could be nice for error reporting, is that we propagate downward the expected value
# the issue is that, the expected value is function dependent: I don't want to construct a tuple for every method call
# also, what is the expected value of "xor" parameters for instance... depends if the problem of the xor is no true, or too much
# well, we could choose arbitrarily true or false, but it means that we don't know why a term has the opposite value
# dunno, if no expected value is given, document everything? Up until a feature, since its value must correspond to the value of its content.
# it's kind of a undertaking, but it can be done

# __call__(self, product, idx=None, my_eval=eval_predicate, expected_value=True)

class _fdgroup__c(object):
  __slots__ = ( "m_name", "m_content", "m_ctcs", "m_attributes", "m_lookup", )
  def __init__(self, name, content, ctcs, attributes):
    self.m_name = name
    self.m_content = content
    self.m_ctcs = ctcs
    self.m_attributes = attributes
    self.m_lookup = None

  ##########################################
  # generate_lookup API

  def generate_lookup(self):
    if(self.m_lookup is None):
      self.m_lookup = {}
      self._generate_lookup__rec([], self.m_lookup)

  def _generate_lookup__rec(self, path_to_self, res):
    # 1. if local names, add it to the table, and check no duplicates
    if(self.m_name is not None):
      path_to_self.append(self.m_name)
      _fdgroup__c._check_duplicate__(self, self.m_name, path_to_self, res)
    # 2. add subs
    for sub in self.m_content:
      sub._generate_lookup__rec(path_to_self, res)
    # 3. add attributes
    path_to_self.append(None)
    for att_def in self.m_attributes.items():
      path_to_self[-1] = att_def[0]
      _fdgroup__c._check_duplicate__(att_def, att_def[0], path_to_self, res)
    path_to_self.pop()
    # 4. check ctcs
    for ctc in self.m_ctcs:
      # need to check what could be a normal form for constraints that could work with a normal form of product. In my point of view: partial paths
      # we take the product with partial paths, translate it with non ambiguous flat mapping, and go as before. -> check vs self for features, and vs attribute_def for attributes
      # could work
    # 5. reset path_to_self
    path_to_self.pop()

  @staticmethod
  def _check_duplicate__(el, name, path, res):
    tmp = res.get(name)
    if(tmp is not None):
      if(any((path == el[1]) for el in tmp)):
        raise Exception(f"ERROR: several features with the same path: \"{path}\"")
      tmp.append( (el, path,) )
    else:
      res[name] = [(el, path,)]


  def clean(self): self.m_lookup = None
  def check(self):
    if(self.m_lookup is not None): return
    # 1. create lookup table
    self.m_lookup = {}
    if(self.m_name is None):
      manage_paths = lambda ps: ps
    else:
      self.m_lookup[self.m_name] = [(self, (self.m_name,),)]
      manage_paths = lambda ps: list((el[0], ((self.m_name,) + el[1]),) for el in ps)
    for sub in self.m_content:
      for feature, paths in sub.m_lookup.items():


    # 3. check and update ctcs

  def _eval_generic__(self, product, fget):
    return 
    res = self._start__()
    for element in self.m_content:
      val = fget(element, product)
      res = self._combine__(res, val)
    return self._conclude__(res)

  def _eval__(self, product): return self._eval_generic__(product, self.get)
  def _eval_shallow__(self, product): return self._eval_generic__(product, self.get_shallow)
  def _ensure_false__(self, name_parent, product):
    for element in self.m_content:
      if(self.get_shallow(element)):
        raise ValueError(f"ERROR: the feature {self.get_name(element)} is activated while the parent feature {name_parent} is not")

  @staticmethod
  def content_to_nf(args):
    return tuple((arg if(isinstance(arg, FD)) else FD(arg)) for arg in args)

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

  def make_product(self, conf, value, res):
    for element in self.m_content:
      element.make_product(conf, value, res)
    return self.get_shallow(res)


class FDAnd(_fdgroup__c):
  def __init__(self, *args):
    self.m_content = _fdgroup__c.content_to_nf(args)
  @staticmethod
  def _start__(): return True
  @staticmethod
  def _combine__(left, right): return left and right
  @staticmethod
  def _conclude__(value): return value
class FDAny(_fdgroup__c):
  def __init__(self, *args):
    self.m_content = _fdgroup__c.content_to_nf(args)
  @staticmethod
  def _start__(): return True
  @staticmethod
  def _combine__(left, right): return True
  @staticmethod
  def _conclude__(value): return value
class FDOr(_fdgroup__c):
  def __init__(self, *args):
    self.m_content = _fdgroup__c.content_to_nf(args)
  @staticmethod
  def _start__(): return False
  @staticmethod
  def _combine__(left, right): return left or right
  @staticmethod
  def _conclude__(value): return value
class FDXor(_fdgroup__c):
  def __init__(self, *args):
    self.m_content = _fdgroup__c.content_to_nf(args)
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

  def make_product(self, conf, value=None, res=None):
    if(res is None):
      res = {}
    # 1 compute a value for self
    set_conf = (self.get_name() in conf)
    set_value = (value is not None)
    if(set_conf and set_value):
      assert(conf[self.get_name()] == value)
    elif(set_conf):
      value = conf[self.get_name()]

    sub_values = (group.make_product(conf, value, res) for group in self.m_groups)
    if(self.m_groups):
      group = self.m_groups[0]
      if(value is None):
        value = group.make_product(conf, value, res)
      elif(value):
        assert(group.make_product(conf, value, res))
      else:
        group._ensure_false__(self.get_name(), res)
    elif(value is None):
      value = False

    res[self.get_name()] = value

    # 2. ensure consistency with attributes
    if(value):
      for att, spec in self.m_attributes:
        assert(att in conf)
        res[att] = conf[att]
    else:
      for att, spec in self.m_attributes:
        assert(att not in conf)

    # 3. propagate and ensure consistency with other subtrees
    if(value):
      for group in self.m_groups[1:]:
        assert(group.make_product(conf, value, res))
    else:
      for group in self.m_groups[1:]:
        group.make_product(conf, value, res)
        group._ensure_false__(self.get_name(), res)

    return res

