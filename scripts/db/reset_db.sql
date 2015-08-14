# remove global router ports
delete from ports where device_id ='PHYSICAL_GLOBAL_ROUTER_ID';

# remove tenant router ha ports
delete from ports where device_owner like '%ha%';

# clean up routers
delete from routers where id='PHYSICAL_GLOBAL_ROUTER_ID';

# clean cisco_phy_router_port_bindings
delete from cisco_phy_router_port_bindings;

# remove cisco_phy_routers
delete from cisco_phy_routers;


