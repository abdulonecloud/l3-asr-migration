from neutronclient.neutron import client as nwc
from oslo_utils import uuidutils
import MySQLdb as mysql

nwclient = nwc.Client('2.0', username = 'admin', password = 'admin123', tenant_name = 'admin', auth_url = 'http://10.1.25.128:5000/v2.0')
db = mysql.connect(host="10.1.25.128", user="nelson.huang", passwd="mysql", db="neutron")
c = db.cursor()

def get_cisco_phy_routers_from_config(config):
    physical_routers = {}
    for asr in config:
        physical_routers[asr] = uuidutils.generate_uuid()
    print physical_routers
    return physical_routers
        
def get_routers():
    routers = nwclient.list_routers()['routers']
    routers = [ router for router in routers if router['id'] != 'PHYSICAL_GLOBAL_ROUTER_ID' ]
    return routers

def get_ports_by_router(router):
    ports = nwclient.list_ports()['ports']
    router_ports = [ port for port in ports if port['device_id'] == router ]
    return router_ports

def populate_cisco_phy_routers(cisco_phy_routers):
    for asr, uuid in cisco_phy_routers.items():
        c.execute("INSERT INTO cisco_phy_routers(id, name) VALUES('%s', '%s')" %(uuid, asr))
    db.commit()

def update_routers_table():
    c.execute("INSERT INTO routers(tenant_id, id, name, status, admin_state_up, enable_snat) VALUES('','PHYSICAL_GLOBAL_ROUTER_ID', 'PHYSICAL_GLOBAL_ROUTER_ID', 'ACTIVE', 1, 1)")
    db.commit()

def add_gateway_for_physical_router():
    networks = nwclient.list_networks()['networks']
    ext_net_list = [ network for network in networks if network['router:external'] ]
    for ext_net in ext_net_list:
        for subnet in ext_net['subnets']:
            body_val = {
                           "port": {
                                    "network_id" : ext_net['id'],
                                    "device_owner": 'network:router_gateway',
                                    "device_id": 'PHYSICAL_GLOBAL_ROUTER_ID'
                           }
                       }
            nwclient.create_port(body=body_val)
            
            body_val = {
                           "port": {
                                    "network_id" : ext_net['id'],
                                    "device_owner": 'network:router_ha_gateway',
                                    "device_id": 'PHYSICAL_GLOBAL_ROUTER_ID'

                           }
                       }

            nwclient.create_port(body=body_val)
            nwclient.create_port(body=body_val)
    db.commit()    

def add_router_ha_interface_for_routers(routers):
    for router in routers:
        router_ports = get_ports_by_router(router['id'])
        router_interface_ports = [ router_port for router_port in router_ports if router_port['device_owner'] == 'network:router_interface' ]
        for port in router_interface_ports:
            fixed_ips = port['fixed_ips']
            subnets = [ fixed_ip['subnet_id'] for fixed_ip in fixed_ips ]
            for subnet in subnets:
                body_val = {
                           "port": {
                                    "network_id" : port['network_id'],
                                    "device_owner": 'network:router_ha_interface',
                                    "device_id": router['id']
                           }
                       }
                nwclient.create_port(body=body_val)
                nwclient.create_port(body=body_val)
    db.commit()

def update_cisco_phy_router_port_bindings(phy_routers, routers):
    for router in routers:
        router_ports = get_ports_by_router(router['id'])
        router_ha_ports = [ port for port in router_ports if port['device_owner'] == 'network:router_ha_interface' ]
        print router_ha_ports
        for k,v in phy_routers.items():
            port = router_ha_ports.pop()
            subnet = port['fixed_ips'][0]['subnet_id']            
            c.execute("INSERT INTO cisco_phy_router_port_bindings VALUES('%s', '%s', '%s', '%s')" %(port['id'], subnet, router['id'], v))
    db.commit()

if __name__ == '__main__':
    asr_config = ['ASR-A', 'ASR-B']
    cisco_phy_routers = get_cisco_phy_routers_from_config(asr_config)
    update_routers_table()
    populate_cisco_phy_routers(cisco_phy_routers)
    add_gateway_for_physical_router()
    routers = get_routers()
    add_router_ha_interface_for_routers(routers)
    update_cisco_phy_router_port_bindings(cisco_phy_routers, routers)
    db.commit()
    db.close()


