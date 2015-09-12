import os
import logging
import logging.config
from libs import os_get_env as os_lib
from libs import traf_tester as remote_libs
from configobj import ConfigObj
from argparse import ArgumentParser
import pprint

if not os.path.exists('logs'):
    os.makedirs('logs')
logging.config.fileConfig('conf/logging.ini')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

action_list = ['start', 'stop']
parser = ArgumentParser(description="Datapath traffic testing")
parser.add_argument("-f", "--cfgfile", required=True, metavar="FILE")
parser.add_argument("-a", "--action", required=True)
parser.add_argument("-t",
                    "--tid",
                    required=True,
                    help="Timestamp ID to reference for labeling test output")
args = parser.parse_args()
cfgfile = args.cfgfile
config = ConfigObj(cfgfile)
action = args.action
tid = args.tid if args.tid else None

osutils = os_lib.OSUtils(config)


def get_routers(tenant):
    neutron = osutils.get_neutron_client_by_tenant(tenant[1])
    routers = neutron.list_routers()['routers']
    routers = [router for router in routers if router['tenant_id'] == tenant[0]]
    router_list = []
    for router in routers:
        if router['name'] != 'PHYSICAL_GLOBAL_ROUTER_ID':
            router_list.append(router)
    return router_list


def get_ports(tenant):
    neutron = osutils.get_neutron_client_by_tenant(tenant[1])
    ports = neutron.list_ports()['ports']
    port_list = [port for port in ports if port['tenant_id'] == tenant[0]]
    return port_list


def get_subnet_detail(tenant, subnet):
    neutron = osutils.get_neutron_client_by_tenant(tenant[1])
    return neutron.show_subnet(subnet)


def get_instance_detail(tenant, instance):
    nova = osutils.get_nova_client_by_tenant(tenant[1])
    return nova.servers.get(instance)


def get_floatingips(tenant):
    neutron = osutils.get_neutron_client_by_tenant(tenant[1])
    return neutron.list_floatingips()


def get_router_ports(router, ports):
    """
    Returns a list of router interface ports for a given router
    """
    router_port_list = []
    for port in ports:
        if (port['device_id'] == router['id'] and
                port['device_owner'] == 'network:router_interface'):
            router_port_list.append(port)
    return router_port_list


def get_port_subnets(tenant, port):
    """
    Using the subnets for a tenant, obtain IP for a given port
    """
    subnet = get_subnet_detail(tenant, port['fixed_ips'][0]['subnet_id'])['subnet']
    return {'id': port['fixed_ips'][0]['subnet_id'], 'name': subnet['name'],
            'ip_address': port['fixed_ips'][0]['ip_address']}



def get_instance_ports(ports):
    """
    Returns a list of instance interface ports
    """
    instance_port_list = []
    for port in ports:
        if port['device_owner'] == 'compute:nova':
            instance_port_list.append(port)
    return instance_port_list



def get_subnet_endpoints(tenant, ports, subnet):
    """
    Returns a list of vm ips for a a given subnet
    """
    endpoints = []
    for port in ports:
        endpoint_detail = {}
        if port['fixed_ips'][0]['subnet_id'] == subnet['id']:
            device_id = port['device_id'].encode('unicode_escape')
            ip = port['fixed_ips'][0]['ip_address'].encode('unicode_escape')
            endpoint_detail['device_id'] = device_id
            endpoint_detail['ip_address'] = ip
            endpoints.append(endpoint_detail)
    return endpoints


def get_endpoint_floatingips(tenant, ip):
    """
    Returns floating ip for a given fixed-ip.
    """
    endpoint = ''
    for entry in get_floatingips(tenant)['floatingips']:
        if entry['fixed_ip_address'] == ip:
            endpoint = entry['floating_ip_address']
    return endpoint.encode('unicode_escape')


def get_default_icmp_contract():
    contract = [{'name': 'allow_icmp',
                 'protocol': 'icmp',
                 'port': 'None',
                 'direction': 'in',
                 'action': 'allow'}]
    return contract


def get_default_tcp_contract():
    contract = [{'name': 'allow_ssh',
                 'protocol': 'tcp',
                 'port': '22',
                 'direction': 'in',
                 'action': 'allow'}]
    return contract


def get_default_udp_contract():
    contract = [{'name': 'allow_udp',
                 'protocol': 'udp',
                 'port': 'None',
                 'direction': 'in',
                 'action': 'allow'}]
    return contract


def get_traffic_testing_endpoint(src_tenant, dest_tenant,
                                 src_eps, dest_eps, contract, test_type):
    endpoint = {'src_tenant': src_tenant,
                'dest_tenant': dest_tenant,
                'src_eps': src_eps,
                'dest_eps': dest_eps,
                'contract': contract,
                'test_type': test_type}
    return endpoint


def main():
    logger.info('Start the program')
    logger.info('Initialize OSUtils')
    endpoints_list = []
    endpoint_list = []
    logger.info('Get tenant details')
    tenants = osutils.get_tenants_list()
    tenant_data = {}
    routers = {}
    for tenant in tenants.items():
        router_data = {}
        # retrieve all rotuers for a tenant
        routers = get_routers(tenant)
        ports = get_ports(tenant)
        instance_ports = get_instance_ports(ports)
        for router in routers:
            router_detail = {}
            router_detail['id'] = router['id']
            router_detail['ports'] = get_router_ports(router, ports)
            subnets = []
            instance_list = []
            for port in router_detail['ports']:
                subnets.append(get_port_subnets(tenant, port))
                router_detail['subnets'] = subnets
            for subnet in router_detail['subnets']:
                if subnet['id'] != '':
                    endpoint_detail = get_subnet_endpoints(tenant, instance_ports, subnet)
                    ip_list = []
                    endpoint_list = []
                    subnet['instances'] = endpoint_detail
                    for entry in endpoint_detail:
                        server = get_instance_detail(tenant, entry['device_id'])
                        if entry['device_id'] not in instance_list and \
                           server.status == 'ACTIVE':
                            instance_list.append(entry['device_id'])
                            ip_list.append(entry['ip_address'])
                        endpoint_list.append({'instances': instance_list,
                                              'endpoints': ip_list})
                    subnet['endpoints'] = ip_list
            router_data[router['name'].encode('unicode_escape')] = router_detail
        tenant_data[tenant[1]] = router_data
    # print tenant_data
    
    test_method = config['traffic']['test_method']
    contract = []
    if 'icmp' in test_method or len(test_method) == 0:
        contract.append(get_default_icmp_contract()[0])
    if 'tcp' in test_method:
        contract.append(get_default_tcp_contract()[0])
    if 'udp' in test_method:
        contract.append(get_default_udp_contract()[0])
    tenant = config['tenants']['tenants']
    
    if config['traffic']['type'] == 'intra-tenant' or config['traffic']['type'] == 'all':
        # intra-tenant
        for tenant in tenants.items():
            current_router = {}
            current_net = {}
            routers = get_routers(tenant)
            for route in routers:
                rsubnets = tenant_data[tenant[1]][route['name']]['subnets']
                if len(rsubnets) > 1:
                    current_net = {}
                    for entry in rsubnets:
                        tsrc = []
                        tdest = []
                        tsrc.append(entry['endpoints'])
                        for nextep in rsubnets:
                            if entry['name'] != nextep['name']:
                                tdest.append(nextep['endpoints'])
                        subnet_data = {'src_eps': [ep for eps in tsrc for ep in eps],
                                       'dest_eps': [ep for eps in tdest for ep in eps]}
                        current_net[entry['name']] = subnet_data
                current_router[route['name']] = current_net
    
            for route in routers:
                if route['name'] in current_router:
                    rsubnets = tenant_data[tenant[1]][route['name']]['subnets']
                    for entry in rsubnets:
                        if entry['name'] in current_router[route['name']]:
                            net = current_router[route['name']][entry['name']]
                            if len(net['src_eps']) > 0 and \
                               len(net['dest_eps']) > 0:
                                endpoints_list.append(
                                    get_traffic_testing_endpoint(tenant[1],
                                                                 tenant[1],
                                                                 net['src_eps'],
                                                                 net['dest_eps'],
                                                                 contract,
                                                                 'intra-tenant'))

    if config['traffic']['type'] == 'inter-tenant' or config['traffic']['type'] == 'all':
        # inter-tenant
        for tenant in tenants.items():
            current_router = {}
            current_net = {}
            routers = get_routers(tenant)
            for route in routers:
                rsubnets = tenant_data[tenant[1]][route['name']]['subnets']
                if len(rsubnets) > 0:
                    current_net = {}
                    tsrc = []
                    tdest = []
                    for entry in rsubnets:
                        tsrc.append(entry['endpoints'])
                    src_eps = [ep for eps in tsrc for ep in eps]
                    for nexttenant in tenants.items():
                        if tenant[1] != nexttenant[1]:
                            for nroute in tenant_data[nexttenant[1]]:
                                for entry in tenant_data[nexttenant[1]][nroute]['subnets']:
                                    if len(rsubnets) > 0:
                                        for ip in entry['endpoints']:
                                            floating_ip = get_endpoint_floatingips(nexttenant, ip)
                                            if floating_ip != '':
                                                tdest.append(floating_ip)
                            dest_eps = tdest
                            if len(src_eps) > 0 and len(dest_eps) > 0:
                                endpoints_list.append(
                                    get_traffic_testing_endpoint(tenant[1],
                                                                 nexttenant[1],
                                                                 src_eps,
                                                                 dest_eps,
                                                                 contract,
                                                                 'inter-tenant'))

    if config['traffic']['type'] == 'south-north' or config['traffic']['type'] == 'all':
        # south-north
        for tenant in tenants.items():
            current_router = {}
            current_net = {}
            routers = get_routers(tenant)
            for route in routers:
                rsubnets = tenant_data[tenant[1]][route['name']]['subnets']
                if len(rsubnets) > 0:
                    current_net = {}
                    tsrc = []
                    for entry in rsubnets:
                        tsrc.append(entry['endpoints'])
                    src_eps = [ep for eps in tsrc for ep in eps]
                    if config['external_host']['host'] != '':
                        dest_eps = [config['external_host']['host']]
                    else:
                        dest_eps = []
                        print "Please specify external host in the config"
                    if len(src_eps) > 0 and len(dest_eps) > 0:
                        endpoints_list.append(
                            get_traffic_testing_endpoint(tenant[1],
                                                         'External Host',
                                                         src_eps,
                                                         dest_eps,
                                                         contract,
                                                         'south-north'))

    if config['traffic']['type'] == 'north-south' or config['traffic']['type'] == 'all':
        # north-south
        for tenant in tenants.items():
            current_router = {}
            current_net = {}
            routers = get_routers(tenant)
            for route in routers:
                rsubnets = tenant_data[tenant[1]][route['name']]['subnets']
                if len(rsubnets) > 0:
                    current_net = {}
                    tdest = []
                    if config['external_host']['host'] != '':
                        src_eps = [config['external_host']['host']]
                    else:
                        src_eps = []
                        print "Please specify external host in the config"
                    for entry in rsubnets:
                        for ip in entry['endpoints']:
                            floating_ip = get_endpoint_floatingips(tenant, ip)
                            if floating_ip != '':
                                tdest.append(floating_ip)
                    dest_eps = tdest
                    if len(src_eps) > 0 and len(dest_eps) > 0:
                        endpoints_list.append(
                            get_traffic_testing_endpoint('External Host',
                                                         tenant[1],
                                                         src_eps,
                                                         dest_eps,
                                                         contract,
                                                         'north-south'))
    logger.debug("endpoints list = %s" % (pprint.pformat(endpoints_list)))


    #src_ip_list = ['192.168.61.131']
    # src_ip_list =['1.1.1.17']
    # dest_ip_list = ['192.168.61.229','192.168.61.132']
    #dest_ip_list = ['192.168.61.129', '192.168.61.132']
    # dest_ip_list = ['10.1.25.128', '10.1.25.129', '10.1.25.130']
    # dest_ip_list = ['1.1.1.15','1.1.1.16','2.2.2.5','2.2.2.6']
    # contract = [{'name': 'allow_ssh',
    #             'protocol': 'tcp',
    #             'port': 22,
    #             'direction': 'in',
    #             'action': 'allow'},
    #            {'name': 'allow_icmp',
    #             'protocol': 'icmp',
    #             'port': 'None',
    #             'direction': 'in',
    #             'action': 'allow'}]

    # endpoints = {'src_tenant': 'dummy_tenant',
    #             'dest_tenant': 'dummy_tenant',
    #             'src_eps': src_ip_list,
    #             'dest_eps': dest_ip_list,
    #             'contract': contract}
    # endpoints_list = [endpoints]

    # # endpoints = {'src_tenant': 'sample',
    # #             'dest_tenant': 'sample',
    # #             'src_eps': src_ip_list,
    # #             'dest_eps': dest_ip_list,
    # #             'contract': contract}
    # # endpoints_list = [endpoints]


    if tid:
        remote_libs.start_task(config, endpoints_list, action, tid)
    else:
        remote_libs.start_task(config, endpoints_list, action)


if __name__ == '__main__':
    main()
