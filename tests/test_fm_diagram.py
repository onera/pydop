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

from pydop.fm_configuration import *
from pydop.fm_result import *
from pydop.fm_constraint import *
from pydop.fm_diagram import *

import enum
import itertools



def test_simple_attribute():
  print("==========================================")
  print("= test_simple_attribute")

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
  att_07 = Enum([1, "toto", None, bool])

  att_11 = List((4,None), Bool())
  att_12 = List(spec=Int(1,5))
  att_13 = List((4,), List(spec=Int(1,5)))
  

  print("str of Class(tmp_1) =", att_01)
  print("str of Bool() =", att_02)
  print("str of String() =", att_03)
  print("str of Enum(tmp_2) =", att_04)
  print("str of Int((1, 5), (9,None)) =", att_05)
  print("str of Float((None, 5), (9,10)) =", att_06)
  print("str of Enum([1, \"toto\", None, bool]) =", att_07)
  print("str of List((4,None), Bool()) =", att_11)
  print("str of List(spec=Int(1,5)) =", att_12)
  print("str of List((4,), List(spec=Int(1,5))) =", att_13)

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




def test_fm_values():
  print("==========================================")
  print("= test_fm_values")

  fm_01 = FD('A',
    FDAnd('B', FDXor(FD('B0'), FD('B1')), FDXor(FD('B2'), FD('B3'))),
    FDAny('C', FD('C0'), FD('C1')),
    FDOr('D', FD('D0'), FD('D1')),
    FDXor('E', FD('E0'), FD('E1')),
    Implies(And('B/B0', 'C/C0'), Not('E1')),
    # Implies(And('B/B1', 'C/C0'), Eq('E1',False)),
    F=List(size=(1,4), spec=Int(3,5))
  )

  conf_empty = {
    'A' : False,
    'B' : False, 'B0': False, 'B1': False, 'B2': False, 'B3': False,
    'C' : False, 'C0': False, 'C1': False,
    'D' : False, 'D0': False, 'D1': False,
    'E' : False, 'E0': False, 'E1': False,
    'F':  False,
  }

  conf_base = {
    'A' : True,
    'B' : True, 'B0': True, 'B1': False, 'B2': True, 'B3': False,
    'C' : True, 'C0': False, 'C1': False,
    'D' : True, 'D0': True, 'D1': False,
    'E' : True, 'E0': True, 'E1': False,
    'F':  (3,),
  }

  def update(**kwargs):
    return dict([(k, v) for d in (conf_base, kwargs) for k,v in d.items()])

  tests = (
    (conf_empty, True),
    (conf_base,  True),
    # B
    (update(B0=False, B1=True), True),
    (update(B2=False, B3=True), True),
    (update(B0=False, B1=True, B2=False, B3=True), True),
    (update(B0=True, B1=True), False),
    (update(B2=True, B3=True), False),
    # C
    (update(C0=True), True),
    (update(C1=True), True),
    (update(C0=True, C1=True), True),
    # D
    (update(D1=True), True),
    (update(D0=True, D1=True), True),
    (update(D0=False, D1=True), True),
    (update(D0=False), False),
    # E
    (update(E0=True), True),
    (update(E0=False, E1=True), True),
    (update(E0=False), False),
    (update(E0=True, E1=True), False),
    # F
    (update(F=(3,4,)), True),
    (update(F=(3,4,4)), True),
    (update(F=()), False),
    (update(F=(3,4,5)), False),
    (update(F=(3,3,3,3)), False),
    # Implies
    (update(C0=True, E0=True), True),
    (update(C0=True, E1=True), False),
  )

  # 2. check FM
  go_on = True
  if(go_on):
    errors = fm_01.generate_lookup()
    if(bool(errors)):
      print("ERROR generate_lookup")
      print(errors)
      go_on = False
  
  if(go_on):
    for conf_raw, expected in tests:
      conf, error = fm_01.close_configuration(conf_raw)

      if(bool(error)):
        print(f"ERROR close_configuration")
        print(error)
        go_on = False

      if(go_on):
        value = fm_01(conf)
        if(bool(value) != expected):
          print(f" value: {value.m_value}")
          print(f" reason: {value.m_reason}")
          print(f" nvalue: {value.m_nvalue}")
          print(f" snodes: {value.m_snodes}")



def test_fm_path():
  print("==========================================")
  print("= test_fm_path")

  fm_01 = FD('A',
    FDAnd('B', FDXor(FD('B0'), FD('B1')), FDXor(FD('B2'), FD('B3'))),
    FDAny('C', FD('C0'), FD('C1')),
    FDOr('D', FD('D0'), FD('D1')),
    FDXor('E', FD('E0'), FD('E1')),
    Implies(And('B/B0', 'C/C0'), Not('E1')),
    # Implies(And('B/B1', 'C/C0'), Eq('E1',False)),
    F=List(size=(1,4), spec=Int(3,5))
  )

  conf_base = {
    'A' : True,
    'B' : True, 'B0': True, 'B1': False, 'B2': True, 'B3': False,
    'C' : True, 'C0': False, 'C1': False,
    'D' : True, 'D0': True, 'D1': False,
    'E' : True, 'E0': True, 'E1': False,
    'F':  (3,),
  }


  paths = {
    'A' : ('A',),
    'B' : ('A/B', 'B'),
    'B0': ('A/B/B0', 'A/B0', 'B/B0', 'B0'),
    'B1': ('A/B/B1', 'A/B1', 'B/B1', 'B1'),
    'B2': ('A/B/B2', 'A/B2', 'B/B2', 'B2'),
    'B3': ('A/B/B3', 'A/B3', 'B/B3', 'B3'),
    'C' : ('A/C', 'C'),
    'C0': ('A/C/C0', 'A/C0', 'C/C0', 'C0'),
    'C1': ('A/C/C1', 'A/C1', 'C/C1', 'C1'),
    'D' : ('A/D', 'D'),
    'D0': ('A/D/D0', 'A/D0', 'D/D0', 'D0'),
    'D1': ('A/D/D1', 'A/D1', 'D/D1', 'D1'),
    'E' : ('A/E', 'E'),
    'E0': ('A/E/E0', 'A/E0', 'E/E0', 'E0'),
    'E1': ('A/E/E1', 'A/E1', 'E/E1', 'E1'),
    'F': ('A/F', 'F'),
  } # > 33M tests, maybe too much


  paths = {
    'A' : ('A',),
    'B' : ('A/B', 'B',),
    'B0': ('A/B/B0', 'A/B0', 'B/B0', 'B0',),
    'B1': ('B/B1', 'B1',),
    'B2': ('A/B2', 'B2',),
    'B3': ('A/B/B3', 'B3',),
    'C' : ('C',),
    'C0': ('C/C0', 'C0',),
    'C1': ('A/C1','C1',),
    'D' : ('D',),
    'D0': ('A/D/D0', 'D0',),
    'D1': ('A/D/D1', 'D1',),
    'E' : ('E',),
    'E0': ('E0',),
    'E1': ('E1',),
    'F': ('A/F', 'F',),
  }

  def get_all_paths():
    for t in itertools.product(*paths.values()):
      yield {k:v for k,v in zip(paths.keys(), t)}


  go_on = True
  if(go_on):
    errors = fm_01.generate_lookup()
    if(bool(errors)):
      print("ERROR generate_lookup")
      print(errors)
      go_on = False

  if(go_on):
    conf_core, error = fm_01.close_configuration(conf_base)
    if(bool(error)):
      print(f"ERROR nf_product")
      print(error)
      go_on = False

  if(go_on):
    for i, cpaths in enumerate(get_all_paths()):
      conf, error = fm_01.close_configuration({cpaths[k]:v for k,v in conf_base.items()})
      if(bool(error)):
        print(f"ERROR nf_product [{i}]")
        print(error)
        go_on = False

      if(go_on and (conf != conf_core)):
        print(f"ERROR conversion [{i}]")
        print(conf_core)
        print('vs')
        print(conf)
        go_on = False




def test_fm_make_product():
  print("==========================================")
  print("= test_fm_make_product")

  # 1. declarations
  fm_01 = FD('A',
    FDAnd('B', FDXor(FD('B0'), FD('B1')), FDXor(FD('B2'), FD('B3'))),
    FDAny('C', FD('C0'), FD('C1')),
    FDOr('D', FD('D0'), FD('D1')),
    FDXor('E', FD('E0'), FD('E1')),
    Implies(And('B/B0', 'C/C0'), Not('E1')),
    # Implies(And('B/B1', 'C/C0'), Eq('E1',False)),
    F=List(size=(1,4), spec=Int(3,5))
  )


  conf_empty = {}
  conf_base  = {'A':True, 'B': True, 'B0': True, 'B2': True, 'C': True, 'D': True, 'D0': True, 'E': True, 'E0': True, 'F':(3,)}

  tests = (
    ((conf_empty,), False),
    ((conf_base, ), True),
    # B
    ((conf_base, {'B1': True}), True),
    ((conf_base, {'B3': True}), True),
    ((conf_base, {'B1': True, 'B3': True}), True),
    ((conf_base, {'B0': True, 'B1': True}), False),
    ((conf_base, {'B2': True, 'B3': True}), False),
    # C
    ((conf_base, {'C0': True}), True),
    ((conf_base, {'C1': True}), True),
    ((conf_base, {'C0': True, 'C1': True}), True),
    # D
    ((conf_base, {'D1': True}), True),
    ((conf_base, {'D0': True, 'D1': True}), True),
    ((conf_base, {'D0': False}), False),
    # E
    ((conf_base, {'E0': True}), True),
    ((conf_base, {'E1': True}), True),
    ((conf_base, {'E0': False}), False),
    ((conf_base, {'E0': True, 'E1': True}), False),
    # F
    ((conf_base, {'F':(3,4,)}), True),
    ((conf_base, {'F':(3,4,4)}), True),
    ((conf_base, {'F':()}), False),
    ((conf_base, {'F':(3,4,5)}), False),
    ((conf_base, {'F':(3,3,3,3)}), False),
    # Implies
    ((conf_base, {'C0': True, 'E0': True}), True),
    ((conf_base, {'C0': True, 'E1': True}), False),
    # Sequence
    ((conf_base, {'B1': True}, {'B0': True}), True),
  )

  # 2. check FM
  go_on = True

  if(go_on):
    errors = fm_01.generate_lookup()
    if(bool(errors)):
      print("ERROR generate_lookup")
      print(errors)
      go_on = False
  
  if(go_on):
    for i, (confs_raw, expected) in enumerate(tests):
      conf, errors = fm_01.close_configuration(*confs_raw)

      if(bool(errors)):
        print(f"ERROR close_configuration [{i}]")
        print(errors)
        go_on = False

      if(go_on):
        value = fm_01(conf)
        if(bool(value) != expected):
          print(f"ERROR in eval [{i}]: expected = {expected}")
          print(f" value: {value.m_value}")
          print(f" reason: {value.m_reason}")
          print(f" nvalue: {value.m_nvalue}")
          print(f" snodes: {value.m_snodes}")



def test_fm_constraint():
  print("==========================================")
  print("= test_fm_constraint")
  # 1. declarations
  fm_01 = FD('A',
    FDAnd('B', FDXor(FD('B0'), FD('B1')), FDXor(FD('B2'), FD('B3'))),
    FDAny('C', FD('C0'), FD('C1')),
    FDOr('D', FD('D0'), FD('D1')),
    FDXor('E', FD('E0'), FD('E1')),
    Implies(And('B/B0', 'C/C0'), Not('E1')),
    # Implies(And('B/B1', 'C/C0'), Eq('E1',False)),
    F=List(size=(1,4), spec=Int(3,5))
  )

  val_1 = "B0"
  val_2 = "B1"
  val_3 = "C"
  val_4 = "D0"
  val_5 = "E0"
  val_6 = "E1"

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

  # 2. checking

  go_on = True
  if(go_on):
    errors = fm_01.check()
    if(bool(errors)):
      print("ERROR check")
      print(errors)
      go_on = False

  for i, (c, prod, expected) in enumerate(test):
    if(go_on):
      c, errors = fm_01.link_constraint(c)
      if(bool(errors)):
        print(f"ERROR link_constraint({c})")
        print(errors)
        go_on = False
    if(go_on):
      prod, errors = fm_01.close_configuration(prod)
      if(bool(errors)):
        print(f"ERROR close_configuration({prod})")
        print(errors)
        go_on = False
    if(go_on):
      res = c(prod, expected=expected)
      assert(bool(res) == expected)





def test_fm_full():
  # 1. declarations
  fm_01 = FD('A',
    FDAnd('B', FDXor(FD('B0'), FD('B1')), FDXor(FD('B2'), FD('B3'))),
    FDAny('C', FD('C0'), FD('C1')),
    FDOr('D', FD('D0'), FD('D1')),
    FDXor('E', FD('E0'), FD('E1')),
    Implies(And('B/B0', 'C/C0'), Not('E1')),
    # Implies(And('B/B1', 'C/C0'), Eq('E1',False)),
    F=List(size=(1,4), spec=Int(3,5))
  )


  paths = {
    'A' : ('A',),
    'B' : ('A/B', 'B'),
    'B0': ('A/B/B0', 'A/B0', 'B/B0', 'B0'),
    'B1': ('A/B/B1', 'A/B1', 'B/B1', 'B1'),
    'B2': ('A/B/B2', 'A/B2', 'B/B2', 'B2'),
    'B3': ('A/B/B3', 'A/B3', 'B/B3', 'B3'),
    'C' : ('A/C', 'C'),
    'C0': ('A/C/C0', 'A/C0', 'C/C0', 'C0'),
    'C1': ('A/C/C1', 'A/C1', 'C/C1', 'C1'),
    'D' : ('A/D', 'D'),
    'D0': ('A/D/D0', 'A/D0', 'D/D0', 'D0'),
    'D1': ('A/D/D1', 'A/D1', 'D/D1', 'D1'),
    'E' : ('A/E', 'E'),
    'E0': ('A/E/E0', 'A/E0', 'E/E0', 'E0'),
    'E1': ('A/E/E1', 'A/E1', 'E/E1', 'E1'),
    'F': ('A/F', 'F'),
  }

  paths = {
    'A' : ('A',),
    'B' : ('A/B', 'B',),
    'B0': ('A/B/B0', 'A/B0', 'B/B0', 'B0',),
    'B1': ('B/B1', 'B1',),
    'B2': ('A/B2', 'B2',),
    'B3': ('A/B/B3', 'B3',),
    'C' : ('C',),
    'C0': ('C/C0', 'C0',),
    'C1': ('A/C1','C1',),
    'D' : ('D',),
    'D0': ('A/D/D0', 'D0',),
    'D1': ('A/D/D1', 'D1',),
    'E' : ('E',),
    'E0': ('E0',),
    'E1': ('E1',),
    'F': ('A/F', 'F',),
  }

  def get_all_paths():
    for t in itertools.product(*paths.values()):
      yield {k:v for k,v in zip(paths.keys(), t)}


  conf_empty = {}
  conf_base  = {'A':True, 'B': True, 'B0': True, 'B2': True, 'C': True, 'D': True, 'D0': True, 'E': True, 'E0': True, 'F':(3,)}

  tests = (
    ((conf_empty,), True),
    ((conf_base, ), True),
    # B
    ((conf_base, {'B1': True}), True),
    ((conf_base, {'B3': True}), True),
    ((conf_base, {'B1': True, 'B3': True}), True),
    ((conf_base, {'B0': True, 'B1': True}), False),
    ((conf_base, {'B2': True, 'B3': True}), False),
    # C
    ((conf_base, {'C0': True}), True),
    ((conf_base, {'C1': True}), True),
    ((conf_base, {'C0': True, 'C1': True}), True),
    # D
    ((conf_base, {'D1': True}), True),
    ((conf_base, {'D0': True, 'D1': True}), True),
    ((conf_base, {'D0': False}), False),
    # E
    ((conf_base, {'E0': True}), True),
    ((conf_base, {'E1': True}), True),
    ((conf_base, {'E0': False}), False),
    ((conf_base, {'E0': True, 'E1': True}), False),
    # F
    ((conf_base, {'F':(3,4,)}), True),
    ((conf_base, {'F':(3,4,4)}), True),
    ((conf_base, {'F':()}), False),
    ((conf_base, {'F':(3,4,5)}), False),
    ((conf_base, {'F':(3,3,3,3)}), False),
    # Implies
    ((conf_base, {'C0': True, 'E0': True}), True),
    ((conf_base, {'C0': True, 'E1': True}), False),
    # Sequence
    ((conf_base, {'B1': True}, {'B0': True}), True),
  )


  # 2. check FM
  go_on = True

  if(go_on):
    errors = fm_01.generate_lookup()
    if(bool(errors)):
      print("ERROR generate_lookup")
      print(errors)
      go_on = False
  
  if(go_on):
    for confs_raw, expected in tests:
      for cpaths in get_all_paths():
        # print(f"TESTING PATH: {cpaths}")
        # print(confs_raw)
        confs_n_errors = tuple(fm_01.close_configuration({cpaths[k]:v for k,v in conf.items()}) for conf in confs_raw)
        confs, errors = tuple(zip(*confs_n_errors))

        for i, err in enumerate(errors):
          if(bool(err)):
            print(f"ERROR close_configuration [{i}]")
            print(err)
            go_on = False

        if(go_on):
          conf, errors = fm_01.close_configuration(*confs)
          value = fm_01(conf)
          if(bool(value) != expected):
            print(f" value: {value.m_value}")
            print(f" reason: {value.m_reason}")
            print(f" nvalue: {value.m_nvalue}")
            print(f" snodes: {value.m_snodes}")




if(__name__ == "__main__"):
  test_simple_attribute()
  test_fm_values()
  test_fm_path()
  test_fm_make_product()
  test_fm_constraint()
  test_fm_full()
