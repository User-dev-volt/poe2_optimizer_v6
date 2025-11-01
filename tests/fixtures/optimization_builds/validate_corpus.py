"""
Validation script for optimization test corpus.

Checks:
1. All PoB codes are valid and parseable
2. Metadata accuracy (level, allocated points match parsed data)
3. Diversity criteria (class, level, archetype distribution)
4. Required field presence
5. Build ID uniqueness

Usage:
    python tests/fixtures/optimization_builds/validate_corpus.py

Author: Bob (Scrum Master) - Prep Sprint Task #4
Date: 2025-10-27
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Set

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from parsers.pob_parser import parse_pob_code
from parsers.exceptions import PoBParseError


class CorpusValidator:
    """Validates optimization test corpus."""

    def __init__(self, corpus_path: Path):
        self.corpus_path = corpus_path
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.corpus_data = None
        self.builds = []

    def load_corpus(self) -> bool:
        """Load and parse corpus.json"""
        try:
            with open(self.corpus_path, 'r', encoding='utf-8') as f:
                self.corpus_data = json.load(f)
            self.builds = self.corpus_data.get('builds', [])
            return True
        except FileNotFoundError:
            self.errors.append(f"Corpus file not found: {self.corpus_path}")
            return False
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False

    def validate_required_fields(self) -> None:
        """Check all builds have required fields."""
        required_fields = [
            'build_id', 'source', 'name', 'pob_code', 'character_class',
            'level', 'allocated_points', 'archetype', 'expected_improvement'
        ]

        for i, build in enumerate(self.builds):
            for field in required_fields:
                if field not in build:
                    self.errors.append(f"Build #{i+1} missing required field: {field}")
                elif not build[field]:  # Check for empty strings
                    self.errors.append(f"Build #{i+1} has empty field: {field}")

    def validate_pob_codes(self) -> Dict[str, any]:
        """Parse all PoB codes and verify metadata accuracy."""
        parse_results = {}

        for i, build in enumerate(self.builds):
            build_id = build.get('build_id', f'build-{i+1}')

            try:
                # Parse PoB code
                parsed_build = parse_pob_code(build['pob_code'])

                # Check metadata accuracy
                if parsed_build.level != build['level']:
                    self.errors.append(
                        f"{build_id}: Level mismatch "
                        f"(metadata={build['level']}, parsed={parsed_build.level})"
                    )

                if len(parsed_build.passive_nodes) != build['allocated_points']:
                    self.errors.append(
                        f"{build_id}: Allocated points mismatch "
                        f"(metadata={build['allocated_points']}, "
                        f"parsed={len(parsed_build.passive_nodes)})"
                    )

                if parsed_build.character_class.value != build['character_class']:
                    self.warnings.append(
                        f"{build_id}: Class mismatch "
                        f"(metadata={build['character_class']}, "
                        f"parsed={parsed_build.character_class.value})"
                    )

                parse_results[build_id] = {
                    'success': True,
                    'parsed_build': parsed_build
                }

            except PoBParseError as e:
                self.errors.append(f"{build_id}: PoB parse error - {e}")
                parse_results[build_id] = {'success': False, 'error': str(e)}
            except Exception as e:
                self.errors.append(f"{build_id}: Unexpected error - {e}")
                parse_results[build_id] = {'success': False, 'error': str(e)}

        return parse_results

    def validate_diversity(self) -> None:
        """Check diversity criteria (class, level, archetype)."""
        # Count distributions
        classes = Counter(b['character_class'] for b in self.builds)
        archetypes = Counter(b['archetype'] for b in self.builds)
        sources = Counter(b['source'] for b in self.builds)

        # Level distribution
        level_ranges = defaultdict(int)
        for build in self.builds:
            level = build['level']
            if level < 61:
                level_ranges['low'] += 1
            elif level < 81:
                level_ranges['mid'] += 1
            elif level < 96:
                level_ranges['high'] += 1
            else:
                level_ranges['max'] += 1

        # Improvement potential
        improvements = Counter(b['expected_improvement'] for b in self.builds)

        # Report diversity
        print("\n📊 Diversity Analysis")
        print("=" * 60)

        print(f"\n**Class Distribution** (target: 2-3 per class):")
        for cls, count in classes.most_common():
            status = "✅" if count >= 2 else "⚠️"
            print(f"  {status} {cls}: {count}")

        print(f"\n**Level Distribution:**")
        print(f"  Low (40-60): {level_ranges['low']} (target: 3-5)")
        print(f"  Mid (61-80): {level_ranges['mid']} (target: 5-8)")
        print(f"  High (81-95): {level_ranges['high']} (target: 8-12)")
        print(f"  Max (96-100): {level_ranges['max']} (target: 2-5)")

        print(f"\n**Archetype Distribution:**")
        for archetype, count in archetypes.most_common():
            print(f"  {archetype}: {count}")

        print(f"\n**Source Distribution:**")
        for source, count in sources.most_common():
            print(f"  {source}: {count}")

        print(f"\n**Expected Improvement Distribution:**")
        for improvement, count in improvements.most_common():
            print(f"  {improvement}: {count}")

        # Warnings for low diversity
        if len(classes) < 7:
            self.warnings.append(f"Only {len(classes)}/7 classes represented")

        if level_ranges['mid'] < 5:
            self.warnings.append("Insufficient mid-level builds (61-80)")

        if sources.get('maxroll', 0) < 10:
            self.warnings.append("Target is 10-15 Maxroll builds")

    def validate_uniqueness(self) -> None:
        """Check build_id uniqueness."""
        build_ids: Set[str] = set()
        duplicates: List[str] = []

        for build in self.builds:
            build_id = build.get('build_id')
            if build_id in build_ids:
                duplicates.append(build_id)
            build_ids.add(build_id)

        if duplicates:
            self.errors.append(f"Duplicate build IDs: {', '.join(duplicates)}")

    def run(self) -> bool:
        """Run all validation checks."""
        print("🔍 Validating Optimization Test Corpus")
        print("=" * 60)

        # Load corpus
        if not self.load_corpus():
            self.print_results()
            return False

        build_count = len(self.builds)
        target_count = self.corpus_data.get('target_build_count', 25)

        print(f"\n📦 Corpus Status:")
        print(f"  Builds found: {build_count}")
        print(f"  Target: {target_count}")
        print(f"  Completion: {(build_count / target_count) * 100:.0f}%")

        if build_count == 0:
            self.errors.append("Corpus is empty - no builds found")
            self.print_results()
            return False

        # Run validation checks
        print("\n🔧 Running Validation Checks...")
        self.validate_required_fields()
        self.validate_uniqueness()
        parse_results = self.validate_pob_codes()
        self.validate_diversity()

        # Print results
        self.print_results()

        return len(self.errors) == 0

    def print_results(self) -> None:
        """Print validation results."""
        print("\n" + "=" * 60)
        print("📋 Validation Results")
        print("=" * 60)

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All validation checks PASSED!")
            print("   Corpus is ready for Epic 2 testing.")
        elif not self.errors:
            print("\n⚠️ Validation PASSED with warnings.")
            print("   Corpus is usable but could be improved.")
        else:
            print("\n❌ Validation FAILED.")
            print("   Fix errors before using corpus.")


def main():
    """Main entry point."""
    corpus_file = Path(__file__).parent / "corpus.json"
    validator = CorpusValidator(corpus_file)
    success = validator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
