import pandas as pd
from sklearn.linear_model import LinearRegression, Lasso, LogisticRegression
from sklearn.ensemble import (
    RandomForestRegressor,
    RandomForestClassifier,
    AdaBoostRegressor,
    GradientBoostingRegressor
)
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import LabelEncoder

def encode_labels(df: pd.DataFrame, label_cols: list) -> pd.DataFrame:
    for col in label_cols:
        if col in df.columns and df[col].dtype == 'object':
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].fillna("missing"))
    return df

def train_models_pandas(df: pd.DataFrame, instructions: dict) -> dict:
    # Extract target column
    target_col = instructions.get('target_column', [None])[0]
    if not target_col or target_col not in df.columns:
        raise ValueError("Target column not specified or not in dataframe")

    label_encode_cols = instructions.get('label_encoding', [])
    # Label encode specified columns
    df = encode_labels(df, label_encode_cols)

    X = df.drop(columns=[target_col])
    y = df[target_col]

   # Get problem type from instructions
    problem_type = instructions.get('problem_type', None)[0]
    if problem_type not in ('classification', 'regression'):
        raise ValueError("Instructions must include 'problem_type' key with value 'classification' or 'regression'")
    

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=17
    )

    classification_models = {
        'LogisticRegression': LogisticRegression(max_iter=2000),
        'RandomForestClassifier': RandomForestClassifier(),
        'DecisionTreeClassifier': DecisionTreeClassifier(),
        'SVM': SVC(),
    }

    regression_models = {
        'GradientBoostingRegressor': GradientBoostingRegressor(),
        'LinearRegression': LinearRegression(),
        'RandomForestRegressor': RandomForestRegressor(),
        'DecisionTreeRegressor': DecisionTreeRegressor(),
        'XGBRegressor': XGBRegressor(),
        'CatBoostingRegressor': CatBoostRegressor(verbose=False),
        'AdaBoostRegressor': AdaBoostRegressor(),
        'Lasso': Lasso(),
    }

    classification_params = {
        'LogisticRegression': {'C': [0.1, 1, 10]},
        'RandomForestClassifier': {
            'criterion': ['gini', 'entropy'],
            'max_features': ['sqrt', 'log2', None],
            'n_estimators': [8, 16, 32, 64, 128, 256]
        },
        'DecisionTreeClassifier': {
            'criterion': ['gini', 'entropy'],
            'splitter': ['best', 'random'],
            'max_features': ['sqrt', 'log2', None],
        },
        'SVM': {'C': [0.1, 1, 10], 'kernel': ['rbf', 'linear']},
    }

    regression_params = {
        'LinearRegression': {},
        'GradientBoostingRegressor': {
            'learning_rate': [0.1, 0.01, 0.05, 0.001],
            'n_estimators': [8, 16, 32, 64, 128, 256]
        },
        'XGBRegressor': {
            'learning_rate': [0.1, 0.01, 0.05, 0.001],
            'n_estimators': [8, 16, 32, 64, 128, 256]
        },
        'CatBoostingRegressor': {
            'depth': [6, 8, 10],
            'learning_rate': [0.01, 0.05, 0.1],
            'iterations': [30, 50, 100]
        },
        'AdaBoostRegressor': {
            'learning_rate': [0.1, 0.01, 0.5, 0.001],
            'loss': ['linear', 'square', 'exponential'],
            'n_estimators': [8, 16, 32, 64, 128, 256]
        },
        'Lasso': {'alpha': [0.1, 1.0, 10]},
    }

    if problem_type == 'classification':
        models = classification_models
        params = classification_params
    else:
        models = regression_models
        params = regression_params

    best_models = {}
    for model_name, model in models.items():
        param_grid = params.get(model_name, {})
        if not param_grid:
            model.fit(X_train, y_train)
            score = model.score(X_test, y_test)
            best_models[model_name] = {'model': model, 'score': score}
            continue
        grid = GridSearchCV(model, param_grid, cv=5, n_jobs=-1, scoring=None)
        grid.fit(X_train, y_train)
        best_models[model_name] = {
            'best_estimator': grid.best_estimator_,
            'best_params': grid.best_params_,
            'best_score': grid.best_score_,
            'test_score': grid.best_estimator_.score(X_test, y_test)
        }

    return best_models

