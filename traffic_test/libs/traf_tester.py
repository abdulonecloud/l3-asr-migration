import fabric
from fabric.api import *
import os
import sys
import logging
import time
import re
from multiprocessing import Pool, Process, Queue
from prettytable import PrettyTable
import json
from itertools import *
from operator import *

path = os.getcwd() + '/scripts'
os.path.join(path)

test_results_path = '~/dp_test_results'

logger = logging.getLogger(__name__)

def unique_justseen(iterable, key=None):
    "List unique elements, preserving order. Remember only the element just seen."
    return imap(next, imap(itemgetter(1), groupby(iterable, key)))


def setup_env(config, endpoints):
    endpoints = endpoints
    test_results_path = config['traffic']['test_results_path']
    test_method = config['traffic']['test_method']
    delta = config['traffic']['allowed_delta_percentage']
    env.hosts = endpoints['src_eps']
    env.user = config['traffic']['remote_user']
    env.password = config['traffic']['remote_pass']
    env.skip_bad_hosts = True
    # env.gateway = config['traffic']['ssh_gateway']
    if endpoints['test_type'] != 'north-south':
        env.gateway = config['tenant_ssh_gateway'][endpoints['src_tenant']]
    else:
        env.gateway = config['tenant_ssh_gateway'][endpoints['dest_tenant']]
    logger.info("Initailized the environment with Endpoints")
    logger.info("test_results_path : %s" % (test_results_path))
    logger.info("test_method : %s" % (test_method))
    logger.info("traffic allowed delta : %s" % (delta))


def get_test_cmd(test_method):
    pass


def install_hping(environment):
    try:
        out = run("python -c 'import platform;"
                  " print platform.linux_distribution()[0]'")
        os_info = out
        logger.debug("Host %s runs %s" % (env.host_string, os_info))
        if out.return_code == 0:
            if os_info in ['CentOS',
                           'Red Hat Enterprise Linux Server',
                           'Fedora']:
                out = sudo("yum -y install hping3")
                if out.return_code == 0:
                    logger.info("Installed hping3 on %s" % (env.host_string))
            elif os_info in ['Ubuntu','LinuxMint']:
                out = sudo("apt-get -y install hping3")
                if out.return_code == 0:
                    logger.info("Installed hping3 on %s" % (env.host_string))
        out = run("mkdir %s" % (test_results_path))
    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


def install_iperf(environment):
    try:
        out = run("python -c 'import platform;"
                  " print platform.linux_distribution()[0]'")
        os_info = out
        logger.debug("Host %s runs %s" % (env.host_string, os_info))
        if out.return_code == 0:
            if os_info in ['CentOS',
                           'Red Hat Enterprise Linux Server',
                           'Fedora']:
                out = sudo("yum -y install iperf3")
                if out.return_code == 0:
                    logger.info("Installed iperf3 on %s" % (env.host_string))
            elif os_info in ['Ubuntu','LinuxMint']:
                out = sudo("apt-get -y install iperf3")
                if out.return_code == 0:
                    logger.info("Installed iperf3 on %s" % (env.host_string))
        out = run("mkdir %s" % (test_results_path))
    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))



def setup_iperf_env(config, src_tenant, dest_tenant, endpoints, test_type):
    endpoints = endpoints
    test_results_path = config['traffic']['test_results_path']
    test_method = config['traffic']['test_method']
    delta = config['traffic']['allowed_delta_percentage']
    env.hosts = endpoints
    env.user = config['traffic']['remote_user']
    env.password = config['traffic']['remote_pass']
    env.skip_bad_hosts = True
    # env.gateway = config['traffic']['ssh_gateway']
    if test_type != 'north-south':
        env.gateway = config['tenant_ssh_gateway'][src_tenant]
    else:
        env.gateway = config['tenant_ssh_gateway'][dest_tenant]
    logger.info("Initailized the environment with Endpoints")
    logger.info("test_results_path : %s" % (test_results_path))
    logger.info("test_method : %s" % (test_method))
    logger.info("traffic allowed delta : %s" % (delta))


def pretty_table_content(config, data):
    x = PrettyTable(["src_tenant",
                     "src_ep",
                     "dest_tenant",
                     "dest_ep",
                     "packets_transmitted",
                     "packets received",
                     "packet_loss %",
                     "rtt_min",
                     "rtt_avg",
                     "rtt_max",
                     "test_status"])

    x.align["src_tenant"] = "l"  # Left align source tenant values

    # One space between column edges and contents (default)
    x.padding_width = 1
    status = None

    dest_ep_regex = ".*-*-(?P<dest_ip>[0-9]+_[0-9]+_[0-9]+_[0-9]+)-.*"
    for content in data:
        for k, v in content.items():
            src_ep = k
            src_tenant = v['src_tenant']
            dest_tenant = v['dest_tenant']
            # out = v['test_result'].split(',')
            test_result_files = v['test_result'].keys()

            for test_result_file in test_result_files:

                dest_ep_match = re.match(dest_ep_regex, test_result_file)

                dest_ep = dest_ep_match.group('dest_ip')
                packet_stats = \
                    v['test_result'][test_result_file]['packet_stats']

                packet_loss_percent = \
                    packet_stats['packet_loss']  # NOQA

                try:
                    if (packet_loss_percent <= int(config['traffic']['allowed_delta_percentage'])):  # NOQA
                            status = 'Success'
                    else:
                        status = 'Failed'
                except ValueError:
                    status = 'Failed'

                rtt_stats = v['test_result'][test_result_file]['rtt']

                x.add_row([src_tenant, src_ep,
                           dest_tenant, dest_ep.replace('_', '.'),
                           packet_stats['packets_transmitted'],
                           packet_stats['packets_received'],
                           packet_loss_percent,
                           rtt_stats['rtt_min'],
                           rtt_stats['rtt_avg'],
                           rtt_stats['rtt_max'],
                           status])
    print x


def iperf_tcp_pretty_table_content(config, data):
    x = PrettyTable(["src_tenant",
                     "src_ep",
                     "dest_tenant",
                     "dest_ep",
                     "interval_time",
                     "transferred",
                     "bandwidth",
                     "retr"])

    x.align["src_tenant"] = "l"  # Left align source tenant values

    # One space between column edges and contents (default)
    x.padding_width = 1

    dest_ep_regex = ".*-*-(?P<dest_ip>[0-9]+_[0-9]+_[0-9]+_[0-9]+)-.*"
    for content in data:
        for k, v in content.items():
            src_ep = k
            src_tenant = v['src_tenant']
            dest_tenant = v['dest_tenant']
            # out = v['test_result'].split(',')
            test_result_files = v['test_result'].keys()

            for test_result_file in test_result_files:

                dest_ep_match = re.match(dest_ep_regex, test_result_file)

                dest_ep = dest_ep_match.group('dest_ip')
                bandwidth_stats = \
                    v['test_result'][test_result_file]['bandwidth_stats']

                if bandwidth_stats['interval_time'] and bandwidth_stats['transferred'] and bandwidth_stats['bandwidth']:
                    x.add_row([src_tenant, src_ep,
                               dest_tenant, dest_ep.replace('_', '.'),
                               bandwidth_stats['interval_time'],
                               bandwidth_stats['transferred'],
                               bandwidth_stats['bandwidth'],
                               bandwidth_stats['retr']])
    print x


def iperf_udp_pretty_table_content(config, data):
    x = PrettyTable(["src_tenant",
                     "src_ep",
                     "dest_tenant",
                     "dest_ep",
                     "interval_time",
                     "transferred",
                     "bandwidth",
                     "jitter",
                     "loss_datagram",
                     "total_datagram",
                     "loss_percent"])

    x.align["src_tenant"] = "l"  # Left align source tenant values

    # One space between column edges and contents (default)
    x.padding_width = 1

    dest_ep_regex = ".*-*-(?P<dest_ip>[0-9]+_[0-9]+_[0-9]+_[0-9]+)-.*"
    for content in data:
        for k, v in content.items():
            src_ep = k
            src_tenant = v['src_tenant']
            dest_tenant = v['dest_tenant']
            # out = v['test_result'].split(',')
            test_result_files = v['test_result'].keys()

            for test_result_file in test_result_files:

                dest_ep_match = re.match(dest_ep_regex, test_result_file)

                dest_ep = dest_ep_match.group('dest_ip')
                bandwidth_stats = \
                    v['test_result'][test_result_file]['bandwidth_stats']

                bandwidth_loss_percent = \
                    bandwidth_stats['loss_percent']  # NOQA

                if bandwidth_stats['interval_time'] and bandwidth_stats['transferred'] and bandwidth_stats['bandwidth']:
                    x.add_row([src_tenant, src_ep,
                               dest_tenant, dest_ep.replace('_', '.'),
                               bandwidth_stats['interval_time'],
                               bandwidth_stats['transferred'],
                               bandwidth_stats['bandwidth'],
                               bandwidth_stats['jitter'],
                               bandwidth_stats['loss_datagram'],
                               bandwidth_stats['total_datagram'],
                               bandwidth_loss_percent+" %"])
    print x


@task
@parallel
def create_test_results_directory(environment):
    try:
        run("mkdir %s" % (test_results_path))
    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


@task
@parallel
def test_ping(environment, config, endpoints, contract, timestamp):
    try:
        for dest_ep in endpoints['dest_eps']:
            if dest_ep != env.host_string:
                sudo("hping3 %s --icmp --fast -q 2>"
                     " testtraffic-%s-%s-%s.txt 1> /dev/null &" %
                     (dest_ep,
                      env.host_string.replace('.', '_'),
                      dest_ep.replace('.', '_'),
                      timestamp),
                     pty=False)

    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


@task
@parallel
def test_tcp(environment, config, server, endpoints, contract, timestamp):
    try:
        if server == '':
            print "TCP server execution"
            for src_ep in endpoints:
                if src_ep == env.host_string:
                    print src_ep
                
                    sudo("iperf3 -s -p 5201 -i 1 > tcptesttrafficserver-%s-%s.txt &" %
                         (env.host_string.replace('.', '_'),
                          timestamp),
                         pty=False)
       
        else:
            print "TCP client execution"
            for dest_ep in endpoints:
                if dest_ep == env.host_string:
                    print dest_ep
                
                    sudo("iperf3 -c %s -t %s -p 5201 > tcptesttrafficclient-%s-%s-%s.txt &" %
                         (server,
                          config['traffic']['iperf_duration'],
                          env.host_string.replace('.', '_'),
                          server.replace('.', '_'),
                          timestamp),
                         pty=False)

    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


@task
@parallel
def test_udp(environment, config, server, endpoints, contract, timestamp):
    try:
        if server == '':
            print "UDP server execution"
            for src_ep in endpoints:
                if src_ep == env.host_string:
                    print src_ep
                
                    sudo("iperf3 -s -p 5202 -i 1 > udptesttrafficserver-%s-%s.txt &" %
                         (env.host_string.replace('.', '_'),
                          timestamp),
                         pty=False)
       
        else:
            print "UDP client execution"
            for dest_ep in endpoints:
                if dest_ep == env.host_string:
                    print dest_ep
                
                    sudo("iperf3 -c %s -u -t %s -p 5202 > udptesttrafficclient-%s-%s-%s.txt &" %
                         (server,
                          config['traffic']['iperf_duration'],
                          env.host_string.replace('.', '_'),
                          server.replace('.', '_'),
                          timestamp),
                         pty=False)

    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


def capture_output():
    pass


@task
@parallel
def stop_traffic(environment, endpoints, timestamp):
    try:
        try:
            sudo("kill -SIGINT `pgrep hping3`")
        except SystemExit, e:
            logger.warn("Exception while executing task: %s", str(e))
        
        print "dest_eps are.....", endpoints['dest_eps']
        put("scripts/get_ping_statistics.py", "get_ping_statistics.py")
        out = run("python get_ping_statistics.py %s" % (timestamp))

        out_dict = json.JSONDecoder().decode(out)

        output = {'src_tenant': endpoints['src_tenant'],
                  'dest_tenant': endpoints['dest_tenant'],
                  'test_result': out_dict}
        # print output

        return output
    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))



@task
@parallel
def stop_iperf_traffic(environment, traffic_type, server, endpoints, src_tenant, dest_tenant, timestamp):
    try:
        
        if server == '':
            try:
                print "Killing iperf on server"
                sudo("kill -SIGINT `pgrep iperf`")
            except SystemExit, e:
                logger.warn("Exception while executing task: %s", str(e))

            print "endpoints are.....", endpoints

            return True
        else:

            try:
                print "Killing iperf on clients"
                sudo("kill -SIGINT `pgrep iperf`")
            except SystemExit, e:
                logger.warn("Exception while executing task: %s", str(e))

            print "endpoints are.....", endpoints

            if traffic_type == 'tcp':
                put("scripts/get_iperf_tcp_statistics.py", "get_iperf_tcp_statistics.py")
                out = run("python get_iperf_tcp_statistics.py %s" % (timestamp))

            if traffic_type == 'udp':
                put("scripts/get_iperf_udp_statistics.py", "get_iperf_udp_statistics.py")
                out = run("python get_iperf_udp_statistics.py %s" % (timestamp))

            out_dict = json.JSONDecoder().decode(out)

            output = {'src_tenant': src_tenant,
                      'dest_tenant': dest_tenant,
                      'test_result': out_dict}
            # print output

            return output
    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


def start_task(config, endpoints_list, action, testPrefix=None):
    timestamp = testPrefix
    if not testPrefix:
        timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")

    output_table_data_list = []
    tcp_output_table_data_list = []
    udp_output_table_data_list = []
    table_data = {}
    iperf_endpoint_list = list(unique_justseen(endpoints_list, key=itemgetter('test_type')))
    if action == 'start':
        for endpoints in endpoints_list:
            for contract in endpoints['contract']:
                if contract['protocol'] == 'icmp':
                    setup_env(config, endpoints)
                    execute(create_test_results_directory, env)
                    execute(install_hping, env)
                    execute(test_ping, env, config,
                            endpoints, contract, timestamp)
        for endpoints in iperf_endpoint_list:
            for contract in endpoints['contract']:
                if contract['protocol'] == 'tcp':
                    server_ip = [endpoints['dest_eps'][0]]
                    client_ip = endpoints['src_eps']
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], server_ip, endpoints['test_type'])
                    execute(create_test_results_directory, env)
                    execute(install_iperf, env)
                    server = ''
                    execute(test_tcp, env, config, server, server_ip, contract, timestamp)
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], client_ip, endpoints['test_type'])
                    execute(install_iperf, env)
                    server = server_ip[0]
                    execute(test_tcp, env, config, server, client_ip, contract, timestamp)
                if contract['protocol'] == 'udp':
                    server_ip = [endpoints['dest_eps'][0]]
                    client_ip = endpoints['src_eps']
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], server_ip, endpoints['test_type'])
                    execute(create_test_results_directory, env)
                    execute(install_iperf, env)
                    server = ''
                    execute(test_udp, env, config, server, server_ip, contract, timestamp)
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], client_ip, endpoints['test_type'])
                    execute(install_iperf, env)
                    server = server_ip[0]
                    execute(test_udp, env, config, server, client_ip, contract, timestamp)
    
    if action == 'stop':
        for endpoints in endpoints_list:
            for contract in endpoints['contract']:
                if contract['protocol'] == 'icmp':
                    setup_env(config, endpoints)
                    table_data = execute(stop_traffic, env, endpoints, timestamp)
                    output_table_data_list.append(table_data)
        for endpoints in iperf_endpoint_list:
            for contract in endpoints['contract']:
                if contract['protocol'] == 'tcp':
                    server_ip = [endpoints['dest_eps'][0]]
                    client_ip = endpoints['src_eps']
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], server_ip, endpoints['test_type'])
                    server = ''
                    execute(stop_iperf_traffic, env, 'tcp', server, server_ip, endpoints['src_tenant'], endpoints['dest_tenant'], timestamp)
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], client_ip, endpoints['test_type'])
                    server = server_ip[0]
                    table_data = execute(stop_iperf_traffic, env, 'tcp', server, client_ip, endpoints['src_tenant'], endpoints['dest_tenant'], timestamp)
                    tcp_output_table_data_list.append(table_data)
                if contract['protocol'] == 'udp':
                    server_ip = [endpoints['dest_eps'][0]]
                    client_ip = endpoints['src_eps']
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], server_ip, endpoints['test_type'])
                    server = ''
                    execute(stop_iperf_traffic, env, 'udp', server, server_ip, endpoints['src_tenant'], endpoints['dest_tenant'], timestamp)
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], client_ip, endpoints['test_type'])
                    server = server_ip[0]
                    table_data = execute(stop_iperf_traffic, env, 'udp', server, client_ip, endpoints['src_tenant'], endpoints['dest_tenant'], timestamp)
                    udp_output_table_data_list.append(table_data)
    
    print "Traffic Test Type: "+config['traffic']['type']
    print "\n"
    if output_table_data_list:
        print "ICMP Traffic Results"
        pretty_table_content(config, output_table_data_list)
        print "\n"
    if tcp_output_table_data_list:
        print "TCP Traffic Results"
        iperf_tcp_pretty_table_content(config, tcp_output_table_data_list)
        print "\n"
    if udp_output_table_data_list:
        print "UDP Traffic Results"
        iperf_udp_pretty_table_content(config, udp_output_table_data_list)
        print "\n"
