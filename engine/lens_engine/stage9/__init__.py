"""Stage 9 only. The ONLY package allowed to pass allow_holdout=True to the loaders.

Nothing in Stage 8 imports this package. Calling it before the Stage 9 pre-registration
hash is published voids the sealed holdout (spec 4.1, R11), and every call is logged
to data/sealed/UNSEAL_LOG.txt by lens_engine.data.guard.
"""
