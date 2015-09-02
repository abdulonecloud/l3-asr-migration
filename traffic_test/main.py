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


def get_routers():
    neutron = osutils.get_neutron_client_by_tenant()
    routers = neutron.list_routers()
    router_list = []
    for router in routers['routers']:
        if router['name'] != 'PHYSICAL_GLOBAL_ROUTER_ID':
            router_list.append(router)
    return router_list


def get_ports():
    neutron = osutils.get_neutron_client_by_tenant()
    return neutron.list_ports()


def get_subnet_detail(subnet):
    neutron = osutils.get_neutron_client_by_tenant()
    return neutron.show_subnet(subnet)


def get_instance_detail(instance):
    nova = osutils.get_nova_client_by_tenant()
    return nova.servers.get(instance)


def get_floatingips():
    neutron = osutils.get_neutron_client_by_tenant()
    return neutron.list_floatingips()


def get_router_ports(router):
    """
    Returns a list of router interface ports for a given router
    """
    ports = get_ports()
    router_port_list = []
    for port in ports['ports']:
        if (port['device_id'] == router['id'] and
                port['device_owner'] == 'network:router_interface'):
            router_port_list.append(port)
    return router_port_list


def get_port_subnets(port):
    """
    Using the subnets for a tenant, obtain IP for a given port
    """
    subnet = get_subnet_detail(port['fixed_ips'][0]['subnet_id'])['subnet']
    return {'id': port['fixed_ips'][0]['subnet_id'], 'name': subnet['name'],
            'ip_address': port['fixed_ips'][0]['ip_address']}


def get_subnet_endpoints(subnet):
    """
    Returns a list of vm ips for a a given subnet
    """
    endpoints = []
    ports = get_ports()
    for port in ports['ports']:
        endpoint_detail = {}
        if (port['fixed_ips'][0]['subnet_id'] == subnet['id'] and
                port['device_owner'] == 'compute:nova'):
            device_id = port['device_id'].encode('unicode_escape')
            ip = port['fixed_ips'][0]['ip_address'].encode('unicode_escape')
            endpoint_detail['device_id'] = device_id
            endpoint_detail['ip_address'] = ip
            endpoints.append(endpoint_detail)
    return endpoints


def get_endpoint_floatingips(ip):
    """
    returns floating ip for a given fixed-ip.
    """
    endpoint = ''
    for entry in get_floatingips()['floatingips']:
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


def get_traffic_testing_endpoint(src_tenant, dest_tenant,
                                 src_eps, dest_eps, contract):
    endpoint = {'src_tenant': src_tenant,
                'dest_tenant': dest_tenant,
                'src_eps': src_eps,
                'dest_eps': dest_eps,
                'contract': contract}
    return endpoint


def main():
    logger.info('Start the program')
    logger.info('Initialize OSUtils')
    endpoints_list = []
    logger.info('Get tenant details')
    router_data = {}
    floatingip_endpoints_list = []

    # retrieve all rotuers for a tenant
    routers = get_routers()
    for router in routers:
        router_detail = {}
        router_detail['id'] = router['id']
        router_detail['ports'] = get_router_ports(router)
        subnets = []
        instance_list = []
        for port in router_detail['ports']:
            subnets.append(get_port_subnets(port))
            router_detail['subnets'] = subnets
        for subnet in router_detail['subnets']:
            if subnet['id'] != '':
                endpoint_detail = get_subnet_endpoints(subnet)
                ip_list = []
                endpoint_list = []
                subnet['instances'] = endpoint_detail
                for entry in endpoint_detail:
                    server = get_instance_detail(entry['device_id'])
                    if entry['device_id'] not in instance_list and \
                       server.status == 'ACTIVE':
                        instance_list.append(entry['device_id'])
                        ip_list.append(entry['ip_address'])
                    endpoint_list.append({'instances': instance_list,
                                          'endpoints': ip_list})
                subnet['endpoints'] = ip_list
        router_data[router['name'].encode('unicode_escape')] = router_detail
    current_router = {}
    for route in routers:
        rsubnets = router_data[route['name']]['subnets']
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
    contract = get_default_icmp_contract()
    tenant = config['tenants']['tenants']
    if config['traffic']['type'] == 'intra-tenant':
        for route in routers:
            if route['name'] in current_router:
                rsubnets = router_data[route['name']]['subnets']
                for entry in rsubnets:
                    if entry['name'] in current_router[route['name']]:
                        net = current_router[route['name']][entry['name']]
                        if len(net['src_eps']) > 0 and \
                           len(net['dest_eps']) > 0:
                            endpoints_list.append(
                                get_traffic_testing_endpoint(tenant,
                                                             tenant,
                                                             net['src_eps'],
                                                             net['dest_eps'],
                                                             contract))
        logger.debug("endpoints list = %s" % (pprint.pformat(endpoints_list)))

    else:
        # inter-tenant
        for ip in endpoint_list:
            floating_ip = get_endpoint_floatingips(ip)
            if floating_ip != '':
                floatingip_endpoints_list.append(floating_ip)

        endpoints_list = \
            [get_traffic_testing_endpoint(tenant,
                                          tenant,
                                          floatingip_endpoints_list,
                                          floatingip_endpoints_list,
                                          contract)]
        logger.debug("endpoints list = %s" % (pprint.pformat(endpoints_list)))

    # src_ip_list =['192.168.61.131']
    # src_ip_list =['1.1.1.17']
    # dest_ip_list = ['192.168.61.229','192.168.61.132']
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

    if tid:
        remote_libs.start_task(config, endpoints_list, action, tid)
    else:
        remote_libs.start_task(config, endpoints_list, action)


if __name__ == '__main__':
    main()
