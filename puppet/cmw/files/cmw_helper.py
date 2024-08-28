#!/usr/bin/env python
##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################
import sys
import yum
import tarfile
import tempfile
import subprocess
import simplejson
import os


def check_rpms(pkgs):
    yb = yum.YumBase()
    yb.conf.cache = 0
    for repo in yb.repos.listEnabled():
        yb.repos.disableRepo(repo.id)
    yb.repos.enableRepo("OS")
    for pkg_name in pkgs:
        yb.install(name=pkg_name)
    yb.resolveDeps()
    f = open("/tmp/cmw_helper.out", "wb")
    for m in yb.tsInfo.getMembers():
        f.write(m.name + "\n")
    f.close()


def rpm_files(tarfile):
    for tarinfo in tarfile:
        if os.path.splitext(tarinfo.name)[1] == ".rpm":
            yield tarinfo


def exec_cmd(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    dummy_ret = p.wait()
    stdout = p.stdout.read().strip()
    stderr = p.stderr.read().strip()
    return p.returncode, stdout, stderr


def verify_rpms(sdp_location, sdp_name):
    tmp_loc = tempfile.mkdtemp()
    filepath = sdp_location + "/" + sdp_name
    result = dict()
    result["result"] = "NOK"
    result["output"] = ""

    if not tarfile.is_tarfile(filepath):
        return result

    tar = tarfile.open(filepath)
    tar.extractall(path=tmp_loc, members=rpm_files(tar))
    tar.close()

    for p, _, files in os.walk(tmp_loc):
        if files:
            for f in files:
                rpm_path = os.path.join(p, f)
                cmd = "rpm --test --replacepkgs -Uvh {0}"\
                    .format(rpm_path)
                r, o, e = exec_cmd(cmd)

                result["result"] = r
                if r == 0:
                    result["output"] = o
                else:
                    result["output"] = e
    return result


def main(argv):
    infilename = argv[0]
    outfilename = argv[1]

    infile = open(infilename, 'r')
    in_stuff = simplejson.load(infile)
    infile.close()

    path = in_stuff["data"]["path"]
    sdpfile = in_stuff["data"]["sdp_name"]

    result = verify_rpms(arg_list[0], arg_list[1])

    outfile = open(outfilename, 'w')
    reply = {}
    reply["retcode"] = result["result"]
    reply["out"] = result["output"]
    reply["err"] = ""
    simplejson.dump(reply, outfile)
    outfile.close()

    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv[1:])
