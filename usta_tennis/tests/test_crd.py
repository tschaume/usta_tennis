from nose.tools import *
from usta_tennis.crd import crd

def test_crd():
    # 3-set matches (always CRD of 0.015)
    assert_almost_equals(crd(['75', '57', '10']), 0.015, places=3)
    assert_almost_equals(crd(['75', '06', '61']), 0.015, places=3)
    # competitive 2-set matches
    # one competitive set (>= 3 games) or
    # total >= 4 games
    assert_almost_equals(crd(['76', '76']), 0.06, places=2)
    assert_almost_equals(crd(['76', '75']), 0.09, places=2)
    assert_almost_equals(crd(['76', '64']), 0.09, places=2)
    assert_almost_equals(crd(['75', '64']), 0.12, places=2)
    assert_almost_equals(crd(['64', '64']), 0.12, places=2)
    assert_almost_equals(crd(['64', '63']), 0.15, places=2)
    assert_almost_equals(crd(['63', '63']), 0.18, places=2)
    assert_almost_equals(crd(['75', '62']), 0.18, places=2)
    assert_almost_equals(crd(['62', '63']), 0.21, places=2)
    assert_almost_equals(crd(['62', '62']), 0.24, places=2)
    assert_almost_equals(crd(['63', '61']), 0.24, places=2)
    assert_almost_equals(crd(['61', '63']), 0.24, places=2)
    assert_almost_equals(crd(['63', '60']), 0.27, places=2)
    assert_almost_equals(crd(['60', '63']), 0.27, places=2)
    # non-competitive matches
    assert_almost_equals(crd(['62', '61']), 0.265, places=3)
    assert_almost_equals(crd(['62', '60']), 0.295, places=3)
    assert_almost_equals(crd(['61', '61']), 0.295, places=3)
    assert_almost_equals(crd(['61', '60']), 0.325, places=3)
    assert_almost_equals(crd(['60', '60']), 0.355, places=3)
