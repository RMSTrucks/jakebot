"""Command line interface for testing JakeBot"""
import click
import logging
from typing import Optional

from .config import JakeBotConfig
from .ai_agents.commitment_detector import CommitmentDetector

@click.group()
def cli():
    """JakeBot CLI tools"""
    pass

@cli.command()
@click.argument('transcript_file', type=click.Path(exists=True))
def analyze_transcript(transcript_file: str):
    """Analyze a transcript file for commitments"""
    config = JakeBotConfig()
    detector = CommitmentDetector()
    
    with open(transcript_file) as f:
        transcript = f.read()
    
    commitments = detector.detect_commitments(transcript)
    
    click.echo("\nDetected Commitments:")
    for c in commitments:
        click.echo(f"\n- {c.description}")
        click.echo(f"  Due: {c.due_date}")
        click.echo(f"  System: {c.system}")
        click.echo(f"  Priority: {c.priority}")
        click.echo(f"  Requires Approval: {c.requires_approval}") 