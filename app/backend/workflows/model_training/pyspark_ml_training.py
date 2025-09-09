import pandas as pd
from pyspark.sql import DataFrame
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml import Pipeline
from pyspark.ml.classification import (
    LogisticRegression, RandomForestClassifier, DecisionTreeClassifier, GBTClassifier, NaiveBayes
)
from pyspark.ml.regression import (
    LinearRegression, RandomForestRegressor, DecisionTreeRegressor, GBTRegressor
)
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, RegressionEvaluator


def train_models_spark(spark_df: DataFrame, instructions: dict):
    # -------------------------------
    # STEP 1: Extract target/problem type
    # -------------------------------
    target_col = instructions.get('target_column')
    if isinstance(target_col, list):
        target_col = target_col[0]
    if not target_col or target_col not in spark_df.columns:
        raise ValueError("Target column not specified or not found in dataframe")

    problem_type = instructions.get('problem_type')
    if isinstance(problem_type, list):
        problem_type = problem_type[0].lower()
    if problem_type not in ('classification', 'regression'):
        raise ValueError("Problem type must be 'classification' or 'regression'")

    print("✅ Detected problem type:", problem_type)

    # -------------------------------
    # STEP 2: Label encoding (categorical cols)
    # -------------------------------
    label_encode_cols = instructions.get('label_encoding', [])
    indexers = [
        StringIndexer(inputCol=col, outputCol=col + "_indexed", handleInvalid="keep")
        for col in label_encode_cols
    ]

    feature_cols = [c for c in spark_df.columns if c != target_col and c not in label_encode_cols]
    indexed_feature_cols = [col + "_indexed" for col in label_encode_cols]

    assembler = VectorAssembler(inputCols=feature_cols + indexed_feature_cols, outputCol="features")

    # Always index target for classification
    if problem_type == "classification":
        label_indexer = StringIndexer(inputCol=target_col, outputCol="label", handleInvalid="keep")
        label_col = "label"
    else:
        label_indexer = None
        label_col = target_col

    # -------------------------------
    # STEP 3: Define models & params
    # -------------------------------
    if problem_type == "classification":
        models = {
            "LogisticRegression": LogisticRegression(featuresCol="features", labelCol=label_col),
            "DecisionTreeClassifier": DecisionTreeClassifier(featuresCol="features", labelCol=label_col),
            "RandomForestClassifier": RandomForestClassifier(featuresCol="features", labelCol=label_col),
            "GBTClassifier": GBTClassifier(featuresCol="features", labelCol=label_col),
            "NaiveBayes": NaiveBayes(featuresCol="features", labelCol=label_col),
        }

        param_grids = {
            "LogisticRegression": ParamGridBuilder()
                .addGrid(models["LogisticRegression"].regParam, [0.01, 0.1, 1.0])
                .addGrid(models["LogisticRegression"].elasticNetParam, [0.0, 0.5, 1.0])
                .build(),
            "DecisionTreeClassifier": ParamGridBuilder()
                .addGrid(models["DecisionTreeClassifier"].maxDepth, [5, 10, 20])
                .addGrid(models["DecisionTreeClassifier"].maxBins, [32, 64])
                .build(),
            "RandomForestClassifier": ParamGridBuilder()
                .addGrid(models["RandomForestClassifier"].numTrees, [20, 50])
                .addGrid(models["RandomForestClassifier"].maxDepth, [5, 10])
                .build(),
            "GBTClassifier": ParamGridBuilder()
                .addGrid(models["GBTClassifier"].maxDepth, [3, 5])
                .addGrid(models["GBTClassifier"].maxIter, [20, 50])
                .build(),
            "NaiveBayes": ParamGridBuilder().build()  # not many tunable params
        }

        metrics_list = ["accuracy", "f1", "weightedPrecision", "weightedRecall"]

    else:
        models = {
            "LinearRegression": LinearRegression(featuresCol="features", labelCol=label_col),
            "DecisionTreeRegressor": DecisionTreeRegressor(featuresCol="features", labelCol=label_col),
            "RandomForestRegressor": RandomForestRegressor(featuresCol="features", labelCol=label_col),
            "GBTRegressor": GBTRegressor(featuresCol="features", labelCol=label_col),
        }

        param_grids = {
            "LinearRegression": ParamGridBuilder()
                .addGrid(models["LinearRegression"].regParam, [0.0, 0.1, 1.0])
                .addGrid(models["LinearRegression"].elasticNetParam, [0.0, 0.5, 1.0])
                .build(),
            "DecisionTreeRegressor": ParamGridBuilder()
                .addGrid(models["DecisionTreeRegressor"].maxDepth, [5, 10, 20])
                .addGrid(models["DecisionTreeRegressor"].maxBins, [32, 64])
                .build(),
            "RandomForestRegressor": ParamGridBuilder()
                .addGrid(models["RandomForestRegressor"].numTrees, [20, 50])
                .addGrid(models["RandomForestRegressor"].maxDepth, [5, 10])
                .build(),
            "GBTRegressor": ParamGridBuilder()
                .addGrid(models["GBTRegressor"].maxDepth, [3, 5])
                .addGrid(models["GBTRegressor"].maxIter, [20, 50])
                .build(),
        }

        metrics_list = ["rmse", "mae", "r2"]

    # -------------------------------
    # STEP 4: Train/test split
    # -------------------------------
    train_df, test_df = spark_df.randomSplit([0.8, 0.2], seed=42)

    # -------------------------------
    # STEP 5: Training loop
    # -------------------------------
    best_models = {}
    primary_metric_name = metrics_list[0]  # e.g., "accuracy" for classification, "rmse" for regression

    for name, model in models.items():
        print(f"🔄 Training {name}...")

        stages = indexers + [assembler]
        if label_indexer:
            stages.append(label_indexer)
        stages.append(model)

        pipeline = Pipeline(stages=stages)

        evaluator = (
            MulticlassClassificationEvaluator(labelCol=label_col, predictionCol="prediction")
            if problem_type == "classification"
            else RegressionEvaluator(labelCol=label_col, predictionCol="prediction")
        )

        cv = CrossValidator(
            estimator=pipeline,
            estimatorParamMaps=param_grids.get(name, ParamGridBuilder().build()),
            evaluator=evaluator,
            numFolds=3,
            parallelism=2
        )

        cv_model = cv.fit(train_df)
        predictions = cv_model.transform(test_df)

        # Compute all metrics
        model_metrics = {}
        for metric in metrics_list:
            eval_inst = (
                MulticlassClassificationEvaluator(labelCol=label_col, metricName=metric)
                if problem_type == "classification"
                else RegressionEvaluator(labelCol=label_col, metricName=metric)
            )
            model_metrics[metric] = eval_inst.evaluate(predictions)

        # Extract best model hyperparameters from last stage
        best_stage_model = cv_model.bestModel.stages[-1]
        best_params = {param.name: best_stage_model.getOrDefault(param)
                    for param in best_stage_model.extractParamMap()}

        # Primary metric
        best_metric_value = model_metrics[primary_metric_name]

        best_models[name] = {
            "best_estimator": cv_model.bestModel,
            "best_params": best_params,
            "metrics": model_metrics,
            "metric": best_metric_value
        }

        print(f"✅ {name} metrics:", model_metrics)

    # -------------------------------
    # Select the overall best model
    # -------------------------------
    if problem_type == "classification":
        # Higher is better
        overall_best_name = max(best_models, key=lambda x: best_models[x]["metric"])
    else:
        # Lower is better (e.g., RMSE, MAE)
        overall_best_name = min(best_models, key=lambda x: best_models[x]["metric"])

    overall_best_model = best_models[overall_best_name]

    print("\n🏆 Overall Best Model:", overall_best_name)
    print("Primary Metric:", overall_best_model["metric"])
    print("All Metrics:", overall_best_model["metrics"])
    print("Best Hyperparameters:", overall_best_model["best_params"])

    # Return only the best model
    return {overall_best_name: overall_best_model}

