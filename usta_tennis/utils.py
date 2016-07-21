def nr_sets_completed(score):
    return sum([
        bool(int(s[0]) >= 6 or int(s[1]) >= 6)
        if i < 2 else True
        for i,s in enumerate(score)
    ])

def pretty_score(score):
    return '/'.join(['-'.join(s) for s in score])

def is_bagel(score):
    return all([not int(s[1]) for s in score])

def pretty_ratings(ratings):
    return ['{0:.3f}'.format(r) for r in ratings]
