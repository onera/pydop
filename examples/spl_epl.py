
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
This file implements the Expression Product Line described in
 [1] Ina Schaefer, Lorenzo Bettini, Viviana Bono, Ferruccio Damiani, and Nico Tanzarella.
     2010. Delta-Oriented Programming of Software Product Lines.
     In Software Product Lines: Going Beyond (SPLC 2010) (LNCS, Vol. 6287). 77–91.
     https://doi.org/10.1007/978-3-642-15579-6_6
"""


from pydop.spl import SPL, RegistryGraph
from pydop.fm_constraint import *
from pydop.fm_diagram import *
from pydop.operations.modules import VariantModule, VariantModules, register_modules, unregister_modules

import sys


def get_fm():
  return FD("epl",
    FDAnd(FD("Lit", default_lit_value=Int())),
    FDAny(FD("Print"), FD("Eval")),
    FDAny(FD("Add"))
  )

def test_epl_single():
  print("==========================================")
  print("= test_epl_single")

  epl_fm = get_fm()
  epl = SPL(epl_fm, RegistryGraph(), VariantModule("EPL"))

  # base exp

  @epl.delta(True)
  def setup_exp(variant):
    @variant.add
    class Exp(object):
      name = "Exp"

    @variant.add
    class A(object): pass


  @epl.delta("Print", after=["setup_exp"])
  def setup_exp_print(variant):
    @variant.Exp.add
    def toString(self): return variant.Exp.name

  @epl.delta("Eval", after=["setup_exp"])
  def setup_exp_eval(variant):
    @variant.Exp.add
    def toInt(self): return None

  # literals

  @epl.delta("Lit", after=["setup_exp"])
  def setup_lit(variant, product):
    default_lit_value = product["default_lit_value"]
    @variant.add
    class Lit(variant.Exp, variant.A):
      # __slots__ = ("val",) <= incomatible with class copying
      def __init__(self, x=default_lit_value):
        self.val = x

  @epl.delta(And("Lit", "Print"), after=["setup_lit"])
  def setup_lit_print(variant):
    @variant.Lit.add
    def toString(self): return f"{self.val}"

  @epl.delta(And("Lit", "Eval"), after=["setup_lit"])
  def setup_lit_eval(variant):
    @variant.Lit.add
    def toInt(self): return self.val

  @epl.delta(And("Lit", "Print", "Eval"), after=["setup_lit_print", "setup_lit_eval"])
  def setup_lit_eval_print(variant):
    @variant.Lit.modify
    def toInt(self):
      res = original()
      # print(self.toString())
      return res

  # Add

  @epl.delta("Add", after=["setup_exp"])
  def setup_add(variant):
    @variant.add
    class Add(variant.Exp):
      # __slots__ = ("a", "b",) <= incomatible with class copying
      def __init__(self, a, b):
        self.a = a
        self.b = b

  @epl.delta(And("Add", "Print"), after=["setup_add"])
  def setup_add_print(variant):
    @variant.Add.add
    def toString(self): return f"({self.a.toString()} + {self.b.toString()})"

  @epl.delta(And("Add", "Eval"), after=["setup_add"])
  def setup_add_eval(variant):
    @variant.Add.add
    def toInt(self): return self.a.toInt() + self.b.toInt()



  # Computation of variant

  conf_1 = {"epl": True, "Lit": True, "default_lit_value": 3, "Print": True, "Eval": True, "Add": True}
  variant = epl(conf_1)

  # insertion in the module list
  register_modules(variant)

  # getting the module EPL
  # EPL = sys.modules['EPL']
  import EPL

  l1 = EPL.Lit(1)
  l2 = EPL.Lit(2)
  l3 = EPL.Add(l1, l2)
  print(l3.toString())
  print(l1.toInt())
  print(EPL.Lit().toString())



def test_epl_multiple():
  print("==========================================")
  print("= test_epl_multiple")

  epl_fm = get_fm()
  epl = SPL(epl_fm, RegistryGraph(), VariantModules("EPL"))

  # base exp

  @epl.delta(True)
  def setup_exp(variant):
    @variant.add
    class Exp(object):
      name = "Exp"

    @variant.add
    class A(object): pass


  @epl.delta("Print", after=["setup_exp"])
  def setup_exp_print(variant):
    @variant.Exp.add
    def toString(self): return variant.Exp.name

  @epl.delta("Eval", after=["setup_exp"])
  def setup_exp_eval(variant):
    @variant.Exp.add
    def toInt(self): return None

  # literals

  @epl.delta("Lit", after=["setup_exp"])
  def setup_lit(variant, product):
    default_lit_value = product["default_lit_value"]
    @variant.add
    class Lit(variant.Exp, variant.A):
      # __slots__ = ("val",) <= incomatible with class copying
      def __init__(self, x=default_lit_value):
        self.val = x

  @epl.delta(And("Lit", "Print"), after=["setup_lit"])
  def setup_lit_print(variant):
    @variant.Lit.add
    def toString(self): return f"{self.val}"

  @epl.delta(And("Lit", "Eval"), after=["setup_lit"])
  def setup_lit_eval(variant):
    @variant.Lit.add
    def toInt(self): return self.val

  @epl.delta(And("Lit", "Print", "Eval"), after=["setup_lit_print", "setup_lit_eval"])
  def setup_lit_eval_print(variant):
    @variant.Lit.modify
    def toInt(self):
      res = original()
      # print(self.toString())
      return res

  # Add

  @epl.delta("Add", after=["setup_exp"])
  def setup_add(variant):
    @variant.add
    class Add(variant.Exp):
      # __slots__ = ("a", "b",) <= incomatible with class copying
      def __init__(self, a, b):
        self.a = a
        self.b = b

  @epl.delta(And("Add", "Print"), after=["setup_add"])
  def setup_add_print(variant):
    @variant.Add.add
    def toString(self): return f"({self.a.toString()} + {self.b.toString()})"

  @epl.delta(And("Add", "Eval"), after=["setup_add"])
  def setup_add_eval(variant):
    @variant.Add.add
    def toInt(self): return self.a.toInt() + self.b.toInt()



  # Computation of variant

  conf_1 = {"epl": True, "Lit": True, "default_lit_value": 3, "Print": True, "Eval": True, "Add": True}
  variant = epl(conf_1)

  # insertion in the module list
  register_modules(variant)

  # getting the module EPL
  # EPL = sys.modules['EPL']
  import EPL

  l1 = EPL.Lit(1)
  l2 = EPL.Lit(2)
  l3 = EPL.Add(l1, l2)
  print(l3.toString())
  print(l1.toInt())
  print(EPL.Lit().toString())

if(__name__ == "__main__"):
  test_epl()
