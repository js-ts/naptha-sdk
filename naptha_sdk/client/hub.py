import jwt
import os
from naptha_sdk.utils import add_credentials_to_env, get_logger
from surrealdb import Surreal
import traceback
from typing import Dict, List, Optional, Tuple

logger = get_logger(__name__)


class Hub:
    """The Hub class is the entry point into Naptha AI Hub."""

    def __init__(self, hub_url, public_key, *args, **kwargs):
        self.hub_url = hub_url
        self.public_key = public_key
        self.ns = "naptha"
        self.db = "naptha"
        self.surrealdb = Surreal(hub_url)
        self.is_authenticated = False
        self.user_id = None
        self.token = None
        
        logger.info(f"Hub URL: {hub_url}")


    def _decode_token(self, token: str) -> str:
        return jwt.decode(token, options={"verify_signature": False})["ID"]

    async def signin(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
        try:
            await self.surrealdb.connect()
            await self.surrealdb.use(namespace=self.ns, database=self.db)
            print("Signing in to hub with username: ", username)
            user = await self.surrealdb.signin(
                {
                    "NS": self.ns,
                    "DB": self.db,
                    "SC": "user",
                    "username": username,
                    "password": password,
                },
            )
            self.user_id = self._decode_token(user)
            self.token = user
            self.is_authenticated = True
            print("User ID: ", self.user_id)
            return True, user, self.user_id
        except Exception as e:
            print(f"Authentication failed: {e}")
            print("Full traceback: ", traceback.format_exc())
            return False, None, None

    async def loop_signup(self) -> Tuple[bool, Optional[str], Optional[str]]:
        while True:
            username = input("Enter username: ")
            password = input("Enter password: ")
            try:
                await self.surrealdb.connect()
                await self.surrealdb.use(namespace=self.ns, database=self.db)
                user = await self.surrealdb.signup(
                    {
                        "NS": self.ns,
                        "DB": self.db,
                        "SC": "user",
                        "name": username,
                        "username": username,
                        "password": password,
                        "invite": "DZHA4ZTK",
                    }
                )
                if user:
                    success, user, user_id = await self.signin(username, password)
                    add_credentials_to_env(username, password)
                    return success, user, user_id
                else:
                    print("Failed to create user. Please try again.")
            except Exception as e:
                print(f"Error creating user: {e}")
                print("Please try again.")

    async def get_user(self, user_id: str) -> Optional[Dict]:
        return await self.surrealdb.select(user_id)

    async def get_credits(self) -> List:
        user = await self.get_user(self.user_id)
        return user['credits']

    async def get_node(self, node_id: str) -> Optional[Dict]:
        return await self.surrealdb.select(node_id)

    async def list_nodes(self) -> List:
        nodes = await self.surrealdb.query("SELECT * FROM node;")
        return nodes[0]['result']

    async def list_modules(self, module_name=None) -> List:
        if not module_name:
            modules = await self.surrealdb.query("SELECT * FROM module;")
            return modules[0]['result']
        else:
            module = await self.surrealdb.query("SELECT * FROM module WHERE id=$module_name;", {"module_name": module_name})
            return module[0]['result'][0]

    async def delete_module(self, module_id: str) -> Tuple[bool, Optional[Dict]]:
        if ":" not in module_id:
            module_id = f"module:{module_id}".strip()
        print(f"Deleting module: {module_id}")
        success = await self.surrealdb.delete(module_id)
        if success:
            print("Deleted module")
        else:
            print("Failed to delete module")
        return success

    async def create_module(self, module_config: Dict) -> Tuple[bool, Optional[Dict]]:
        if not module_config.get('id'):
            return await self.surrealdb.create("module", module_config)
        else:
            return await self.surrealdb.create(module_config.pop('id'), module_config)

    async def list_tasks(self) -> List:
        tasks = await self.surrealdb.query("SELECT * FROM lot;")
        return tasks[0]['result']

    async def list_rfps(self) -> List:
        rfps = await self.surrealdb.query("SELECT * FROM auction;")
        return rfps[0]['result']

    async def list_rfps_from_consumer(self, consumer: Dict) -> List:
        proposals = await self.surrealdb.query("SELECT * FROM auction WHERE node=$node;", consumer)
        proposals = proposals[0]['result']
        return proposals

    async def submit_proposal(self, proposal: Dict) -> Tuple[bool, Optional[Dict]]:
        proposal = await self.surrealdb.query("RELATE $me->requests_to_bid_on->$auction SET amount=1.0;", proposal)
        return proposal[0]['result'][0]

    def list_active_proposals(self):
        pass

    async def list_accepted_proposals(self, plan_id=None) -> List:
        if not plan_id:
            proposals = await self.surrealdb.query("SELECT * FROM wins WHERE in=$user;", {"user": self.user_id})
            return proposals[0]['result']
        else:
            proposals = await self.surrealdb.query("SELECT * FROM wins WHERE in=$user AND out=$plan;", {"user": self.user_id, "plan": plan_id})
            return proposals[0]['result'][0]
