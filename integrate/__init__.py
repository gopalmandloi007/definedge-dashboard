class ConnectToIntegrate:
    def login(self, *args, **kwargs):
        pass
    def set_session_keys(self, *args, **kwargs):
        pass

class IntegrateOrders:
    def __init__(self, conn):
        self.conn = conn
    def holdings(self):
        return {"data": []}  # Dummy data, real logic baad me
