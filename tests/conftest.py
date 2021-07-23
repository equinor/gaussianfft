try:
    import scipy.stats
except ImportError:
    # Importing it here avoids a segmentation fault when running the tests (specifically `test_simulate1d.py`)
    # For some reason, this happens if we importing it after the setup, and the tests before `test_chi2` are run.
    pass
