#!/usr/bin/python

import argparse
import sys
import subprocess

""" This script prints to stdout /etc/network/interfaces entries for
    requested interfaces.

    Currently it supports generation of interfaces(5) section for all
    swp interfaces on the system. And also an interface section 
    for a bridge with all swp ports.

    Example use of this script:

    generate the swp_defaults file:
    (bkup existing /etc/network/interfaces.d/swp_defaults file if one exists)

    #generate_interfaces.py -s > /etc/network/interfaces.d/swp_defaults

    User -m option if you want the new swp_defaults to be auto merged
    with the contents from the old file, use -m option

    #generate_interfaces.py -s -m /etc/network/interfaces.d/swp_defaults > /etc/network/interfaces.d/swp_defaults.new

    Include the swp_defaults file in /etc/network/interfaces file
    (if not already there) using the source command as shown below:

    source /etc/network/interfaces.d/swp_defaults

"""

def get_swp_interfaces():
    porttab_path = '/var/lib/cumulus/porttab'
    ports = []

    ptfile = open(porttab_path, 'r')
    for line in ptfile.readlines():
        line = line.strip()
        if '#' in line:
            continue
        try:
            ports.append(line.split()[0])
        except ValueError:
            continue
    return ports

def print_swp_defaults_header():
    print '''
# ** This file is autogenerated by /usr/share/doc/python-ifupdown2/generate_interfaces.py **
#
# This is /etc/network/interfaces section for all available swp
# ports on the system.
#
# To include this file in the main /etc/network/interfaces file,
# copy this file under /etc/network/interfaces.d/ and use the
# source line in the /etc/network/interfaces file.
#
# example entry in /etc/network/interfaces:
#   source /etc/network/interfaces.d/<filename>
#
# See manpage interfaces(5) for details.
'''

def print_bridge_untagged_defaults_header():
    print '''
# ** This file is autogenerated by /usr/share/doc/python-ifupdown2/generate_interfaces.py **
#
# This is /etc/network/interfaces section for a bridge device with all swp
# ports in the system.
#
# To include this file in the main /etc/network/interfaces file,
# copy this file under /etc/network/interfaces.d/ and use the
# source line in the /etc/network/interfaces file as shown below.
# details.
#
# example entry in /etc/network/interfaces:
#   source /etc/network/interfaces.d/filename
#
# See manpage interfaces(5) for details
'''

def interfaces_print_swp_default(swp_intf):
    outbuf = None
    if args.mergefile:
        try:
            cmd = ['/sbin/ifquery', '%s' %swp_intf, '-i', '%s' %args.mergefile]
            outbuf = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except Exception, e:
            # no interface found gen latest
            pass
    if not outbuf:
        outbuf = 'auto %s\niface %s\n\n' %(swp_intf, swp_intf)
    return outbuf

def interfaces_print_swp_defaults(swp_intfs):
    print_swp_defaults_header()
    outbuf = ''
    for i in swp_intfs:
        outbuf += interfaces_print_swp_default(i)
    print outbuf

def interfaces_print_bridge_default(swp_intfs):
    print_bridge_untagged_defaults_header()
    outbuf = 'auto bridge-untagged\n' 
    outbuf += 'iface bridge-untagged\n'
    outbuf += '  bridge-ports \\\n'
    linen = 5
    ports = ''
    for i in range(0, len(swp_intfs), linen):
        if ports:
            ports += ' \\\n'
        ports += '      %s' %(' '.join(swp_intfs[i:i+linen]))
    outbuf += ports
    print outbuf

def populate_argparser(argparser):
    group = argparser.add_mutually_exclusive_group(required=False)
    group.add_argument('-s', '--swp-defaults', action='store_true',
                       dest='swpdefaults', help='generate swp defaults file')
    group.add_argument('-b', '--bridge-default', action='store_true',
                       dest='bridgedefault',
                       help='generate default untagged bridge')
    argparser.add_argument('-m', '--merge', dest='mergefile', help='merge ' +
                           'new generated iface content with the old one')

argparser =  argparse.ArgumentParser(description='ifupdown interfaces file gen helper')
populate_argparser(argparser)
args = argparser.parse_args(sys.argv[1:])

if not args.swpdefaults and not args.bridgedefault:
    argparser.print_help()
    exit(1)

if args.bridgedefault and args.mergefile:
    print 'error: mergefile option currently only supported with -s'
    argparser.print_help()
    exit(1)

swp_intfs = get_swp_interfaces()
if not swp_intfs:
    print 'error: no ports found'
    exit(1)

if args.swpdefaults:
    interfaces_print_swp_defaults(swp_intfs)
elif args.bridgedefault:
    interfaces_print_bridge_default(swp_intfs)
else:
    argparser.print_help()
