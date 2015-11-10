#!/usr/bin/env python

"""
Description: This script is to initialize the L3/HA scale test deployment
Developer: gopal@onecloudinc.com
"""

import os
from neutronclient.v2_0 import client
from credentials import get_credentials
from config import TENANT_BASE_INDEX, NETWORK_COUNT, \
    EXTERNAL_NETWORK, print_scale_test_config, DEPLOYMENT_ID, \
    ASR_HOST, ASR_USER, ASR_PASSWORD, ENABLE_ASR_VERIFICATION, TENANT_COUNT, \
    TENANT_NAME_PREFIX
from tenants import create_tenant
from networks import create_network
from prettytable import PrettyTable
from asr import GetASRCmd

credentials = get_credentials()
neutron = client.Client(**credentials)


def print_tenant_info(tenant_data):
    x = PrettyTable(['Tenant Name', 'Status'])
    x.align["Tenant Name"] = "l"   # Left align source tenant values
    x.padding_width = 1
    for entry in tenant_data:
        x.add_row([entry['tenant_name'], entry['status']])
    return x


def print_router_info(router_data):
    x = PrettyTable(['Tenant Name', 'Router Name', 'Status'])
    x.align["Tenant Name"] = "l"   # Left align source tenant values
    x.padding_width = 1
    for entry in router_data:
        x.add_row([entry['tenant_name'], entry['router_name'],
                  entry['router_status']])
    return x


def print_network_info(test_data):
    y = PrettyTable(['Tenant Name', 'Network Name', 'Network CIDR',
                    'Vlan ID', 'Subnet Name', 'Status'])
    y.align["Tenant_Name"] = "l"   # Left align source tenant values
    y.padding_width = 1
    for entry in test_data:
        y.add_row([entry['network_data']['tenant_name'],
                  entry['network_data']['network_name'],
                  entry['network_data']['network_cidr'],
                  entry['network_data']['network_vlan_id'],
                  entry['network_data']['subnet_name'],
                  entry['network_data']['status']])
    return y


def print_instance_info(test_data):
    z = PrettyTable(['Tenant Name', 'Instance Name', 'Status'])
    z.align["Tenant Name"] = "l"   # Left align source tenant values
    z.padding_width = 1
    for data in test_data:
        for ins in data['instance_data']:
            z.add_row([data['network_data']['tenant_name'],
                      ins['instance_name'],
                      ins['status']])
    return z


def asr_router_vrf_info(router_data):
    x = PrettyTable(['Tenant Name', 'Router Name', 'Router VRF Name',
                    'Interfaces', 'Status'])
    x.align["Tenant Name"] = "l"   # Left align source tenant values
    x.padding_width = 2
    for entry in router_data:
        interfaces = ', '.join(entry['router_detail']['interfaces'])
        x.add_row([entry['tenant_name'], entry['router_name'],
                  entry['router_detail']['vrfname'],
                  interfaces,
                  entry['router_detail']['status']])
    return x


def asr_ipnat_pool_info(router_data):
    x = PrettyTable(['Tenant Name', 'Router Name', 'Router VRF Name',
                     'NAT Pool Name', 'Start IP', 'End IP', 'Netmask',
                     'Status'])
    x.align["Tenant Name"] = "l"   # Left align source tenant values
    x.padding_width = 2
    for entry in router_data:
        x.add_row([entry['tenant_name'], entry['router_name'],
                   entry['ipnatpool_data']['vrfname'],
                   entry['ipnatpool_data']['nat_pool_name'],
                   entry['ipnatpool_data']['start_ip'],
                   entry['ipnatpool_data']['end_ip'],
                   entry['ipnatpool_data']['netmask'],
                  entry['ipnatpool_data']['status']])
    return x


def asr_iproute_info(router_data):
    x = PrettyTable(['Tenant Name', 'Router Name', 'Router VRF Name',
                     'Prefix', 'Mask', 'Interface', 'Next Hop Address',
                     'Status'])
    x.align["Tenant Name"] = "l"   # Left align source tenant values
    x.padding_width = 2
    for entry in router_data:
        x.add_row([entry['tenant_name'], entry['router_name'],
                   entry['iproute_data']['vrfname'],
                   entry['iproute_data']['prefix'],
                   entry['iproute_data']['mask'],
                   entry['iproute_data']['interface'],
                   entry['iproute_data']['next_hop_address'],
                   entry['iproute_data']['status']])
    return x


def asr_network_vrf_info(router_data):
    y = PrettyTable(['Tenant Name', 'Router Name', 'Network Name',
                     'Interface VRF Name', 'Internet Address',
                     'Vlan ID', 'Interfaces Status', 'Status'])
    y.align["Tenant Name"] = "l"   # Left align source tenant values
    y.padding_width = 2
    for entry in router_data:
        for interface in entry['interface_data']:
            y.add_row([entry['tenant_name'], entry['router_name'],
                       entry['network_vlan'][interface['vlan_id']],
                       interface['interface_name'], interface['ip_address'],
                       interface['vlan_id'], interface['interface_status'],
                       interface['status']])
    return y


def asr_interface_nat_info(router_data):
    y = PrettyTable(['Tenant Name', 'Router Name', 'Network Name',
                     'Interface Vlan ID', 'Dynamic NAT Entry',
                     'Access-list Entry', 'Status'])
    y.align["Tenant Name"] = "l"   # Left align source tenant values
    y.padding_width = 2
    for entry in router_data:
        for interface in entry['nat_data']:
            y.add_row([entry['tenant_name'], entry['router_name'],
                       entry['network_vlan'][interface['vlan_id']],
                       interface['vlan_id'], interface['nat_entry'],
                       interface['access_list_entry'], interface['status']])
    return y


def main():
    """
    This method will initialize the scale test deployment based on the global \
    config parameters mentioned on config.py file and creates the router with \
    external gateway connectivity to public network.
    """

    print "\n"
    print_scale_test_config()
    print "\n"
    print "Starting Scale Test Deployment"

    tenant_data = []
    index = TENANT_BASE_INDEX
    for i in range(1, TENANT_COUNT + 1):
        tenant_name = TENANT_NAME_PREFIX + '-' + str(index)
        index += 1
        try:
            tenant_data.append(create_tenant(tenant_name))
        except Exception as exc:
            print "Exception accoured on Tenant Creation: %s" % (exc.message)
            pass

    router_data = []
    test_data = []
    for tenant in tenant_data:
        router_dict = {}
        prefix = tenant['tenant_name']
        router_name = prefix + '-router'
        router_dict['tenant_name'] = tenant['tenant_name']
        router_dict['router_name'] = router_name
        router_dict['network_vlan'] = {}
        router_dict['router_detail'] = {}
        router_dict['ipnatpool_data'] = {}
        router_dict['iproute_data'] = {}
        router_dict['interface_data'] = []
        router_dict['nat_data'] = []

        router = neutron.list_routers(name=router_name)['routers']
        if not router:
            router_info = neutron.create_router({'router': {
                'name': router_name, 'tenant_id': tenant['tenant_id']}})
            router = router_info['router']
            status = True
        elif router[0]['tenant_id'] == tenant['tenant_id']:
            router = router[0]
            status = True
        else:
            router = {}
            status = False

        router_dict['router_status'] = status
        networks = neutron.list_networks(name=EXTERNAL_NETWORK)
        network_id = networks['networks'][0]['id']
        neutron.add_gateway_router(router['id'],
                                   {'network_id': network_id,
                                    'tenant_id': tenant['tenant_id']})
        router_id = router['id']
        print('   - Created Router %s' % router['name'])

        for i in range(1, NETWORK_COUNT + 1):
            network_index = str(i)
            network_cidr = str(i) + "." + str(i) + "." + str(i) + ".0/24"
            test_data.append(create_network(tenant, router,
                             network_index, network_cidr))

        network_vlan = {}
        for entry in test_data:
            network_vlan[str(entry['network_data']['network_vlan_id'])] = \
                entry['network_data']['network_name']
        router_dict['network_vlan'] = network_vlan

        if ENABLE_ASR_VERIFICATION:
            vrf_router_id = router_id[:6]
            vrfname = "nrouter" + '-' + vrf_router_id + '-' + DEPLOYMENT_ID

            asr_verify_cmd = GetASRCmd(asr_host=ASR_HOST,
                                       asr_host_port=22,
                                       asr_user=ASR_USER,
                                       asr_password=ASR_PASSWORD,
                                       asr_slots=["0"])
            router_detail = {'vrfname': vrfname, 'interfaces': '',
                             'status': ''}
            ipnatpool_data = {'vrfname': vrfname, 'nat_pool_name': '',
                              'start_ip': '', 'end_ip': '', 'netmask': '',
                              'status': ''}
            iproute_data = {'vrfname': vrfname, 'prefix': '', 'mask': '',
                            'interface': '', 'next_hop_address': '',
                            'status': ''}
            interface_data = []
            nat_data = []
            try:
                router_detail = asr_verify_cmd.get_router_detail(vrfname)
                ipnatpool_data = asr_verify_cmd.get_ipnat_pool_detail(vrfname)
                iproute_data = asr_verify_cmd.get_iproute_detail(vrfname)
                for interface in router_detail['interfaces']:
                    interface_data.append(
                        asr_verify_cmd.get_network_interface_detail(vrfname,
                                                                    interface))
                for interface in interface_data:
                    interfaceid = DEPLOYMENT_ID + '_' + interface['vlan_id']
                    nat_data.append(
                        asr_verify_cmd.get_interface_nat_access_detail(
                            interface['vlan_id'], interfaceid))
                asr_report = True
            except Exception as exc:
                print "\n"
                print "[ERROR] Caught exception on ASR Verification : %s" % \
                    (exc.message)
                print "\n"
                asr_report = False
            router_dict['router_detail'] = router_detail
            router_dict['ipnatpool_data'] = ipnatpool_data
            router_dict['iproute_data'] = iproute_data
            router_dict['interface_data'] = interface_data
            router_dict['nat_data'] = nat_data
        router_data.append(router_dict)
    print "=" * 50
    print "\n"
    print "Scale Test Deployment Completed"
    print "\n"

    print "*" * 80
    print "Scale Test Deployment OpenStack Report"
    print "*" * 80

    print "\n"
    print "           Tenant Creation Results      "
    print print_tenant_info(tenant_data)
    print "\n"
    print "           Router Creation Results      "
    print print_router_info(router_data)
    print "\n"
    print "                 Network Creation Results      "
    print print_network_info(test_data)
    print "\n"

    print "            Instance Creation Results      "
    print print_instance_info(test_data)
    print "\n"

    if ENABLE_ASR_VERIFICATION and asr_report:
        print "           OpenStack-ASR Router VRF Verification Results      "
        print asr_router_vrf_info(router_data)
        print "\n"

        print "           OpenStack-ASR IP NAT Pool Verification Results     "
        print asr_ipnat_pool_info(router_data)
        print "\n"
        print "           OpenStack-ASR IP Route Verification Results        "
        print asr_iproute_info(router_data)
        print "\n"

        print "           OpenStack-ASR Network VRF Verification Results     "
        print asr_network_vrf_info(router_data)
        print "\n"

        print("           OpenStack-ASR Network Interface's Dynamic NAT & "
              "Access list Entry Verification Results              ")
        print asr_interface_nat_info(router_data)
        print "\n"

if __name__ == '__main__':
    main()
