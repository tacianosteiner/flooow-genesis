"""Exact clock boundaries and recorded-sample integrity, not health authority."""
import io
import json
import unittest
import package_0090_native_100us as n


def fresh(origin, observer, emitter_clock='CLOCK_BOOTTIME', observer_clock='CLOCK_BOOTTIME'):
    return (emitter_clock == observer_clock == 'CLOCK_BOOTTIME'
            and isinstance(origin, int) and isinstance(observer, int)
            and 0 <= observer-origin <= 100000)


def validate_samples(data):
    n.q.require(len(data['samples'])==500,'Exact sample count')
    for sample in data['samples']:
        n.q.require(sample['work_valid'],'Mechanism work invalid')
        n.q.require(len(sample['participants'])==7,'Seven participants required')
        n.q.require(sorted(p['index'] for p in sample['participants'])==list(range(7)),'Exact distinct participant classes required')
        projection=[]
        for p in sample['participants']:
            t=p['t'];n.q.require(len(t)==11 and all(isinstance(v,int) and v>0 for v in t),'Missing clocks')
            n.q.require(t[0]<=t[1]<=t[2]<=t[3]<=t[4]<=t[5]<=t[6]<=t[7]<=t[9]<=t[10],'Event causal order')
            n.q.require(p['age_ns']==t[10]-t[3] and p['decision_age_ns']==t[9]-t[3],'Age/source mismatch')
            projection.append(fresh(t[3],t[10]))
        n.q.require(all(projection)==sample['consumer_under_100us'],'Clock projection differs from executable')


class Boundaries(unittest.TestCase):
    def test_99us(self):self.assertTrue(fresh(1,99001))
    def test_100us_inclusive(self):self.assertTrue(fresh(1,100001))
    def test_101us(self):self.assertFalse(fresh(1,101001))
    def test_one_ns_over_is_not_rounded(self):self.assertFalse(fresh(1,100002))
    def test_future(self):self.assertFalse(fresh(2,1))
    def test_clock_mixing(self):self.assertFalse(fresh(1,2,'CLOCK_REALTIME','CLOCK_BOOTTIME'))


if __name__=='__main__':
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Boundaries))
    (n.OUT/'clock-tests.txt').write_text(stream.getvalue(),encoding='utf-8')
    n.a.save(n.OUT,'clock-tests.json',{'tests':result.testsRun,'errors':len(result.errors),'failures':len(result.failures),'skipped':len(result.skipped)})
    print(stream.getvalue());raise SystemExit(0 if result.wasSuccessful() else 1)
