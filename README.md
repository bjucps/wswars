# CpS 320 Web Server Wars

The following components are involved:

* register.c - used to register students in the wars
* warproxy.py - used to adjudicate the contest
* grammalog.py - used to log the reports from warproxy
* scoreboard/webapp.py - a scoreboard web app

## Student piece (warproxy.py)

See student usage instructions online:

https://protect.bju.edu/cps/courses/cps250/labs/WebServerWars.html

The warproxy sends logging messages to csunix via UDP to be
received by grammalog.py.

Students register using setup.sh, which invokes register utility on csunix 
(source register.c in this folder).

## On csunix

Edit /home/cps250/wswars/users.txt and delete entries.

Then, execute 

    ./grammalog.py

This will log messages sent from the warproxies to war.log

Execute:

    cd scoreboard
    ./webapp.py

This will run a web application that displays statistics based on war.log

## Build Instructions

Execute `make` to compile register.c and create wswars_kit.tar.gz distribution package.

## Contest Procedures

1. Ensure that all contestants have addresses on the same VLAN (all wired or all wireless)

1. Delete war.log and start grammalog.py and webapp.py (in that order).

1. After initial testing and warmup period, shutdown scoreboard app and
   grammalog. Delete war.log and restart grammalog.py and webapp.py. Have all
   contestants stop their war proxies and restart using go.sh.
   