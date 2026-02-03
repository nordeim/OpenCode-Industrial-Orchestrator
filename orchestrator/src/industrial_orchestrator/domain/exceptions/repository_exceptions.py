class RepositoryError(Exception): pass
class EntityNotFoundError(RepositoryError): pass
class EntityAlreadyExistsError(RepositoryError): pass
class OptimisticLockError(RepositoryError): pass
class DatabaseConnectionError(RepositoryError): pass
