"""Concurrent calculation preserves ordering, cancellation and valid caches."""
from contextlib import redirect_stdout
import io
from threading import Barrier, Event, Lock
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np

from core.cancellation import cancellation_scope, check_cancelled, ProcessingCancelled
from core.layer_engine import LayerEngine
from core.parallelism import CPU_CORES, filter_cpu_budget, layer_workers


class ParallelLayerTests(unittest.TestCase):
    def setUp(self):
        self.source=np.arange(192,dtype=np.float32).reshape(12,16)
        self.params=dict(sx=8,sy=6,sr=2,mgn_enabled=True,mgn_str=100,mgn_opacity=70,
                         wow_enabled=True,wow_str=100,wow_opacity=80)
        self.display=dict(strength=4)
        self.quiet=redirect_stdout(io.StringIO());self.quiet.__enter__()

    def tearDown(self):
        self.quiet.__exit__(None,None,None)

    def layer_data(self,name):
        yy,xx=np.indices(self.source.shape)
        values=np.where((xx+yy)%2,50000,20000).astype(np.uint16)
        if name=='wow':values=65535-values
        return dict(image=values,alpha=np.full(values.shape,65535,np.uint16),mode='Overlay',mapping={})

    def test_parallel_work_finishes_out_of_order_but_composes_in_recipe_order(self):
        engine=LayerEngine();barrier=Barrier(2,timeout=3);second_done=Event()
        active=[];lock=Lock()
        def calculate(worker,source,params,name,variant):
            with lock:active.append((name,filter_cpu_budget()))
            barrier.wait()
            if name=='mgn':
                self.assertTrue(second_done.wait(3))
            else:second_done.set()
            return self.layer_data(name)
        with patch('core.layer_engine.layer_workers',return_value=2), \
             patch.object(engine,'_calculate',side_effect=calculate) as operation:
            actual=engine.render(Mock(),self.source,self.params,self.display)
            self.assertEqual(operation.call_count,2)
            # Recomposition and activation do not start a new numerical batch.
            engine.render(Mock(),self.source,dict(self.params,mgn_opacity=30),self.display)
            engine.render(Mock(),self.source,dict(self.params,mgn_enabled=False),self.display)
            engine.render(Mock(),self.source,self.params,self.display)
            self.assertEqual(operation.call_count,2)
        self.assertEqual({n for n,b in active},{'mgn','wow'})
        self.assertTrue(all(b==max(1,CPU_CORES//2) for n,b in active))
        serial=LayerEngine()
        with patch('core.layer_engine.layer_workers',return_value=1), \
             patch.object(serial,'_calculate',side_effect=lambda w,s,p,n,v:self.layer_data(n)):
            expected=serial.render(Mock(),self.source,self.params,self.display)
        np.testing.assert_array_equal(actual,expected)

    def test_external_cancellation_reaches_all_parallel_filters_and_no_cache_is_published(self):
        engine=LayerEngine();event=Event();barrier=Barrier(2,timeout=3)
        def calculate(worker,source,params,name,variant):
            barrier.wait()
            event.set()
            check_cancelled()
            self.fail('Cancellation token did not reach a filter thread')
        with patch('core.layer_engine.layer_workers',return_value=2), \
             patch.object(engine,'_calculate',side_effect=calculate):
            with self.assertRaises(ProcessingCancelled):
                with cancellation_scope(event):
                    engine.prepare(Mock(),self.source,self.params)
        self.assertFalse(engine.sources[id(self.source)][1])
        check_cancelled()  # caller's context was restored

    def test_failure_stops_other_running_filter_and_drains_threads(self):
        engine=LayerEngine();other_started=Event();other_stopped=Event()
        def calculate(worker,source,params,name,variant):
            if name=='mgn':
                self.assertTrue(other_started.wait(3))
                raise ValueError('filter failed')
            other_started.set()
            deadline=time.monotonic()+3
            try:
                while time.monotonic()<deadline:
                    check_cancelled()
                    other_stopped.wait(.01)
                self.fail('Sibling filter was not cancelled')
            finally:other_stopped.set()
        with patch('core.layer_engine.layer_workers',return_value=2), \
             patch.object(engine,'_calculate',side_effect=calculate):
            with self.assertRaisesRegex(ValueError,'filter failed'):
                engine.prepare(Mock(),self.source,self.params)
        self.assertTrue(other_stopped.is_set())
        self.assertFalse(engine.sources[id(self.source)][1])

    def test_native_concurrency_limits_and_unknown_memory_fallback(self):
        image=SimpleNamespace(size=3744*5608)
        def memory(name):return (24*1024**3//4096 if name=='SC_PHYS_PAGES' else 4096)
        with patch('core.parallelism.os.sysconf',side_effect=memory), \
             patch('core.parallelism.CPU_CORES',10):
            self.assertEqual(layer_workers(image,10),2)
            self.assertEqual(layer_workers(SimpleNamespace(size=640*427),10),4)
            self.assertEqual(layer_workers(image,1),1)
        with patch('core.parallelism.os.sysconf',side_effect=OSError('unknown')):
            self.assertEqual(layer_workers(image,10),1)
        with patch('core.parallelism.CPU_CORES',1):
            self.assertEqual(layer_workers(image,10),1)


if __name__=='__main__':unittest.main()
