.. _stats:

####################
Graphical statistics
####################

This plugin collects various statistics about emails traffic on your
server. It parses a log file to collect information, store it into RRD
files (see `rrdtool <http://oss.oetiker.ch/rrdtool/>`_) and then
generates graphics in PNG format.

To use it, go to the online parameters panel and adapt the following
ones to your environment:

+--------------------+--------------------+--------------------------+
|Name                |Description         |Default value             |
+====================+====================+==========================+
|Path to the log file|Path to log file    |/var/log/mail.log         |
|                    |used to collect     |                          |
|                    |statistics          |                          |
+--------------------+--------------------+--------------------------+
|Directory to store  |Path to directory   |/tmp/modoboa              |
|RRD files           |where RRD files are |                          |
|                    |stored              |                          |
+--------------------+--------------------+--------------------------+
|Directory to store  |Path to directory   |<modoboa_site>/media/stats|
|PNG files           |where PNG files are |                          |
|                    |stored              |                          |
+--------------------+--------------------+--------------------------+

Make sure the directory that will contain RRD files exists. If not,
create it before going further. For example (according to the previous
parameters)::

  $ mkdir /tmp/modoboa

To finish, you need to collect information periodically in order to
feed the RRD files. Add the following line into root's crontab::

  */5 * * * * <modoboa_site>/manage.py logparser &> /dev/null
  #
  # Or like this if you use a virtual environment:
  # 0/5 * * * * <virtualenv path/bin/python> <modoboa_site>/manage.py logparser &> /dev/null

Replace ``<modoboa_site>`` with the path of your Modoboa instance.

Graphics will be automatically created after each parsing.
