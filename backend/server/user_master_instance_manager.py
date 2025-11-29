import asyncio

class UserMasterInstanceManager:
    def __init__(self):
        self._master_instances = {}
        self._lock = asyncio.Lock()
    
    async def add_user(self, user_id, master_instance):
        async with self._lock:
            self._master_instances[user_id] = master_instance
    
    async def remove_user(self, user_id):
        async with self._lock:
            if user_id in self._master_instances:
                del self._master_instances[user_id]
    
    # This will return either True or False
    async def check_if_user_exists(self, user_id):
        async with self._lock:
            return user_id in self._master_instances

    async def get_master_instance(self, user_id):
        async with self._lock:
            return self._master_instances.get(user_id, None)