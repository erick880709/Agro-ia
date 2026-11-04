class CreditWorker:
    def __init__(self):
        self.running = False
        self.balance = 0
        self.processed = set()

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def handle(self, message_id, amount):
        if not self.running:
            raise RuntimeError('worker is stopped')
        self.balance += amount
        self.processed.add(message_id)
        return self.balance
