
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


# create a variant from a set of modules
# operation to modify modules / classes

import sys
import importlib
import inspect
import copy

_module_class_ = importlib.__class__


def extract_module_and_name(param):
  if(isinstance(param, str)):
    name = param
    module = sys.modules.get(name)
    if(module is None):
      spec = importlib.util.find_spec(name)
      if(spec is None): # this name cannot be loaded: create an empty module
        module = _module_class_(name)
      else:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
      del sys.modules[name]
  elif(isinstance(param, module_c)):
    module = param
    name = module.__name__
  elif(isinstance(module, (list, tuple))):
    res = module
    name = res[1]
    tmp = res[0]
    module = (extract_module_and_name(tmp)[0]) if(isinstance(tmp, str)) else tmp
  else:
    raise Exception(f"ERROR: invalid parameter (expected str or module or pair, \"{type(param)}\" found)")
  return module, name


class VariantModules(object):
  __slots__ = ("m_content",)

  def __init__(self, *args):
    self.m_content = {}

    for arg in args:
      module, name = extract_module_and_name(arg)
      if(name in self.m_content):
        raise Exception(f"ERROR: module \"{name}\" already declared")
      self.m_content[name] = module

  def new_instance(self):
    return VariantModulesInstance(self)



class VariantModulesInstance(object):
  __slots__ = ("m_root", "m_ids",)

  class wrapper(object):
    __slots__ = ("m_instance", "m_root", "m_obj",)
    def __new__(cls, *args):
      if((len(args) == 3) and (isinstance(args[0], VariantModulesInstance))):
        return super(VariantModulesInstance.wrapper, cls).__new__(cls)
      else:
        name = args[0]
        bases = tuple((el.m_obj if(isinstance(el, VariantModulesInstance.wrapper)) else el) for el in args[1])
        content = args[2]
        # print(bases)
        return type(name, bases, content)
    def __init__(self, instance, root, obj):
      object.__setattr__(self, "m_instance", instance)
      object.__setattr__(self, "m_root", root)
      object.__setattr__(self, "m_obj", obj)

    def __getattr__(self, name):
      if(hasattr(self.m_obj, name)):
        return VariantModulesInstance.wrapper(self.m_instance, self, getattr(self.m_obj, name))
      else:
        return object.__getattribute__(self.m_obj, name)

    def __setattr__(self, name, value):
      # print(f"__setattr__({name}, {value})")
      object.__setattr__(self, "m_obj", self.m_instance._get_replica__(self.m_obj))
      # print("TOTO2 :", type(self.m_obj))
      self.m_instance._register_obj__(value)
      return setattr(self.m_obj, name, value)

  def __init__(self, root):
    self.m_root = root
    self.m_ids = {}

  def __getattr__(self, name):
    module = self.m_root.m_content[name]
    module_id = id(module)
    module = self.m_ids.get(module_id, module)
    return VariantModulesInstance.wrapper(self, None, module)

  def _get_replica__(self, obj):
    obj_id = id(obj)
    obj_replica = self.m_ids.get(obj_id)
    # print(f"_get_replica__({obj}) => {obj_replica is None}")
    if(obj_replica is None):
      if(inspect.isclass(obj)):
        obj_replica = type(obj.__name__, obj.__bases__, dict(obj.__dict__))
      elif(isinstance(obj, _module_class_)):
        obj_replica = type(obj)(obj.__name__, obj.__doc__)
        obj_replica.__dict__.update(obj.__dict__)
      else:
        obj_replica = copy.copy(obj)
      self.m_ids[obj_id] = obj_replica
      self.m_ids[id(obj_replica)] = obj_replica
    return obj_replica

  def _register_obj__(self, obj):
    # print(f"_register_obj__({obj})")
    if(isinstance(obj, VariantModulesInstance.wrapper)):
      print(obj.m_obj)
    if(inspect.isclass(obj)):
      for i in range(len(obj.__bases__)):
        if(isinstance(obj.__bases__[i], VariantModulesInstance.wrapper)):
          obj.__bases__[i] = obj.__bases__[i].m_obj
    self.m_ids[id(obj)] = obj

  def import_modules(self):
    for name, module in self.m_root.m_content.items():
      if(name in sys.modules):
        raise Exception(f"ERROR: module \"{name}\" already declared")
      module_id = id(module)
      module = self.m_ids.get(module_id, module)
      sys.modules[name] = module
