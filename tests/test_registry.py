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

from pydop.spl import RegistryGraph, RegistryCategory
import networkx as nx

class info_cls(object):
  def __init__(self, name):
    self.name = name
  def __repr__(self):
    return self.name

def test_RegistryGraph_1():
  reg = RegistryGraph()
  d = { f"d{i}": info_cls(f"d{i}") for i in range(5) }
  reg.add(d["d0"])
  reg.add(d["d1"])
  reg.add(d["d2"], after=("d0", "d1",))
  reg.add(d["d3"], after="d2")
  reg.add(d["d4"], after=("d2",))

  succs = { f"d{i}": frozenset(reg.m_content.successors(f"d{i}")) for i in range(5) }
  assert (succs["d0"] == frozenset(("d2",)))
  assert (succs["d1"] == frozenset(("d2",)))
  assert (succs["d2"] == frozenset(("d3", "d4")))
  assert (succs["d3"] == frozenset())
  assert (succs["d4"] == frozenset())


def test_RegistryGraph_2():
  reg = RegistryGraph()
  d = { f"d{i}": info_cls( f"d{i}") for i in range(5) }
  for i in range(5):
    reg.add(d[f"d{i}"])

  reg.add_order(("d0", "d1"), "d2", ("d3", "d4"))

  succs = { f"d{i}": frozenset(reg.m_content.successors(f"d{i}")) for i in range(5) }
  assert (succs["d0"] == frozenset(("d2",)))
  assert (succs["d1"] == frozenset(("d2",)))
  assert (succs["d2"] == frozenset(("d3", "d4")))
  assert (succs["d3"] == frozenset())
  assert (succs["d4"] == frozenset())


def test_RegistryCategory():
  categories = (1,2,3,)
  def get_category(delta_info, *args, **kwargs):
    name = delta_info.name
    if(name[-1] < "2"): return 3
    elif(name[-1] == "2"): return 2
    else: return 1

  reg = RegistryCategory(categories, get_category)
  d = { f"d{i}": info_cls( f"d{i}") for i in range(5) }
  for i in range(5):
    reg.add(d[f"d{i}"])

  deltas = tuple(reg)
  assert(deltas == (d["d3"], d["d4"], d["d2"], d["d0"], d["d1"],))



if(__name__ == '__main__'):
  test_RegistryGraph_1()
  test_RegistryGraph_2()
  test_RegistryCategory()




