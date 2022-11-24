
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

import networkx as nx
import inspect


###############################################################################
# GENERIC SPL DEFINITION
###############################################################################

def check_default(el, product):
  res = None
  if(callable(el)):
    res = el(product)
  else:
    res = product.get(el, el)
  return res

class SPL(object):

  __slots__ = ("m_check", "m_fm", "m_core", "m_reg")

  def __init__(self, fm, dreg, core=None, fm_check=check_default):
    self.m_check = fm_check 
    self.m_fm = fm
    self.m_reg = dreg
    self.m_core = core

  def __call__(self, product, core=None):
    if(self.m_check(self.m_fm, product)):
      variant = core
      if((variant is None) and (self.m_core is not None)):
        variant = self.m_core.new_instance()

      for delta_f, guard, nb_args in self.m_reg:
        if(self.m_check(guard, product)):
          # print(f"BEGIN {delta_f.__name__}")
          if(nb_args == 0):
            tmp_variant = delta_f()
          elif(nb_args == 1):
            tmp_variant = delta_f(variant)
          else:
            tmp_variant = delta_f(variant, product)
          if(tmp_variant is not None):
            variant = tmp_variant
          # print(f"END {delta_f.__name__}")

      return variant
    else:
      raise Exception("The given configuration is not a valid product for this SPL")


  def delta(self, guard, *args, **kwargs):
    def __inner(delta_f):
      sig = inspect.signature(delta_f)

      nb_args = len(sig.parameters)
      if (nb_args > 2):
        raise Exception(f"number of argument for delta {delta_f.__name__} must be <= 2.")
      self.m_reg.add((delta_f, guard, nb_args), *args, **kwargs)

      return delta_f
    return __inner

  def __getattr__(self, name):
    if(hasattr(self.m_reg, name)):
      return getattr(self.m_reg, name)
    else:
      return object.__getattribute__(self, name)



###############################################################################
# MAIN DELTA REGISTRIES
###############################################################################

##########################################
# Generic graph

class RegistryGraph(object):
  __slots__ = ("m_content",)

  def __init__(self):
    self.m_content = nx.DiGraph()

  def add(self, delta_spec, *args, **kwargs):
    name = kwargs.get("name", delta_spec[0].__name__)
    tmp = self.m_content.nodes.get(name)
    if((tmp is not None) and (tmp.get("spec") is not None)):
      raise Exception(f"ERROR: delta \"{name}\" already declared")
    self.m_content.add_node(name, spec=delta_spec)
    # args and kwargs["after"] are previous nodes
    prevs = tuple(args) + tuple(kwargs.get("after", ()))
    for prev in args:
      self.m_content.add_edge(prev, name)

  def add_order(self, *args):
    def manage_element(el):
      if(isinstance(el, str)): return (el,)
      else: return el
    if(args):
      ds_previous = manage_element(args[0])
      for tmp in args[1:]:
        ds_next = manage_element(tmp)
        for d1 in ds_previous:
          for d2 in ds_next:
            self.m_content.add_edge(d1, d2)
        ds_previous = ds_next

  def __iter__(self):
    for name in nx.topological_sort(self.m_content):
      spec = self.m_content.nodes[name].get("spec")
      if(spec is None):
        raise Exception(f"ERROR: delta \"{name}\" not declared")
      yield spec


##########################################
# Categories

class RegistryCategory(object):
  __slots__ = ("m_content", "m_categories", "m_get",)

  def __init__(self, categories, get_categories):
    self.m_categories = tuple(*categories)
    self.m_get = get_categories
    self.m_content = {c: [] for c in self.m_categories}

  def add(self, delta_spec, *args, **kwargs):
    cat = self.m_get(delta_spec[0], *args, **kwargs)
    l = self.m_content.get(cat)
    if(l is None):
      raise Exception(f"ERROR: category \"{cat}\" not declared")
    l.append(delta_spec)

  def __iter__(self):
    for cat in self.m_categories:
      for el in self.m_content[cat]:
        yield el

