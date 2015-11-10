import os
import logging
from ncclient import manager
from lxml import etree as etree

LOG = logging.getLogger("scale_tester")

formatter = \
    logging.Formatter('%(asctime)s - %(module)s - %(funcName)s - '
                      '(%(lineno)d) %(levelname)s \n %(message)s')

# All inclusive log
fh = logging.FileHandler("scale_tester_ASR.log")
fh.setFormatter(formatter)
LOG.addHandler(fh)
LOG.setLevel(logging.DEBUG)


GET_ROUTER_INFO = """
<filter type="subtree">
    <config-format-text-cmd>
        <text-filter-spec> | inc FFFFFFFFFFFFFFFF</text-filter-spec>
    </config-format-text-cmd>
    <oper-data-format-text-block>
        <exec>show vrf detail %s</exec>
    </oper-data-format-text-block>
</filter>
"""

GET_IP_NAT_POOL_INFO = """
<filter type="subtree">
    <config-format-text-cmd>
        <text-filter-spec> | inc FFFFFFFFFFFFFFFF</text-filter-spec>
    </config-format-text-cmd>
    <oper-data-format-text-block>
        <exec>show run | inc ip nat pool %s</exec>
    </oper-data-format-text-block>
</filter>
"""

GET_IP_ROUTE_INFO = """
<filter type="subtree">
    <config-format-text-cmd>
        <text-filter-spec> | inc FFFFFFFFFFFFFFFF</text-filter-spec>
    </config-format-text-cmd>
    <oper-data-format-text-block>
        <exec>show run | inc ip route vrf %s</exec>
    </oper-data-format-text-block>
</filter>
"""

GET_NETWORK_INTERFACE_INFO = """
<filter type="subtree">
    <config-format-text-cmd>
        <text-filter-spec> | inc FFFFFFFFFFFFFFFF</text-filter-spec>
    </config-format-text-cmd>
    <oper-data-format-text-block>
        <exec>show interfaces %s</exec>
    </oper-data-format-text-block>
</filter>
"""

GET_IP_NAT_COUNT = """
<filter type="subtree">
    <config-format-text-cmd>
        <text-filter-spec> | inc FFFFFFFFFFFFFFFF</text-filter-spec>
    </config-format-text-cmd>
    <oper-data-format-text-block>
        <exec>show run | count neutron_acl_%s pool</exec>
    </oper-data-format-text-block>
</filter>
"""

GET_IP_ACCESS_LIST_COUNT = """
<filter type="subtree">
    <config-format-text-cmd>
        <text-filter-spec> | inc FFFFFFFFFFFFFFFF</text-filter-spec>
    </config-format-text-cmd>
    <oper-data-format-text-block>
        <exec>show ip access-lists | count neutron_acl_%s</exec>
    </oper-data-format-text-block>
</filter>
"""


def asr_connect(host, port, user, password):
    """
    ncclient manager factory method
    """
    return manager.connect(host=host,
                           port=port,
                           username=user,
                           password=password,
                           # device_params={'name': "csr"},
                           timeout=30)


class GetASRCmd():
    """
    This command will fetch and log the CPU and resource health for a
    specified ASR router
    """

    def __init__(self, **kwargs):
        """
        constructor
        """

        # obtain connection information for router
        self.asr_host = kwargs['asr_host']
        self.asr_host_port = kwargs['asr_host_port']
        self.asr_user = kwargs['asr_user']
        self.asr_password = kwargs['asr_password']

        self.asr_slots = kwargs.get('asr_slots', None)

    def init(self):
        LOG.debug("init")
        return True

    def get_router_detail(self, vrfname):
        """
        Gets the vrf detail from the designated ASR router,
        invokes show vrf detail
        """
        LOG.debug("get router detail")

        with asr_connect(self.asr_host,
                         port=self.asr_host_port,
                         user=self.asr_user,
                         password=self.asr_password) as conn:
            interfaces = ""
            try:
                filter_str = GET_ROUTER_INFO % (vrfname)
                rpc_obj = conn.get(filter=filter_str)

                LOG.info("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                LOG.info("ASR Host %s VRF = %s" % (self.asr_host,
                                                   rpc_obj.data_xml))
                tree = etree.XML(rpc_obj.data_xml)
                ns = '{urn:ietf:params:xml:ns:netconf:base:1.0}'
                search_str = '{0}cli-oper-data-block/{0}item/{0}response'
                response = tree.find(search_str.format(ns)).text
                response_data = iter(response.splitlines())
                for line in response_data:
                    if " Interfaces:" in line:
                        interfaces = next(response_data)
                        interfaces = [x for x in interfaces.split(' ') if x]

                LOG.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status = "Pass"

            except Exception as exc:
                LOG.debug("Caught exception %s" % (exc.message))
                status = "Fail"
            router_vrf_data = {}
            router_vrf_data['vrfname'] = vrfname
            router_vrf_data['interfaces'] = interfaces
            router_vrf_data['status'] = status
        return router_vrf_data

    def get_ipnat_pool_detail(self, vrfname):
        """
        Gets the vrf detail from the designated ASR router,
        invokes show ip nat pool detail
        """
        LOG.debug("get ip nat pool detail")

        with asr_connect(self.asr_host,
                         port=self.asr_host_port,
                         user=self.asr_user,
                         password=self.asr_password) as conn:
            nat_pool_name = vrfname + "_nat_pool"
            start_ip = ""
            end_ip = ""
            netmask = ""
            try:
                filter_str = GET_IP_NAT_POOL_INFO % (nat_pool_name)
                rpc_obj = conn.get(filter=filter_str)

                LOG.info("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                LOG.info("ASR Host %s VRF = %s" % (
                    self.asr_host, rpc_obj.data_xml))
                tree = etree.XML(rpc_obj.data_xml)
                ns = '{urn:ietf:params:xml:ns:netconf:base:1.0}'
                search_str = '{0}cli-oper-data-block/{0}item/{0}response'
                response = tree.find(search_str.format(ns)).text
                response_data = iter(response.splitlines())
                for line in response_data:
                    if "ip nat pool " + nat_pool_name in line:
                        poolinfo = line.split("ip nat pool " + nat_pool_name +
                                              " ")[1]
                        natpool_info = poolinfo.split(' ')
                        start_ip = natpool_info[0]
                        end_ip = natpool_info[1]
                        netmask = natpool_info[3]
                LOG.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status = "Pass"

            except Exception as exc:
                LOG.debug("Caught exception %s" % (exc.message))
                status = "Fail"
            ipnat_pool_data = {}
            ipnat_pool_data['vrfname'] = vrfname
            ipnat_pool_data['nat_pool_name'] = nat_pool_name
            ipnat_pool_data['start_ip'] = start_ip
            ipnat_pool_data['end_ip'] = end_ip
            ipnat_pool_data['netmask'] = netmask
            ipnat_pool_data['status'] = status
        return ipnat_pool_data

    def get_iproute_detail(self, vrfname):
        """
        Gets the vrf detail from the designated ASR router,
        invokes show ip route vrf detail
        """
        LOG.debug("get ip route detail")

        with asr_connect(self.asr_host,
                         port=self.asr_host_port,
                         user=self.asr_user,
                         password=self.asr_password) as conn:
            prefix = ""
            mask = ""
            interface = ""
            next_hop_address = ""
            try:
                filter_str = GET_IP_ROUTE_INFO % (vrfname)
                rpc_obj = conn.get(filter=filter_str)

                LOG.info("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                LOG.info("ASR Host %s VRF = %s" % (self.asr_host,
                                                   rpc_obj.data_xml))
                tree = etree.XML(rpc_obj.data_xml)
                ns = '{urn:ietf:params:xml:ns:netconf:base:1.0}'
                search_str = '{0}cli-oper-data-block/{0}item/{0}response'
                response = tree.find(search_str.format(ns)).text
                response_data = iter(response.splitlines())
                for line in response_data:
                    if "ip route vrf " + vrfname in line:
                        routeinfo = line.split("ip route vrf " + vrfname +
                                               " ")[1]
                        iproute_info = routeinfo.split(' ')
                        prefix = iproute_info[0]
                        mask = iproute_info[1]
                        interface = iproute_info[2]
                        next_hop_address = iproute_info[3]
                LOG.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status = "Pass"

            except Exception as exc:
                LOG.debug("Caught exception %s" % (exc.message))
                status = "Fail"
            iproute_data = {}
            iproute_data['vrfname'] = vrfname
            iproute_data['prefix'] = prefix
            iproute_data['mask'] = mask
            iproute_data['interface'] = interface
            iproute_data['next_hop_address'] = next_hop_address
            iproute_data['status'] = status
        return iproute_data

    def get_network_interface_detail(self, vrfname, interfacename):
        """
        Gets the vrf detail from the designated ASR router,
        invokes show interfaces detail
        """
        LOG.debug("get interface detail")

        with asr_connect(self.asr_host,
                         port=self.asr_host_port,
                         user=self.asr_user,
                         password=self.asr_password) as conn:

            interfaces_status = ''
            desc = ''
            ip = ''
            vlanid = ''

            try:
                filter_str = GET_NETWORK_INTERFACE_INFO % (interfacename)
                rpc_obj = conn.get(filter=filter_str)

                LOG.info("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                LOG.info("ASR Host %s VRF = %s" % (self.asr_host,
                                                   rpc_obj.data_xml))
                tree = etree.XML(rpc_obj.data_xml)
                ns = '{urn:ietf:params:xml:ns:netconf:base:1.0}'
                search_str = '{0}cli-oper-data-block/{0}item/{0}response'
                response = tree.find(search_str.format(ns)).text
                response_data = iter(response.splitlines())
                interfaces_status = response.splitlines()[1]
                for line in response_data:
                    if " Description:" in line:
                        desc = line.split(' Description: ')[1]
                    if " Internet address is" in line:
                        ip = line.split(' Internet address is ')[1]
                    if " Vlan ID" in line:
                        vlanid = line.split(' Vlan ID  ')[1].split('.')[0]

                status = "Pass"
                LOG.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

            except Exception as exc:
                LOG.debug("Caught exception %s" % (exc.message))
                status = "Fail"

            interface_vrf_data = {}
            interface_vrf_data['vrfname'] = vrfname
            interface_vrf_data['interface_name'] = interfacename
            interface_vrf_data['interface_status'] = interfaces_status
            interface_vrf_data['description'] = desc
            interface_vrf_data['ip_address'] = ip
            interface_vrf_data['vlan_id'] = vlanid
            interface_vrf_data['status'] = status
        return interface_vrf_data

    def get_interface_nat_access_detail(self, vlanid, interfaceid):
        """
        Gets the vrf detail from the designated ASR router,
        invokes show run vrf detail
        """
        LOG.debug("get router detail")

        with asr_connect(self.asr_host,
                         port=self.asr_host_port,
                         user=self.asr_user,
                         password=self.asr_password) as conn:
            nat_entry = "Not Found"
            access_list_entry = "Not Found"
            try:
                filter_str = GET_IP_NAT_COUNT % (interfaceid)
                rpc_obj = conn.get(filter=filter_str)

                LOG.info("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                LOG.info("ASR Host %s VRF = %s" % (self.asr_host,
                                                   rpc_obj.data_xml))
                tree = etree.XML(rpc_obj.data_xml)
                ns = '{urn:ietf:params:xml:ns:netconf:base:1.0}'
                search_str = '{0}cli-oper-data-block/{0}item/{0}response'
                response = tree.find(search_str.format(ns)).text
                response_data = iter(response.splitlines())
                for line in response_data:
                    if "Number of lines which match regexp" in line:
                        nat_count = line.split('Number of lines which match '
                                               'regexp = ')[1]
                        if int(nat_count) >= 1:
                            nat_entry = "Found"
                            status = "Pass"
                        if int(nat_count) == 0:
                            status = "Fail"

                LOG.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

            except Exception as exc:
                LOG.debug("Caught exception %s" % (exc.message))
                status = "Fail"

            try:
                filter_str = GET_IP_ACCESS_LIST_COUNT % (interfaceid)
                rpc_obj = conn.get(filter=filter_str)

                LOG.info("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                LOG.info("ASR Host %s VRF = %s" % (self.asr_host,
                                                   rpc_obj.data_xml))
                tree = etree.XML(rpc_obj.data_xml)
                ns = '{urn:ietf:params:xml:ns:netconf:base:1.0}'
                search_str = '{0}cli-oper-data-block/{0}item/{0}response'
                response = tree.find(search_str.format(ns)).text
                response_data = iter(response.splitlines())
                for line in response_data:
                    if "Number of lines which match regexp" in line:
                        access_list_count = line.split('Number of lines '
                                                       'which match '
                                                       'regexp = ')[1]
                        if int(access_list_count) >= 1:
                            access_list_entry = "Found"
                            status = "Pass"
                        if int(access_list_count) == 0:
                            status = "Fail"

                LOG.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

            except Exception as exc:
                LOG.debug("Caught exception %s" % (exc.message))
                status = "Fail"

            interface_nat_data = {}
            interface_nat_data['vlan_id'] = vlanid
            interface_nat_data['nat_entry'] = nat_entry
            interface_nat_data['access_list_entry'] = access_list_entry
            interface_nat_data['status'] = status
        return interface_nat_data

    def done(self):
        LOG.debug("done")
        return True

    def undo(self):
        LOG.debug("Undo")
        return True
