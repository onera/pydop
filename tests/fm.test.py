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

# from pydop.fm_core import product_default
from pydop.fm_diagram import *
import enum


def test_simple_constraint():
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



def test_simple_attribute():
  class tmp_1(object): pass
  class tmp_2(enum.Enum):
    TMP_20 = 0
    TMP_21 = 1
  att_01 = Class(tmp_1)
  att_02 = Bool()
  att_03 = String()
  att_04 = Enum(tmp_2)
  att_05 = Int((1, 5), (9,None))
  att_06 = Float((None, 5), (9,10))

  att_11 = List((4,None), Bool())
  att_12 = List(spec=Int(1,5))
  att_13 = List((4,), List(spec=Int(1,5)))
  
  test = (
    (att_01, tmp_1(), True),        # test  0
    (att_01,       1, False),       # test  1
    (att_02,    True, True),        # test  2
    (att_02,       1, False),       # test  3
    (att_03, "tmp_1", True),        # test  4
    (att_03,       1, False),       # test  5
    (att_04, tmp_2.TMP_20, True),   # test  6
    (att_04,       1, False),       # test  7
    (att_05,       1, True),        # test  8
    (att_05,       5, False),       # test  9
    (att_05,       8, False),       # test 10
    (att_05,      24, True),        # test 11
    (att_06,  -100.0, True),        # test 12
    (att_06,     4.0, True),        # test 13
    (att_06,     5.0, False),       # test 14
    (att_06,     8.0, False),       # test 15
    (att_06,     9.0, True),        # test 16
    (att_06,    10.0, False),       # test 17
    
    (att_11, (True, True, True, True,), True),          # test 18
    (att_11, (True, True, True, True, True,), True),    # test 19
    (att_11, (True, True, True, True, 1,), False),      # test 20
    (att_11, (True, True, True,), False),               # test 21
    (att_12, (), True),                                 # test 22
    (att_12, (1,2,3,4,3,2,), True),                     # test 23
    (att_12, (1,2,3,4,5,2,), False),                    # test 24
    (att_12, (1, 2, 3, True, 2,), True),                # test 25 // ...
    (att_12, (1, 2, 3, 4.0, 2,), False),                # test 26

    (att_13, ((), (), (), ()), True),                   # test 27
    (att_13, ((1,2,), (3,4,), (3,2,), (),), True),      # test 28
    (att_13, (1,(2,),(3,4,),(5,2,)), False),            # test 29
    (att_13, ((1, 2,), (3,), (), (4.0, 2,),), False),   # test 30

  )

  for i, (c, val, expected) in enumerate(test):
    res = c(val)
    assert(res == expected)
    # if(bool(res) != expected):
    #   print(f"== ERROR IN TEST {i}")
    #   print(f" res: {res}")
    #   # print(f" expected: {expected}")
    #   # print(f" value: {res.m_value}")
    #   # print(f" reason: {res.m_reason}")


# def test_test():
#   val_1 = "val_1"
#   val_2 = "val_2"
#   val_3 = "val_3"
#   val_4 = "val_4"

#   constraint_01 = Lt (val_1, val_2)
#   constraint_02 = Leq(val_2, val_3)
#   constraint_03 = Eq (val_3, val_4)

#   constraint_06 = And(constraint_01, constraint_02, constraint_03)
#   constraint_08 = Not(constraint_06)
#   constraint_07 = Or(constraint_01, constraint_02, constraint_06)

#   res = constraint_07({ val_1: 0, val_2: 0, val_3: 0, val_4: 0 })
#   print(f" value: {res.m_value}")
#   print(f" reason: {res.m_reason}")

def test_simple_fm():
  val_1 = "val_1"
  val_2 = "val_2"
  val_3 = "val_3"

  f_1 = "f_1"
  f_2 = "f_2"
  f_3 = "f_3"
  f_4 = "f_4"

  fm_1 = FDAnd(f_1, FDAnd(f_2, Or(f_2, Not(f_2))), FDAnd(f_3), Lt(val_1, val_2), val_1=Int(), val_2=Int(0, 9))
  errors = fm_1.generate_lookup()
  print("========")
  print(fm_1.m_lookup)
  print("========")
  print(errors)

  p_1 = {f_1: True, f_2: False, f_3: True, val_1: 1, val_2: 10}
  p1, errors = fm_1.nf_product(p_1)
  print(f" errors: {errors}")
  res = fm_1(p1)
  print(f" value: {res.m_value}")
  print(f" reason: {res.m_reason}")


if(__name__ == "__main__"):
  test_simple_constraint()
  test_simple_attribute()
  # test_test()
  test_simple_fm()