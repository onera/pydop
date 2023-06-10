
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
This file contains
 - the class `SPL`, that implements Delta-Oriented SPLs
 - the class `RegistryGraph`, that implements delta-ordering for the [1] and [2] approaches to construct the Configuration Knowledge
 - the class `RegistryCategory` that orders delta w.r.t. to some user-defined categories
[1] Dave Clarke, Radu Muschevici, José Proença, Ina Schaefer, and Rudolf Schlatte.
    2010. Variability Modelling in the ABS Language.
    In FMCO (LNCS, Vol. 6957). Springer, 204–224.
[2] Ferruccio Damiani, Reiner Hähnle, Eduard Kamburjan, Michael Lienhardt, and Luca Paolini.
    2023. Variability modules.
    In J. Syst. Softw. 195 (2023), 111510.
"""

import itertools
import inspect
from collections import namedtuple

import networkx as nx

from pydop.fm_result import decl_errors__c, eval_result__c
from pydop.fm_configuration import configuration__c


###############################################################################
# GENERIC SPL DEFINITION
###############################################################################

class SPL(object):
  """
SPL(FM, ordering) -> SPL
SPL(FM, ordering, base_module_factory) -> SPL

Creates an new Delta-Oriented SPLs with the input Feature Model `fm`, delta-ordering object `order` and base module factory in parameter `bmf`.
Deltas can be registered later to the SPL when constructing the SPL's Configuration Knowledge.
This CK is constructed with ith the `delta` method which in turns calls the `add` method of `order`,
 and optionally, with other methods of that object.
The `order` object is accessible from the SPL with the `ordering` attribute.

Variant generation is done by simply calling the SPL with a valid product.
  """

  __slots__ = ("m_fm", "m_bm_factory", "m_reg",)

  def __init__(self, fm, dreg, bm_factory=None):
    """parameters:
  fm: the feature model of the SPL (can be an object of any class with the same API of the `fm_diagram._fd__c` class)
  dreg: the ordering object of the SPL (can be an object of any class with an `add` and `__iter__` methods like the `spl.RegistryCategory` class)
  bm_factory: an optional factory (i.e., a function () -> object) generating the base module of the SPL
    """
    # 1. ensures that the feature model is correctly constructed
    errors = fm.check()
    if(bool(errors)):
      raise ValueError(errors)
    # 2. setup the SPL
    self.m_fm = fm
    self.m_reg = dreg
    self.m_bm_factory = bm_factory

  @property
  def ordering(self): return self.m_reg


  def link_constraint(self, c):
    """Simple alias to the `link_constraint` method of the feature model"""
    return self.m_fm.link_constraint(c)

  def link_configuration(self, conf):
    """Simple alias to the `link_configuration` method of the feature model"""
    return self.m_fm.link_configuration(conf)

  def close_configuration(self, *confs):
    """Simple alias to the `close_configuration` method of the feature model"""
    return self.m_fm.close_configuration(*confs)

  def __call__(self, conf, bm=None):
    """Variant Generation
parameters:
  conf: the product triggering the variant generation (can be a dictionary, or a `fm_configuration.configuration__c` object)
  bm: an optional base module. If this parameter is provided, the bm_factory will not be used.
      Moreover, if bm and bm_factory are not provided, the bm is set to None
"""
    # 1. check that the conf parameter is a valid product of the SPL
    if(not isinstance(conf, configuration__c)):
      conf, errors = self.close_configuration(conf)
      if(bool(errors)):
        raise ValueError(errors)
    is_product = self.m_fm(conf)
    # 2. generate the variant
    if(bool(is_product)):
      # 2.1. get the base module
      variant = bm
      if((variant is None) and (self.m_bm_factory is not None)):
        variant = self.m_bm_factory()

      # 2.2. iterate over all delta and execute the activated ones
      for delta_f, guard, _, nb_args in self.m_reg:
        act = guard(conf)
        # print(f"checking delta \"{delta_f.__name__}\" ({guard}) -> {type(act)}:{bool(act)}")
        if(act):
          # executes the delta with the correct numbers of parameters
          # and manages its return value: if not None, it is the updated version of the variant
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
    """Delta Registration: this method registers a function as a delta of the SPL, and setup the SPL's CK.
This method is structurated to be used as a decorator to the function to be registered as a delta:
 it returns a function that does perform the registration
Parameters:
  guard: the activation condition of the delta (can be an object of any class with the same API of the `fm_constraint._expbool__c` class)
  args: additional non keyworded arguments for the `order` object
  kwargs: additional keyworded arguments for the `order` object
          moreover, the keyword `"name"` sets the name of the delta (by default, the name of the function is used)
    """
    def __inner(delta_f):
      nonlocal guard
      # 1. ensures that the guard is well formed
      guard, errors = self.m_fm.link_constraint(guard)
      if(bool(errors)):
        raise Exception(f"ERROR in guard of delta {delta_f.__name__}:\n{str(errors)}")

      # 2. ensures the delta has the correct numbers of parameters
      sig = inspect.signature(delta_f)
      nb_args = len(sig.parameters)
      if (nb_args > 2):
        raise Exception(f"number of argument for delta {delta_f.__name__} must be <= 2.")

      # 3. registers the delta
      delta_name = kwargs.get("name", delta_f.__name__) # get the name of the delta
      self.m_reg.add(delta_info_cls(delta_f, guard, delta_name, nb_args), *args, **kwargs)

      return delta_f
    return __inner

delta_info_cls = namedtuple("delta_info_cls", ("delta", "guard", "name", "nb_args"))


###############################################################################
# MAIN DELTA REGISTRIES
###############################################################################

##########################################
# Generic graph

class RegistryGraph(object):
  """Implements a delta ordering using a networkx graph"""
  __slots__ = ("m_content",)

  def __init__(self):
    self.m_content = nx.DiGraph()

  def add(self, delta_info, *args, **kwargs):
    """Adds a delta to the order
Parameters:
  delta_info a tuple (delta, guard, nb_args) giving the delta to add (the tuple is create by the `SPL.delta` method)
  args: additional non keyworded arguments: deltas that must be executed before this one
  kwargs: the keyword `"after"` indicates which deltas must be executed before this one
    """
    name = delta_info.name
    # 1. check that the delta does not already exist
    tmp = self.m_content.nodes.get(name)
    if((tmp is not None) and (tmp.get("spec") is not None)):
      raise Exception(f"ERROR: delta \"{name}\" already declared")
    # 2. add the delta
    self.m_content.add_node(name, spec=delta_info)
    # 3. add the ordering relation
    for prev in itertools.chain(self._manage_element__(args), self._manage_element__(kwargs.get("after", ()))):
      # print(f"  adding edge {prev} -> {name}")
      self.m_content.add_edge(prev, name)

  def add_order(self, *args):
    """Adds new ordering constraints between the delta
Parameters:
  args: a list of delta names or list of delta names.
Example:
  add_order(("d1", "d2"), "d3", ("d4", "d5")) states that:
   - "d1" and "d2" must be executed before "d3"
   - and "d3" must be executed before "d4" and "d5"
    """
    if(len(args) > 1):
      ds_previous = tuple(self._manage_element__(args[0]))
      for tmp in args[1:]:
        ds_next = tuple(self._manage_element__(tmp))
        for d1 in ds_previous:
          for d2 in ds_next:
            # print(f"  adding edge {d1} -> {d2}")
            self.m_content.add_edge(d1, d2)
        ds_previous = ds_next

  @staticmethod
  def _manage_element__(el):
    if(isinstance(el, (tuple, list, set))):
      for sub in el: 
        yield from RegistryGraph._manage_element__(sub)
    elif(isinstance(el, str)):
      yield el
    elif(inspect.isfunction(el)):
      yield el.__name__

  def __iter__(self):
    """Yields all the registered deltas in an order compatible with the user specification"""
    for name in nx.topological_sort(self.m_content):
      spec = self.m_content.nodes[name].get("spec")
      if(spec is None):
        raise Exception(f"ERROR: delta \"{name}\" not declared")
      yield spec


##########################################
# Categories

class RegistryCategory(object):
  """Implements a delta ordering by associating to each delta a category (the categories are totally ordered by the user)"""
  __slots__ = ("m_content", "m_categories", "m_get", "m_delta_names")

  def __init__(self, categories, get_categories):
    self.m_categories = tuple(*categories)
    self.m_get = get_categories
    self.m_content = {c: [] for c in self.m_categories}
    self.m_delta_names = set()

  def add(self, delta_info, *args, **kwargs):
    """Adds a delta to the order
Parameters:
  delta_info a tuple (delta, guard, nb_args) giving the delta to add (the tuple is create by the `SPL.delta` method)
  args: additional non keyworded arguments: deltas that must be executed before this one
  kwargs: the keyword `"after"` indicates which deltas must be executed before this one
    """
    name = delta_info.name
    # 1. check that the delta does not already exist
    if(name in self.m_delta_names):
      raise Exception(f"ERROR: delta \"{name}\" already declared")
    # 2. get the category of the delta
    cat = self.m_get(name, *args, **kwargs)
    l = self.m_content.get(cat)
    if(l is None):
      raise Exception(f"ERROR: category \"{cat}\" not declared")
    # 3. add the delta
    l.append(delta_info)
    self.m_delta_names.add(name)


  def __iter__(self):
    """Yields all the registered deltas in an order compatible with the order of the categories given by the user"""
    for cat in self.m_categories:
      for el in self.m_content[cat]:
        yield el

