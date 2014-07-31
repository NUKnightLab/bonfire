import os
import sys
from collections import Counter
from .twitter import lookup_users, get_friends
from .db import build_universe_mappings, get_user_ids, save_user, delete_user
from .config import get_universe_seed


def build_universe(universe, build_mappings=True):
    """Expand the universe from the seed user list in the universe file.
    Should only be called once every 15 minutes.

    This command also functions as an update of a universe.

    Seed is currently limited to the first 14 users in the file. API threshold
    limit is 15 calls per 15 minutes, and we need an extra call for
    the initial request for seed user IDs. If we want a seed > 14, we will
    need to be sure not to exceed 15 hits/15 min.
    """
    if build_mappings:
        build_universe_mappings(universe)
    seed_usernames = get_universe_seed(universe)

    authorities = lookup_users(universe, seed_usernames[:14])
    authorities_ids = set([a.id_str for a in authorities])
    # Make a flat list of all the authorities and their friends for tallying weights
    all_citizens = list(authorities_ids) + [item for sublist in
        [get_friends(universe, authority_id) for authority_id in authorities_ids]
        for item in sublist]

    # Now run the weight tally
    # Weight is determined by the percentage of authorities who follow the user
    counter = Counter()
    for citizen_id in all_citizens:
        counter[citizen_id] += 1
    for citizen_id, num_follows in counter.items():
        if citizen_id in authorities_ids:
            # we want to save the full user object since we have it
            user = filter(lambda a: a.id_str == citizen_id, authorities)[0]
            # birdy returns a read-only object which we want to write to, so:
            user = dict(user)
            user['id'] = user['id_str']
        else:
            user = {'id': citizen_id}

        user['weight'] = float(num_follows) / float(len(authorities_ids))
        save_user(universe, user)

    # Clean up any users that used to be in the universe.
    obsolete_users = set(get_user_ids(universe)) - set(all_citizens)
    for user in obsolete_users:
        delete_user(universe, user)
