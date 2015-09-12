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

    def get_neutron_client_by_tenant(self, tenant):
        nwclient = nwc.Client(
            '2.0',
            username=self.ks_user,
            password=self.ks_pass,
            tenant_name=tenant,
            auth_url=self.ks_auth_url)
        return nwclient

    def get_nova_client_by_tenant(self, tenant):
        novaclient = novac.Client(
            '2',
            username=self.ks_user,
            api_key=self.ks_pass,
            project_id=tenant,
            auth_url=self.ks_auth_url)
        return novaclient

    def get_tenants_list(self):
        self.logger.info('Get tenant list from Keystone')
        tenants = self.ks.tenants.list()
        self.logger.info(tenants)
        if self.config['traffic']['type'] == 'intra-tenant' or self.config['traffic']['type'] == 'all':
            self.logger.info('\n\t\tPerforming Intra-tenant Test.\n')
            if len(self.config['tenants']['tenants']) > 0:
                self.logger.info('\n\t\tMore than one Tenant found. Processing first tenant alone by default.\n')
                cfgtenants = self.config['tenants']['tenants'][0]
            else:
                cfgtenants = self.config['tenants']['tenants']
        if self.config['traffic']['type'] == 'inter-tenant' or self.config['traffic']['type'] == 'all':
            self.logger.info('\n\n\t\tPerforming Inter-tenant Test.\n')
            if len(self.config['tenants']['tenants']) < 2:
                cfgtenants = ''
                self.logger.info('\n\t\tMinimum Tenants count should be 2\n')
            else:
                cfgtenants = self.config['tenants']['tenants']
        if self.config['traffic']['type'] == 'south-north' or self.config['traffic']['type'] == 'all':
            self.logger.info('\n\n\t\tPerforming south-north Test.\n')
            if len(self.config['tenants']['tenants']) < 1:
                cfgtenants = ''
            else:
                cfgtenants = self.config['tenants']['tenants']
        if self.config['traffic']['type'] == 'north-south' or self.config['traffic']['type'] == 'all':
            self.logger.info('\n\n\t\tPerforming north-south Test.\n')
            if len(self.config['tenants']['tenants']) < 1:
                cfgtenants = ''
            else:
                cfgtenants = self.config['tenants']['tenants']

        return {tenant.id: tenant.name for tenant in tenants if tenant.enabled and tenant.name in cfgtenants}

