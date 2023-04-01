
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
from pydop.operations.modules import VariantModule

import importlib


##########################################
# utils


def spl_factory(spl_id, fm):
  return SPL(fm, RegistryGraph(), VariantModule(spl_id))



def test_station():
  print("==========================================")
  print("= test_station")

  mspl = MSPL(spl_factory=spl_factory)

  ##########################################
  # signal SPL

  signals_fm = FD("Signals",
    FDXor(FD("Light"), FD("Form")),
    FDAny(FD("Dir"))
  )
  signals = mspl.new("signals", signals_fm)

  LSig = { "Signals": True, "Light": True, "Form": False , "Dir": False }

  @signals.delta(True)
  def signal_init(variant):
    @variant.add
    class CSig(object):
      __slots__ = ()

  @signals.delta("Light", after=["signal_init"])
  def LDelta(variant):
    @variant.add
    class CBulb(object):
      __slots__ = ()

    @variant.CSig.add
    def addBulb(self):
      variant.signals.CBulb()

  @signals.delta("Form", after=["signal_init"])
  def FDelta(variant):
    variant.CSig.__slots__ = variant.CSig.__slots__ + ("nextMotorMaintain",)

  @signals.delta("Dir", after=["signal_init"])
  def DDelta(variant):
    @variant.add
    class CDir(object):
      __slots__ = ()

    @variant.CSig.add
    def getDirection(self):
      return variant.CDir()



  ##########################################
  # switches SPL

  switches_fm = FD("Switch",
    FDXor(FD("Electric"), FD("Mechanic")),
  )
  switches = mspl.new("switches", switches_fm)

  @switches.delta(True)
  def switches_init(variant):
    @variant.add
    class CSwitch(object):
      __slots__ = ()

    @variant.add
    class CTrack(object):
      __slots__ = ()
      def appendSwitch(self):
        sw = variant.CSwitch()
        return sw

  @switches.delta("Electric", after=["switches_init"])
  def EDelta(variant):
    variant.CSwitch.__slots__ = variant.CSwitch.__slots__ + ("nextMotorMaintain",)

  @switches.delta("Mechanic", after=["switches_init"])
  def MDelta(variant):
    @variant.CSwitch.add
    def isMechanic(self):
      return True


  ##########################################
  # interlocking SPL

  interlocking_fm = FD("Interlocking",
    FDAny(FD("Modern"), FD("DirOut"))
  )
  interlocking = mspl.new("interlocking", interlocking_fm)

  def PSwitch(product):
    # default correct product
    res = { "Switch": True, "Electric": True, "Mechanic": False }
    if(not product["Modern"]):
      res, errors = switches_fm.close_configuration(res, {"Mechanic": True})
      # no error can actually occur
    return res

  def PSignal(product):
    # default correct product
    res = { "Signals": True, "Light": True, "Form": False , "Dir": True }
    if(And("DirOut", "Modern")(product)):
      pass
    elif(product["Modern"]):
      res, errors =  signals_fm.close_configuration(res, {"Dir": False})
    elif(And("DirOut", Not("Modern"))(product)):
      res, errors =  signals_fm.close_configuration(res, {"Form": True})
    else:
      res, errors = signals_fm.close_configuration(res, {"Form": True, "Dir": False})
    return res


  @interlocking.delta(True)
  def interlocking_init(variant, product):
    @variant.add
    class CILS(object):
      def testSig(self):
        p1 = { "Switch": True, "Electric": True, "Mechanic": False }
        p2 = { "Switch": True, "Electric": False, "Mechanic": True }

        swNormal = mspl["switches", p1].CSwitch()
        track = mspl["switches", p2].CTrack()
        swNew = track.appendSwitch ()


        p3 = { "Signals": True, "Light": False, "Form": True , "Dir": False }

        sigNormal = mspl["signals", LSig].CSig()
        sigShunt  = mspl["signals", p3].CSig()

        return sigNormal.eqAspect(sigShunt)

      def createSwitch(self):
        switches_prod = PSwitch(product)
        return mspl["switches", switches_prod].CSwitch()

      def createOutSignal(self):
        signals_prod = PSignal(product)
        return mspl["signals", signals_prod].CSig()

      def createInSignal(self):
        signals_prod = PSignal(product)
        signals_prod = signals_fm.combine_product(signals_prod, {"Dir": False})
        return mspl["signals", signals_prod].CSig()


  ##########################################
  # railway station

  interlocking_prod = { "Interlocking": True, "Modern": False, "DirOut": False }

  p1, err1 = interlocking_fm.close_configuration(interlocking_prod, {"DirOut": True})
  p2, err2 = interlocking_fm.close_configuration(interlocking_prod, {"Modern": True})

  # testing mspl getters with spl_id
  ils1 = mspl["interlocking", p1].CILS()
  ils2 = mspl["interlocking", p2].CILS()

  print(f"type(ils1) = {type(ils1)}")
  print(f"type(ils2) = {type(ils2)}")
  print(f"type(ils1) == type(ils2): {type(ils1) == type(ils2)}")

  # testing mspl getters with spl object
  ils3 = mspl[interlocking, p1].CILS()
  ils4 = mspl[interlocking, p2].CILS()

  print(f"type(ils1) == type(ils3): {type(ils1) == type(ils3)}")
  print(f"type(ils2) == type(ils4): {type(ils2) == type(ils4)}")

  ils5 = mspl["interlocking", p1].CILS()
  ils6 = mspl["interlocking", p2].CILS()

  print(f"type(ils1) == type(ils5): {type(ils1) == type(ils5)}")
  print(f"type(ils2) == type(ils6): {type(ils2) == type(ils6)}")



if(__name__ == "__main__"):
  test_station()
