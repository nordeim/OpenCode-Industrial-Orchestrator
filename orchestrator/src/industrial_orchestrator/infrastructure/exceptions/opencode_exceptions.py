class OpenCodeError(Exception): pass
class OpenCodeAPIError(OpenCodeError): pass
class OpenCodeConnectionError(OpenCodeError): pass
class OpenCodeTimeoutError(OpenCodeError): pass
class OpenCodeRateLimitError(OpenCodeError): pass
class OpenCodeSessionNotFoundError(OpenCodeError): pass
