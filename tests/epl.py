
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
from pydop.variant_module import VariantModules

import sys

if(__name__ == "__main__"):
  epl_fm = FD("epl",
    FDAnd("Lit"),
    FDAny("Print", "Eval"),
    FDAny("Add")
  )
  epl = SPL(epl_fm, RegistryGraph(), VariantModules("EPL"))

  # base exp

  @epl.delta(True)
  def setup_exp(variant):
    class Exp(object):
      name = "Exp"
    variant.EPL.Exp = Exp

  @epl.delta("Print", after=["setup_exp"])
  def setup_exp_print(variant):
    def toString(self): return variant.EPL.Exp.name
    setattr(variant.EPL.Exp, "toString", toString)

  @epl.delta("Eval", after=["setup_exp"])
  def setup_exp_eval(variant):
    def toInt(self): return None
    setattr(variant.EPL.Exp, "toInt", toInt)

  # literals

  @epl.delta("Lit", after=["setup_exp"])
  def setup_lit(variant):
    class Lit(variant.EPL.Exp):
      __slots__ = ("val",)
      def __init__(self, x=None):
        self.val = x
    variant.EPL.Lit = Lit

  @epl.delta("Print", after=["setup_lit"])
  def setup_lit_print(variant):
    def toString(self): return f"{self.val}"
    setattr(variant.EPL.Lit, "toString", toString)

  @epl.delta("Eval", after=["setup_lit"])
  def setup_lit_eval(variant):
    def toInt(self): return self.val
    setattr(variant.EPL.Lit, "toInt", toInt)

  # Add

  @epl.delta("Add", after=["setup_exp"])
  def setup_add(variant):
    class Add(variant.EPL.Exp):
      __slots__ = ("a", "b",)
      def __init__(self, a, b):
        self.a = a
        self.b = b
    variant.EPL.Add = Add

  @epl.delta(And("Add", "Print"), after=["setup_add"])
  def setup_add_print(variant):
    def toString(self): return f"({self.a.toString()} + {self.b.toString()})"
    setattr(variant.EPL.Add, "toString", toString)

  @epl.delta(And("Add", "Eval"), after=["setup_add"])
  def setup_add_eval(variant):
    def toInt(self): return self.a.toInt() + self.b.toInt()
    setattr(variant.EPL.Add, "toInt", toInt)



  # Computation of variant

  conf_1 = {"epl": True, "Lit": True, "Print": False, "Eval": True, "Add": True}
  variant = epl.apply(conf_1)

  # insertion in the module list
  variant.import_modules()

  # getting the module EPL
  EPL = sys.modules['EPL']

  l1 = EPL.Lit(1)
  l2 = EPL.Lit(2)
  l3 = EPL.Add(l1, l2)
  print(l3.toInt())
