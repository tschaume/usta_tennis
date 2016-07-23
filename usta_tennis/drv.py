import pymongo, math, sys
from datetime import datetime
from usta_tennis.utils import *
from usta_tennis.crd import crd

client = pymongo.MongoClient('mongodb://localhost:27017')
players, matches = client['usta'].players, client['usta'].matches
tlsentries = client['usta'].tlsentries

def drv(year):
    """dynamic rating values for all matches and players"""
    dt = datetime(year, 1, 1)
    drv, missing_players = {}, []
    for imatch, match in enumerate(matches.find({'date': {'$gte': dt}}).sort('date')):
        for sd in ['singles', 'doubles']:
            for individual_match in match[sd]:
                skip = False
                score = individual_match['score']
                if score[0] == 'Double Default' or nr_sets_completed(score) < 2:
                    continue
                default = False
                dr = {}
                for wl in ['winner', 'loser']:
                    id_or_ids = individual_match[wl]
                    ids = id_or_ids if isinstance(id_or_ids, list) else [id_or_ids]
                    if None in ids:
                        default = True
                        break # default
                    for i in ids:
                        if i not in drv:
                            player = players.find_one({'_id': str(i)})
                            if player is None:
                                missing_players.append(i)
                                skip = True
                                break
                            drv[i] = [float(player['rating_level']) - 0.25] # TODO
                        if wl not in dr:
                            dr[wl] = drv[i][-1]
                        else:
                            # average dynamic ratings for doubles
                            dr[wl] = (dr[wl] + drv[i][-1]) / 2
                    if skip:
                        break
                if default or skip:
                    continue
                #print(individual_match)
                prd = dr['winner'] - dr['loser'] # Player Rating Differential
                #print('\tprd = {0:.3f}'.format(prd))
                rdd = crd(score) - prd # Rating Differential Discrepancy
                #print('\trdd = {0:.3f}'.format(rdd))
                for idx, wl in enumerate(['winner', 'loser']):
                    id_or_ids = individual_match[wl]
                    ids = id_or_ids if isinstance(id_or_ids, list) else [id_or_ids]
                    for i in ids:
                        ar = drv[i][-1] + (-1)**idx * rdd/2 # Adjusted Winner/Loser’s Rating (before averaging)
                        #print('\tar for {0} = {1:.4f}'.format(i, ar))
                        h = drv[i][-3:] # winner/loser's dynamic rating history (last three)
                        #print('\th for {} ='.format(i), ' '.join(['{0:.3f}'.format(r) for r in h]))
                        drv[i].append((sum(h) + ar) / (len(h) + 1)) # Dynamic Winner’s Rating
                        #print('\tdwr for {0} = {1:.3f}'.format(i, drv[i][-1]))
                    # adjust doubles partners' ratings after averaging to ensure
                    # same differential between partners as before
                    if len(ids) > 1:
                        i, j = ids
                        drv_diff_before = drv[i][-2] - drv[j][-2]
                        drv_diff_after = drv[i][-1] - drv[j][-1]
                        if not math.isclose(drv_diff_before, drv_diff_after, abs_tol=0.001):
                            drv_adjust = (drv_diff_before - drv_diff_after) / 2
                            drv[i][-1] += drv_adjust
                            drv[j][-1] -= drv_adjust
                            drv_diff_before = drv[i][-2] - drv[j][-2]
                            drv_diff_after = drv[i][-1] - drv[j][-1]
                            if not math.isclose(drv_diff_before, drv_diff_after, abs_tol=0.001):
                                raise ValueError(drv_diff_before, drv_diff_after)
        sys.stdout.write('\r{}'.format(imatch))
    print('\n', len(missing_players), players.count())
    return drv
