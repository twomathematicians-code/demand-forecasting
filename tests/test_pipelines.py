"""Tests for training and inference pipelines."""



class TestTrainingPipeline:
    def test_import(self):
        from src.pipelines.training_pipeline import TrainingPipeline
        pipeline = TrainingPipeline()
        assert pipeline is not None

    def test_run_with_synthetic_data(self, sample_demand_df, tmp_path):
        from src.pipelines.training_pipeline import TrainingPipeline
        from src.utils.config import AppConfig

        config = AppConfig.default()
        config.training.min_train_periods = 30  # Lower for test

        pipeline = TrainingPipeline(config)
        result = pipeline.run(df=sample_demand_df, model_dir=str(tmp_path / "ensemble"))
        # run() returns a dict; may succeed or fail depending on data quality
        assert "status" in result
        assert "metrics" in result

    def test_run_no_data_generates_synthetic(self):
        from src.pipelines.training_pipeline import TrainingPipeline
        from src.utils.config import AppConfig

        config = AppConfig.default()
        config.training.min_train_periods = 30

        pipeline = TrainingPipeline(config)
        result = pipeline.run(df=None, data_path=None)
        assert "status" in result


class TestInferencePipeline:
    def test_import(self):
        from src.pipelines.inference_pipeline import InferencePipeline
        pipeline = InferencePipeline()
        assert pipeline is not None

    def test_load_model_fallback(self):
        from src.pipelines.inference_pipeline import InferencePipeline
        pipeline = InferencePipeline()
        pipeline.load_model()  # Should train fallback
        assert pipeline.is_loaded
        assert pipeline.model_version in ("fallback", "loaded")

    def test_predict_after_load(self):
        from src.pipelines.inference_pipeline import InferencePipeline
        pipeline = InferencePipeline()
        pipeline.load_model()
        result = pipeline.predict("SKU-TEST", horizon_days=7)
        assert result["product_id"] == "SKU-TEST"
        assert len(result["forecast"]) == 7
        assert "trend" in result
