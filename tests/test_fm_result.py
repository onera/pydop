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

from pydop.fm_result import *


def test_declaration():
  print("==========================================")
  print("= test_declaration")

  ## 1. test empty error list
  errors = decl_errors__c()
  assert(not bool(errors))

  ## 2. unbound
  not_declared = "not_declared"
  errors = decl_errors__c()
  assert(not bool(errors))
  res = errors.add_unbound(not_declared)
  assert(bool(errors))
  assert(len(tuple(iter(errors))) == 1)
  assert(str(errors) == f"ERROR: variable \"{not_declared}\" not declared")
  assert(res is errors)

  not_declared = "not_declared"
  in_path = "in_path"
  errors = decl_errors__c()
  assert(not bool(errors))
  res = errors.add_unbound(not_declared, in_path)
  assert(bool(errors))
  assert(len(tuple(iter(errors))) == 1)
  assert(str(errors) == f"ERROR: variable \"{not_declared}\" not declared in (partial) path \"{in_path}\"")
  assert(res is errors)

  ## 3. ambiguity
  ref = "ref"
  paths = tuple(f"path_{i}" for i in range(10))
  errors = decl_errors__c()
  assert(not bool(errors))
  res = errors.add_ambiguous(ref, paths[0], paths[1:])
  assert(bool(errors))
  tmp = ", ".join(f"\"{p}\"" for p in paths[1:])
  assert(len(tuple(iter(errors))) == 1)
  assert(str(errors) == f"ERROR: reference \"{paths[0]}[{ref}]\" is ambiguous (corresponds to paths: {tmp})")
  assert(res is errors)

  ## 4. duplicate
  ref_1 = "ref_1"
  ref_2 = "ref_2"
  in_path = "in_path"
  errors = decl_errors__c()
  assert(not bool(errors))
  res = errors.add_duplicate(in_path, ref_1, ref_2)
  assert(bool(errors))
  assert(len(tuple(iter(errors))) == 1)
  print(str(errors))
  tmp = ', '.join(f"\"{str(type(el))}\"" for el in (ref_1, ref_2))
  print(f"ERROR: path \"{in_path}\" correspond to more than one object (found types {tmp})")
  assert(str(errors) == f"ERROR: path \"{in_path}\" correspond to more than one object (found types {tmp})")
  assert(res is errors)

  ## 5. arity
  ref_1 = "ref_1"
  ref_2 = "ref_2"
  in_path = "in_path"
  errors = decl_errors__c()
  assert(not bool(errors))
  res1 = errors.add_unbound(ref_1, in_path)
  res2 = errors.add_unbound(ref_2, in_path)
  assert(bool(errors))
  assert(len(tuple(iter(errors))) == 2)
  res3 = errors.add_duplicate(in_path, ref_1, ref_2)
  assert(len(tuple(iter(errors))) == 3)
  assert(res1 is errors)
  assert(res2 is errors)
  assert(res3 is errors)



def test_reason_tree():
  print("==========================================")
  print("= test_reason_tree")

  ## 1. value mismatch
  ref = "ref"
  ref_val = "val"
  errors = reason_tree__c(ref, 0)
  assert(not bool(errors))
  res = errors.add_reason_value_mismatch(ref_val, 1, 2)
  assert(bool(errors))
  assert(len(tuple(iter(errors))) == 1)
  assert(str(errors) == f"{ref}: {ref_val} vs {1} (expected: {2})")
  assert(res is errors)

  ## 2. none
  ref = "ref"
  ref_val = "val"
  errors = reason_tree__c(ref, 0)
  assert(not bool(errors))
  res = errors.add_reason_value_none(ref_val)
  assert(bool(errors))
  assert(len(tuple(iter(errors))) == 1)
  assert(str(errors) == f"{ref}: {ref_val} has no value in the input configuration")
  assert(res is errors)

  ## 3. dependencies
  ref = "ref"
  ref_val = "val"
  deps = tuple(f"dep_{i}" for i in range(10))
  errors = reason_tree__c(ref, 0)
  assert(not bool(errors))
  res = errors.add_reason_dependencies(ref_val, deps)
  assert(bool(errors))
  assert(len(tuple(iter(errors))) == 1)
  tmp = ', '.join(f"\"{d}\"" for d in deps)
  assert(str(errors) == f"{ref}: {ref_val} should be True due to dependencies (found: {tmp})")
  assert(res is errors)

  ## 4. sub tree
  ref = "ref_1"
  ref_sub = "ref_2"
  ref_val = "val"
  errors = reason_tree__c(ref, 0)
  assert(not bool(errors))
  res = errors.add_reason_sub(eval_result__c(True, reason_tree__c(ref_sub, 0)))
  assert(not bool(errors))
  assert(res is errors)

  errors = reason_tree__c(ref, 0)
  assert(not bool(errors))
  res = errors.add_reason_sub(eval_result__c(True, reason_tree__c(ref_sub, 0).add_reason_value_mismatch(ref_val, 1, 2)))
  assert(bool(errors))
  assert(len(tuple(iter(errors))) == 1)
  assert(str(errors) == f"{ref}: {ref_sub}: {ref_val} vs {1} (expected: {2})")
  assert(res is errors)

  ## 5. arity
  ref = "ref"
  ref_1_val = "val_1"
  ref_2_val = "val_2"
  errors = reason_tree__c(ref, 0)
  assert(not bool(errors))
  res1 = errors.add_reason_value_mismatch(ref_1_val, 1, 2)
  res2 = errors.add_reason_value_mismatch(ref_2_val, 1, 2)
  assert(bool(errors))
  assert(len(tuple(iter(errors))) == 2)
  assert(res1 is errors)
  assert(res2 is errors)

  ## 6. update
  ref = "ref_1"
  ref_sub = "ref_2"
  ref_val_1 = "val_1"
  ref_val_2 = "val_2"
  errors = reason_tree__c(ref, 0)
  res = errors.add_reason_sub(eval_result__c(True, reason_tree__c(ref_sub, 0).add_reason_value_mismatch(ref_val_1, 1, 2)))

  def updater(s):
    if(s == ref):
      return ref_sub
    elif(s == ref_sub):
      return ref
    elif(s == ref_val_1):
      return ref_val_2
    else:
      return s
  errors.update_ref(updater)
  assert(str(errors) == f"{ref_sub}: {ref}: {ref_val_2} vs {1} (expected: {2})")



def test_eval_result():
  print("==========================================")
  print("= test_eval_result")

  ## 1. true value
  res = eval_result__c(True, None)
  assert(res.value())

  ## 2. false value
  res = eval_result__c(False, None)
  assert(not res.value())



if(__name__ == "__main__"):
  test_declaration()
  test_reason_tree()
  test_eval_result()

