from time import sleep

import nrlib
import unittest
import numpy as np
from multiprocessing import Process, Queue, set_start_method


def create_realization():
    # Returns a 100 x 100 realization of a random field
    v = nrlib.variogram('exponential', 100.0, 50.0)
    s = nrlib.simulate(v, 100, 10.0, 100, 10.0)
    return np.array(s).reshape((100, 100), order='F')


def run_simulation_process(q, dt):
    # Sleep to enable different automatic seeding for different runs
    sleep(dt)
    s = create_realization()
    q.put((nrlib.seed(), s))


class TestMultiprocessSeeding(unittest.TestCase):
    def test_mp(self):
        """ Two random fields are generated in two different processes using the multiprocessing module. The purpose
        of this test is to show how automatic seed generation works for sub processes. """

        # Set start method if multiprocessing since the default is different on
        # Windows and Linux
        set_start_method('spawn')

        queue = Queue()
        # Set an arbitrary starting seed. This will never be used since simulation
        # is done in child processes
        t0_seed = 123
        nrlib.seed(t0_seed)
        p1 = Process(target=run_simulation_process, args=(queue, 0))
        # Sleep >1 second to ensure a different seed for the second process
        p2 = Process(target=run_simulation_process, args=(queue, 1.1))
        p1.start()
        p2.start()
        p1.join(2)
        p2.join(2)
        seed_1, sim_1 = queue.get()
        seed_2, sim_2 = queue.get()

        # Repeat simulation 1, no parallelism
        nrlib.seed(seed_1)
        seq_sim_1 = create_realization()

        # Repeat simulation 2, no parallelism
        nrlib.seed(seed_2)
        seq_sim_2 = create_realization()

        # None of the three seeds that have been used should be equal
        self.assertNotEqual(seed_1, seed_2)
        self.assertNotEqual(seed_1, t0_seed)
        self.assertNotEqual(seed_2, t0_seed)

        # Check that realizations are reproduced correctly
        self.assertTrue(np.all(np.allclose(seq_sim_1, sim_1)))
        self.assertTrue(np.all(np.allclose(seq_sim_2, sim_2)))


if __name__ == '__main__':
    unittest.main()
