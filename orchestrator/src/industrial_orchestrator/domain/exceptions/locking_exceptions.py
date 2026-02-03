class LockingError(Exception): pass
class LockAcquisitionError(LockingError): pass
class LockTimeoutError(LockingError): pass
class LockNotOwnedError(LockingError): pass
class DeadlockDetectedError(LockingError): pass
