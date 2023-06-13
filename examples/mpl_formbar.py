
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
This file implements the FormbaR Statechart Multi-Product Line described in
 [1] Ferruccio Damiani, Reiner Hähnle, Eduard Kamburjan, Michael Lienhardt, and Luca Paolini.
     2023. Variability modules.
     In J. Syst. Softw. 195 (2023), 111510.
     https://doi.org/10.1016/j.jss.2022.111510
"""


from pydop.spl import SPL, RegistryGraph
from pydop.mpl import MPL
from pydop.fm_constraint import *
from pydop.fm_diagram import *
from pydop.operations.modules import Module, add, remove, modify

import sys


def mpl_definition():

  def spl_factory(spl_id, fm):
    return SPL(fm, RegistryGraph(), lambda:Module(spl_id))

  mpl = MPL(spl_factory=spl_factory)


  ##########################################
  # signal SPL

  signals_fm = FD("Signals",
    FDXor(FD("Light"), FD("Form")),
    FDAny(FD("Dir"))
  )
  signals = mpl.new("signals", signals_fm)

  LSig = { "Signals": True, "Light": True, "Form": False , "Dir": False }

  @signals.delta(True)
  def signal_init(variant):
    @add(variant)
    class CSig(object):
      __slots__ = ()
      def eqAspect(self, other): return False # implementation not provided in the paper

  @signals.delta("Light", after=["signal_init"])
  def LDelta(variant):
    @add(variant)
    class CBulb(object):
      __slots__ = ()

    @add(variant.CSig)
    def addBulb(self):
      variant.signals.CBulb()

  @signals.delta("Form", after=["signal_init"])
  def FDelta(variant):
    variant.CSig.__slots__ = variant.CSig.__slots__ + ("nextMotorMaintain",)

  @signals.delta("Dir", after=["signal_init"])
  def DDelta(variant):
    @add(variant)
    class CDir(object):
      __slots__ = ()

    @add(variant.CSig)
    def getDirection(self):
      return variant.CDir()


  ##########################################
  # switches SPL

  switches_fm = FD("Switch",
    FDXor(FD("Electric"), FD("Mechanic")),
  )
  switches = mpl.new("switches", switches_fm)

  @switches.delta(True)
  def switches_init(variant):
    @add(variant)
    class CSwitch(object):
      __slots__ = ()

    @add(variant)
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
    @add(variant.CSwitch)
    def isMechanic(self):
      return True


  ##########################################
  # interlocking SPL

  interlocking_fm = FD("Interlocking",
    FDAny(FD("Modern"), FD("DirOut"))
  )
  interlocking = mpl.new("interlocking", interlocking_fm)

  def PSwitch(product):
    # default correct product
    res = { "Switch": True, "Electric": True, "Mechanic": False }
    if(not product["Modern"]):
      res, errors = switches.close_configuration(res, {"Mechanic": True})
      # no error can actually occur
    return res

  def PSignal(product):
    # default correct product
    res = { "Signals": True, "Light": True, "Form": False , "Dir": True }
    if(And("DirOut", "Modern")(product)):
      pass
    elif(product["Modern"]):
      res, errors =  signals.close_configuration(res, {"Dir": False})
    elif(And("DirOut", Not("Modern"))(product)):
      res, errors =  signals.close_configuration(res, {"Form": True})
    else:
      res, errors = signals.close_configuration(res, {"Form": True, "Dir": False})
    return res


  @interlocking.delta(True)
  def interlocking_init(variant, product):
    @add(variant)
    class CILS(object):
      def testSig(self):
        p1 = { "Switch": True, "Electric": True, "Mechanic": False }
        p2 = { "Switch": True, "Electric": False, "Mechanic": True }

        swNormal = mpl["switches", p1].CSwitch()
        track = mpl["switches", p2].CTrack()
        swNew = track.appendSwitch ()


        p3 = { "Signals": True, "Light": False, "Form": True , "Dir": False }

        sigNormal = mpl["signals", LSig].CSig()
        sigShunt  = mpl["signals", p3].CSig()

        return sigNormal.eqAspect(sigShunt)

      def createSwitch(self):
        switches_prod = PSwitch(product)
        return mpl["switches", switches_prod].CSwitch()

      def createOutSignal(self):
        signals_prod = PSignal(product)
        return mpl["signals", signals_prod].CSig()

      def createInSignal(self):
        signals_prod = PSignal(product)
        signals_prod, errors = signals.close_configuration(signals_prod, {"Dir": False})
        return mpl["signals", signals_prod].CSig()


  return mpl



if(__name__ == '__main__'):
  mpl = mpl_definition()

  conf = {}
  conf = {}
  for arg in sys.argv[1:]:
    conf[arg] = True

  interlocking = mpl["interlocking", conf]
  CILS = interlocking.CILS()
  print(CILS.createSwitch())
  print(CILS.createOutSignal())
  print(CILS.createInSignal())

  print(CILS.testSig())


