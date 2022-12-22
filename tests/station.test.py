
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
from pydop.mspl import MSPL
from pydop.fm_diagram import *
from pydop.operations.modules import VariantModules

import importlib

class W: pass

if(__name__ == "__main__"):

  mspl = MSPL()

  def import_path(spl_id, prod, path=None):
    v = mspl.import_variant(spl_id, prod)
    if(path is None):
      res = W()
      res.__dict__.update(v.m_names)
    else:
      v.register_modules()
      path = path.split(".")
      res = importlib.import_module(path[0])
      for name in path[1:]:
        res = getattr(res, name)
      v.unregister_modules()
    return res

  ##########################################
  # signal SPL

  signals_fm = FD("Signals",
    FDXor(FD("Light"), FD("Form")),
    FDAny(FD("Dir"))
  )
  signals = SPL(signals_fm, RegistryGraph(), VariantModules("signals"))
  mspl.add("signals", signals)

  LSig = { "Signals": True, "Light": True, "Form": False , "Dir": False }

  @signals.delta(True)
  def signal_init(variant):
    @variant.signals.add
    class CSig(object):
      __slots__ = ()

  @signals.delta("Light", after=["signal_init"])
  def LDelta(variant):
    @variant.signals.add
    class CBulb(object):
      __slots__ = ()

    @variant.signals.CSig.add
    def addBulb(self):
      variant.signals.CBulb()

  @signals.delta("Form", after=["signal_init"])
  def FDelta(variant):
    variant.signals.CSig.__slots__ = variant.signals.CSig.__slots__ + ("nextMotorMaintain",)

  @signals.delta("Dir", after=["signal_init"])
  def DDelta(variant):
    @variant.signals.add
    class CDir(object):
      __slots__ = ()

    @variant.signals.CSig.add
    def getDirection(self):
      return variant.signals.CDir()



  ##########################################
  # switches SPL

  switches_fm = FD("Switch",
    FDXor(FD("Electric"), FD("Mechanic")),
  )
  switches = SPL(switches_fm, RegistryGraph(), VariantModules("switches"))
  mspl.add("switches", switches)

  @switches.delta(True)
  def switches_init(variant):
    @variant.switches.add
    class CSwitch(object):
      __slots__ = ()

    @variant.switches.add
    class CTrack(object):
      __slots__ = ()
      def appendSwitch(self):
        sw = variant.switches.CSwitch()
        return sw

  @switches.delta("Electric", after=["switches_init"])
  def EDelta(variant):
    variant.switches.CSwitch.__slots__ = variant.switches.CSwitch.__slots__ + ("nextMotorMaintain",)

  @switches.delta("Mechanic", after=["switches_init"])
  def MDelta(variant):
    @variant.switches.CSwitch.add
    def isMechanic(self):
      return True


  ##########################################
  # interlocking SPL

  interlocking_fm = FD("Interlocking",
    FDAny(FD("Modern"), FD("DirOut"))
  )
  interlocking = SPL(interlocking_fm, RegistryGraph(), VariantModules("InterlockingSys"))
  mspl.add("interlocking", interlocking)


  def PSwitch(product):
    # default correct product
    res = { "Switch": True, "Electric": True, "Mechanic": False }
    if(eval("Modern", product)):
      return res
    else:
      return switches_fm.combine_product(res, {"Mechanic": True})

  def PSignal(product):
    # default correct product
    res = { "Signals": True, "Light": True, "Form": False , "Dir": True }
    if(eval(And("DirOut", "Modern"), product)):
      return res
    elif(eval("Modern", product)):
      return signals_fm.combine_product(res, {"Dir": False})
    elif(eval(And("DirOut", Not("Modern")), product)):
      return signals_fm.combine_product(res, {"Form": True})
    else: signals_fm.combine_product(res, {"Form": True, "Dir": False})


  @interlocking.delta(True)
  def interlocking_init(variant, product):
    @variant.InterlockingSys.add
    class CILS(object):
      def testSig(self):
        p1 = { "Switch": True, "Electric": True, "Mechanic": False }
        p2 = { "Switch": True, "Electric": False, "Mechanic": True }

        swNormal = import_path("switches", p1, "switches").CSwitch()
        track = import_path("switches", p2, "switches").CTrack()
        swNew = track.appendSwitch ()


        p3 = { "Signals": True, "Light": False, "Form": True , "Dir": False }

        sigNormal = import_path("signals", LSig, "signals").CSig()
        sigShunt  = import_path("signals", p3, "signals").CSig()

        return sigNormal.eqAspect(sigShunt)

      def createSwitch(self):
        switches_prod = PSwitch(product)
        return import_path("switches", switches_prod, "switches").CSwitch()

      def createOutSignal(self):
        signals_prod = PSignal(product)
        return import_path("signals", signals_prod, "signals").CSig()

      def createInSignal(self):
        signals_prod = PSignal(product)
        signals_prod = signals_fm.combine_product(signals_prod, {"Dir": False})
        return import_path("signals", signals_prod, "signals").CSig()


  ##########################################
  # railway station

  interlocking_prod = { "Interlocking": True, "Modern": False, "DirOut": False }

  p1, err1 = interlocking_fm.close_configuration(interlocking_prod, {"DirOut": True})
  p2, err2 = interlocking_fm.close_configuration(interlocking_prod, {"Modern": True})
  ils1 = import_path("interlocking", p1, "InterlockingSys").CILS()
  ils2 = import_path("interlocking", p2, "InterlockingSys").CILS()

  print(f"type(ils1) = {type(ils1)}")
  print(f"type(ils2) = {type(ils2)}")
  print(f"type(ils1) == type(ils2): {type(ils1) == type(ils2)}")

  ils3 = import_path("interlocking", p1, "InterlockingSys").CILS()
  ils4 = import_path("interlocking", p2, "InterlockingSys").CILS()

  print(f"type(ils1) == type(ils3): {type(ils1) == type(ils3)}")
  print(f"type(ils2) == type(ils4): {type(ils2) == type(ils4)}")

  ils5 = import_path("interlocking", p1).InterlockingSys.CILS()
  ils6 = import_path("interlocking", p2).InterlockingSys.CILS()

  print(f"type(ils1) == type(ils5): {type(ils1) == type(ils5)}")
  print(f"type(ils2) == type(ils6): {type(ils2) == type(ils6)}")
