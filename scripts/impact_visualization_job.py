#!/usr/bin/env python3
"""
Impact Visualization Spark Job
Demonstrates processing lineage data for impact analysis using PySpark.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lit, sum as _sum
import os

def main():
    # Initialize Spark session
    spark = SparkSession.builder \
        .appName("ImpactVisualizationJob") \
        .master("local[*]") \
        .getOrCreate()

    # Define paths
    input_path = "data/tables/dependencies.csv"
    output_path = "output/impact_results"

    # Read input data
    df = spark.read.option("header", "true").csv(input_path)
    print("Input data:")
    df.show()

    # Example impact analysis: count downstream dependencies per source
    impact_df = df.groupBy("source") \
        .agg(_sum(when(col("target").isNotNull(), 1).otherwise(0)).alias("impact_count")) \
        .orderBy(col("impact_count").desc())

    print("Impact analysis results:")
    impact_df.show()

    # Write results
    impact_df.coalesce(1).write.mode("overwrite").option("header", "true").csv(output_path)
    print(f"Results written to {output_path}")

    spark.stop()

if __name__ == "__main__":
    main()