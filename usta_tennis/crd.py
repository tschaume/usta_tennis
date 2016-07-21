from usta_tennis.utils import pretty_score

def crd(score):
    """CRD - Computer Rated Differential (numerical value for score)

    One way to assign a value to a specific score, is to count the number of
    service breaks and scale it to a value appropriate for NTRP ratings. For
    instance, at-level/true 4.5 players should populate the core of the 4.5
    interval. Defining the core of a 0.5-wide interval as its inner 90%, yields
    the range 4.05 - 4.45. An average upper 4.5 player would then correspond to
    a 4.35 rating and a lower 4.5 player to 4.15.

    A good scale for the CRD reflects the fact that an upper 4.5 player
    routinely beats a lower 4.5 player. A sensible choice for a routine but
    competitive win is a score of 6-3/6-3 or 6-3/6-2 [see below].

    The number of service breaks in these cases should hence be equivalent to
    the difference of 0.2 between an upper and a lower 4.5 player. A 6-3/6-3 win
    entails 3 service breaks whereas a 6-3/6-2 win could be counted as 3.5
    service breaks. Assigning a scaling factor of 0.06 for each additional
    service break is thus a good choice and results in CRDs of 0.18 and 0.21,
    respectively.

    In the CRD, the number of service breaks in the third set also counts half
    since the opponents are basically even but the loser of the third set
    doesn't get a chance to even out in a fourth.

    A match is considered competitive if the loser plays one competitive set (>=
    3 games) or scores at least 4 games in total. If this isn't the case, the
    outcome of the match would almost always be a non-competitive score
    regardless of how often they play each other.  Since neither player probably
    plays their best due to the non-competitiveness of the match, the score
    likely is inaccurate.

    In the worst case of a 6-0/6-0 score, it's tough to assess performance of
    either player at all without a game on the scoreboard for the loser. The
    loser might have been close to scoring a game in every game of the match or
    in none at all.

    It hence makes sense to treat 6-0/6-0 scores as outliers in the calculation
    of ratings and discard them. But we can use this score to estimate the score
    inaccuracy of a non-competitive match. In such a match, the winner scored 6
    service breaks, and an additional game for the loser would correspond to
    half a service break difference in the CRD, i.e. 0.03. Say the loser got
    close to winning one of the winner's 6 service games. The change in CRD
    value equivalent to this performance would be 0.03/6 = 0.005.  For
    non-competitive matches, the CRD is hence adjusted downward by 0.005 to not
    affect both the players ratings as much as two competitive sets [which would
    have been more fun for both].

    See http://web.archive.org/web/20051211104109/http://www.wetennis.com/rate.htm
    """
    if score == ['60', '60']:
        raise ValueError('{} should be ignored!'.format(pretty_score(score)))
    crd = 0 # computer rated differential (CRD)
    scf = 0.06 # scaling factor = CRD equivalent for one service break
    competitive_set = False # one competitive set played (> 2 games)
    glt = 0 # number of games scored by loser
    for i,s in enumerate(score):
        gw, gl = map(int, s) # games winner and loser
        nb = float(gw-gl)/2 # number of breaks
        crd += (nb/2 if i == 2 else nb) * scf # third set counts half
        glt += gl
        if i < 2 and gl > 2: # skip third set
            competitive_set = True
    return crd if competitive_set or glt > 3 else crd-scf/12
