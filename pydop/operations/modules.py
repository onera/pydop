
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


# This file contains the implementation for Delta Operations on Python modules
# In particular, this file provides two variant implementations:
#  - VariantModules, that contains a set of module (it is possible to add/remove/modify modules)
#  - VariantModule, that corresponds to one module (it is possible to add/remove/modify classes/functions/other)
# Moreover, classes can be modified by adding/removing/modifying fields and methods to/from them
# It is also possible to call the unbound "original" function during the modification of a method to call the previous definition of that method

import sys
import importlib
import importlib.util
import inspect
import copy
import ast
import textwrap



##########################################
# wrapper utils

class wrapper_cls(object):
  __slots__ = ("m_content")

def unwrap(el):
  while(issubclass(type(el), wrapper_cls)):
    el = el.m_content
  return el


################################################################################
# Variant
################################################################################

Module = type(importlib)

################################################################################
# DELTA OPERATIONS
################################################################################

_obj__ = object()

def hasattr_static(obj, name):
  global _obj__
  return (inspect.getattr_static(obj, name, default=_obj__) is not _obj__)

def add(obj):
  def res(param1, param2=_obj__):
    global _obj__
    nonlocal obj
    if(param2 == _obj__):
      name  = param1.__name__
      value = param1
    else:
      name  = param1
      value = param2
  
    obj = unwrap(obj)
    value = unwrap(value)
    if(hasattr_static(obj, name)):
      name_kind = obj.__class__.__name__
      name_obj  = obj.__name__
      raise Exception(f"ERROR: {name_kind} {name_obj} already has an element named {name}")
    else:
      setattr(obj, name, value)
  return res

def remove(obj, name):
  obj = unwrap(obj)
  if(hasattr_static(obj, name)):
    delattr(obj, name)
  else:
    name_kind = obj.__class__.__name__
    name_obj  = obj.__name__
    raise Exception(f"ERROR: {name_kind} {name_obj} has no element named {name}")

def modify(obj):
  def res(param1, param2=_obj__):
    global _obj__
    global original_replacer
    nonlocal obj
    if(param2 == _obj__):
      name  = param1.__name__
      value = param1
    else:
      name  = param1
      value = param2

    obj = unwrap(obj)
    value = unwrap(value)

    if(hasattr_static(obj, name)):
      if(inspect.isfunction(value)):
        # print("modify", value.__name__, ":", inspect.getclosurevars(value).nonlocals)
        value, name_original = original_replacer(obj, name, value, inspect.getclosurevars(value).nonlocals)
        if(name_original != name):
          setattr(obj, name_original, getattr(obj, name))
      setattr(obj, name, value) 
    else:
      name_kind = obj.__class__.__name__
      name_obj  = obj.__name__
      raise Exception(f"ERROR: {name_kind} {name_obj} has no element named {name}")
  return res


def add_extends(obj):
  obj = unwrap(obj)
  if(inspect.isclass(obj)):
    def res(*bases):
      nonlocal obj
      bases = map(unwrap, bases)
      bases = tuple(filter(lambda x: x not in obj.__bases__, bases))
      obj.__bases__ += bases
    return res
  else:
    raise Exception(f"ERROR: delta operation \"add_extends\" can only be applied on classes (\"{type(obj)}\" found)")


def remove_extends(obj):
  obj = unwrap(obj)
  if(inspect.isclass(obj)):
    def res(*bases):
      nonlocal obj
      bases_rm = frozenset(map(unwrap, bases))
      bases = frozenset(obj.__bases__)
      bases_error = bases_rm - bases
      if(bases_error):
        raise Exception(f"ERROR: trying to remove non-superclasses {bases_error}")
      else:
        obj.__bases__ = tuple(el for el in obj.__bases__ if(el not in bases_rm))
    return res
  else:
    raise Exception(f"ERROR: delta operation \"remove_extends\" can only be applied on classes (\"{type(obj)}\" found)")

def set_extends(obj):
  obj = unwrap(obj)
  if(inspect.isclass(obj)):
    def res(*bases):
      nonlocal obj
      bases = tuple(map(unwrap, bases))
      self.m_obj.__bases__ = bases
    return res
  else:
    raise Exception(f"ERROR: delta operation \"set_extends\" can only be applied on classes (\"{type(obj)}\" found)")



##########################################
# original function call replacer

class _original_replacer_cls(ast.NodeTransformer):
  __slots__ = ("m_obj", "name_original", "m_obj_name", "m_name_new",)
  def __init__(self):
    ast.NodeTransformer.__init__(self)

  def visit_Name(self, node):
    if(node.id == "original"):
      return ast.Attribute(value=ast.Name(id=self.m_obj_name, ctx=ast.Load()), attr=self.name_new, ctx=ast.Load())
      # if(inspect.isclass(self.m_obj)):
      #   return ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=self.m_name_new, ctx=ast.Load())
      # else:
      #   return ast.Name(id=self.m_name_new, ctx=ast.Load())
    else:
      return node

  def visit_Attribute(self, node):
    if((node.attr == "original") and ((type(node.value) == ast.Name) and (node.value.id == "self"))):
      return ast.Attribute(value=node.value, attr=self.name_new, ctx=ast.Load())
    else:
      return node

  def __call__(self, obj, name, function, nonlocals):
    self.m_obj = obj
    self.name_original = name
    self.m_name_new = None
    # self.m_qualast  = None

    exec_env = self.create_exec_env(nonlocals)

    function_name = function.__name__
    function_namefile = inspect.getfile(function)
    function_lines, function_start_lineno = inspect.getsourcelines(function)
    # remove the @ decorations
    function_start = 0
    while(function_lines[function_start].lstrip()[0] == '@'):
      function_start += 1
    source = "".join(function_lines[function_start:])
    source = textwrap.dedent(source)

    node = ast.parse(source)
    ast.increment_lineno(node, function_start_lineno + function_start - 1) # setup the correct line number
    node = self.visit(node)

    if(self.m_name_new is None): name_original = self.name_original
    else: name_original = self.m_name_new

    ast.fix_missing_locations(node)
    exec(compile(node, function_namefile, 'exec'), exec_env, locals())
    function = locals()[function_name]
    return function, name_original

  @property
  def name_new(self):
    if(self.m_name_new is None):
      count = 0
      self.m_name_new = f"{self.name_original}#{count}"
      while(hasattr_static(self.m_obj, self.m_name_new)):
        count += 1
        self.m_name_new = f"{self.name_original}#{count}"
    return self.m_name_new

  @property
  def qualast(self):
    if(self.m_qualast is None):
      if(hasattr_static(self.m_obj, "__qualname__")):
        tmp = self.m_obj.__qualname__
      else:
        tmp = self.m_obj.__name__
      quallist = tmp.split('.')
      print("replacing original with ", tmp)
      self.m_qualast = ast.Name(id=quallist[0], ctx=ast.Load())
      for attr in quallist[1:]:
        self.m_qualast = ast.Attribute(value=self.m_qualast, attr=attr, ctx=ast.Load())
    return self.m_qualast

  def create_exec_env(self, nonlocals):
    exec_env = globals() | nonlocals
    exec_env_keys = frozenset(exec_env.keys())
    self.m_obj_name = " "
    while(self.m_obj_name in exec_env_keys):
      self.m_obj_name += " "
    exec_env[self.m_obj_name] = self.m_obj
    return exec_env


original_replacer = _original_replacer_cls()









################################################################################
# information lookup in python modules
################################################################################

_module_class_ = importlib.__class__

def extract_module_and_name(param):
  if(isinstance(param, str)):
    name = param
    module = sys.modules.get(name)
    if(module is None):
      spec = importlib.util.find_spec(name)
      if(spec is None): # this name cannot be loaded: create an empty module
        module = _module_class_(name)
        is_local = True
      else:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        is_local = False
    else:
      sys.modules.pop(name)
      is_local = False
  elif(isinstance(module, (list, tuple))):
    tmp = module
    name = tmp[0]
    module, _, is_local = extract_module_and_name(tmp[1])
  elif(isinstance(param, module_c)):
    module = param
    name = module.__name__
    is_local = False
  else:
    raise Exception(f"ERROR: invalid parameter (expected str or module or pair, \"{type(param)}\" found)")
  return module, name, is_local

################################################################################
# variant and factories
################################################################################

class VariantModules(object):
  __slots__ = ("m_content",)
  def __init__(self, *args):
    self.m_content = {}
    for arg in args:
      module, name, _ = extract_module_and_name(arg)
      if(name in self.m_content):
        raise Exception(f"ERROR: module \"{name}\" already declared")
      self.m_content[name] = module

  def __call__(self):
    variant = VariantModulesInstance()
    variant.__dict__ = dict(self.m_content)
    reg = _registry__c(variant)
    res = _wrapper__c(reg, None, None, variant)
    return res

class VariantModulesInstance(object): pass


class VariantModule(object):
  __slots__ = ("m_module",)
  def __init__(self, arg):
    self.m_module, _, _ = extract_module_and_name(arg)

  def __call__(self):
    variant = type(self.m_module)(self.m_module.__name__, self.m_module.__doc__)
    variant.__dict__.update(self.m_module.__dict__)
    reg = _registry__c(variant)
    res = _wrapper__c(reg, None, None, variant)
    return res





################################################################################
# registering and unregistering modules
################################################################################

def register_modules(obj):
  if(isinstance(obj, _wrapper__c)):
    obj = obj.m_obj
  if(isinstance(obj, _module_class_)):
    name = obj.__name__
    if(name in sys.modules):
      raise Exception(f"ERROR: module \"{name}\" already declared")
    # print("registering module", name)
    sys.modules[name] = obj
  elif(hasattr(obj, "__dict__")):
    for sub in obj.__dict__.values():
      register_modules(sub)

def unregister_modules(obj):
  if(isinstance(obj, _wrapper__c)):
    obj = obj.m_obj
  if(isinstance(obj, _module_class_)):
    name = obj.__name__
    # print("un-registering module", name)
    sys.modules.pop(name)
  elif(hasattr(obj, "__dict__")):
    for sub in obj.__dict__.values():
      unregister_modules(sub)


def register_module(obj):
  sys.modules[obj.__name__] = obj

################################################################################
# original function call replacer
################################################################################

class _replace_original__c(ast.NodeTransformer):
  __slots__ = ("m_instance", "m_name_original", "m_name_new",)
  def __init__(self, instance):
    ast.NodeTransformer.__init__(self)
    self.m_instance = instance
    self.m_name_original = None
    self.m_name_new = None
  def visit_Name(self, node):
    if(node.id == "original"):
      self.m_name_new = self.m_instance._get_original_name__(self.m_name_original)
      # return ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=self.m_name_new, ctx=ast.Load())
      return ast.Name(id=self.m_name_new, ctx=ast.Load())
    else:
      return node

  def __call__(self, function, nonlocals):
    self.m_name_original = function.__name__
    source = inspect.getsource(function)
    source = textwrap.dedent(source)
    source = source.split('\n', 1)[1]
    node = ast.parse(source)
    node = self.visit(node)
    if(self.m_name_new is None):
      name_original = name
    else:
      name_original = self.m_name_new
      ast.fix_missing_locations(node)
      exec(compile(node, '<ast>', 'exec'), globals() | nonlocals, locals())
      function = locals()[self.m_name_original]
    return function, name_original

################################################################################
# registry: ensures that all modifications are done to local objects
# wrapper: for the add add/modify/remove decorators
################################################################################

class _registry__c(object):
  __slots__ = ("m_ids", "m_originals", "m_original_count",)
  def __init__(self, variant):
    self.m_ids = {}
    self.m_originals = []
    self._register_obj__(variant)
    self.m_original_count = 0

  def _check_replica__(self, wrapper):
    obj = wrapper.m_obj
    obj_id = id(obj)
    obj_replica = self.m_ids.get(obj_id)
    if(obj_replica is None): # the object is not local: need to do a copy
      if(inspect.isclass(obj)):
        obj_replica = type(obj.__name__, obj.__bases__, dict(obj.__dict__))
      elif(isinstance(obj, _module_class_)):
        obj_replica = type(obj)(obj.__name__, obj.__doc__)
        obj_replica.__dict__.update(obj.__dict__)
      else:
        obj_replica = copy.copy(obj)
      # need to put the new object in the father (which may need to be duplicated also)
      if(wrapper.m_parent is not None):
        new_root = self._check_replica__(wrapper.m_parent)
        setattr(new_root, wrapper.m_name, obj_replica)
      self.m_ids[obj_id] = obj_replica
      self.m_ids[id(obj_replica)] = obj_replica
      self.m_originals.append(obj)
      object.__setattr__(wrapper, "m_obj", obj_replica)
    return obj_replica

  def _register_obj__(self, obj):
    if(inspect.isclass(obj)): # the superclasses might be wrapped
      for i in range(len(obj.__bases__)):
        if(isinstance(obj.__bases__[i], _wrapper__c)):
          obj.__bases__[i] = obj.__bases__[i].m_obj
    self.m_ids[id(obj)] = obj

  def _get_original_name__(self, name):
    res = f"{name}#{self.m_original_count}"
    self.m_original_count += 1
    return res


def _hasattr_no_follow__(obj, name):
  try:
    object.__getattribute__(obj, name)
    return True
  except:
    return False

class _wrapper__c(object):
  __slots__ = (
    "m_reg",    # the local object registry
    "m_parent", # the parent wrapper (None if not relevant)
    "m_name",   # the name of the wrapped object (None if not relevant)
    "m_obj",    # the wrapped object
  )
  def __new__(cls, *args): # Necessary, when a wrapper is used as a superclass
    # print(f"_wrapper__c.__new__({cls}, {args})")
    if((len(args) == 4) and (isinstance(args[0], _registry__c))):
      return super(_wrapper__c, cls).__new__(cls)
    else:
      name = args[0]
      bases = tuple((el.m_obj if(isinstance(el, _wrapper__c)) else el) for el in args[1])
      content = args[2]
      # print(bases)
      return type(name, bases, content)
  def __init__(self, registry, parent, name, obj):
    object.__setattr__(self, "m_reg", registry)
    object.__setattr__(self, "m_parent", parent)
    object.__setattr__(self, "m_name", name)
    object.__setattr__(self, "m_obj", obj)

  def __getattr__(self, name):
    if(hasattr(self.m_obj, name)):
      return _wrapper__c(self.m_reg, self, name, getattr(self.m_obj, name))
    else:
      return object.__getattribute__(self.m_obj, name)

  def __setattr__(self, name, value):
    raise Exception("Direct assigment is not allowed in variants")

  def __call__(self, *args, **kwargs):
    return self.m_obj(*args, **kwargs)

  def add(self, param1, param2=_obj__):
    if(param2 == _obj__):
      name  = param1.__name__
      value = param1
    else:
      name  = param1
      value = param2
    if(_hasattr_no_follow__(self.m_obj, name)):
      name_kind = self.m_obj.__class__.__name__
      name_obj  = self.m_obj.__name__
      raise Exception(f"ERROR: {name_kind} {name_obj} already has an element named {name}")
    else:
      self.m_reg._check_replica__(self)
      # self.m_reg._register_obj__(value)
      return setattr(self.m_obj, name, value)

  def remove(self, name):
    if(_hasattr_no_follow__(self.m_obj, name)):
      delattr(self.m_obj, name)
    else:
      name_kind = self.m_obj.__class__.__name__
      name_obj  = self.m_obj.__name__
      raise Exception(f"ERROR: {name_kind} {name_obj} has no element named {name}")

  def modify(self, param1, param2=_obj__):
    if(param2 == _obj__):
      name  = param1.__name__
      value = param1
    else:
      name  = param1
      value = param2
    if(_hasattr_no_follow__(self.m_obj, name)):
      if(inspect.isfunction(value)):
        # print("modify", value.__name__, ":", inspect.getclosurevars(value).nonlocals)
        value, name_original = _replace_original__c(self.m_reg)(value, inspect.getclosurevars(value).nonlocals)
        if(name_original != name):
          setattr(self.m_obj, name_original, getattr(self.m_obj, name))
      setattr(self.m_obj, name, value) 
    else:
      name_kind = self.m_obj.__class__.__name__
      name_obj  = self.m_obj.__name__
      raise Exception(f"ERROR: {name_kind} {name_obj} has no element named {name}")

  def add_extends(self, *args):
    if(inspect.isclass(self.m_obj)):
      bases = tuple((el.m_obj if(isinstance(el, _wrapper__c)) else el) for el in args)
      bases = tuple(filter(lambda x: x not in self.m_obj.__bases__, bases))
      self.m_obj.__bases__ += bases
    else:
      raise Exception(f"ERROR: delta operation \"add_extends\" can only be applied on classes (\"{type(self.m_obj)}\" found)")

  def remove_extends(self, *args):
    if(inspect.isclass(self.m_obj)):
      bases_rm = frozenset((el.m_obj if(isinstance(el, _wrapper__c)) else el) for el in args)
      bases = frozenset(self.m_obj.__bases__)
      bases_error = bases_rm - bases
      if(bases_error):
        raise Exception(f"ERROR: trying to remove non-superclasses {bases_error}")
      else:
        self.m_obj.__bases__ = tuple(el for el in self.m_obj.__bases__ if(el not in bases_rm))
    else:
      raise Exception(f"ERROR: delta operation \"remove_extends\" can only be applied on classes (\"{type(self.m_obj)}\" found)")

  def set_extends(self, *args):
    if(inspect.isclass(self.m_obj)):
      bases = tuple((el.m_obj if(isinstance(el, _wrapper__c)) else el) for el in args)
      self.m_obj.__bases__ = bases
    else:
      raise Exception(f"ERROR: delta operation \"set_extends\" can only be applied on classes (\"{type(self.m_obj)}\" found)")

