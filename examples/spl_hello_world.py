
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


def gen_base_artifact():
 res = Module("HW")
 @add(res)
 class Greater(object):
   def sayHello(self): return "Hello World"
 return res
spl = SPL(fm, RegistryGraph(), gen_base_artifact)


def Nl(module):
 @modify(module.Greater)
 def sayHello(self): return "Hallo wereld"

def Rpt(module, product):
 @modify(module.Greater)
 def sayHello(self):
  tmp_str = self.original()
  return " ".join(tmp_str for _ in range(product["times"]))

def De(module):
 @modify(module.Greater)
 def sayHello(self): return "Hallo Welt"


spl.delta("Dutch")(Nl)
spl.delta("German")(De)
spl.delta("Repeat", after=["Nl", "De"])(Rpt)

conf, err = spl.close_configuration({"English": True, "Repeat": True}, {"Dutch": True})
if(err):
  print(err); sys.exit(-1)

try:
  hw_duch_4 = spl(conf)
except Exception as e:
  print(e); sys.exit(-1)
 
print(hw_duch_4.Greater().sayHello())

