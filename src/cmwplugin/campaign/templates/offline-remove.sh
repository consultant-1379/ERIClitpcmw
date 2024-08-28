#!/bin/sh
#
# This procedure looks in a base directory after a defined file structure and
# removes any rpms that it finds according to certain rules.
#
# One arguments are given:
# $1 - The base directory of this SDP
#
# Rules:
# 1) RPMs are packaged in the SDP under a 'rpms' directory
# 2) Any *.rpm files located directly under rpms will be removed from all nodes.
# 3) RPMs that should be removed from a sub-set of nodes should be located in a
#    special directory. Two special directories are managed: payload and control
# 4) Any *.rpm files located under 'rpms/control' will be removed from nodes
#    with TIPC address 1 and 2
# 5) Any *.rpm files located under 'rpms/payload' will be removed from nodes
#    with TIPC address 3 and larger.
#
die () {
  echo "ERROR: $@"
  exit 1
}

remove_rpms ()
{
  local sdpdir=$1/rpms
  local host=`hostname`
  local rpmname

    for file in `ls ${sdpdir}/*.rpm 2>/dev/null`
    do
        rpmfile=`basename $file`
        rpmname=`grep $rpmfile ${sdpdir}/rpm.list | sed "s/${rpmfile}://"`
        test -n "${rpmname}" || continue
        cmwea rpm-config-delete $rpmname $host || die "Failed to remove $rpmname on $host"
        echo "HUZH remove 1 RPM $file"
    done
}

remove_rpms `dirname $0`