# ⏳ *rsfstat* - ASTERIOS Application Scheduling Plans Stats

[![](https://github.com/krono-safe/rsfstat/actions/workflows/test.yml/badge.svg)](https://github.com/krono-safe/rsfstat/actions/workflows/test.yml)

## Installation

*rsfstat* is tested for Python 3.7 or above, and is currently only compatible
with Applications compiled with **ASTERIOS Developer K19.2** (*psyko* versions
from 8.2.0 up to 8.19.0).

*rsfstat* is not deployed on PyPi, so you need to install it from the
repository:

```bash
pip install --user git+https://github.com/krono-safe/rsfstat.git
```

Of if you use [pipx][3]

```bash
pipx install git+https://github.com/krono-safe/rsfstat.git
```

A note to Windows users: you should use a terminal emulator that supports
unicode characters, such as [Windows Terminal][1] or [ConEmu][2]. You'd be
missing emojis in your console output otherwise! 😉


## Features Overview

This is a free an open-source tool developed by [**Krono-Safe**][6], to be used
along with our commercial toolsuite **ASTERIOS Developer** and its associated
Real-Time Kernels.

*rsfstat* is a CLI tool written in Python that computes some interesting stats on
the static scheduling plans generated for an ASTERIOS Application. Run it on the
binary files `core_<N>_rt_rsf.ks` created under `app_gendir/psylink/db/rsfs/`in
your generation directory _(where `<N>` is a CPU identifier)_. A set of examples
is available in this repository for you to test the tool:

```bash
# An Application that maps Tasks on 3 different cores has 3 RSFs:
rsfstat doc/examples/gendir/app_gendir/psylink/db/rsfs/core_{0,1,2}_rt_rsf.ks
```

Here's the expected output:

![](doc/img/console-screenshot.png)

> **⚠ WARNING**: The values computed by the tool are correct only if the quota
> timers have the same frequency across all cores.


### CPU Load

*rsfstat* prints out three types of CPU load:

* a global CPU load computed on all cores (average CPU load);
* a CPU load computed separately for each core;
* a CPU load computed for each Task mapped on a given core.

Note that these values are computed _only on the periodic part_ (a.k.a. "loop")
of the static scheduling plans (RSFs), ignoring the transient state occurring at
initialization.

### Parallelism Ratio

#### Properties, Definition

*rsfstat* also computes a "parallelism ratio", verifying these key properties:

1. it equals 0 iff. at any given time in steady state, at most one Task is
   scheduled among all the RSFs;
2. it equals 1 iff. at any given time in steady state, either **all** the RSFs
   schedule a Task, or **no** RSF schedules a Task (i.e. all cores are idling);
3. given a certain timeslot, it increases linearly with the number of cores
   executing a Task during that slot.

Note that these properties are not restrictive enough to infer a unique
definition. *rsfstat* computes *one* parallelism ratio verifying these
properties, expressed mathematically as follows:

<img src="https://latex.codecogs.com/svg.image?\alpha&space;=&space;\frac{1}{T_\text{RSF}&space;\times&space;(N-1)&space;\times&space;L_\text{global}}&space;\times&space;\int_0^{T_\text{RSF}}&space;\max\left\{0,&space;\left(\sum_{k=1}^{N}&space;\delta^k(t)\right)&space;-&space;1\right\}\&space;dt" title="https://latex.codecogs.com/svg.image?\alpha = \frac{1}{T_\text{RSF} \times (N-1) \times L_\text{global}} \times \int_0^{T_\text{RSF}} \max\left\{0, \left(\sum_{k=1}^{N} \delta^k(t)\right) - 1\right\}\ dt" />

where:

* ![](https://latex.codecogs.com/svg.image?T_\text{RSF}) is the length of the loop of the RSFs *(all RSFs of the same
  Application have the same loop length by construction)*;
* ![](https://latex.codecogs.com/svg.image?N%3E1) is the number of active cores *(and thus the number of RSFs)*
* ![](https://latex.codecogs.com/svg.image?L_\text{global}) is the global CPU load computed on all the loops of all the RSFs
  of the Application;
* by convention ![](https://latex.codecogs.com/svg.image?t=0) corresponds to the date when the last RSF starts its steady
  state, i.e. starts executing its loop;
* ![](https://latex.codecogs.com/svg.image?%5Cforall%20t%5Cin%5B0,%20T_%5Ctext%7BRSF%7D%5D,%5Cquad%5Cdelta%5Ek(t)=%5Cbegin%7Bcases%7D1&%5Ctext%7Bif%20a%20Task%20is%20scheduled%20on%20the%20%7Dk%5Ctext%7B-th%20RSF%20at%20date%20%7Dt%5C%5C0&%5Ctext%7Botherwise%7D%5Cend%7Bcases%7D)

The intuition behind this formula is actually quite simple: for each time
increment, we want to count how many cores are "active", i.e. are scheduled to
execute a task. The more cores are active, the more "points" we score on this
time increment: when only one core or zero core is active, we get no point; and
when all cores are active, we get the maximum. We then sum the total number of
points scored on the duration of the RSF loop, and normalize this quantity with
the length of the loop, and the global CPU load, in order to satisfy the three
properties listed above.


#### Examples

A few examples give a quicker understanding of that ratio. Consider for instance
the scheduling plans for two cores *(for the sake of brevity, only the "loop"
part of the RSFs is represented)*, as represented below:

![](./doc/img/parallelism-ratio-100.drawio.svg)

Tasks are always scheduled to be executed simultaneously *(colored blocks)*,
and both cores are also idling at the same time. Thus, the global CPU load is of
60% (as each core has a 60% load), but the parallelism ratio is of 100%.

The next case below is the exact opposite:

![](./doc/img/parallelism-ratio-0.drawio.svg)

No Tasks are executed simultaneously _ever_: the CPU load of each core is of
50%, so is the global CPU load, and the parallelism ratio is 0.

At last, the case below is an in-between: sometimes Tasks are executed
simultaneously *(for 2 time units per cycle, represented by red double-arrows)*,
but most of the time they are not *(there are 6 time units per cycle where only
one Task is executed while the other core is idling)*:

![](./doc/img/parallelism-ratio-18.drawio.svg)

As a final note: by convention, the parallelism ratio for a single core
Application (i.e. `N=1`) is set to 0.

#### Discussion: other possible definition

As stated before, the three key properties do not imply a unique definition for
a parallelism ratio, and the one computed by *rsfstat* is an opinionated choice.

For instance, going back to the last example above, one could have expected from
a "sane" parallelism ratio a value of 20% instead of 40%: 2 time units of
parallel computing, divided by 10 time units in a complete cycle. However this
method would correspond more or less to removing the normalization by
![](https://latex.codecogs.com/svg.image?L_\text{global}), thus failing to
verify the key property 2. _(reaching 100% when at any given time either all the
RSFs schedule a Task, or no RSF schedules a Task)_.

A valid alternate definition however could lead to a parallelism ratio of 25% on
that same example: for each cycle, 2 time units of parallel computing, divided
by 8 time units corresponding to time slots when at least one core is busy. This
would correspond effectively to replacing in the definition above
![](https://latex.codecogs.com/svg.image?L_\text{global}) with a "pooled load",
computed on a virtual scheduling plan obtained by merging all the RSFs.
Formally, this pooled load is given by:

<img
src="https://latex.codecogs.com/svg.image?L_{\text{pooled}}&space;=&space;\frac{1}{T_{\text{RSF}}}\times&space;\int_0^{T_{\text{RSF}}}\Delta(t)\&space;dt\qquad\text{where&space;}\Delta(t)&space;=&space;\begin{cases}1&space;&&space;\text{when&space;at&space;least&space;one&space;core&space;is&space;active&space;at&space;}t&space;\\&space;0&space;&&space;\text{otherwise}\\\end{cases}"
title="https://latex.codecogs.com/svg.image?L_{\text{pooled}} =
\frac{1}{T_{\text{RSF}}}\times \int_0^{T_{\text{RSF}}}\Delta(t)\
dt\qquad\text{where }\Delta(t) = \begin{cases}1 & \text{when at least one core
is active at }t \\ 0 & \text{otherwise}\\\end{cases}" />

However, we believe it makes more sense to normalize our ratio with the global
CPU load ![](https://latex.codecogs.com/svg.image?L_\text{global}) rather than
with the pooled load ![](https://latex.codecogs.com/svg.image?L_\text{pooled}).
With the current definition, the computed value indicates how "far" the current
scheduling plan is from a "fully parallel" plan, **for a given, fixed global CPU
load**.

To illustrate that point, let's go back to our last example: if the developer
were to modify their Application to have a "fully parallel" plan _(assuming of
course no precedence constraint exists between the Tasks)_, they could for
instance shuffle the execution time slots like so:

![](doc/img/parallelism-ratio-18-to-100.drawio.svg)

_(notice that the purple Task has been moved from core 1 to core 0 to achieve a
"fully parallel" plan)_

Now that the Application has been completely optimized to be fully parallel, see
that the cores are *both* active on **5 time slots** _(over a period of 10 time
slots)_. Whereas before the optimization, both cores were active only on **2
time slots** _(over the same period)_, thus explaining the previous ratio of 2 /
5 = 40%.

Of course, this figure is a fairly theoretical view: the developer does not
"move around" frames from the RSF like this, they can only manipulate Elementary
Actions; running Tasks in parallel on several core is likely to cause hardware
interferences, leading to increased CPU budget times and reshuffling the RSF;
etc. Still, the ratio computed by the current implementation gives a meaningful
hint to the PsyC developer as to how much their Application leverages a
multi-core architecture, and how much more they could theoretically get,
assuming the same global CPU load.


## For developers

The issue tracker of this project is closed, but contributions are welcome: do
not hesitate to submit a pull-request!

Install extra dependencies to develop:

```sh
pip install "rsfstat[dev]"
```

Run tests with [pytest][4]:

```sh
# from the project root directory
pytest
```

This project uses [bump2version][5]: run this e.g. to bump the minor version
number, create and commit a tag:

```shell
bump2version minor
```

See `setup.cfg` for the configuration of *bump2version*.

[1]: https://aka.ms/terminal
[2]: https://conemu.github.io/
[3]: https://github.com/pypa/pipx
[4]: https://docs.pytest.org/
[5]: https://github.com/c4urself/bump2version
[6]: https://www.krono-safe.com
