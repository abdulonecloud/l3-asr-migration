
* icehouse_initial_setup.yml

This playbook performs the initial setup for deploying the icehouse l3ha neutron plugin/agent. 

* check that /etc/ansible/hosts has entries under [opstk_icehouse]

Example: 

[opstk_icehouse]
10.1.25.128

To run...
ansible-playbook icehouse_initial_setup.yml
