from neutron import manager
from neutron import context as neutron_context
from neutron.plugins.common import constants as plugin_constants
from neutron.api.rpc.agentnotifiers import l3_rpc_agent_api
from neutron.services.l3_router import l3_router_plugin
from neutron.common import topics
from neutron.openstack.common import rpc as n_rpc
from neutron.openstack.common import jsonutils
from neutron.common import constants as q_const


class ManticoreL3RouterPluginRpcCallbacks(l3_router_plugin.
                                          L3RouterPluginRpcCallbacks):

    def get_floatingip_mappings(self, context):
        context = neutron_context.get_admin_context()
        l3plugin = manager.NeutronManager.get_service_plugins()[
            plugin_constants.L3_ROUTER_NAT]

        with context.session.begin(subtransactions=True):
            floating_ips = l3plugin.get_floatingips(
                context, fields=['floating_ip_address', 'router_id'])

            router_ids = list(set([floating_ip['router_id']
                                   for floating_ip in floating_ips]))

            bindings = l3plugin._get_l3_bindings_hosting_routers(
                context, router_ids)

        l3_agents = [{'router_id': binding.router_id,
                      'configurations': jsonutils.loads(
                          binding.l3_agent.configurations), }
                     for binding in bindings]
        l3_agents_dict = {}
        for l3_agent in l3_agents:
            l3_agents_dict[l3_agent['router_id']] = l3_agent

        mappings = []
        for floating_ip in floating_ips:
            l3_agent = l3_agents_dict.get(floating_ip['router_id'])
            if l3_agent:
                mappings.append(
                    [floating_ip['floating_ip_address'],
                     l3_agent['configurations'].get('routing_ip')]
                )

        return mappings


class ManticoreL3RouterPlugin(l3_router_plugin.L3RouterPlugin):
    """
    The service plugin for L3 agents. Added rpc callback for
    getting the floating ip and L3 agent mappings
    """

    def __init__(self):
        super(ManticoreL3RouterPlugin, self).__init__()

    def setup_rpc(self):
        # RPC support
        self.topic = topics.L3PLUGIN
        self.conn = n_rpc.create_connection(new=True)
        self.agent_notifiers.update(
            {q_const.AGENT_TYPE_L3: l3_rpc_agent_api.L3AgentNotifyAPI()})
        self.callbacks = ManticoreL3RouterPluginRpcCallbacks()
        self.dispatcher = self.callbacks.create_rpc_dispatcher()
        self.conn.create_consumer(self.topic, self.dispatcher,
                                  fanout=False)
        self.conn.consume_in_thread()
