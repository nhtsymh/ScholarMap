from datetime import date
from scholarmap.models import Paper
from scholarmap.ranking.common import impact_percentiles, age_normalized_impact


def test_age_normalized_rewards_fast_new_impact():
    old=Paper(id="o",title="old",publication_date=date(2020,1,1),cited_by_count=100)
    new=Paper(id="n",title="new",publication_date=date(2025,12,1),cited_by_count=80)
    asof=date(2026,1,1)
    assert age_normalized_impact(new,asof) > age_normalized_impact(old,asof)

def test_percentile_is_topic_age_local():
    ps=[Paper(id=str(i),title=str(i),publication_date=date(2025,1,1),cited_by_count=i) for i in range(1,6)]
    r=impact_percentiles(ps,date(2025,6,1))
    assert r["5"]==100.0
    assert r["1"] < r["5"]
