from usta_tennis.utils import pretty_score

def crd(score):
    """CRD - Computer Rated Differential (numerical value for score)

    One way to assign a value to a specific score, is to calculate the
    difference in games and scale it to a value appropriate for NTRP ratings.
    For instance, at-level/true 4.5 players should populate the core of the 4.5
    interval. Defining the core of a 0.5-wide interval as its inner 90%, yields
    the range 4.05 - 4.45. An average upper 4.5 player would then correspond to
    a 4.35 rating and a lower 4.5 player to 4.15.

    A good scale for the CRD reflects the fact that an upper 4.5 player
    routinely beats a lower 4.5 player. A sensible choice for a routine but
    competitive win is a score of 6-3/6-3 or 6-3/6-2 [see below].

    The differences in games in these cases should hence be approx. equivalent
    to the difference of 0.2 between an upper and a lower 4.5 player. Assigning
    a scaling factor of 0.03 for each additional game is thus a good choice and
    results in CRDs of 0.18 and 0.21, respectively.

    In the CRD, the difference in games in the third set also counts half
    since the opponents are basically even but the loser of the third set
    doesn't get a chance to even out in a fourth. Also, the USTA only records
    a score of 1-0 for a won third set regardless of whether a full third or a
    super-tiebreak was played. Without any further information, the according
    CRD for a three-setter should not be more than the closest two-setter but
    instead consider the two opponents even with a slight edge for the winner.
    Ignoring the specific scores of the first two sets, and counting the
    super-tiebreak as half a game, namely with a CRD of 0.015, seems fair.

    A match is considered competitive if the loser plays one competitive set (>=
    3 games) or scores at least 4 games in total. If this isn't the case, the
    outcome of the match would almost always be a non-competitive score
    regardless of how often they play each other. Since neither player probably
    plays their best due to the non-competitiveness of the match, the score
    likely is inaccurate.

    In the worst case of a 6-0/6-0 score, it's tough to assess performance of
    either player at all without a game on the scoreboard for the loser. The
    loser might have been close to scoring a game in every game of the match or
    in none at all.

    However, we can use this score to estimate the score inaccuracy of a
    non-competitive match. An additional game for the loser would correspond to
    difference in CRD of 0.03. Say the loser got close to winning one of his 6
    service games. The change in CRD value equivalent to this performance would
    be 0.03/6 = 0.005. For non-competitive matches, the CRD is hence adjusted
    downward by 0.005 to not affect both the players ratings as much as two
    competitive sets [which would have been more fun for both].

    See http://web.archive.org/web/20051211104109/http://www.wetennis.com/rate.htm
    """
    crd = 0 # computer rated differential (CRD)
    scf = 0.03 # scaling factor = CRD equivalent for one game
    if len(score) > 2: # 3-set match
        return scf/2 # recorded as 1-0
    else:
        competitive_set = False # one competitive set played (> 2 games)
        glt = 0 # number of games scored by loser
        for i,s in enumerate(score):
            gw, gl = map(int, s) # games winner and loser
            crd += (gw-gl)*scf # CRD based on difference in games
            glt += gl
            if gl > 2:
                competitive_set = True
        if competitive_set or glt > 3:
            return crd
        else:
            return crd-scf/6
