
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
This file implements the Clock Statechart Product Line described in
 [1] Michael Lienhardt, Ferruccio Damiani, Lorenzo Testa, and Gianluca Turin.
     2018. On checking delta-oriented product lines of statecharts.
     In Sci. Comput. Program. 166 (2018), 3–34.
     https://doi.org/10.1016/j.scico.2018.05.007

Few modification have been made to the structure of the statechart so it could work properly:
 - the clock self-loop that is triggered by a guard in [1] is not triggered by the event Clock.tick
 - the same transition now ends in a deep history state, so seconds could pass without bugs while setting the clock or the timer
Moreover, the sismic library requires to remove transitions before removing a state,
 and unsets the initial state of a compound state whenever it is removed
 (and so, even if we add back a new state with the same name, we need to reset the compound's initial state)

Moreover, we integrated a small tk GUI to control the clock.
Seconds must be triggered manually.

usage: run this file with the selected features in parameter.
 example: `python3 spl_clock.py DisplayMode`
"""


from pydop.spl import SPL, RegistryGraph
from pydop.fm_constraint import *
from pydop.fm_diagram import *
from pydop.operations.modules import Module, add, remove, modify, register_module

import sys
import time
import sismic.model
import sismic.io
import sismic.interpreter

import tkinter as tk
from threading import Thread


def spl_definition():


  # the base module is presented in [1], page 3 (Figure 1)
  def base_module_factory():
    # setup the module, starting empty
    res = Module("Clock")

    # setup the Clock implementation
    @add(res)
    class Clock(object):
      __slots__ = ("hours", "minutes", "seconds", "listeners")
      event_tick = "tick"
      event_mode = "mode"
      event_set  = "set"
      def __init__(self):
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.listeners = []

      def add_listener(self, listener):
        self.listeners.append(listener)

      def nextSecond(self):
        if(self.seconds == 59):
          self.seconds = 0
          if(self.minutes == 59):
            self.minutes = 0
            if(self.hours == 23):
              self.hours = 0
            else: self.hours += 1
          else: self.minutes += 1
        else: self.seconds += 1

        for obj in self.listeners:
          obj.react(self)

    # setup the Display implementation
    @add(res)
    class Display(object):
      __slots__ = ("mode",)
      def __init__(self):
        self.hour()
      def hour(self): self.mode = 0
      def minute(self): self.mode = 1

      def react(self, clock):
        if(self.mode == 0):
          print(f"{clock.hours}:{clock.minutes}:{clock.seconds}")
        else:
          print(f"{(clock.hours*60)+clock.minutes}:{clock.seconds}")

    # setup the Set implementation
    @add(res)
    class Set(object):
      __slots__ = ("obj_clock",)
      def __init__(self, obj_clock):
        self.obj_clock = obj_clock

      def nextHour(self):
        if(self.obj_clock.hours == 23):
          self.obj_clock.hours = 0
        else:self.obj_clock.hours += 1

      def nextMinute(self):
        if(self.obj_clock.minutes == 59):
          self.obj_clock.minutes = 0
          self.nextHour()
        else:self.obj_clock.minutes += 1


    # setup the statechart
    statechart = sismic.model.Statechart("Clock")

    ## the root state
    statechart.add_state(sismic.model.CompoundState("root"), None)
    statechart.add_state(sismic.model.CompoundState("Display"), "root")
    statechart.add_state(sismic.model.CompoundState("Set"), "root")
    statechart.state_for("root").initial = "Display"
    statechart.add_state(sismic.model.DeepHistoryState("DH"), "root")

    # this transition is different from [1]: it points to a deep history state
    statechart.add_transition(sismic.model.Transition("root", "DH", event=res.Clock.event_tick, action="obj_clock.nextSecond()"))

    ## the Display state
    statechart.add_state(sismic.model.BasicState("DisplayHour"), "Display")
    statechart.add_state(sismic.model.BasicState("DisplayMinute"), "Display")
    statechart.add_state(sismic.model.ShallowHistoryState("SH"), "Display")
    statechart.add_transition(sismic.model.Transition("DisplayHour", "DisplayMinute", event=res.Clock.event_mode, action="obj_display.minute()"))
    statechart.add_transition(sismic.model.Transition("DisplayMinute", "DisplayHour", event=res.Clock.event_mode, action="obj_display.hour()"))
    statechart.state_for("Display").initial = "DisplayHour"

    ## the Set state
    statechart.add_state(sismic.model.BasicState("SetHour"), "Set")
    statechart.add_state(sismic.model.BasicState("SetMinute"), "Set")
    statechart.add_transition(sismic.model.Transition("SetHour", "SetHour", event=res.Clock.event_mode, action="obj_set.nextHour()"))
    statechart.add_transition(sismic.model.Transition("SetMinute", "SetMinute", event=res.Clock.event_mode, action="obj_set.nextMinute()"))
    statechart.add_transition(sismic.model.Transition("SetHour", "SetMinute", event=res.Clock.event_set))
    statechart.add_transition(sismic.model.Transition("SetMinute", "SH", event=res.Clock.event_set))
    statechart.state_for("Set").initial = "SetHour"

    statechart.add_transition(sismic.model.Transition("Display", "Set", event=res.Clock.event_set))

    # add the statechart to the module
    add(res)("statechart", statechart)

    # add a setup function
    # this function is used to construct the context of the statechart interpreter
    # it is a map from names used in the statechart actions to the actual objects corresponding to these names
    @add(res)
    def setup_context():
      obj_clock = res.Clock()
      obj_display = res.Display()
      obj_set = res.Set(obj_clock)
      obj_clock.add_listener(obj_display)
      return {
        "obj_clock"  : obj_clock,
        "obj_display": obj_display,
        "obj_set"    : obj_set,
      }

    return res



  # the feature model, as in [1], page 10 (Figure 4)
  fm = FD("Clock",
    FDOptional(
      FD("DisplayMode"),
      FD("Timer")
  ))

  # SPL declaration
  spl = SPL(fm, RegistryGraph(), base_module_factory)


  # the deltas, as in [1], page 10 (Figure 4)

  @spl.delta(Not("DisplayMode"))
  def dSMode1(variant):
    remove(variant, "Display")
    statechart = variant.statechart
    # need to remove the transition t6 before removing the Display state, instead of modifying it
    t6 = statechart.transitions_to("SH")[0]
    statechart.remove_transition(t6)
    statechart.remove_state("Display")

    @modify(variant)
    def setup_context():
      obj_clock = variant.Clock()
      obj_set = variant.Set(obj_clock)
      return {
        "obj_clock"  : obj_clock,
        "obj_set"    : obj_set,
      }


  @spl.delta(Not("DisplayMode"), after=("dSMode1",))
  def dSMode2(variant):
    statechart = variant.statechart
    statechart.add_state(sismic.model.BasicState("Display"), "root")
    statechart.add_transition(sismic.model.Transition("Display", "Set", event=variant.Clock.event_set))
    # insert back the transition t6, with correct destination
    statechart.add_transition(sismic.model.Transition("SetMinute", "Display", event=variant.Clock.event_set))
    # reset the initial state of root (with the same state name as before)
    statechart.state_for("root").initial = "Display"



  @spl.delta("Timer", after=("dSMode2",))
  def dTimer(variant):
    @add(variant)
    class Timer(object):
      __slots__ = ("time", "running")
      event_timer = "timer"
      def __init__(self):
        self.time = 0
        self.running = False
      def incrTimer(self):
        self.time += 1
        print("Timer set to:", self.time)
      def startTimer(self):
        print("startTimer")
        self.running = True
      def isTime(self):
        # print("checking isTime:", self.time, self.time == 0)
        return self.time == 0
      def ring(self):
        print("TIMER FINISHED!!!")
        self.running = False

      def react(self, clock):
        print("REACTING:", self.running, self.time)
        if(self.running and (self.time > 0)):
          self.time -= 1

    statechart = variant.statechart

    statechart.add_state(sismic.model.CompoundState("Timer"), "root")
    statechart.add_state(sismic.model.BasicState("SetTimer"), "Timer")
    statechart.add_state(sismic.model.BasicState("runTimer"), "Timer")
    statechart.add_transition(sismic.model.Transition("SetTimer", "SetTimer", event=variant.Clock.event_mode, action="obj_timer.incrTimer()"))
    statechart.add_transition(sismic.model.Transition("SetTimer", "runTimer", event=variant.Timer.event_timer, action="obj_timer.startTimer()"))
    statechart.state_for("Timer").initial = "SetTimer"

    statechart.add_transition(sismic.model.Transition("Display", "Timer", event=variant.Timer.event_timer))
    # sismic does not allow to add invalid transition, instead of [1]
    # so the "runTimer -> SH" transition is added in a new dModeTimer delta

    @modify(variant)
    def setup_context():
      res = original()
      obj_timer = variant.Timer()
      res["obj_clock"].add_listener(obj_timer)
      res["obj_timer"] = obj_timer
      return res


  @spl.delta(And("DisplayMode", "Timer"), after=("dTimer",))
  def dModeTimer(variant):
    statechart = variant.statechart
    statechart.add_transition(sismic.model.Transition("runTimer", "SH", event=variant.Clock.event_tick, guard="obj_timer.isTime()", action="obj_timer.ring()"))


  @spl.delta(And(Not("DisplayMode"), "Timer"), after=("dTimer",))
  def dSModeTimer(variant):
    statechart = variant.statechart
    statechart.add_transition(sismic.model.Transition("runTimer", "Display", event=variant.Clock.event_tick, guard="obj_timer.isTime()", action="obj_timer.ring()"))


  return spl


if(__name__ == '__main__'):
  spl = spl_definition()

  conf = {"Clock": True, "DisplayMode": False, "Timer": False}
  for arg in sys.argv:
    if(arg in conf):
      conf[arg] = True

  variant = spl(conf)
  register_module(variant)
  import Clock

  context = Clock.setup_context()
  interpreter = sismic.interpreter.Interpreter(Clock.statechart, initial_context=context)
  interpreter.execute_once()
  print("DEBUG: state =", interpreter.configuration)

  def react_gen(ev):
    def res():
      interpreter.queue(ev)
      interpreter.execute_once()
      print("DEBUG: sending event", ev, "=> state =", interpreter.configuration)
    return res

  def gui():
    app = tk.Tk()
    app.wm_title('Clock')
    frame = tk.Frame(app)
    frame.grid()
    
    # collect the available events to the GUI: i.e., the ones declared in the classes of the objects in the context
    klasses = set(obj.__class__ for obj in context.values())
    ev_idx = 0
    for c in klasses:
      for ev_name, v in filter((lambda x: x[0].startswith("event_")), c.__dict__.items()):
        ev_name = ev_name[6:]

        # create a button for the event
        tk.Button(frame, text=ev_name, command=react_gen(v)).grid(column=ev_idx, row=0)
        ev_idx += 1

    app.mainloop()

  gui()

