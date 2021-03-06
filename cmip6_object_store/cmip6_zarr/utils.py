import json
import os
import uuid

import s3fs
import xarray as xr

from ..config import CONFIG
from .pickle_store import PickleStore

known_pickles = ["zarr", "error", "verify"]
verification_status = ["VERIFIED", "FAILED"]


def get_credentials(creds_file=None):

    if not creds_file:
        creds_file = CONFIG["store"]["credentials_file"]

    with open(creds_file) as f:
        creds = json.load(f)

    return creds


def get_uuid():
    _uuid = uuid.uuid4()
    return _uuid


def get_var_id(dataset_id, project):
    var_index = CONFIG[f"project:{project}"]["var_index"]
    return dataset_id.split(".")[var_index]


def create_dir(dr):
    if not os.path.isdir(dr):
        os.makedirs(dr)


def get_pickle_store(store_type, project):
    """
    Return a pickle store of type: `store_type`.
    Pickle store types can be any listed in: `known_pickles`

    Args:
        store_type ([string]): pickle type
        project ([string]): project
    """
    if store_type not in known_pickles:
        raise KeyError(f"Pickle store type not known: {store_type}")

    _config = CONFIG[f"project:{project}"]
    return PickleStore(_config[f"{store_type}_pickle"])


def split_string_at(s, sep, indx):
    items = s.split(sep)
    first, last = sep.join(items[:indx]), sep.join(items[indx:])
    return first, last


def to_dataset_id(path, project="cmip6"):
    items = path.replace("/", ".").split(".")
    if items[-1].endswith(".nc") or items[-1] == "zarr":
        items = items[:-1]

    n_facets = CONFIG[f"project:{project}"]["n_facets"]
    return ".".join(items[-n_facets:])


def get_zarr_url(path):
    dataset_id = to_dataset_id(path)
    zarr_path = "/".join(split_string_at(dataset_id, ".", 4)) + ".zarr"

    prefix = CONFIG["store"]["endpoint_url"]
    return f"{prefix}{zarr_path}"


def read_zarr(path, **kwargs):
    dataset_id = to_dataset_id(path)
    zarr_path = "/".join(split_string_at(dataset_id, ".", 4)) + ".zarr"

    endpoint_url = CONFIG["store"]["endpoint_url"]
    jasmin_s3 = s3fs.S3FileSystem(
        anon=True, client_kwargs={"endpoint_url": endpoint_url}
    )

    s3_store = s3fs.S3Map(root=zarr_path, s3=jasmin_s3)
    ds = xr.open_zarr(store=s3_store, consolidated=True, **kwargs)
    return ds


def get_archive_path(path, project="cmip6"):
    dataset_id = to_dataset_id(path)
    archive_dir = CONFIG[f"project:{project}"]["archive_dir"]

    return os.path.join(archive_dir, dataset_id.replace(".", "/"))
