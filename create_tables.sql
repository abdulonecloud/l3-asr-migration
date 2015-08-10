CREATE TABLE `cisco_hosting_devices` (
  `tenant_id` varchar(255) DEFAULT NULL,
  `id` varchar(36) NOT NULL,
  `complementary_id` varchar(36) DEFAULT NULL,
  `device_id` varchar(255) DEFAULT NULL,
  `admin_state_up` tinyint(1) NOT NULL,
  `management_port_id` varchar(36) DEFAULT NULL,
  `protocol_port` int(11) DEFAULT NULL,
  `cfg_agent_id` varchar(36) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `status` varchar(16) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `management_port_id` (`management_port_id`),
  KEY `cfg_agent_id` (`cfg_agent_id`),
  CONSTRAINT `cisco_hosting_devices_ibfk_1` FOREIGN KEY (`management_port_id`) REFERENCES `ports` (`id`) ON DELETE SET NULL,
  CONSTRAINT `cisco_hosting_devices_ibfk_2` FOREIGN KEY (`cfg_agent_id`) REFERENCES `agents` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `cisco_phy_routers` (
  `id` varchar(36) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `status` varchar(16) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `cisco_phy_router_port_bindings` (
  `port_id` varchar(36) NOT NULL,
  `subnet_id` varchar(36) DEFAULT NULL,
  `router_id` varchar(36) DEFAULT NULL,
  `phy_router_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`port_id`),
  KEY `subnet_id` (`subnet_id`),
  KEY `router_id` (`router_id`),
  KEY `phy_router_id` (`phy_router_id`),
  CONSTRAINT `cisco_phy_router_port_bindings_ibfk_1` FOREIGN KEY (`port_id`) REFERENCES `ports` (`id`) ON DELETE CASCADE,
  CONSTRAINT `cisco_phy_router_port_bindings_ibfk_2` FOREIGN KEY (`subnet_id`) REFERENCES `subnets` (`id`) ON DELETE CASCADE,
  CONSTRAINT `cisco_phy_router_port_bindings_ibfk_3` FOREIGN KEY (`router_id`) REFERENCES `routers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `cisco_phy_router_port_bindings_ibfk_4` FOREIGN KEY (`phy_router_id`) REFERENCES `cisco_phy_routers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `cisco_port_mappings` (
  `logical_resource_id` varchar(36) NOT NULL,
  `logical_port_id` varchar(36) NOT NULL,
  `port_type` varchar(32) DEFAULT NULL,
  `network_type` varchar(32) DEFAULT NULL,
  `hosting_port_id` varchar(36) DEFAULT NULL,
  `segmentation_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`logical_resource_id`,`logical_port_id`),
  KEY `logical_port_id` (`logical_port_id`),
  KEY `hosting_port_id` (`hosting_port_id`),
  CONSTRAINT `cisco_port_mappings_ibfk_1` FOREIGN KEY (`logical_port_id`) REFERENCES `ports` (`id`) ON DELETE CASCADE,
  CONSTRAINT `cisco_port_mappings_ibfk_2` FOREIGN KEY (`hosting_port_id`) REFERENCES `ports` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `cisco_router_mappings` (
  `router_id` varchar(36) NOT NULL,
  `auto_schedule` tinyint(1) NOT NULL,
  `hosting_device_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`router_id`),
  KEY `hosting_device_id` (`hosting_device_id`),
  CONSTRAINT `cisco_router_mappings_ibfk_1` FOREIGN KEY (`router_id`) REFERENCES `routers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `cisco_router_mappings_ibfk_2` FOREIGN KEY (`hosting_device_id`) REFERENCES `cisco_hosting_devices` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
