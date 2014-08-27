from neutron.agent import l3_agent
from neutron.common import constants as l3_constants
from neutron.openstack.common.rpc import proxy
from neutron.agent.linux import ip_lib
from oslo.config import cfg


opts = [
    cfg.StrOpt('routing_ip', default='',
               help=("The routing ip of this agent")),
]

cfg.CONF.register_opts(opts)


class ManticoreRPCApi(proxy.RpcProxy):

    def __init__(self):
        super(ManticoreRPCApi, self).__init__(
            topic='q-bgp-speaker',
            default_version='1.0')

    def prefix_add(self, context, floatingip, next_hop):
        self.fanout_cast(context,
                         self.make_msg('prefix_add',
                                       floatingip=floatingip,
                                       next_hop=next_hop))


class ManticoreL3Agent(l3_agent.L3NATAgentWithStateReport):
    """
    This class is a inheritance from neutron's original L3 agent to add
    the routing information for the BGP speaker
    """

    def __init__(self, host, conf=None):
        super(ManticoreL3Agent, self).__init__(host, conf)
        self.agent_state['configurations']['routing_ip'] = cfg.CONF.routing_ip
        self.manticore_rpc_api = ManticoreRPCApi()

    def process_router_floating_ip_addresses(self, ri, ex_gw_port):
        interface_name = self.get_external_device_name(ex_gw_port['id'])
        device = ip_lib.IPDevice(interface_name, self.root_helper,
                                 namespace=ri.ns_name)
        existing_cidrs = set([addr['cidr'] for addr in device.addr.list()])

        fip_statuses = super(ManticoreL3Agent, self).\
            process_router_floating_ip_addresses(ri, ex_gw_port)

        # Loop once to ensure that floating ips are configured.
        for fip in ri.router.get(l3_constants.FLOATINGIP_KEY, []):
            fip_ip = fip['floating_ip_address']
            ip_cidr = str(fip_ip) + l3_agent.FLOATING_IP_CIDR_SUFFIX
            if ip_cidr not in existing_cidrs:
                self.manticore_rpc_api.prefix_add({},
                                                  ip_cidr,
                                                  cfg.CONF.routing_ip)

        return fip_statuses


def main():
    l3_agent.main(manager='manticore.l3_agent.ManticoreL3Agent')
