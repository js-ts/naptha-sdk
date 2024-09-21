from typing import Dict, Optional
from naptha_sdk.schemas import AgentRun, AgentRunInput
from naptha_sdk.client.comms.http_client import (
    check_user_http, register_user_http, run_agent_http, check_agent_run_http, 
    create_agent_run_http, update_agent_run_http, read_storage_http, write_storage_http
)
from naptha_sdk.client.comms.ws_client import (
    check_user_ws, register_user_ws, run_agent_ws, check_agent_run_ws, 
    create_agent_run_ws, update_agent_run_ws, read_storage_ws, write_storage_ws
)
from naptha_sdk.utils import get_logger


logger = get_logger(__name__)

class Node:
    def __init__(self, node_url: Optional[str] = None, indirect_node_id: Optional[str] = None, routing_url: Optional[str] = None):
        self.node_url = node_url
        self.indirect_node_id = indirect_node_id
        self.routing_url = routing_url

        # at least one of node_url and indirect_node_id must be set
        if not node_url and not indirect_node_id:
            raise ValueError("Either node_url or indirect_node_id must be set")
        
        # if indirect_node_id is set, we need the routing_url to be set
        if indirect_node_id and not routing_url:
            raise ValueError("routing_url must be set if indirect_node_id is set")
        
        if self.node_url:
            self.client = 'http'
            logger.info("Using http client")
            logger.info(f"Node URL: {self.node_url}")
        else:
            self.client = 'ws'
            logger.info("Using ws client")
            logger.info(f"Routing URL: {self.routing_url}")
            logger.info(f"Indirect Node ID: {self.indirect_node_id}")
        
        self.access_token = None


    async def check_user(self, user_input):
        print("Checking user... ", user_input)
        if self.client == 'http':
            return await check_user_http(self.node_url, user_input)
        else:
            return await check_user_ws(self.routing_url, self.indirect_node_id, user_input)


    async def register_user(self, user_input):
        if self.client == 'http':
            return await register_user_http(self.node_url, user_input)
        else:
            return await register_user_ws(self.routing_url, self.indirect_node_id, user_input)

    async def run_agent(self, agent_run_input: AgentRunInput) -> AgentRun:
        if self.client == 'http':
            return await run_agent_http(
                node_url=self.node_url,
                agent_run_input=agent_run_input,
                access_token=self.access_token
            )
        else:
            return await run_agent_ws(
                routing_url=self.routing_url,
                indirect_node_id=self.indirect_node_id,
                agent_run_input=agent_run_input
            )

    async def check_agent_run(self, agent_run: AgentRun) -> AgentRun:
        if self.client == 'http':
            return await check_agent_run_http(self.node_url, agent_run)
        else:
            return await check_agent_run_ws(self.routing_url, self.indirect_node_id, agent_run)

    async def create_agent_run(self, agent_run_input: AgentRunInput) -> AgentRun:
        if self.client == 'http':
            logger.info(f"Creating agent run with input: {agent_run_input}")
            logger.info(f"Node URL: {self.node_url}")
            return await create_agent_run_http(self.node_url, agent_run_input)
        else:
            return await create_agent_run_ws(self.routing_url, self.indirect_node_id, agent_run_input)

    async def update_agent_run(self, agent_run: AgentRun):
        if self.client == 'http':
            return await update_agent_run_http(self.node_url, agent_run)
        else:
            return await update_agent_run_ws(self.routing_url, self.indirect_node_id, agent_run)

    async def read_storage(self, agent_run_id, output_dir, ipfs=False):
        if self.client == 'http':
            return await read_storage_http(self.node_url, agent_run_id, output_dir, ipfs)
        else:
            return await read_storage_ws(self.routing_url, self.indirect_node_id, agent_run_id, output_dir, ipfs)
    
    async def write_storage(self, storage_input: str, ipfs: bool = False, publish_to_ipns: bool = False, update_ipns_name: Optional[str] = None):
        if self.client == 'http':
            return await write_storage_http(self.node_url, storage_input, ipfs, publish_to_ipns, update_ipns_name)
        else:
            return await write_storage_ws(self.routing_url, self.indirect_node_id, storage_input, ipfs, publish_to_ipns, update_ipns_name)