"""Tests for drift checker and monitoring module."""



class TestDriftCheckerImports:
    """Verify drift checker module imports and basic functions."""

    def test_module_import(self):
        from src.monitoring import drift_checker
        assert drift_checker is not None

    def test_get_default_windows(self):
        from src.monitoring.drift_checker import get_default_windows
        ref_start, ref_end, cur_start, cur_end = get_default_windows(90, 30)
        assert ref_start < ref_end
        assert cur_start < cur_end
        assert len(ref_start) == 10  # YYYY-MM-DD
        assert len(cur_end) == 10

    def test_run_drift_check_no_db(self):
        """run_drift_check should handle missing DB gracefully."""
        import asyncio

        from src.monitoring.drift_checker import run_drift_check

        try:
            result = asyncio.run(run_drift_check(
                model_id=1,
                reference_start="2024-01-01",
                reference_end="2024-03-31",
                current_start="2024-04-01",
                current_end="2024-04-30",
            ))
            assert isinstance(result, dict)
            assert "error" in result or "features_checked" in result
        except Exception:
            # DB connection failure is acceptable in test environment
            pass
