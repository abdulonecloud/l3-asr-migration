# A set of queries that will dump a view of the icehouse neutron db
connect neutron;
# MariaDB [neutron]> desc networks;
# +----------------+--------------+------+-----+---------+-------+
# | Field          | Type         | Null | Key | Default | Extra |
# +----------------+--------------+------+-----+---------+-------+
# | tenant_id      | varchar(255) | YES  |     | NULL    |       |
# | id             | varchar(36)  | NO   | PRI | NULL    |       |
# | name           | varchar(255) | YES  |     | NULL    |       |
# | status         | varchar(16)  | YES  |     | NULL    |       |
# | admin_state_up | tinyint(1)   | YES  |     | NULL    |       |
# | shared         | tinyint(1)   | YES  |     | NULL    |       |
# +----------------+--------------+------+-----+---------+-------+


# MariaDB [neutron]> desc subnets;
# +-------------------+----------------------------------------------------+------+-----+---------+-------+
# | Field             | Type                                               | Null | Key | Default | Extra |
# +-------------------+----------------------------------------------------+------+-----+---------+-------+
# | tenant_id         | varchar(255)                                       | YES  |     | NULL    |       |
# | id                | varchar(36)                                        | NO   | PRI | NULL    |       |
# | name              | varchar(255)                                       | YES  |     | NULL    |       |
# | network_id        | varchar(36)                                        | YES  | MUL | NULL    |       |
# | ip_version        | int(11)                                            | NO   |     | NULL    |       |
# | cidr              | varchar(64)                                        | NO   |     | NULL    |       |
# | gateway_ip        | varchar(64)                                        | YES  |     | NULL    |       |
# | enable_dhcp       | tinyint(1)                                         | YES  |     | NULL    |       |
# | shared            | tinyint(1)                                         | YES  |     | NULL    |       |
# | ipv6_ra_mode      | enum('slaac','dhcpv6-stateful','dhcpv6-stateless') | YES  |     | NULL    |       |
# | ipv6_address_mode | enum('slaac','dhcpv6-stateful','dhcpv6-stateless') | YES  |     | NULL    |       |
# +-------------------+----------------------------------------------------+------+-----+---------+-------+

# MariaDB [neutron]> desc ports;
# +----------------+--------------+------+-----+---------+-------+
# | Field          | Type         | Null | Key | Default | Extra |
# +----------------+--------------+------+-----+---------+-------+
# | tenant_id      | varchar(255) | YES  |     | NULL    |       |
# | id             | varchar(36)  | NO   | PRI | NULL    |       |
# | name           | varchar(255) | YES  |     | NULL    |       |
# | network_id     | varchar(36)  | NO   | MUL | NULL    |       |
# | mac_address    | varchar(32)  | NO   |     | NULL    |       |
# | admin_state_up | tinyint(1)   | NO   |     | NULL    |       |
# | status         | varchar(16)  | NO   |     | NULL    |       |
# | device_id      | varchar(255) | NO   |     | NULL    |       |
# | device_owner   | varchar(255) | NO   |     | NULL    |       |
# +----------------+--------------+------+-----+---------+-------+

# MariaDB [neutron]> desc ipallocations;
# +------------+-------------+------+-----+---------+-------+
# | Field      | Type        | Null | Key | Default | Extra |
# +------------+-------------+------+-----+---------+-------+
# | port_id    | varchar(36) | YES  | MUL | NULL    |       |
# | ip_address | varchar(64) | NO   | PRI | NULL    |       |
# | subnet_id  | varchar(36) | NO   | PRI | NULL    |       |
# | network_id | varchar(36) | NO   | PRI | NULL    |       |
# +------------+-------------+------+-----+---------+-------+

select "ip allocation pools" as query_description;
select sub.name, ipa.first_ip, ipa.last_ip
from ipallocationpools ipa
         join (subnets sub)
         on (ipa.subnet_id = sub.id);
select "ips still available" as query_description;
select * from ipavailabilityranges;

select "routers and agents" as query_description;
select routers.tenant_id,
       routers.name,
       routers.status,
       ipallocations.ip_address as gw_interface_ip,
       routers.enable_snat,
       agents.binary as agent_binary,
       agents.host as agent_host
from routers left join (ports, ipallocations, routerl3agentbindings, agents)
on (routers.gw_port_id = ports.id and
    ports.id = ipallocations.port_id and
    routers.id = routerl3agentbindings.router_id and
    routerl3agentbindings.l3_agent_id = agents.id);

select "networks and subnets" as query_description;
select sub.tenant_id,
       net.name as network_name,
       sub.name as subnet_name,
       sub.cidr,
       sub.gateway_ip,
       sub.enable_dhcp
from subnets sub join (networks net) on (sub.network_id=net.id);

select "networks, subnets, and ports" as query_description;
select sub.tenant_id,
       net.name,
       sub.name,
       ports.mac_address,
       sub.cidr,
       ipallocations.ip_address,
       ports.status,
       ports.device_owner
from subnets sub join (networks net, ports, ipallocations) 
on (sub.network_id=net.id and
    ports.network_id = sub.network_id and
    ports.id = ipallocations.port_id
   );

select "floating ips" as query_description;
select fip.floating_ip_address,
       floating_ports.mac_address as floating_mac_addr,
       n.name as network_name,
       r.name,
       fip.fixed_ip_address,
       fixed_ports.mac_address as fixed_mac_addr
from floatingips fip
join (ports floating_ports, ports fixed_ports, routers r, networks n)
on (fip.floating_network_id = n.id and
    fip.router_id = r.id and
    fip.floating_port_id = floating_ports.id and
    fip.fixed_port_id = fixed_ports.id)
