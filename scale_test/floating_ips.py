#!/usr/bin/env python
"""
Description: This script is to allocate & associate the floating IP.
Developer: gopal@onecloudinc.com
"""

import os
from neutronclient.v2_0 import client
import novaclient.v1_1.client as nvclient
from credentials import get_credentials, get_nova_credentials, \
    get_tenant_nova_credentials
from config import FLOATING_IP_POOL

neutron_credentials = get_credentials()
credentials = get_nova_credentials()
neutron = client.Client(**neutron_credentials)
nova = nvclient.Client(**credentials)
if not nova.keypairs.findall(name="admin"):
    with open(os.path.expanduser('~/.ssh/id_rsa.pub')) as fpubkey:
        nova.keypairs.create(name="admin", public_key=fpubkey.read())


def add_floating_ip_for_vm(tenant_name, instance):
    """
    This method is used to allocate & associate floating IP to the given VM\
    based on the availability from the defined pool.
    """
    tenant_credentials = get_tenant_nova_credentials(tenant_name)
    nova = nvclient.Client(**tenant_credentials)
    floating_ip = nova.floating_ips.create(FLOATING_IP_POOL)
    instance.add_floating_ip(floating_ip)
    print "   - Assigned Floating IP: " + str(floating_ip.ip)
    return True


def release_all_floating_ips():
    """
    This method is used to release all the disallocated floating IPs.
    """
    floating_ips = neutron.list_floatingips()['floatingips']
    try:
        for ip in floating_ips:
            neutron.delete_floatingip(ip['id'])
    except:
        pass
    return True
