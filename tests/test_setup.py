import pytest
import os
from ctf import create_app


def test_setup():
    with pytest.raises(IOError):
        os.environ["CTF_CONFIG"] = "tests/configs/nx.json"
        create_app(test=True)

    with pytest.raises(ValueError):
        os.environ["CTF_CONFIG"] = "tests/configs/teapot.json"
        create_app(test=True)
