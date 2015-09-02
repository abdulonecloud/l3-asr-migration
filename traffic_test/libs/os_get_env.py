import logging
from keystoneclient.v2_0 import client as ksc
from neutronclient.neutron import client as nwc
from novaclient import client as novac


class OSUtils(object):

    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.ks_user = config['default']['keystone_user']
        self.ks_pass = config['default']['keystone_password']
        self.ks_auth_url = config['default']['keystone_auth_url']
        self.ks_tenant_name = config['default']['keystone_tenant_name']
        self.ks = ksc.Client(
            username=self.ks_user,
            password=self.ks_pass,
            tenant_name=self.ks_tenant_name,
            auth_url=self.ks_auth_url)
        self.logger.info('OSUtils intialized successfully')

    def get_neutron_client_by_tenant(self):
        nwclient = nwc.Client(
            '2.0',
            username=self.ks_user,
            password=self.ks_pass,
            tenant_name=self.config['tenants']['tenants'],
            auth_url=self.ks_auth_url)
        return nwclient

    def get_nova_client_by_tenant(self):
        novaclient = novac.Client(
            '2',
            username=self.ks_user,
            api_key=self.ks_pass,
            project_id=self.config['tenants']['tenants'],
            auth_url=self.ks_auth_url)
        return novaclient

    def get_tenants_list(self):
        self.logger.info('Get tenant list from Keystone')
        tenants = self.ks.tenants.list()
        self.logger.info('\n\t\tTenants\n')
        self.logger.info(tenants)
        cfgtenants = self.config['tenants']['tenants']
        return {tenant.id: tenant.name for tenant in tenants if tenant.enabled and tenant.name in cfgtenants}

