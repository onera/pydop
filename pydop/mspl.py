
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


from pydop.spl import SPL
from pydop.utils import _empty__

###############################################################################
# MSPL DEFINITION
###############################################################################

def default_factory(spl_id, *args, **kwargs):
  return SPL(*args, **kwars)



class MSPL(object):
  __slots__ = ("m_spl_factory", "m_reg",)
  def __init__(self, spl_factory=default_factory):
    self.m_spl_factory = spl_factory
    self.m_reg = {}

  def _check_name__(self, name):
    if(name in self.m_reg):
      raise KeyError(f"ERROR: spl id \"{name}\" already registered")

  ## spl creation
  def new(self, spl_id, *args, **kwargs):
    self._check_name__(spl_id)
    res = self.m_spl_factory(spl_id, *args, **kwargs)
    return self._add__(spl_id, res)

  def add(self, spl_id, spl):
    self._check_name__(spl_id)
    self._check_name__(spl)
    return self._add__(spl_id, res)

  def __setitem__(self, spl_id, spl):
    return self.add(spl_id, spl)

  def _add__(self, spl_id, spl):
    res = _wrapper__c(spl)
    self.m_reg[spl_id] = res
    self.m_reg[spl] = res
    return res

  ## getters
  def get(self, spl_id, default=None):
    return self.m_reg.get(key, default)

  def get(self, spl_id, conf, default=None):
    global _empty__
    spl = self.m_reg.get(key, _empty__)
    if(spl is not _empty__):
      return spl(conf)
    else:
      return default

  def __getitem__(self, key):
    global _empty__
    res = self.m_reg.get(key, _empty__)
    if(res is _empty__):
      if(isinstance(key, (list, tuple)) and (len(key) == 2)):
        spl_id, conf = key
        spl = self.m_reg[spl_id]
        res = spl(conf)
    return res


##########################################
# SPL wrapper that stores variants

class _wrapper__c(object):
  __slots__ = ("m_obj", "m_reg",)
  def __init__(self, obj):
    self.m_obj = obj
    self.m_reg = {}

  def __call__(self, conf, core=None):
    global _empty__
    conf = self.m_obj.close_configuration(conf)
    key = tuple(sorted(conf.items()))
    res = self.m_reg.get(key, _empty__)
    if(res is _empty__):
      res = self.m_obj(conf, core)
      self.m_reg[key] = res
    return res

  def __getattr__(self, name):
    return getattr(self.m_obj, name)

