#!/usr/bin/env python
"""
Description: This script is to create network, subnets, router with \
             external gateway mapping.
Developer: gopal@onecloudinc.com
"""

import os
from neutronclient.v2_0 import client
from credentials import get_credentials
from config import NETWORK_COUNT, VM_COUNT, FLOATING_IP_CREATION
from vm_instances import launch_vm_on_network, terminate_vm_on_network
from floating_ips import release_all_floating_ips

credentials = get_credentials()
neutron = client.Client(**credentials)


def create_network(tenant, router, network_index, network_cidr):
    """
    This method is used to create network, subnets, interfaces on router with \
    external gateway mapping for the given network name and CIDR.
    """

    try:
        prefix = tenant['tenant_name']
        network_name = prefix + '-net-' + network_index
        print "\n"
        print "=" * 50
        print "   Initiated Network Creation for " + network_name
        print "=" * 50
        print "\n"

        body_sample = {'network': {'name': network_name,
                                   'tenant_id': tenant['tenant_id']}}
        try:
            net = neutron.create_network(body=body_sample)
            net_dict = net['network']
            network_id = net_dict['id']
            network_vlan = net_dict['provider:segmentation_id']
            print('   - Network %s created' % net_dict['name'])
            net_status = True
        except Exception:
            net_dict = {}
            net_status = False

        subnet_name = prefix + "-subnet-" + network_index
        try:
            tenant_id = tenant['tenant_id']
            body_create_subnet = {'subnets': [{'name': subnet_name,
                                               'cidr': network_cidr,
                                               'ip_version': 4,
                                               'network_id': network_id,
                                               'tenant_id': tenant_id}]}
            subnet_detail = neutron.create_subnet(body=body_create_subnet)
            subnet = subnet_detail['subnets'][0]
            print('   - Created subnet %s' % subnet['name'])
            net_status = True
        except Exception:
            subnet = {}
            net_status = False

        neutron.add_interface_router(router['id'], {'subnet_id': subnet['id'],
                                     'tenant_id': tenant['tenant_id']})
        print ('   - Created interface between %s' % subnet['name'])

    finally:
        print "\n"
        msg = "<== Completed Network Creation with External Gateway "
        msg += "Successfully ==>"
        print msg
    print "\n"
    print "=" * 50
    print "   Initiated VM Deployment " + network_name
    print "=" * 50
    print "\n"

    ins_data = []
    for i in range(1, VM_COUNT + 1):
        vm_name = network_name + '-vm-' + str(i)
        ins_data.append(launch_vm_on_network(tenant['tenant_name'],
                        vm_name, network_id))

    print "\n"
    msg = "<== Completed VM Launch on Network with Floating IP Allocation "
    msg += "Successfully ==>"
    print msg

    result = {'network_data': {'tenant_name': tenant['tenant_name'],
                               'network_name': network_name,
                               'network_cidr': network_cidr,
                               'subnet_name': subnet_name,
                               'network_id': network_id,
                               'network_vlan_id': network_vlan,
                               'status': net_status},
              'instance_data': ins_data}
    return result


def delete_network(tenant_name):
    """
    This method is used to delete vms, network, subnets, interfaces on router \
    with external gateway mapping for the given network name and CIDR.
    """
    prefix = tenant_name
    network_list = []
    router_list = []
    router_list.append(prefix + '-router')
    for i in range(1, NETWORK_COUNT + 1):
        network_list.append(prefix + '-net-' + str(i))
    for network_name in network_list:
        print "\n"
        print "=" * 50
        print "   Terminating VM launched on " + network_name
        print "=" * 50
        print "\n"
        for i in range(1, VM_COUNT + 1):
            vm_name = network_name + '-vm-' + str(i)
            terminate_vm_on_network(tenant_name, vm_name, network_name)
        print "\n"
        print("<== Completed VM Termination on Network ==>")
    networks = neutron.list_networks()['networks']
    routers = neutron.list_routers()['routers']
    print "\n"
    print "=" * 50
    print "   Initiated Network Deletion "
    print "=" * 50
    print "\n"
    for router in routers:
        if router['name'] in router_list:
            tenant_id = router['tenant_id']
            for network in networks:
                if network['name'] in network_list:
                    tenant_id = network['tenant_id']
                    subnets = neutron.list_subnets(
                        network_id=network['id'])['subnets']
                    for subnet in subnets:
                        ports = neutron.list_ports(
                            subnet_id=subnet['id'],
                            tenant_id=tenant_id)['ports']
                        for port in ports:
                            try:
                                neutron.delete_port(port['id'])
                            except:
                                pass
                            try:
                                neutron.remove_interface_router(
                                    router['id'], {'subnet_id': subnet['id']})
                            except:
                                pass

                        neutron.delete_subnet(subnet['id'])
                    neutron.delete_network(network['id'])
                    print "   Deleted " + network['name']
            print "\n"
            neutron.remove_gateway_router(router['id'])
            try:
                neutron.delete_router(router['id'])
            except:
                pass
            print "   Deleted " + router['name']
    print "\n"
    msg = "<== Completed Network, Router Deletion from External Gateway "
    msg += "Successfully ==>"
    print msg
    if FLOATING_IP_CREATION:
        release_all_floating_ips()
        print "\n"
        print("<== Released all Floating IPs Successfully ==>")
    return True
