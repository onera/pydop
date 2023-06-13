
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
from pydop.operations.modules import Module, add, remove, modify
from pydop.operations.modules import register_modules

import sys



def spl_definition():

  epl_fm = FD("epl",
    FDMandatory(
      FD("Lit", default_lit_value=Int())),
    FDOptional(FD("Print"), FD("Eval"), FD("Add")),
  )

  def base_artifact_factory():
    res = Module("EPL")
    @add(res)
    class Exp(object): 
      name = "Exp"
    return res

  epl = SPL(epl_fm, RegistryGraph(), base_artifact_factory)

  # base exp

  @epl.delta("Print")
  def setup_exp_print(variant):
    @add(variant.Exp)
    def toString(self): return variant.Exp.name

  @epl.delta("Eval")
  def setup_exp_eval(variant):
    @add(variant.Exp)
    def toInt(self): return None

  # literals

  @epl.delta("Lit")
  def setup_lit(variant, product):
    default_lit_value = product["default_lit_value"]
    @add(variant)
    class Lit(variant.Exp):
      def __init__(self, x=default_lit_value):
        self.val = x

  @epl.delta(And("Lit", "Print"), after=["setup_lit"])
  def setup_lit_print(variant):
    @add(variant.Lit)
    def toString(self): return f"{self.val}"

  @epl.delta(And("Lit", "Eval"), after=["setup_lit"])
  def setup_lit_eval(variant):
    @add(variant.Lit)
    def toInt(self): return self.val

  # Add

  @epl.delta("Add")
  def setup_add(variant):
    @add(variant)
    class Add(variant.Exp):
      def __init__(self, a, b):
        self.a = a
        self.b = b

  @epl.delta(And("Add", "Print"), after=["setup_add"])
  def setup_add_print(variant):
    @add(variant.Add)
    def toString(self): return f"({self.a.toString()} + {self.b.toString()})"

  @epl.delta(And("Add", "Eval"), after=["setup_add"])
  def setup_add_eval(variant):
    @add(variant.Add)
    def toInt(self): return self.a.toInt() + self.b.toInt()


  return epl



if(__name__ == '__main__'):
  spl = spl_definition()

  conf = {}
  for arg in sys.argv[1:]:
    if("=" in arg):
      arg, val = arg.split("=")
      conf[arg] = int(val)
    else: conf[arg] = True

  conf, err = spl.close_configuration(conf)
  if(err):
    print(err); sys.exit(-1)

  EPL = spl(conf)
  register_modules(EPL)
  from EPL import *

  while True:
    line = input("Please enter an expression or quit:\n")
    if('quit' in line): break
    exp = eval(line)
    print("expression =", exp)
    if(conf["Print"]): print(" print =", exp.toString())
    if(conf["Eval"]):  print(" eval  =", exp.toInt())

