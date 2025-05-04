# Initial GPT-generated code (IGNORE)

#!/usr/bin/env python3
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.compose      import ColumnTransformer
from sklearn.pipeline     import Pipeline
from sklearn.impute       import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import Ridge
from sklearn.metrics      import mean_squared_error, r2_score

def main():
    # ── 1) Load data
    df = pd.read_csv("final_enriched_dataset.csv", low_memory=False)

    # ── 2) Split into parent vs. London
    parents = df[df["city"].isin(
        ["King County", "Melbourne", "New York", "Perth"]
    )].copy()
    london  = df[df["city"].str.lower() == "london"].copy()

    # ── 3) Features & targets
    X_par, y_par = parents.drop(columns="sale_price"), parents["sale_price"]
    X_lon, y_lon = london .drop(columns="sale_price"), london ["sale_price"]

    # ── 4) Fix mixed‐type categoricals
    cat_cols = X_par.select_dtypes(include=["object","category"]).columns
    X_par[cat_cols] = X_par[cat_cols].astype(str)
    X_lon[cat_cols] = X_lon[cat_cols].astype(str)

    # ── 5) London train/test split
    X_L_train, X_L_test, y_L_train, y_L_test = train_test_split(
        X_lon, y_lon, test_size=0.20, random_state=42
    )

    # ── 6) Build two separate preprocessors
    num_cols = X_par.select_dtypes(include=["int64","float64"]).columns

    preprocess_parent = ColumnTransformer([
        ("num", Pipeline([
            ("imp",   SimpleImputer(strategy="median")),
            ("scale", StandardScaler())
        ]), num_cols),
        ("cat", Pipeline([
            ("imp",   SimpleImputer(strategy="constant", fill_value="missing")),
            ("oh",    OneHotEncoder(handle_unknown="ignore"))
        ]), cat_cols),
    ], remainder="drop")

    preprocess_london = ColumnTransformer([
        ("num", Pipeline([
            ("imp",   SimpleImputer(strategy="median")),
            ("scale", StandardScaler())
        ]), num_cols),
        ("cat", Pipeline([
            ("imp",   SimpleImputer(strategy="constant", fill_value="missing")),
            ("oh",    OneHotEncoder(handle_unknown="ignore"))
        ]), cat_cols),
    ], remainder="drop")

    # ── 7) Teacher: Ridge on parent markets
    teacher = Pipeline([
        ("prep", preprocess_parent),
        ("reg",  Ridge(alpha=10.0))
    ])
    print("Training teacher on parent markets…")
    teacher.fit(X_par, y_par)

    # ── 8) Soft-labels: teacher predictions on London train
    z_T = teacher.predict(X_L_train)

    # ── 9) Pseudo-labels for joint loss
    alpha = 0.5
    y_pseudo = alpha * y_L_train.values + (1 - alpha) * z_T

    # ── 10) Student: Ridge on London with pseudo-labels
    student = Pipeline([
        ("prep", preprocess_london),
        ("reg",  Ridge(alpha=1.0))
    ])
    print("Training student on London (joint‐loss pseudo-labels)…")
    student.fit(X_L_train, y_pseudo)

    # ── 11) Evaluate on London test
    def report(name, model):
        preds = model.predict(X_L_test)
        rmse  = np.sqrt(mean_squared_error(y_L_test, preds))
        r2    = r2_score(y_L_test, preds)
        print(f"{name:<10} | RMSE: {rmse:,.0f}  R²: {r2:.3f}")

    print("\n=== Distillation Results on London Test ===")
    report("Teacher", teacher)
    report("Student", student)

if __name__ == "__main__":
    main()
