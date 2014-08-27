import eventlet
import sys

from oslo.config import cfg
from oslo import messaging
from ryu.services.protocols.bgp.bgpspeaker import BGPSpeaker

from manticore import config
from manticore import rpc


class RpcAPI(object):
    """ Client side RPC API for BGP Speaker """

    def __init__(self):
        target = messaging.Target(topic='q-l3-plugin', version='1.0')
        self.client = rpc.get_client(target)

    def make_msg(self, method, **kwargs):
        return {'method': method,
                'args': kwargs}

    def get_floatingip_mappings(self, context, router_ids=None):
        """Make a remote process call to retrieve the floatingip mappings."""
        return self.client.call(context, 'get_floatingip_mappings')


class RPCCallbacks(object):
    """
    Callbacks for communication from L3 agents to BGP speaker via RPC.
    """

    def __init__(self, speaker):
        self.speaker = speaker

    def prefix_add(self, context, floatingip, next_hop):
        self.speaker.prefix_add(floatingip, next_hop=next_hop)


class ManticoreSpeaker(object):
    """
    The BGP speaker which will advertise the prefixes for
    floating ips to route them to the L3 agent.
    """

    def __init__(self):
        self.setup_bgp_speaker()
        self.rpcapi = RpcAPI()
        self.init_prefixes()
        self.setup_rpc()

    def setup_bgp_speaker(self):
        self.speaker = BGPSpeaker(as_number=cfg.CONF.BGP.as_number,
                                  router_id=cfg.CONF.BGP.router_id)
        self.speaker.neighbor_add(cfg.CONF.BGP.neighbor_router_id,
                                  cfg.CONF.BGP.neighbor_as_number)

    def setup_rpc(self):
        target = messaging.Target(topic='q-bgp-speaker', server=cfg.CONF.host)
        endpoints = [RPCCallbacks(self.speaker)]
        self.rpc_server = rpc.get_server(target, endpoints=endpoints)
        self.rpc_server.start()

    def init_prefixes(self):
        mappings = self.rpcapi.get_floatingip_mappings({})
        for floatingip, routing_ip in mappings:
            self.speaker.prefix_add(floatingip, next_hop=routing_ip)

    def wait(self):
        while True:
            eventlet.sleep(1)


def main():
    eventlet.monkey_patch()
    config.init(sys.argv[1:])
    speaker = ManticoreSpeaker()
    speaker.wait()
