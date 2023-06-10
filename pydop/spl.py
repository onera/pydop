
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
import inspect
import typing

import networkx as nx


from pydop.fm_result import decl_errors__c, eval_result__c
from pydop.fm_configuration import configuration__c
from pydop.fm_constraint import Lit
# from pydop.fm_diagram import decl_errors__c, _configuration__c, _fd__c


###############################################################################
# EXPECTED API
###############################################################################


# for constraints

# class constraint__proto(typing.Protocol):
#   def __call__(self, p: typing.Union[dict, configuration__c]) -> eval_result__c: pass

# # for feature models


# T = typing.TypeVar('T')
# class feature_model_proto(typing.Protocol):
#   # declaration part
#   def check(self) -> decl_errors__c: pass
#   def link_constraint(self, c: constraint__proto ) -> tuple[constraint__proto, decl_errors__c]: pass
#   def link_configuration(self, p: typing.Union[dict, configuration__c]) -> tuple[configuration__c, decl_errors__c]: pass
#   # check part
#   def __call__(self, p: typing.Union[dict, configuration__c]) -> eval_result__c




###############################################################################
# GENERIC SPL DEFINITION
###############################################################################

class SPL(object):

  __slots__ = ("m_fm", "m_bm_factory", "m_reg",)

  def __init__(self, fm, dreg, bm_factory=None):
    errors = fm.check()
    if(bool(errors)):
      raise ValueError(errors)
    self.m_fm = fm
    self.m_reg = dreg
    self.m_bm_factory = bm_factory


  def link_constraint(self, c):
    return self.m_fm.link_constraint(c)

  def link_configuration(self, conf):
    return self.m_fm.link_configuration(conf)

  def close_configuration(self, *confs):
    return self.m_fm.close_configuration(*confs)

  def __call__(self, conf, bm=None):
    if(not isinstance(conf, configuration__c)):
      conf, errors = self.close_configuration(conf)
      if(bool(errors)):
        raise ValueError(errors)
    is_product = self.m_fm(conf)
    if(bool(is_product)):
      variant = bm
      if((variant is None) and (self.m_bm_factory is not None)):
        variant = self.m_bm_factory()

      for delta_f, guard, nb_args in self.m_reg:
        act = guard(conf)
        # print(f"checking delta \"{delta_f.__name__}\" ({guard}) -> {type(act)}:{bool(act)}")
        if(act):
          # print(f"BEGIN {delta_f.__name__}")
          if(nb_args == 0):
            tmp_variant = delta_f()
          elif(nb_args == 1):
            tmp_variant = delta_f(variant)
          else:
            tmp_variant = delta_f(variant, conf)
          if(tmp_variant is not None):
            variant = tmp_variant
          # print(f"END {delta_f.__name__}")

      return variant
    else:
      raise Exception(f"The given configuration is not a valid product for this SPL:\n{is_product.m_reason}")


  def delta(self, guard, *args, **kwargs):
    def __inner(delta_f):
      nonlocal guard
      guard, errors = self.m_fm.link_constraint(guard)
      if(bool(errors)):
        raise Exception(f"ERROR in guard of delta {delta_f.__name__}:\n{str(errors)}")
      sig = inspect.signature(delta_f)
      # print(f"Guard for delta \"{delta_f.__name__}\" = {guard}")

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
    for prev in itertools.chain(args, kwargs.get("after", ())):
      # print(f"  adding edge {prev} -> {name}")
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

