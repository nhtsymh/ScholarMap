import sys
from scholarmap import cli

def test_cli_demo(monkeypatch,capsys):
    monkeypatch.setattr(sys,'argv',['scholarmap','continual learning','--from','2025-01','--to','2026-07','--limit','1'])
    cli.main()
    out=capsys.readouterr().out
    assert 'Top Conference Papers' in out
    assert 'Continual Adaptation' in out
