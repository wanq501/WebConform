"""WebConform: decision-level conformance testing of multimodal web agents against operation semantics.

The package runs the test on any model behind an OpenAI-compatible chat API and scores the decisions:
    python -m webconform.run    a setting of the test on a test suite bundle, one decision per test case
    python -m webconform.score  violation rate, chance level and their ratio per relation
"""
__version__ = "1.0.0"
