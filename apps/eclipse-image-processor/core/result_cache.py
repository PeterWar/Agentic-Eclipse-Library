"""In-process numerical result signatures, including every array-valued mask."""
import hashlib
import json
import numpy as np


def parameter_signature(parameters):
    digest = hashlib.sha256(b'pipeline-v2')
    for key, value in sorted(parameters.items()):
        digest.update(key.encode())
        if isinstance(value, np.ndarray):
            digest.update(str((value.shape, value.dtype.str)).encode())
            digest.update(np.ascontiguousarray(value).tobytes())
        else:
            digest.update(json.dumps(value, sort_keys=True, allow_nan=False).encode())
    return digest.hexdigest()
