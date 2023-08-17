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

from pydop.fm_constraint import *
from pydop.utils import dimacs__c


def test_constraint():
  print("==========================================")
  print("= test_constraint")

  val_1 = "val_1"
  val_2 = "val_2"
  val_3 = "val_3"
  val_4 = "val_4"
  val_5 = "val_5"
  val_6 = "val_6"

  constraint_01 = Lt (val_1, val_2)
  constraint_02 = Leq(val_2, val_3)
  constraint_03 = Eq (val_3, val_4)
  constraint_04 = Geq(val_4, val_5)
  constraint_05 = Gt (val_5, val_6)

  constraint_10 = And(constraint_01, constraint_02, constraint_03)
  constraint_11 = Or(constraint_01, constraint_02, constraint_03)
  constraint_12 = Not(constraint_01)
  constraint_13 = Xor(constraint_01, constraint_02, constraint_03)
  constraint_14 = Conflict(constraint_01, constraint_02, constraint_03)
  constraint_15 = Implies(constraint_01, constraint_02)
  constraint_16 = Iff(constraint_01, constraint_02)

  constraint_20 = And(constraint_11, constraint_04, constraint_05)
  constraint_21 = Or(constraint_10, constraint_12, constraint_13)
  constraint_22 = Not(constraint_11)
  constraint_23 = Xor(constraint_14, constraint_15, constraint_16)
  constraint_24 = Conflict(constraint_14, constraint_15, constraint_16)
  constraint_25 = Implies(constraint_14, constraint_15)
  constraint_26 = Iff(constraint_14, constraint_16)


  test = (
    ( constraint_01, { val_1: 0, val_2: 1, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, True),  # test  0
    ( constraint_01, { val_1: 0, val_2: 0, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, False), # test  1
    ( constraint_02, { val_1: 0, val_2: 0, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, True),  # test  2
    ( constraint_02, { val_1: 0, val_2: 1, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, False), # test  3
    ( constraint_03, { val_1: 0, val_2: 0, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, True),  # test  4
    ( constraint_03, { val_1: 0, val_2: 0, val_3: 1, val_4: 0, val_5: 0, val_6: 0 }, False), # test  5
    ( constraint_04, { val_1: 0, val_2: 0, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, True),  # test  6
    ( constraint_04, { val_1: 0, val_2: 0, val_3: 0, val_4: 0, val_5: 1, val_6: 0 }, False), # test  7
    ( constraint_05, { val_1: 0, val_2: 0, val_3: 0, val_4: 0, val_5: 1, val_6: 0 }, True),  # test  8
    ( constraint_05, { val_1: 0, val_2: 0, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, False), # test  9

    ( constraint_10, { val_1: 0, val_2: 1, val_3: 1, val_4: 1, val_5: 0, val_6: 0 }, True),  # test 10
    ( constraint_10, { val_1: 0, val_2: 0, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, False), # test 11
    ( constraint_11, { val_1: 0, val_2: 0, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, True),  # test 12
    ( constraint_11, { val_1: 1, val_2: 1, val_3: 0, val_4: 1, val_5: 0, val_6: 0 }, False), # test 13
    ( constraint_12, { val_1: 0, val_2: 0, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, True),  # test 14
    ( constraint_12, { val_1: 0, val_2: 1, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, False), # test 15
    ( constraint_13, { val_1: 0, val_2: 1, val_3: 0, val_4: 1, val_5: 0, val_6: 0 }, True),  # test 16
    ( constraint_13, { val_1: 0, val_2: 1, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, False), # test 17
    ( constraint_14, { val_1: 1, val_2: 1, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, True),  # test 18
    ( constraint_14, { val_1: 0, val_2: 1, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, False), # test 19
    ( constraint_15, { val_1: 0, val_2: 0, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, True),  # test 20
    ( constraint_15, { val_1: 0, val_2: 1, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, False), # test 21
    ( constraint_16, { val_1: 1, val_2: 1, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, True),  # test 22
    ( constraint_16, { val_1: 0, val_2: 0, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, False), # test 23

    ( constraint_20, { val_1: 0, val_2: 1, val_3: 1, val_4: 1, val_5: 1, val_6: 0 }, True),  # test 24
    ( constraint_20, { val_1: 0, val_2: 0, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, False), # test 25
    ( constraint_21, { val_1: 0, val_2: 0, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, True),  # test 26
    ( constraint_21, { val_1: 0, val_2: 1, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, False), # test 27
    ( constraint_22, { val_1: 1, val_2: 1, val_3: 0, val_4: 1, val_5: 0, val_6: 0 }, True),  # test 28
    ( constraint_22, { val_1: 0, val_2: 1, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, False), # test 29
    ( constraint_23, { val_1: 0, val_2: 1, val_3: 0, val_4: 1, val_5: 0, val_6: 0 }, True),  # test 30
    ( constraint_23, { val_1: 0, val_2: 1, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, False), # test 31
    ( constraint_24, { val_1: 0, val_2: 1, val_3: 0, val_4: 1, val_5: 0, val_6: 0 }, True),  # test 32
    ( constraint_24, { val_1: 1, val_2: 1, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, False), # test 33
    ( constraint_25, { val_1: 0, val_2: 0, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, True),  # test 34
    ( constraint_25, { val_1: 0, val_2: 1, val_3: 0, val_4: 1, val_5: 0, val_6: 0 }, False), # test 35
    ( constraint_26, { val_1: 1, val_2: 1, val_3: 0, val_4: 0, val_5: 0, val_6: 0 }, True),  # test 36
    ( constraint_26, { val_1: 0, val_2: 1, val_3: 1, val_4: 0, val_5: 0, val_6: 0 }, False), # test 37
  )
  for i, (c, prod, expected) in enumerate(test):
    res = c(prod, expected=expected)
    assert(bool(res) == expected)
    # if(bool(res) != expected):
    #   print(f"== ERROR IN TEST {i}")
    #   print(f" res: {bool(res)}")
    #   print(f" expected: {expected}")
    #   print(f" value: {res.m_value}")
    #   print(f" reason: {res.m_reason}")


def test_constraint_dimacs():
  print("==========================================")
  print("= test_constraint_dimacs")

  val_1 = "val_1"
  val_2 = "val_2"
  val_3 = "val_3"

  c_01 = And(val_1, val_2, val_3)
  c_02 = Or(val_1, val_2, val_3)
  c_03 = Xor(val_1, val_2, val_3)
  c_04 = Conflict(val_1, val_2, val_3)
  c_05 = Implies(val_1, val_2)
  c_06 = Iff(val_1, val_2)

  # for i, c in enumerate( (c_01, c_02, c_03, c_04, c_05, c_06,) ):
  # # for i, c in enumerate( (c_01,) ):
  #   print("====================")
  #   print("=", i)
  #   dimacs_obj = dimacs_cls()
  #   c.add_to_dimacs(dimacs_obj)
  #   print("==", c.vars)
  #   print(dimacs_obj.to_string(c.vars))

  c = And(c_02, c_05)
  dimacs_obj = dimacs__c()
  c.add_to_dimacs(dimacs_obj)
  print(dimacs_obj.to_string(c.vars))




if(__name__ == "__main__"):
  test_constraint()
  # test_constraint_dimacs()
