
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

  def new_instance(self):
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

  def new_instance(self):
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
      return ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=self.m_name_new, ctx=ast.Load())
    else:
      return node

  def __call__(self, function):
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
      exec(compile(node, '<ast>', 'exec'))
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

_obj__ = object()

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
        value, name_original = _replace_original__c(self.m_reg)(value)
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


################################################################################
# python object , 
################################################################################






# class VariantModulesInstance(object):
#   __slots__ = ("m_root", "m_ids", "m_names", "m_original_count",)

#   def add(self, param1, param2=_obj__):
#     if(param2 == _obj__):
#       value, name, is_local = extract_module_and_name(param1)
#     else:
#       value, name, is_local = extract_module_and_name((param1, param2))
#     if(name in self.m_names):
#       raise Exception(f"ERROR: the variant already has an element named {name}")
#     else:
#       self.m_names[name] = value
#       if(is_local):
#         v_id = id(value)
#         self.m_ids[v_id] = value

#   def remove(self, name):
#     try:
#       self.m_names.pop(name)
#     except:
#       raise Exception(f"ERROR: the variant has no element named {name}")


#   def __init__(self, root):
#     self.m_root = root
#     self.m_ids = {}
#     self.m_names = dict(self.m_root.m_content)
#     self.m_original_count = 0



#   def __getattr__(self, name):
#     module = self.m_names[name]
#     # module_id = id(module)
#     # module = self.m_ids.get(module_id, module)
#     return _wrapper__c(self, None, name, module)

#   def _get_original_name__(self, name):
#     res = f"{name}#{self.m_original_count}"
#     self.m_original_count += 1
#     return res

#   def _check_replica__(self, wrapper):
#     obj = wrapper.m_obj
#     obj_id = id(obj)
#     obj_replica = self.m_ids.get(obj_id)
#     # print(f"_get_replica__({obj}) => {obj_replica is None}")
#     if(obj_replica is None):
#       if(inspect.isclass(obj)):
#         obj_replica = type(obj.__name__, obj.__bases__, dict(obj.__dict__))
#       elif(isinstance(obj, _module_class_)):
#         obj_replica = type(obj)(obj.__name__, obj.__doc__)
#         obj_replica.__dict__.update(obj.__dict__)
#       else:
#         obj_replica = copy.copy(obj)
#       # need to put the new object in the father (which may need to be duplicated also)
#       if(wrapper.m_root is not None):
#         new_root = self._check_replica__(wrapper.m_root)
#         setattr(new_root, wrapper.m_name, obj_replica)
#       else: # need to update the ref in the m_names map
#         self.m_names[wrapper.m_name] = obj_replica
#       self.m_ids[obj_id] = obj_replica
#       self.m_ids[id(obj_replica)] = obj_replica
#       object.__setattr__(wrapper, "m_obj", obj_replica)
#     return obj_replica

#   def _register_obj__(self, obj):
#     # print(f"_register_obj__({obj})")
#     # if(isinstance(obj, _wrapper__c)):
#     #   print(obj.m_obj)
#     if(inspect.isclass(obj)):
#       for i in range(len(obj.__bases__)):
#         if(isinstance(obj.__bases__[i], _wrapper__c)):
#           obj.__bases__[i] = obj.__bases__[i].m_obj
#     self.m_ids[id(obj)] = obj

#   def register_modules(self):
#     for name, module in self.m_names.items():
#       if(name in sys.modules):
#         raise Exception(f"ERROR: module \"{name}\" already declared")
#       # module_id = id(module)
#       # module = self.m_ids.get(module_id, module)
#       sys.modules[name] = module

#   def unregister_modules(self):
#     for name in self.m_names:
#       sys.modules.pop(name)
