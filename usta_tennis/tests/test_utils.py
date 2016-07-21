from nose.tools import *
from usta_tennis.utils import *

def test_nr_sets_completed():
    assert_equals(nr_sets_completed(['76', '64', '10']), 3)
    assert_equals(nr_sets_completed(['51']), 0)
    assert_equals(nr_sets_completed(['16', '75']), 2)

def test_pretty_score():
    assert_equals(pretty_score(['76', '64']), '7-6/6-4')

def test_is_bagel():
    assert_false(is_bagel(['76', '64']))
    assert_true(is_bagel(['60', '30']))
