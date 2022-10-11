
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


from pydop.spl import SPL, RegistryGraph
from pydop.fm_diagram import *
from pydop.operations.modules import VariantModules

import sys

if(__name__ == "__main__"):
  epl_fm = FD("epl",
    FDAnd(FD("Lit", default_lit_value=Int())),
    FDAny("Print", "Eval"),
    FDAny("Add")
  )
  epl = SPL(epl_fm, RegistryGraph(), VariantModules("EPL"))

  # base exp

  @epl.delta(True)
  def setup_exp(variant):
    @variant.EPL.add
    class Exp(object):
      name = "Exp"

    @variant.EPL.add
    class A(object): pass


  @epl.delta("Print", after=["setup_exp"])
  def setup_exp_print(variant):
    @variant.EPL.Exp.add
    def toString(self): return variant.EPL.Exp.name

  @epl.delta("Eval", after=["setup_exp"])
  def setup_exp_eval(variant):
    @variant.EPL.Exp.add
    def toInt(self): return None

  # literals

  @epl.delta("Lit", after=["setup_exp"])
  def setup_lit(variant, product):
    default_lit_value = product["default_lit_value"]
    @variant.EPL.add
    class Lit(variant.EPL.Exp, variant.EPL.A):
      __slots__ = ("val",)
      def __init__(self, x=default_lit_value):
        self.val = x

  @epl.delta(And("Lit", "Print"), after=["setup_lit"])
  def setup_lit_print(variant):
    @variant.EPL.Lit.add
    def toString(self): return f"{self.val}"

  @epl.delta(And("Lit", "Eval"), after=["setup_lit"])
  def setup_lit_eval(variant):
    @variant.EPL.Lit.add
    def toInt(self): return self.val

  @epl.delta(And("Lit", "Print", "Eval"), after=["setup_lit_print", "setup_lit_eval"])
  def setup_lit_eval_print(variant):
    @variant.EPL.Lit.modify
    def toInt(self):
      res = original()
      print(self.toString())
      return res

  # Add

  @epl.delta("Add", after=["setup_exp"])
  def setup_add(variant):
    @variant.EPL.add
    class Add(variant.EPL.Exp):
      __slots__ = ("a", "b",)
      def __init__(self, a, b):
        self.a = a
        self.b = b

  @epl.delta(And("Add", "Print"), after=["setup_add"])
  def setup_add_print(variant):
    @variant.EPL.Add.add
    def toString(self): return f"({self.a.toString()} + {self.b.toString()})"

  @epl.delta(And("Add", "Eval"), after=["setup_add"])
  def setup_add_eval(variant):
    @variant.EPL.Add.add
    def toInt(self): return self.a.toInt() + self.b.toInt()



  # Computation of variant

  conf_1 = {"epl": True, "Lit": True, "default_lit_value": 3, "Print": True, "Eval": True, "Add": True}
  variant = epl(conf_1)

  # insertion in the module list
  variant.register_modules()

  # getting the module EPL
  # EPL = sys.modules['EPL']
  import EPL

  l1 = EPL.Lit(1)
  l2 = EPL.Lit(2)
  l3 = EPL.Add(l1, l2)
  print(l3.toString())
  print(l1.toInt())
  print(EPL.Lit().toString())

