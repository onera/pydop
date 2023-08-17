
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
This file implements the Multi-Lingual Hello World Product Line described in
 [1] Dave Clarke, Radu Muschevici, José Proença, Ina Schaefer, and Rudolf Schlatte.
     2010. Variability Modelling in the ABS Language.
     In FMCO (LNCS, Vol. 6957). Springer, 204–224.
     10.1007/978-3-642-25271-6_11
"""

from pydop.fm_constraint import *
from pydop.fm_diagram import *
from pydop.spl import SPL, RegistryGraph
from pydop.operations.modules import *

import sys


def spl_definition():
  fm = FD("HelloWorld",
   FDMandatory(
    FD("Language",
     FDAlternative(
      FD("English"), FD("Dutch"),
      FD("German")
   ))),
   FDOptional(
    FD("Repeat", times=Int(0,1000))
  ))


  def base_artifact_factory():
   res = Module("HW")
   @add(res)
   class Greeter(object):
     def sayHello(self): return "Hello World"
   return res

  spl = SPL(fm, RegistryGraph(), base_artifact_factory)


  def Nl(module):
   @modify(module.Greeter)
   def sayHello(self): return "Hallo wereld"

  def De(module):
   @modify(module.Greeter)
   def sayHello(self): return "Hallo Welt"

  def Rpt(module, product):
   @modify(module.Greeter)
   def sayHello(self):
    tmp_str = self.original()
    return " ".join(tmp_str for _ in range(product["times"]))


  spl.delta("Dutch")(Nl)
  spl.delta("German")(De)
  spl.delta("Repeat", after=["Nl", "De"])(Rpt)

  return spl



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

  HW = spl(conf)
  print(HW.Greeter().sayHello())

