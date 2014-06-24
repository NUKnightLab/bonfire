import os
import sys
from .twitter import lookup_users, get_friends
from .db import save_user, build_universe_mappings
from .config import get_universe_seed


def build_universe(universe, build_mappings=True):
    """Expand the universe from the seed user list in the universe file.
    Should only be called once every 15 minutes.

    Seed is currently limited to the first 14 users in the file. API threshold
    limit is 15 calls per 15 minutes, and we need an extra call for
    the initial request for seed user IDs. If we want a seed > 14, we will
    need to be sure not to exceed 15 hits/15 min.
    """
    if build_mappings:
        build_universe_mappings(universe)
    seed_usernames = get_universe_seed(universe)
    for user in lookup_users(universe, seed_usernames[:14]):
        save_user(universe, user)
        for friend_id in get_friends(universe, user.id):
            save_user(universe, { 'id': friend_id } )
