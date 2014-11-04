from neutron.agent import l3_agent
from neutron.common import constants as l3_constants
from neutron.common import rpc as n_rpc
from neutron.agent.linux import ip_lib
from oslo.config import cfg


opts = [
    cfg.StrOpt('routing_ip', default='',
               help=("The routing ip of this agent")),
]

cfg.CONF.register_opts(opts)
FLOATING_IP_CIDR_SUFFIX = '/32'


class ManticoreRPCApi(n_rpc.RpcProxy):

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
        """Configure IP addresses on router's external gateway interface.

        Ensures addresses for existing floating IPs and cleans up
        those that should not longer be configured.
        """

        fip_statuses = {}
        floating_ips = ri.router.get(l3_constants.FLOATINGIP_KEY, [])
        interface_name = self._get_external_device_interface_name(
            ri, ex_gw_port, floating_ips)
        if interface_name is None:
            return fip_statuses

        device = ip_lib.IPDevice(interface_name, self.root_helper,
                                 namespace=ri.ns_name)
        existing_cidrs = set([addr['cidr'] for addr in device.addr.list()])
        new_cidrs = set()

        # Loop once to ensure that floating ips are configured.
        for fip in floating_ips:
            fip_ip = fip['floating_ip_address']
            ip_cidr = str(fip_ip) + FLOATING_IP_CIDR_SUFFIX
            new_cidrs.add(ip_cidr)
            fip_statuses[fip['id']] = l3_constants.FLOATINGIP_STATUS_ACTIVE
            if ip_cidr not in existing_cidrs:
                fip_statuses[fip['id']] = self._add_floating_ip(
                    ri, fip, interface_name, device)
                # add BGP prefix for the floating IP
                self.manticore_rpc_api.prefix_add({},
                                                  ip_cidr,
                                                  cfg.CONF.routing_ip)

        fips_to_remove = (
            ip_cidr for ip_cidr in existing_cidrs - new_cidrs if
            ip_cidr.endswith(FLOATING_IP_CIDR_SUFFIX))
        for ip_cidr in fips_to_remove:
            self._remove_floating_ip(ri, device, ip_cidr)

        return fip_statuses


def main():
    l3_agent.main(manager='manticore.l3_agent.ManticoreL3Agent')
