
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


###############################################################################
# GENERIC MSPL DEFINITION
###############################################################################

class MSPL(object):
  __slots__ = ("m_spls", "m_proxies",)
  def __init__(self):
    self.m_spls = {}
    self.m_proxies = {}

  class proxy(object):
    __slots__ = ("m_main", "m_spl_id", "m_conf", "m_obj",)
    def __init__(self, main, spl_id, conf):
      self.m_main   = main
      self.m_spl_id = spl_id
      self.m_conf   = conf
      self.m_obj    = self

    def _generate_(self):
      tmp = object.__getattribute__(self, "m_obj")
      if(tmp is self):
        main   = object.__getattribute__(self, "m_main")
        spl_id = object.__getattribute__(self, "m_spl_id")
        conf   = object.__getattribute__(self, "m_conf")
        tmp    = main.m_spls[spl_id](conf)
        setattr(self, "m_obj", tmp)
      return tmp

    def __getattribute__(self, name):
      tmp = object.__getattribute__(self, "_generate_")()
      return getattr(tmp, name)

  def add(self, spl_id, spl=None):
    if(spl_id in self.m_spls):
      raise KeyError(f"ERROR: spl id \"{spl_id}\" already registered")
    if(spl is None):
      def res(spl):
        self.m_spls[spl_id] = spl
      return res
    else:
      self.m_spls[spl_id] = spl

  def import_variant(self, spl_id, conf):
    conf_key = tuple(sorted(conf.items()))
    key = (spl_id, conf_key,)
    value = self.m_proxies.get(key)
    if(value is None):
      value = MSPL.proxy(self, spl_id, conf)
      self.m_proxies[key] = value
    return value

