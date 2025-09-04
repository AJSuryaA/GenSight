import os
import shutil
import subprocess
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form

from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


from app.backend.workflows.etl.pandas_processing import get_dataset_info as get_pandas_info
from app.backend.workflows.etl.pyspark_processing import get_dataset_info as get_pyspark_info

from app.backend.workflows.eda.pandas_eda import pandas_eda
from app.backend.workflows.eda.pyspark_eda import pyspark_eda
import pandas as pd
from pyspark.sql import SparkSession

from app.backend.workflows.eda.pandas_profiling_eda import generate_pandas_eda_report

from app.backend.workflows.eda.gpt_integration import create_eda_summary_prompt, call_gpt_api, parse_gpt_structured_response, create_eda_summary_prompt_spark
from app.backend.workflows.eda.data_cleaning_pyspark import clean_data_spark, save_cleaned_spark, drop_columns_spark, drop_empty_columns_spark 
import pandas as pd

from app.backend.workflows.eda.data_cleaning_pandas import clean_data, save_cleaned_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: run before app starts receiving requests
    ensure_hadoop_running()

    yield

    # Shutdown: run after app stops receiving requests (optional cleanup)
    # Put any cleanup code here if needed


app = FastAPI(lifespan=lifespan)

# Paths for frontend files (adjust if needed)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../frontend")
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

# Directory to save uploaded files temporarily before moving to data lake
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/reports", StaticFiles(directory="app/backend/workflows/eda/reports"), name="reports")

# Serve the upload page
@app.get("/")
async def read_index():
    return FileResponse(os.path.join(TEMPLATES_DIR, "index.html"))

def check_hadoop_running():
    try:
        result = subprocess.run(['jps'], capture_output=True, text=True)
        running_services = [line.split()[1] for line in result.stdout.strip().split('\n') if len(line.split()) > 1]

        required_services = ['NameNode', 'DataNode', 'ResourceManager', 'NodeManager']
        missing_services = [service for service in required_services if service not in running_services]

        if missing_services:
            print(f"Missing Hadoop services: {missing_services}")
            return False
        print("All essential Hadoop services are running.")
        return True
    except Exception as e:
        print(f"Error checking Hadoop services: {e}")
        return False


def start_hadoop_services():
    try:
        # Replace with your actual Hadoop sbin path
        hadoop_home = os.environ.get('HADOOP_HOME')
        hadoop_sbin_path = f'{hadoop_home}/sbin'
        subprocess.run(['bash', f'{hadoop_sbin_path}/start-dfs.sh'], check=True)
        subprocess.run(['bash', f'{hadoop_sbin_path}/start-yarn.sh'], check=True)
        print("Hadoop DFS and YARN started successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to start Hadoop services: {e}")


def ensure_hadoop_running():
    if not check_hadoop_running():
        print("Hadoop services not running. Starting services...")
        start_hadoop_services()
    else:
        print("Hadoop services already running.")

def choose_processing_mode(file_path, command_input=None):
    SIZE_THRESHOLD = 100 * 1024 * 1024  # 100MB
    if command_input:
        if command_input.strip() == "-f:p":
            return "pandas"
        elif command_input.strip() == "-f:ps":
            return "pyspark"

    file_size = os.path.getsize(file_path)
    if file_size <= SIZE_THRESHOLD:
        return "pandas"
    else:
        return "pyspark"

def upload_to_hdfs(local_file_path, hdfs_dir="/user/gen_sight/uploads"):
    try:
        subprocess.run(["hdfs", "dfs", "-mkdir", "-p", hdfs_dir], check=True)
        result = subprocess.run(
            ["hdfs", "dfs", "-put", "-f", local_file_path, hdfs_dir],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return os.path.join(hdfs_dir, os.path.basename(local_file_path))
    except subprocess.CalledProcessError as e:
        print(f"Error uploading to HDFS: {e.stderr}")
        raise
    


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), command: str = Form(None)):
    try:
        
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        await file.close()

        # Determine processing mode
        mode = choose_processing_mode(file_location, command)

        # Upload to HDFS
        print(f"Uploading file to HDFS: {file_location} => directory: /user/gen_sight/uploads")
        hdfs_path = upload_to_hdfs(file_location)
        print(f"File uploaded to HDFS path: {hdfs_path}")


        # Get dataset info based on processing mode
        if mode == "pandas":
            dataset_info = get_pandas_info(file_location)

            # Run EDA for pandas
            df = pd.read_csv(file_location)
            # report_file = generate_pandas_eda_report(df)
            # report_url = report_file.replace("app/backend", "app/backend/workflows/eda/reports")
             # Create EDA prompt
            prompt = create_eda_summary_prompt(df)
            # Call GPT API
            gpt_response = call_gpt_api(prompt)
            # Parse GPT response to get columns to drop
            structured_data = parse_gpt_structured_response(gpt_response)

            df_cleaned = clean_data(df, structured_data)
            save_cleaned_data(df_cleaned, "data.csv")
            # Drop columns from df
            # df_cleaned = drop_columns(df, cols_to_drop)
             # Save cleaned data if needed
            # cleaned_path = file_location.replace(".csv", "_cleaned.csv")
            # df_cleaned.to_csv(cleaned_path, index=False)
            print("sonar raw response:", gpt_response)
            print("\n\n"+"\n_______________________________________________________________________")
            print("Parsed GPT Data:", structured_data)
            print("\n\n"+"\n_______________________________________________________________________")
            
            

            pandas_eda(df)
            return JSONResponse({
                # other fields...
                # "eda_report_url": report_url,
                "original_columns": list(df.columns),
                # "columns_removed": cols_to_drop,
                # "cleaned_file_path": cleaned_path,
                "gpt_suggestions": gpt_response
            })
            

        elif mode == "pyspark":
            dataset_info = get_pyspark_info(hdfs_path)

            spark = SparkSession.builder.appName("EDA").getOrCreate()
            try:
                print("starrted_____________________1")
                sdf = spark.read.csv(hdfs_path, header=True, inferSchema=True)
                print("starrted_____________________2")
                if '_c0' in sdf.columns:
                    sdf = sdf.drop('_c0')
                print("starrted_____________________3")
                pyspark_eda(sdf)  # your existing EDA function
                print("starrted_____________________4")
                
                prompt = create_eda_summary_prompt_spark(sdf)
                gpt_response = call_gpt_api(prompt)
                structured_data = parse_gpt_structured_response(gpt_response)
                print("sonar raw response:", gpt_response)
                print("\n\n"+"\n_______________________________________________________________________")
                print("Parsed GPT Data:", structured_data)
                print("\n\n"+"\n_______________________________________________________________________")
                print("starrted_____________________5")
                # Clean Spark dataframe based on GPT instructions
                sdf_cleaned = clean_data_spark(sdf, structured_data)
                print("starrted_____________________6")
                hdfs_exact_file_path = "/user/gen_sight/uploads/data.csv"
                save_cleaned_spark(sdf_cleaned, hdfs_exact_file_path)

            except Exception as e:
                spark.stop()
                print(f"Error during PySpark processing: {e}")
                return JSONResponse(status_code=500, content={"error": str(e)})

            spark.stop()

            return JSONResponse({
                "filename": file.filename,
                "processing_mode": mode,
                "message": "File uploaded and cleaned successfully.",
                "local_path": file_location,
                "hdfs_path": hdfs_path,
                "dataset_info": dataset_info,
                "gpt_suggestions": gpt_response
            })


    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})