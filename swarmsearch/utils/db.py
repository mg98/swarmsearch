import lmdb
import pickle
import time
import random
from swarmsearch.dart.types import ClickThroughRecord
import numpy as np

def retrieve(db_name: str, id: str, max_retries=8) -> np.ndarray:
    retries = 0
    while retries < max_retries:
        try:
            with lmdb.open(db_name, readonly=True, lock=False) as db:
                with db.begin() as txn:
                    data = txn.get(str(id).encode())
                    if data is None:
                        # warnings.warn(f"No embedding found for {id} in {db_name}")
                        return None
                    return pickle.loads(data)
        except lmdb.Error as e:
            retries += 1
            if retries >= max_retries:
                raise
            # Exponential backoff with jitter
            sleep_time = (2 ** retries) * 0.1 + random.uniform(0, 0.1)
            print(f"LMDB error: {e}. DB: {db_name}. ID: {id}. Retrying in {sleep_time:.2f}s...")
            time.sleep(sleep_time)

def get_doc_embedding(doc_id) -> np.ndarray:
    return retrieve('data/doc_embeddings.lmdb', doc_id)

def get_query_embedding(query_id) -> np.ndarray:
    return retrieve('data/query_embeddings.lmdb', query_id)

def get_user_embedding(user_id) -> np.ndarray:
    return retrieve('data/user_embeddings.lmdb', user_id)

def get_ctrs(user_id: str) -> list[ClickThroughRecord]:
    ctrs = retrieve('data/ctrs.lmdb', user_id)
    if ctrs is None:
        return None
    return [ ClickThroughRecord.from_array(ctr) for ctr in ctrs ]

def get_ctrs_from_users(user_ids: list[str]) -> list:
    all_ctrs = []
    for user_id in user_ids:
        ctrs = get_ctrs(user_id)
        if ctrs is not None:
            all_ctrs.extend(ctrs)
    random.shuffle(all_ctrs)
    return all_ctrs